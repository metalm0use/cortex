#!/usr/bin/env python3
"""Lint one markdown skill file for the Cortex contract."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "schema_version",
    "tags",
    "topics",
    "status",
    "created",
    "updated",
    "sources",
    "source_count",
    "aliases",
    "skill_id",
    "summary",
    "model_role",
}
LIST_KEYS = {"tags", "topics", "sources", "aliases", "depends_on", "related"}
VALID_STATUS = {"seed", "active", "draft", "deprecated", "conflict"}
VALID_MODEL_ROLES = {"thinking", "execution", "reference"}
VALID_MODEL_TIERS = {"thinking", "execution", "reference", "inherit"}
VALID_REVIEW_STATUS = {"unreviewed", "human-noted", "reviewed", "disputed", "needs-refresh"}
VALID_CONFIDENCE = {"low", "medium", "high"}
# Worker definitions under a skill's agents/ folder. Model-agnostic source:
# model is chosen by routing class (model_tier/model_role), and domain
# knowledge is referenced by skill_id, never inlined.
REQUIRED_AGENT_KEYS = {"name", "description"}
VALID_AGENT_KEYS = {
    "name",
    "description",
    "model_tier",
    "model_role",
    "skills",
    "tools",
    "allowed-tools",
    "schema_version",
    # Worker prompts are self-learning Cortex source: they carry the same
    # optional review metadata skills do, so a human-validated worker can be
    # tracked and improved through the meta/contributing loop.
    "review_status",
    "reviewed_by",
    "expertise_domain",
    "confidence",
    "reviewed_at",
}
SCHEMA_VERSION = 1
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROVENANCE_RE = re.compile(
    r"<!--\s*learned:\s*\d{4}-\d{2}\s*\|\s*project:\s*[^|]+"
    r"\|\s*model:\s*[^>]+-->"
)
VENDOR_LANGUAGE = [
    re.compile(r"\b(?:Claude|ChatGPT|GPT|Gemini)\s+(?:will|should|must|needs?|does|can)\b", re.I),
    re.compile(r"\bask the model to\b", re.I),
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
ABS_SKILL_REF_RE = re.compile(r"(?<![A-Za-z0-9_:/.-])(/?skills/[A-Za-z0-9_./-]+\.md)")
GENERATED_WRAPPER_MARKERS = (
    "This is a generated",
    "## Embedded Cortex Skill",
    "## Python Script Access",
    "## Feedback To Cortex",
)
GENERIC_DISCOVERY_TERMS = {
    "skill",
    "skills",
    "help",
    "guide",
    "workflow",
    "task",
    "domain",
    "specific topic",
}


def repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / ".git").exists() or (path / "skills").exists():
            return path
    return start


def skill_path(root: Path, skill_id: str) -> Path:
    return root / "skills" / Path(*skill_id.split("/")) / "SKILL.md"


def index_path(root: Path) -> Path:
    return skill_path(root, "meta/index")


def source_manifest_path(root: Path) -> Path:
    return skill_path(root, "meta/source-manifest")


def parse_scalar(value: str):
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("missing closing frontmatter delimiter")

    data = {}
    current_key = None
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_key is None:
                raise ValueError(f"list item without key: {line}")
            data.setdefault(current_key, []).append(parse_scalar(line[4:]))
            continue
        if ":" not in line:
            raise ValueError(f"cannot parse frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        else:
            data[key] = parse_scalar(value)
    return data, "\n".join(lines[end + 1 :])


def expected_skill_id(path: Path, root: Path) -> str | None:
    try:
        rel = path.resolve().relative_to((root / "skills").resolve())
    except ValueError:
        return None
    if rel.parts and rel.parts[-2:] == ("scripts", path.name):
        return None
    if path.name == "SKILL.md":
        return Path(*rel.parts[:-1]).as_posix()
    if len(rel.parts) >= 2 and path.stem == path.parent.name:
        return Path(*rel.parts[:-1]).as_posix()
    return rel.with_suffix("").as_posix()


def load_index_ids(root: Path) -> set[str]:
    path = index_path(root)
    if not path.exists():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text()
    return set(re.findall(r"`([a-z0-9_./-]+)`", text))


def resolve_reference(ref: str, source: Path, root: Path) -> Path:
    clean = ref.split("#", 1)[0]
    if clean.startswith("/skills/"):
        return root / clean.lstrip("/")
    if clean.startswith("skills/"):
        return root / clean
    return (source.parent / clean).resolve()


def discover_skill_files(root: Path) -> list[Path]:
    skills_root = root / "skills"
    # `agents` holds bundle-local orchestration worker definitions, not skills;
    # it is excluded here and linted separately via discover_agent_files.
    resource_parts = {"assets", "references", "scripts", "vendor", "agents"}
    return [
        path
        for path in sorted(skills_root.rglob("*.md"))
        if not any(part in resource_parts for part in path.relative_to(skills_root).parts)
    ]


def discover_agent_files(root: Path) -> list[Path]:
    skills_root = root / "skills"
    return [
        path
        for path in sorted(skills_root.rglob("*.md"))
        if "agents" in path.relative_to(skills_root).parts
    ]


def lint(path: Path) -> list[str]:
    errors: list[str] = []
    root = repo_root(path.resolve())

    if not path.exists():
        return [f"{path}: file does not exist"]
    if path.suffix.lower() != ".md":
        errors.append("skill files must be markdown files ending in .md")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["file must be UTF-8 encoded"]

    try:
        frontmatter, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    missing = sorted(REQUIRED_KEYS - set(frontmatter))
    if missing:
        errors.append(f"missing frontmatter keys: {', '.join(missing)}")

    if frontmatter.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    for key in LIST_KEYS | {"reviewed_by", "expertise_domain"}:
        if key in frontmatter and not isinstance(frontmatter[key], list):
            errors.append(f"frontmatter key '{key}' must be a list")

    status = frontmatter.get("status")
    if status not in VALID_STATUS:
        errors.append(f"status must be one of: {', '.join(sorted(VALID_STATUS))}")

    for key in ("created", "updated"):
        value = str(frontmatter.get(key, ""))
        if not DATE_RE.match(value):
            errors.append(f"{key} must use YYYY-MM-DD")
        else:
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append(f"{key} is not a valid calendar date")

    sources = frontmatter.get("sources", [])
    source_count = frontmatter.get("source_count")
    if isinstance(sources, list) and isinstance(source_count, int):
        if len(sources) != source_count:
            errors.append("source_count must match the number of sources")
    else:
        errors.append("sources must be a list and source_count must be an integer")

    summary = str(frontmatter.get("summary", "")).strip()
    if len(summary) < 20:
        errors.append("summary must be at least 20 characters")

    skill_id_value = str(frontmatter.get("skill_id", ""))
    aliases = frontmatter.get("aliases", [])
    topics = frontmatter.get("topics", [])
    if isinstance(aliases, list) and isinstance(topics, list) and skill_id_value and not skill_id_value.startswith("meta/"):
        discovery_terms = [str(item).strip().lower() for item in [*aliases, *topics] if str(item).strip()]
        meaningful_terms = [
            term for term in discovery_terms if term not in GENERIC_DISCOVERY_TERMS and len(term) >= 3
        ]
        if not aliases:
            errors.append("non-meta skills must include at least one alias for native skill discovery")
        if not topics:
            errors.append("non-meta skills must include at least one topic for native skill discovery")
        if len(meaningful_terms) < 2:
            errors.append("non-meta skills must include at least two meaningful alias/topic trigger terms")

    model_role = frontmatter.get("model_role")
    if model_role not in VALID_MODEL_ROLES:
        errors.append(f"model_role must be one of: {', '.join(sorted(VALID_MODEL_ROLES))}")

    model_tier = frontmatter.get("model_tier")
    if model_tier is not None and model_tier not in VALID_MODEL_TIERS:
        errors.append(f"model_tier must be one of: {', '.join(sorted(VALID_MODEL_TIERS))}")

    review_status = frontmatter.get("review_status")
    if review_status is not None and review_status not in VALID_REVIEW_STATUS:
        errors.append(f"review_status must be one of: {', '.join(sorted(VALID_REVIEW_STATUS))}")

    confidence = frontmatter.get("confidence")
    if confidence is not None and confidence not in VALID_CONFIDENCE:
        errors.append(f"confidence must be one of: {', '.join(sorted(VALID_CONFIDENCE))}")

    reviewed_at = frontmatter.get("reviewed_at")
    if reviewed_at is not None:
        value = str(reviewed_at)
        if not DATE_RE.match(value):
            errors.append("reviewed_at must use YYYY-MM-DD")
        else:
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append("reviewed_at is not a valid calendar date")

    expected_id = expected_skill_id(path, root)
    if expected_id and frontmatter.get("skill_id") != expected_id:
        errors.append(f"skill_id must match path: {expected_id}")

    if not PROVENANCE_RE.search(text):
        errors.append("missing provenance comment: <!-- learned: YYYY-MM | project: ... | model: ... -->")

    for pattern in VENDOR_LANGUAGE:
        match = pattern.search(body)
        if match:
            errors.append(f"vendor-specific instruction language found: {match.group(0)!r}")

    for marker in GENERATED_WRAPPER_MARKERS:
        if marker in body:
            errors.append(f"generated-wrapper boilerplate found in source skill: {marker!r}")

    for match in MARKDOWN_LINK_RE.finditer(text):
        ref = match.group(1)
        if "://" in ref:
            continue
        target = resolve_reference(ref, path, root)
        if not target.exists():
            errors.append(f"markdown reference does not resolve: {ref}")

    for match in ABS_SKILL_REF_RE.finditer(text):
        target = resolve_reference(match.group(1), path, root)
        if not target.exists():
            errors.append(f"skill path reference does not resolve: {match.group(1)}")

    index_ids = load_index_ids(root)
    skill_id = frontmatter.get("skill_id")
    if skill_id != "meta/index" and index_ids and skill_id not in index_ids:
        errors.append(f"skill_id {skill_id!r} is missing from skills/meta/index/SKILL.md")
    if skill_id != "meta/index" and not index_ids:
        errors.append("skills/meta/index/SKILL.md does not exist or has no skill entries")

    return errors


def skill_reference_exists(skill_id: str, root: Path, index_ids: set[str]) -> bool:
    if skill_id in index_ids:
        return True
    return skill_path(root, skill_id).exists()


def lint_agent(path: Path) -> list[str]:
    """Lint one orchestration worker definition under a skill's agents/ folder."""
    errors: list[str] = []
    root = repo_root(path.resolve())

    if not path.exists():
        return [f"{path}: file does not exist"]
    if path.suffix.lower() != ".md":
        errors.append("agent files must be markdown files ending in .md")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["file must be UTF-8 encoded"]

    try:
        frontmatter, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    missing = sorted(REQUIRED_AGENT_KEYS - set(frontmatter))
    if missing:
        errors.append(f"missing agent frontmatter keys: {', '.join(missing)}")

    unknown = sorted(set(frontmatter) - VALID_AGENT_KEYS)
    if unknown:
        errors.append(f"unknown agent frontmatter keys: {', '.join(unknown)}")

    name = str(frontmatter.get("name", "")).strip()
    if name and name != path.stem:
        errors.append(f"agent name must match file stem: {path.stem}")

    description = str(frontmatter.get("description", "")).strip()
    if len(description) < 20:
        errors.append("description must be at least 20 characters")

    model_tier = frontmatter.get("model_tier")
    if model_tier is not None and model_tier not in VALID_MODEL_TIERS:
        errors.append(f"model_tier must be one of: {', '.join(sorted(VALID_MODEL_TIERS))}")

    model_role = frontmatter.get("model_role")
    if model_role is not None and model_role not in VALID_MODEL_ROLES:
        errors.append(f"model_role must be one of: {', '.join(sorted(VALID_MODEL_ROLES))}")

    schema_version = frontmatter.get("schema_version")
    if schema_version is not None and schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    # Optional review metadata, validated exactly as for skills so a worker can
    # be human-reviewed and matured through the contributing loop.
    for key in ("reviewed_by", "expertise_domain"):
        if key in frontmatter and not isinstance(frontmatter[key], list):
            errors.append(f"frontmatter key '{key}' must be a list")

    review_status = frontmatter.get("review_status")
    if review_status is not None and review_status not in VALID_REVIEW_STATUS:
        errors.append(f"review_status must be one of: {', '.join(sorted(VALID_REVIEW_STATUS))}")

    confidence = frontmatter.get("confidence")
    if confidence is not None and confidence not in VALID_CONFIDENCE:
        errors.append(f"confidence must be one of: {', '.join(sorted(VALID_CONFIDENCE))}")

    reviewed_at = frontmatter.get("reviewed_at")
    if reviewed_at is not None:
        value = str(reviewed_at)
        if not DATE_RE.match(value):
            errors.append("reviewed_at must use YYYY-MM-DD")
        else:
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append("reviewed_at is not a valid calendar date")

    skills = frontmatter.get("skills", [])
    if "skills" in frontmatter and not isinstance(skills, list):
        errors.append("frontmatter key 'skills' must be a list")
    elif isinstance(skills, list):
        index_ids = load_index_ids(root)
        for ref in skills:
            if not skill_reference_exists(str(ref), root, index_ids):
                errors.append(f"referenced skill does not resolve: {ref}")

    # Workers are bundle-local: the agents/ folder must sit beside an orchestrator SKILL.md.
    if "agents" in path.parts:
        agents_dir = path.parent
        while agents_dir.name != "agents" and agents_dir != agents_dir.parent:
            agents_dir = agents_dir.parent
        if not (agents_dir.parent / "SKILL.md").exists():
            errors.append("worker agents/ folder must sit beside an orchestrator SKILL.md")

    if not PROVENANCE_RE.search(text):
        errors.append("missing provenance comment: <!-- learned: YYYY-MM | project: ... | model: ... -->")

    for pattern in VENDOR_LANGUAGE:
        match = pattern.search(body)
        if match:
            errors.append(f"vendor-specific instruction language found: {match.group(0)!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Markdown skill file to lint")
    parser.add_argument("--all", action="store_true", help="Lint every skill file under skills/")
    args = parser.parse_args()

    root = repo_root(Path.cwd())
    if args.all:
        skill_paths = discover_skill_files(root)
        agent_paths = discover_agent_files(root)
    elif args.path:
        target = Path(args.path)
        if "agents" in target.resolve().parts:
            skill_paths, agent_paths = [], [target]
        else:
            skill_paths, agent_paths = [target], []
    else:
        skill_paths, agent_paths = [], []
    if not skill_paths and not agent_paths:
        parser.error("provide a path or --all")

    failed = False
    for path in skill_paths:
        errors = lint(path)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
        else:
            print(f"OK: {path}")
    for path in agent_paths:
        errors = lint_agent(path)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
        else:
            print(f"OK (agent): {path}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
