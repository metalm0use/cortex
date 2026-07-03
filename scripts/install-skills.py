#!/usr/bin/env python3
"""Interactive and scripted Cortex skill installer."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
META_SCRIPTS = ROOT / "skills" / "meta" / "scripts"
sys.path.insert(0, str(META_SCRIPTS))

import lint_skill  # noqa: E402


CORE_DOMAIN = "meta"
AGENTS = ("codex", "claude", "cursor")
SCOPES = ("global", "project")
MODES = ("wrapper", "symlink", "copy")
ACTIONS = ("install", "status", "sync", "repair", "uninstall", "cleanup")
METADATA_FILE = ".cortex-metadata.json"
GENERATOR_VERSION = 8
RESOURCE_DIR_NAMES = ("assets", "references", "scripts", "vendor")

# Vendor-specific routing maps. Cortex skill frontmatter stays model-agnostic
# (capability classes thinking/execution/reference); these tables map a skill's
# routing class to a model alias per agent. Upgrade-only by default: judgment
# skills bump to Opus, mechanical skills drop to Haiku, and ordinary domain
# skills inherit the session model so they never silently downgrade. "inherit"
# (or null) means "emit no model line", i.e. keep whatever model the session is
# already using. Only the Claude adapter consumes this today.
DEFAULT_MODEL_ROUTING: dict[str, dict[str, str]] = {
    "claude": {
        "thinking": "opus",
        "execution": "haiku",
        "reference": "inherit",
    },
}
# Teams change this decision by editing the committed config file below and
# re-running a sync; the built-in default is used when the file is absent.
MODEL_ROUTING_FILE = ROOT / "config" / "model-routing.json"
VALID_MODEL_ALIASES = {"opus", "sonnet", "haiku", "fable", "inherit"}
INHERIT_VALUES = {"inherit", "", None}

_MODEL_ROUTING_CACHE: dict[str, dict[str, str]] | None = None


def build_model_routing(raw: dict) -> dict[str, dict[str, str]]:
    """Validate raw routing config and merge it over the built-in default.

    Raw shape is {agent: {routing_class: model_alias}}. Values must be a known
    model alias (opus/sonnet/haiku/fable/inherit) or null. Partial files are
    allowed; unspecified agents and classes keep their defaults.
    """
    routing = {agent: dict(classes) for agent, classes in DEFAULT_MODEL_ROUTING.items()}
    if not isinstance(raw, dict):
        raise SystemExit(f"ERROR: model routing config must be a JSON object: {MODEL_ROUTING_FILE}")
    for agent, classes in raw.items():
        if not isinstance(classes, dict):
            raise SystemExit(f"ERROR: model routing for {agent!r} must be a JSON object: {MODEL_ROUTING_FILE}")
        merged = dict(routing.get(agent, {}))
        for routing_class, value in classes.items():
            normalized = "inherit" if value in INHERIT_VALUES else value
            if normalized not in VALID_MODEL_ALIASES:
                raise SystemExit(
                    f"ERROR: invalid model {value!r} for {agent}/{routing_class} in {MODEL_ROUTING_FILE}; "
                    f"use one of: {', '.join(sorted(VALID_MODEL_ALIASES))} or null"
                )
            merged[routing_class] = normalized
        routing[agent] = merged
    return routing


def model_routing() -> dict[str, dict[str, str]]:
    """Load the routing config once, falling back to the built-in default."""
    global _MODEL_ROUTING_CACHE
    if _MODEL_ROUTING_CACHE is None:
        if MODEL_ROUTING_FILE.exists():
            try:
                raw = json.loads(MODEL_ROUTING_FILE.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise SystemExit(f"ERROR: could not read model routing config {MODEL_ROUTING_FILE}: {exc}") from exc
            _MODEL_ROUTING_CACHE = build_model_routing(raw)
        else:
            _MODEL_ROUTING_CACHE = build_model_routing({})
    return _MODEL_ROUTING_CACHE


def model_for_class(routing_class: str, agent: str, routing: dict[str, dict[str, str]] | None = None) -> str | None:
    """Map a routing class to a model for an agent, or None to inherit.

    Only the Claude adapter emits a model selection today; other agents read the
    routing metadata as advisory and inherit the session model.
    """
    if agent != "claude":
        return None
    routing = routing if routing is not None else model_routing()
    value = routing.get(agent, {}).get(routing_class)
    if value in INHERIT_VALUES:
        return None
    return value


def resolve_model(skill: "Skill", agent: str, routing: dict[str, dict[str, str]] | None = None) -> str | None:
    """Resolve the native model override for a skill, or None to inherit.

    Routing class is the explicit model_tier when set, else model_role.
    """
    routing_class = skill.model_tier or skill.model_role
    value = model_for_class(routing_class, agent, routing)
    if value in INHERIT_VALUES:
        return None
    return value


@dataclass(frozen=True)
class Skill:
    skill_id: str
    path: Path
    summary: str
    model_role: str
    model_tier: str
    status: str
    aliases: tuple[str, ...]
    topics: tuple[str, ...]
    install_name: str

    @property
    def domain(self) -> str:
        return self.skill_id.split("/", 1)[0]

    @property
    def leaf(self) -> str:
        return self.skill_id.split("/", 1)[-1]

    @property
    def companion_dir(self) -> Path:
        if self.path.name == "SKILL.md":
            return self.path.parent
        if self.path.stem == self.path.parent.name:
            return self.path.parent
        return self.path.with_suffix("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=ACTIONS, default="install", help="Action to run, default: install")
    parser.add_argument("--skills", help="Comma-separated skill ids, or 'all'")
    parser.add_argument("--categories", help="Comma-separated domains/categories, or 'all'")
    parser.add_argument("--agents", help="Comma-separated agents: codex,claude,cursor, or 'all'")
    parser.add_argument("--scope", choices=SCOPES, help="Install scope")
    parser.add_argument("--mode", choices=MODES, help="Install mode, default: wrapper")
    parser.add_argument("--project", default=str(ROOT), help="Project root for project-scoped installs")
    parser.add_argument("--profile-file", help="Shared profile JSON file to use as defaults")
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files")
    parser.add_argument("--hide-missing", action="store_true", help="Omit missing packages from status output")
    parser.add_argument("--yes", action="store_true", help="Do not ask for confirmation in scripted mode")
    return parser.parse_args()


def apply_profile_file(args: argparse.Namespace) -> None:
    if not args.profile_file:
        return
    path = Path(args.profile_file)
    if not path.is_absolute():
        path = ROOT / path
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: could not read profile file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: profile file must contain a JSON object: {path}")
    allowed = {"skills", "categories", "agents", "scope", "mode", "project"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise SystemExit(f"ERROR: unknown profile keys in {path}: {', '.join(unknown)}")
    for key in allowed:
        if getattr(args, key, None) in {None, ""} and data.get(key) is not None:
            setattr(args, key, str(data[key]))


def parse_list(value: str | None) -> set[str]:
    if not value:
        return set()
    parts = {part.strip() for part in value.split(",") if part.strip()}
    return {"all"} if "all" in parts else parts


def slug(value: str) -> str:
    return "-".join(
        "".join(ch.lower() if ch.isalnum() else "-" for ch in value).split("-")
    ).strip("-")


def native_install_names(skills: list[Skill]) -> dict[str, str]:
    def preferred_short_name(skill: Skill) -> str:
        return slug(skill.aliases[0]) if skill.aliases else slug(skill.leaf)

    short_counts: dict[str, int] = {}
    for skill in skills:
        if skill.domain == CORE_DOMAIN:
            continue
        short_name = preferred_short_name(skill)
        short_counts[short_name] = short_counts.get(short_name, 0) + 1

    names: dict[str, str] = {}
    for skill in skills:
        if skill.domain == CORE_DOMAIN:
            names[skill.skill_id] = "cortex-" + slug(skill.skill_id)
            continue
        short_name = preferred_short_name(skill)
        names[skill.skill_id] = short_name if short_counts[short_name] == 1 else slug(skill.skill_id)
    return names


def load_skills() -> list[Skill]:
    raw_skills: list[Skill] = []
    for path in lint_skill.discover_skill_files(ROOT):
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = lint_skill.parse_frontmatter(text)
        raw_skills.append(
            Skill(
                skill_id=str(frontmatter["skill_id"]),
                path=path,
                summary=str(frontmatter.get("summary", "")),
                model_role=str(frontmatter.get("model_role", "reference")),
                model_tier=str(frontmatter.get("model_tier", "") or ""),
                status=str(frontmatter.get("status", "unknown")),
                aliases=tuple(str(item) for item in frontmatter.get("aliases", []) or []),
                topics=tuple(str(item) for item in frontmatter.get("topics", []) or []),
                install_name="",
            )
        )
    install_names = native_install_names(raw_skills)
    skills = [
        Skill(
            skill_id=skill.skill_id,
            path=skill.path,
            summary=skill.summary,
            model_role=skill.model_role,
            model_tier=skill.model_tier,
            status=skill.status,
            aliases=skill.aliases,
            topics=skill.topics,
            install_name=install_names[skill.skill_id],
        )
        for skill in raw_skills
    ]
    return sorted(skills, key=lambda skill: skill.skill_id)


def checkbox_menu(title: str, options: list[str], selected: set[int] | None = None) -> set[int]:
    selected = set(selected or set())
    cursor = 0

    if not sys.stdin.isatty():
        raise SystemExit(f"ERROR: interactive selection for {title!r} requires a TTY")

    def render() -> None:
        print("\033[2J\033[H", end="")
        print(title)
        print("Use Up/Down, Space to toggle, Enter to continue, q to cancel.\n")
        for index, option in enumerate(options):
            pointer = ">" if index == cursor else " "
            mark = "x" if index in selected else " "
            print(f"{pointer} [{mark}] {option}")

    if os.name == "nt":
        import msvcrt

        while True:
            render()
            key = msvcrt.getwch()
            if key == "\r":
                return selected
            if key.lower() == "q":
                raise SystemExit("cancelled")
            if key == " ":
                if cursor in selected:
                    selected.remove(cursor)
                else:
                    selected.add(cursor)
            elif key == "\xe0":
                arrow = msvcrt.getwch()
                if arrow == "H":
                    cursor = (cursor - 1) % len(options)
                elif arrow == "P":
                    cursor = (cursor + 1) % len(options)
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                render()
                key = sys.stdin.read(1)
                if key == "\n":
                    return selected
                if key.lower() == "q":
                    raise SystemExit("cancelled")
                if key == " ":
                    if cursor in selected:
                        selected.remove(cursor)
                    else:
                        selected.add(cursor)
                elif key == "\x1b" and sys.stdin.read(1) == "[":
                    arrow = sys.stdin.read(1)
                    if arrow == "A":
                        cursor = (cursor - 1) % len(options)
                    elif arrow == "B":
                        cursor = (cursor + 1) % len(options)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def choose_interactively(skills: list[Skill], args: argparse.Namespace) -> tuple[set[str], set[str], str, str]:
    domains = sorted({skill.domain for skill in skills})
    category_options = ["all", *domains, "none"]
    category_indexes = checkbox_menu("Select categories", category_options)
    if not category_indexes:
        raise SystemExit("No categories selected")
    selected_categories = {category_options[index] for index in category_indexes}

    if "all" in selected_categories:
        selected_skill_ids = {skill.skill_id for skill in skills}
    else:
        selected_skill_ids = {
            skill.skill_id for skill in skills if skill.domain in selected_categories
        }
        if "none" in selected_categories:
            skill_options = [f"{skill.skill_id} - {skill.summary}" for skill in skills]
            skill_indexes = checkbox_menu("Select individual skills", skill_options)
            selected_skill_ids.update(skills[index].skill_id for index in skill_indexes)

    agent_indexes = checkbox_menu("Select agents", list(AGENTS))
    if not agent_indexes:
        raise SystemExit("No agents selected")
    selected_agents = {AGENTS[index] for index in agent_indexes}

    scope_index = checkbox_menu("Select scope", list(SCOPES), {0})
    if len(scope_index) != 1:
        raise SystemExit("Select exactly one scope")
    scope = SCOPES[next(iter(scope_index))]

    mode_index = checkbox_menu("Select install mode", list(MODES), {0})
    if len(mode_index) != 1:
        raise SystemExit("Select exactly one install mode")
    mode = MODES[next(iter(mode_index))]

    return selected_skill_ids, selected_agents, scope, mode


def resolve_selection(skills: list[Skill], args: argparse.Namespace) -> tuple[list[Skill], set[str], str, str]:
    by_id = {skill.skill_id: skill for skill in skills}
    skill_ids = parse_list(args.skills)
    categories = parse_list(args.categories)
    agents = parse_list(args.agents)

    if not skill_ids and not categories and not agents and not args.scope and args.action == "install":
        selected_ids, selected_agents, scope, mode = choose_interactively(skills, args)
    else:
        selected_ids: set[str] = set()
        if "all" in skill_ids or "all" in categories:
            selected_ids.update(by_id)
        else:
            selected_ids.update(skill_ids)
            selected_ids.update(skill.skill_id for skill in skills if skill.domain in categories)
        if not selected_ids and args.action != "install":
            selected_ids.update(by_id)
        selected_agents = set(AGENTS if "all" in agents or (not agents and args.action != "install") else agents)
        scope = args.scope or "global"
        mode = args.mode or "wrapper"

    unknown_skills = sorted(skill_id for skill_id in selected_ids if skill_id not in by_id)
    unknown_agents = sorted(agent for agent in selected_agents if agent not in AGENTS)
    if unknown_skills:
        raise SystemExit(f"ERROR: unknown skills: {', '.join(unknown_skills)}")
    if unknown_agents:
        raise SystemExit(f"ERROR: unknown agents: {', '.join(unknown_agents)}")
    if not selected_ids:
        raise SystemExit("ERROR: no skills selected")
    if not selected_agents:
        raise SystemExit("ERROR: no agents selected")

    selected_ids.update(skill.skill_id for skill in skills if skill.domain == CORE_DOMAIN)
    return [by_id[skill_id] for skill_id in sorted(selected_ids)], selected_agents, scope, mode


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def yaml_list(name: str, values: tuple[str, ...]) -> str:
    if not values:
        return f"{name}: []"
    lines = [f"{name}:"]
    lines.extend(f"  - \"{yaml_escape(value)}\"" for value in values)
    return "\n".join(lines)


def source_body(skill: Skill) -> str:
    text = skill.path.read_text(encoding="utf-8")
    _, body = lint_skill.parse_frontmatter(text)
    return body.strip()


def source_hash(skill: Skill) -> str:
    digest = hashlib.sha256()
    digest.update(skill.path.relative_to(ROOT).as_posix().encode("utf-8"))
    digest.update(b"\0")
    digest.update(skill.path.read_bytes())
    for resource in resource_files(skill):
        digest.update(b"\0")
        digest.update(resource.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(resource.read_bytes())
    return digest.hexdigest()


def resource_roots(skill: Skill) -> list[Path]:
    if not skill.companion_dir.is_dir():
        return []
    return [skill.companion_dir / name for name in RESOURCE_DIR_NAMES if (skill.companion_dir / name).exists()]


def _is_pycache(path: Path) -> bool:
    # Bytecode caches are never deployed (copy_resources ignores them), so they
    # must not enter the manifest either, or the package is perpetually stale.
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def resource_files(skill: Skill) -> list[Path]:
    files: list[Path] = []
    for root in resource_roots(skill):
        if root.is_file():
            files.append(root)
            continue
        files.extend(path for path in root.rglob("*") if path.is_file() and not _is_pycache(path))
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def resource_manifest(skill: Skill) -> list[dict[str, str | int]]:
    manifest: list[dict[str, str | int]] = []
    for path in resource_files(skill):
        manifest.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return manifest


def copy_resources(skill: Skill, destination: Path) -> list[str]:
    copied: list[str] = []
    for source in resource_roots(skill):
        target = destination / source.name
        if target.exists():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, target)
        copied.append(source.name)
    return copied


def cursor_resource_path(rule_path: Path) -> Path:
    return Path(str(rule_path) + ".resources")


def resource_target(skill: Skill, agent: str, target: Path) -> Path:
    if agent == "cursor":
        return cursor_resource_path(target)
    return target


def resources_installed(skill: Skill, agent: str, target: Path, expected_manifest: list[dict] | None = None) -> bool:
    if not resource_roots(skill):
        return True
    resource_root = resource_target(skill, agent, target)
    manifest = expected_manifest if expected_manifest is not None else resource_manifest(skill)
    for item in manifest:
        source = ROOT / str(item["path"])
        try:
            relative = source.relative_to(skill.companion_dir)
        except ValueError:
            return False
        installed = resource_root / relative
        if not installed.is_file():
            return False
        if installed.stat().st_size != item["size"]:
            return False
        if hashlib.sha256(installed.read_bytes()).hexdigest() != item["sha256"]:
            return False
    return True


def git_command() -> str | None:
    git = shutil.which("git")
    if git:
        return git
    for candidate in (
        Path("C:/Program Files/Git/cmd/git.exe"),
        Path("C:/Program Files/Git/bin/git.exe"),
    ):
        if candidate.exists():
            return str(candidate)
    return None


def git_commit() -> str:
    git = git_command()
    if git is None:
        return "unknown"
    result = subprocess.run(
        [git, "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def metadata(skill: Skill, agent: str, scope: str, mode: str, target: Path,
             worker_agents: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "generated_by": "cortex",
        "generator_version": GENERATOR_VERSION,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "cortex_commit": git_commit(),
        "vault_root": str(ROOT),
        "source_skill_id": skill.skill_id,
        "source_path": str(skill.path),
        "source_hash": source_hash(skill),
        "resource_paths": [path.relative_to(ROOT).as_posix() for path in resource_roots(skill)],
        "resource_manifest": resource_manifest(skill),
        "install_name": skill.install_name,
        "worker_agents": worker_agents or [],
        "agent": agent,
        "scope": scope,
        "install_mode": mode,
        "python_executable": sys.executable,
        "target_path": str(target),
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def command_line(*parts: Path | str) -> str:
    return " ".join(f'"{part}"' if " " in str(part) or "\\" in str(part) else str(part) for part in parts)


def compact_cortex_footer(skill: Skill, agent: str) -> str:
    validate = ROOT / "skills" / "meta" / "scripts" / "validate.py"
    log_entry = ROOT / "skills" / "meta" / "scripts" / "log_entry.py"
    commit_skill = ROOT / "skills" / "meta" / "scripts" / "commit_skill.py"
    return f"""## Cortex Source

Generated for {agent} from Cortex skill `{skill.skill_id}`.

- Source: `{skill.path}`
- Vault: `{ROOT}`
- Index: `{lint_skill.index_path(ROOT)}`
- Contribution protocol: `{lint_skill.skill_path(ROOT, "meta/contributing")}`
- Validate after source edits: `{command_line(sys.executable, validate)} --fix-generated`
- Log useful context: `{command_line(sys.executable, log_entry)} --title "short title" --details "what changed and why"`
- Commit skill changes: `{command_line(sys.executable, commit_skill)}`

Do not edit this generated package directly. Update the Cortex source,
validate, commit, then reinstall or sync generated native packages. If
the recorded interpreter is unavailable, use `python3`, `python`, or `py`
with the same script path.
"""


def wrapper_text(skill: Skill, agent: str) -> str:
    hints = sorted(set(skill.aliases + skill.topics + (skill.domain, skill.leaf, skill.skill_id)))
    hint_text = f"Use when the user mentions or works on: {', '.join(hints)}." if hints else ""
    description = yaml_escape(
        f"{skill.summary} Use when this Cortex skill matches the user's task. "
        f"{hint_text} Update Cortex source if the agent learns reusable knowledge."
    )
    body = source_body(skill)
    model = resolve_model(skill, agent)
    model_line = f"model: {model}\n" if model else ""
    trigger_block = ""
    if hints:
        trigger_block = (
            "## Trigger Hints\n\n"
            f"Use this skill for: {', '.join(hints)}.\n\n"
        )
    return f"""---
name: {skill.install_name}
{model_line}description: "{description}"
cortex_skill_id: "{yaml_escape(skill.skill_id)}"
cortex_domain: "{yaml_escape(skill.domain)}"
cortex_leaf: "{yaml_escape(skill.leaf)}"
{yaml_list("aliases", skill.aliases)}
{yaml_list("topics", skill.topics)}
---

{trigger_block}
{body}

{compact_cortex_footer(skill, agent)}
"""


def cursor_rule_text(skill: Skill) -> str:
    hints = sorted(set(skill.aliases + skill.topics + (skill.domain, skill.leaf, skill.skill_id)))
    hint_text = f"Use when the user mentions or works on: {', '.join(hints)}." if hints else ""
    description = yaml_escape(f"{skill.summary} Use when this Cortex skill matches the project task.{hint_text}")
    body = source_body(skill)
    trigger_block = ""
    if hints:
        trigger_block = (
            "## Trigger Hints\n\n"
            f"Use this rule for: {', '.join(hints)}.\n\n"
        )
    return f"""---
description: "{description}"
alwaysApply: false
cortex_skill_id: "{yaml_escape(skill.skill_id)}"
cortex_domain: "{yaml_escape(skill.domain)}"
cortex_leaf: "{yaml_escape(skill.leaf)}"
{yaml_list("aliases", skill.aliases)}
{yaml_list("topics", skill.topics)}
---

{trigger_block}
{body}

{compact_cortex_footer(skill, "cursor")}
"""


def discover_agents(skill: Skill) -> list[dict]:
    """Parse worker definitions in a skill's agents/ folder.

    Returns a list of {path, frontmatter, body} dicts, one per worker .md.
    """
    agents_dir = skill.companion_dir / "agents"
    if not agents_dir.is_dir():
        return []
    workers: list[dict] = []
    for path in sorted(agents_dir.glob("*.md")):
        frontmatter, body = lint_skill.parse_frontmatter(path.read_text(encoding="utf-8"))
        workers.append({"path": path, "frontmatter": frontmatter, "body": body})
    return workers


def worker_agent_text(worker: dict, agent: str, skill_names: dict[str, str] | None = None,
                      routing: dict[str, dict[str, str]] | None = None) -> str:
    """Generate a native subagent file body for a worker definition.

    The Claude adapter emits a `model:` line from the worker's routing class and
    a `skills:` scoping list (mapped to native skill names when known). A body
    pointer always names the referenced skills so the worker reaches for them;
    skill bodies are never inlined.
    """
    frontmatter = worker["frontmatter"]
    name = str(frontmatter.get("name", worker["path"].stem))
    description = yaml_escape(str(frontmatter.get("description", "")))
    routing_class = str(frontmatter.get("model_tier") or frontmatter.get("model_role") or "")
    model = model_for_class(routing_class, agent, routing) if routing_class else None
    model_line = f"model: {model}\n" if model else ""

    skill_ids = [str(item) for item in (frontmatter.get("skills") or [])]
    skill_names = skill_names or {}
    native = [skill_names.get(sid, sid) for sid in skill_ids]
    skills_block = ""
    if native:
        skills_block = "skills:\n" + "".join(f"  - {yaml_escape(item)}\n" for item in native)
    pointer = ""
    if skill_ids:
        # Name the invokable handle the worker reaches for (the deployed native
        # command), keeping the source skill_id in parentheses for traceability.
        refs = ", ".join(f"/{skill_names.get(sid, sid)} ({sid})" for sid in skill_ids)
        pointer = (
            "## Skills\n\n"
            f"Use these Cortex skills via the Skill tool for this work: {refs}. "
            "Reach for them; their content is not inlined here.\n\n"
        )
    return (
        "---\n"
        f"name: {name}\n"
        f"{model_line}"
        f'description: "{description}"\n'
        f"{skills_block}"
        "---\n\n"
        f"{pointer}{worker['body'].strip()}\n"
    )


def agents_home(agent: str, scope: str, project: Path) -> Path | None:
    """Directory that holds generated native worker subagents, or None.

    Only Claude has a native subagent home today. Global installs target the
    Claude agents home; project installs keep workers under the project's
    Cortex tree alongside the project-scoped skills.
    """
    if agent != "claude":
        return None
    if scope == "global":
        return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "agents"
    return project / ".cortex" / agent / "agents"


def generated_workers(skill: Skill, agent: str, skill_names: dict[str, str] | None,
                      routing: dict[str, dict[str, str]] | None = None) -> list[tuple[str, str, str]]:
    """Generated worker files for a skill: list of (filename, text, name).

    Filenames are namespaced by the orchestrator's install name so workers from
    different orchestrators never collide in the shared agents home.
    """
    workers: list[tuple[str, str, str]] = []
    for worker in discover_agents(skill):
        name = str(worker["frontmatter"].get("name", worker["path"].stem))
        text = worker_agent_text(worker, agent, skill_names, routing)
        workers.append((f"{skill.install_name}__{name}.md", text, name))
    return workers


def worker_manifest(skill: Skill, agent: str, home: Path | None, skill_names: dict[str, str] | None,
                    routing: dict[str, dict[str, str]] | None = None) -> list[dict[str, str]]:
    """Manifest of generated worker files: target path + content hash + name.

    The hash is over the generated text only (not the path), so a changed worker
    source or routing map changes the hash and a relocated agents home does not.
    """
    if home is None:
        return []
    manifest: list[dict[str, str]] = []
    for filename, text, name in generated_workers(skill, agent, skill_names, routing):
        manifest.append(
            {
                "name": name,
                "path": str(home / filename),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
    return manifest


def _worker_owned(path: Path, prior: list[dict] | None) -> bool:
    """True if Cortex may overwrite/remove this worker file (we generated it)."""
    if prior is None:
        return False
    return any(str(path) == str(item.get("path")) for item in prior)


def sync_worker_agents(skill: Skill, agent: str, scope: str, project: Path,
                       skill_names: dict[str, str] | None, prior: list[dict] | None,
                       dry_run: bool) -> list[dict[str, str]]:
    """Write a skill's worker subagents into the agents home; prune removed ones.

    Returns the manifest to record in the orchestrator's metadata. Skips files
    that exist but were not generated by Cortex (foreign user agents).
    """
    home = agents_home(agent, scope, project)
    if home is None:
        return []
    new_manifest = worker_manifest(skill, agent, home, skill_names)
    new_paths = {item["path"] for item in new_manifest}

    # Prune previously-generated workers that this skill no longer defines.
    for item in prior or []:
        old_path = Path(str(item.get("path", "")))
        if str(old_path) in new_paths or not old_path.exists():
            continue
        print(f"REMOVE-WORKER: {agent} {skill.skill_id} -> {old_path}")
        if not dry_run:
            old_path.unlink(missing_ok=True)

    by_name = {name: text for _, text, name in generated_workers(skill, agent, skill_names)}
    for item in new_manifest:
        target = Path(item["path"])
        if target.exists() and not _worker_owned(target, prior):
            print(f"SKIP-WORKER: {target} exists and is not Cortex-managed")
            continue
        print(f"WORKER: {agent} {skill.skill_id} -> {target}")
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(by_name[item["name"]], encoding="utf-8", newline="\n")
    return new_manifest


def remove_worker_agents(agent: str, skill: Skill, data: dict | None, dry_run: bool) -> None:
    """Delete generated worker subagent files recorded in a skill's metadata."""
    if not data:
        return
    for item in data.get("worker_agents", []) or []:
        path = Path(str(item.get("path", "")))
        if not path.exists():
            continue
        print(f"UNINSTALL-WORKER: {agent} {skill.skill_id} -> {path}")
        if not dry_run:
            path.unlink(missing_ok=True)


def workers_current(skill: Skill, agent: str, scope: str, project: Path,
                    skill_names: dict[str, str] | None, data: dict) -> bool:
    """True if generated worker files match the current source and routing."""
    home = agents_home(agent, scope, project)
    expected = worker_manifest(skill, agent, home, skill_names)
    stored = data.get("worker_agents") or []
    if {(w["name"], w["sha256"]) for w in expected} != {(w["name"], w["sha256"]) for w in stored}:
        return False
    for item in expected:
        path = Path(item["path"])
        if not path.is_file():
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            return False
    return True


def global_target(agent: str) -> Path | None:
    if agent == "codex":
        return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"
    if agent == "claude":
        return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "skills"
    return None


def project_target(agent: str, project: Path) -> Path:
    if agent in {"codex", "claude"}:
        return project / ".cortex" / agent / "skills"
    if agent == "cursor":
        return project / ".cursor" / "rules"
    raise ValueError(agent)


def safe_existing(destination: Path) -> bool:
    return (
        not destination.exists()
        or (destination / ".cortex-managed").exists()
        or (destination / METADATA_FILE).exists()
    )


def cleanup_legacy_wrappers(skill: Skill, agent: str, root: Path, destination: Path, dry_run: bool) -> None:
    if not root.exists():
        return
    for candidate in root.iterdir():
        if candidate == destination or not candidate.is_dir():
            continue
        metadata_file = candidate / METADATA_FILE
        marker = candidate / ".cortex-managed"
        if not metadata_file.exists() or not marker.exists():
            continue
        data = read_json(metadata_file)
        if not data or data.get("source_skill_id") != skill.skill_id or data.get("agent") != agent:
            continue
        print(f"REMOVE-LEGACY: {agent} {skill.skill_id} -> {candidate}")
        if dry_run:
            continue
        if candidate.is_symlink():
            candidate.unlink()
        else:
            shutil.rmtree(candidate)


def write_skill_wrapper(skill: Skill, agent: str, root: Path, scope: str, mode: str, dry_run: bool,
                        project: Path | None = None, skill_names: dict[str, str] | None = None) -> None:
    destination = root / skill.install_name
    marker = destination / ".cortex-managed"
    skill_file = destination / "SKILL.md"
    metadata_file = destination / METADATA_FILE
    if not safe_existing(destination):
        print(f"SKIP: {destination} exists and is not Cortex-managed")
        return

    cleanup_legacy_wrappers(skill, agent, root, destination, dry_run)

    # Worker subagents (Claude only). Read prior manifest before overwriting so
    # removed/renamed workers can be pruned from the agents home.
    project = project or ROOT
    worker_agents: list[dict] = []
    if agent == "claude" and discover_agents(skill):
        prior_data = read_json(metadata_file)
        if prior_data is None and mode == "symlink":
            prior_data = read_json(ROOT / ".cortex" / "generated" / agent / skill.install_name / METADATA_FILE)
        prior_workers = (prior_data or {}).get("worker_agents") if prior_data else None
        worker_agents = sync_worker_agents(skill, agent, scope, project, skill_names, prior_workers, dry_run)

    print(f"INSTALL: {agent} {skill.skill_id} -> {destination} ({mode})")
    if dry_run:
        return

    if mode == "copy":
        destination.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(wrapper_text(skill, agent), encoding="utf-8", newline="\n")
        copy_resources(skill, destination)
    elif mode == "symlink":
        source_dir = ROOT / ".cortex" / "generated" / agent / skill.install_name
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "SKILL.md").write_text(wrapper_text(skill, agent), encoding="utf-8", newline="\n")
        copy_resources(skill, source_dir)
        (source_dir / ".cortex-managed").write_text(
            f"generated_by=cortex\nvault_root={ROOT}\nsource={skill.path}\nagent={agent}\n",
            encoding="utf-8",
            newline="\n",
        )
        data = metadata(skill, agent, scope, mode, destination, worker_agents)
        data["generated_path"] = str(source_dir)
        write_json(source_dir / METADATA_FILE, data)
        if destination.exists() and not destination.is_symlink():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.symlink_to(source_dir, target_is_directory=True)
    else:
        destination.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(wrapper_text(skill, agent), encoding="utf-8", newline="\n")
        copy_resources(skill, destination)

    if mode != "symlink":
        destination.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            f"generated_by=cortex\nvault_root={ROOT}\nsource={skill.path}\nagent={agent}\n",
            encoding="utf-8",
            newline="\n",
        )
        write_json(metadata_file, metadata(skill, agent, scope, mode, destination, worker_agents))


def cursor_rule_path(skill: Skill, project: Path) -> Path:
    return project / ".cursor" / "rules" / f"{skill.install_name}.mdc"


def cursor_metadata_path(rule_path: Path) -> Path:
    return Path(str(rule_path) + ".cortex.json")


def write_cursor_rule(skill: Skill, project: Path, scope: str, mode: str, dry_run: bool) -> None:
    target = cursor_rule_path(skill, project)
    metadata_file = cursor_metadata_path(target)
    if target.exists() and not metadata_file.exists():
        print(f"SKIP: {target} exists and is not Cortex-managed")
        return
    resources = cursor_resource_path(target)
    if resources.exists() and not (resources / ".cortex-managed").exists():
        print(f"SKIP: {resources} exists and is not Cortex-managed")
        return
    print(f"INSTALL: cursor {skill.skill_id} -> {target}")
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(cursor_rule_text(skill), encoding="utf-8", newline="\n")
    if resource_roots(skill):
        resources.mkdir(parents=True, exist_ok=True)
        copy_resources(skill, resources)
        (resources / ".cortex-managed").write_text(
            f"generated_by=cortex\nvault_root={ROOT}\nsource={skill.path}\nagent=cursor\n",
            encoding="utf-8",
            newline="\n",
        )
    write_json(metadata_file, metadata(skill, "cursor", scope, mode, target))


def status_for_metadata(skill: Skill, agent: str, target: Path, data: dict | None,
                        scope: str = "global", project: Path | None = None,
                        skill_names: dict[str, str] | None = None) -> str:
    if data is None:
        return "unmanaged"
    if data.get("source_skill_id") != skill.skill_id:
        return "stale"
    if data.get("generator_version") != GENERATOR_VERSION:
        return "stale"
    if data.get("source_hash") != source_hash(skill):
        return "stale"
    if not resources_installed(skill, agent, target, data.get("resource_manifest")):
        return "stale"
    if not workers_current(skill, agent, scope, project or ROOT, skill_names, data):
        return "stale"
    return "current"


def skill_target(skill: Skill, agent: str, scope: str, project: Path) -> tuple[Path | None, Path | None]:
    if scope == "global":
        root = global_target(agent)
        if root is None:
            return None, None
    else:
        root = project_target(agent, project)

    if agent == "cursor":
        target = cursor_rule_path(skill, project)
        return target, cursor_metadata_path(target)
    target = root / skill.install_name
    return target, target / METADATA_FILE


def status(skills: list[Skill], agents: set[str], scope: str, project: Path, hide_missing: bool = False,
           skill_names: dict[str, str] | None = None) -> int:
    for agent in sorted(agents):
        if scope == "global" and global_target(agent) is None:
            print(f"unsupported {agent} {scope}: no supported global target")
            continue
        for skill in skills:
            target, metadata_file = skill_target(skill, agent, scope, project)
            if target is None or metadata_file is None:
                print(f"unsupported {agent} {scope} {skill.skill_id}")
                continue
            if not target.exists():
                if hide_missing:
                    continue
                print(f"missing {agent} {scope} {skill.skill_id} -> {target}")
                continue
            state = status_for_metadata(
                skill, agent, target, read_json(metadata_file), scope, project, skill_names
            )
            print(f"{state} {agent} {scope} {skill.skill_id} -> {target}")
    return 0


def uninstall(skills: list[Skill], agents: set[str], scope: str, project: Path, dry_run: bool) -> int:
    for agent in sorted(agents):
        if scope == "global" and global_target(agent) is None:
            print(f"SKIP: {agent} has no supported global target")
            continue
        for skill in skills:
            target, metadata_file = skill_target(skill, agent, scope, project)
            if target is None or metadata_file is None or not target.exists():
                continue
            if not metadata_file.exists():
                print(f"SKIP: {target} exists and is not Cortex-managed")
                continue
            remove_worker_agents(agent, skill, read_json(metadata_file), dry_run)
            print(f"UNINSTALL: {agent} {skill.skill_id} -> {target}")
            if dry_run:
                continue
            if agent == "cursor":
                target.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                resources = cursor_resource_path(target)
                if resources.exists() and (resources / ".cortex-managed").exists():
                    shutil.rmtree(resources)
            elif target.is_symlink():
                data = read_json(metadata_file)
                target.unlink()
                generated_path = Path(str(data.get("generated_path", ""))) if data else None
                if (
                    generated_path
                    and generated_path.exists()
                    and (generated_path / ".cortex-managed").exists()
                    and generated_path.resolve().is_relative_to(ROOT.resolve())
                ):
                    shutil.rmtree(generated_path)
            else:
                shutil.rmtree(target)
    return 0


def install(skills: list[Skill], agents: set[str], scope: str, mode: str, project: Path, dry_run: bool,
            skill_names: dict[str, str] | None = None) -> None:
    for agent in sorted(agents):
        if scope == "global":
            target = global_target(agent)
            if target is None:
                print(f"SKIP: {agent} has no supported global SKILL.md target. Use project scope.")
                continue
        else:
            target = project_target(agent, project)

        for skill in skills:
            if agent == "cursor":
                if scope == "global":
                    continue
                write_cursor_rule(skill, project, scope, mode, dry_run)
            else:
                write_skill_wrapper(skill, agent, target, scope, mode, dry_run, project, skill_names)


def main() -> int:
    args = parse_args()
    apply_profile_file(args)
    skills = load_skills()
    selected_skills, selected_agents, scope, mode = resolve_selection(skills, args)
    project = Path(args.project).resolve()
    # Map every vault skill id to its native install name so worker `skills:`
    # references resolve consistently regardless of the current selection.
    skill_names = {skill.skill_id: skill.install_name for skill in skills}

    print("Selected skills:")
    for skill in selected_skills:
        core = " core" if skill.domain == CORE_DOMAIN else ""
        print(f"- {skill.skill_id}{core}")
    print(f"Agents: {', '.join(sorted(selected_agents))}")
    print(f"Scope: {scope}")
    print(f"Mode: {mode}")
    print(f"Action: {args.action}")

    scripted = bool(args.skills or args.categories or args.agents or args.scope)
    if not args.yes and not args.dry_run and scripted and args.action in {"install", "sync", "repair", "uninstall", "cleanup"}:
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            raise SystemExit("cancelled")

    if args.action == "status":
        return status(selected_skills, selected_agents, scope, project, args.hide_missing, skill_names)
    if args.action in {"uninstall", "cleanup"}:
        return uninstall(selected_skills, selected_agents, scope, project, args.dry_run)

    install(selected_skills, selected_agents, scope, mode, project, args.dry_run, skill_names)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
