"""Optional Typer/Rich CLI for Cortex deployment UX."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table


BANNER = r"""
   ______ ____   ____   ______ ______ _  __
  / ____// __ \ / __ \ /_  __// ____/| |/ /
 / /    / / / // /_/ /  / /  / __/   |   /
/ /___ / /_/ // _, _/  / /  / /___  /   |
\____/ \____//_/ |_|  /_/  /_____/ /_/|_|
"""


def repo_root() -> Path:
    env_root = os.environ.get("CORTEX_ROOT")
    candidates: list[Path] = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path.cwd(), *Path.cwd().parents])
    package_root = Path(__file__).resolve()
    candidates.extend([package_root, *package_root.parents])

    for candidate in candidates:
        root = candidate if candidate.is_dir() else candidate.parent
        if (root / "scripts" / "install-skills.py").is_file() and (
            root / "skills" / "meta" / "scripts" / "validate.py"
        ).is_file():
            return root

    console.print(
        "[red]Could not find Cortex repository root. "
        "Run from the repo or set CORTEX_ROOT.[/red]"
    )
    raise typer.Exit(1)


console = Console()
ROOT = repo_root()
INSTALLER = ROOT / "scripts" / "install-skills.py"
VALIDATE = ROOT / "skills" / "meta" / "scripts" / "validate.py"
CAPTURE_EXPERTISE = ROOT / "skills" / "meta" / "scripts" / "capture_expertise.py"
SKILL_BRIEF = ROOT / "skills" / "meta" / "scripts" / "skill_brief.py"
PROFILE_DIR = ROOT / ".cortex" / "profiles"
DEFAULT_PROFILE_NAME = "default"
AGENTS = ("codex", "claude", "cursor")
SCOPES = ("global", "project")
MODES = ("wrapper", "symlink", "copy")
INSTALLER_ACTIONS = ("install", "status", "sync", "repair", "uninstall")
COMPLETION_SHELLS = ("powershell", "bash", "zsh", "fish")
CORE_DOMAIN = "meta"

app = typer.Typer(
    help="Cortex enhanced CLI. Core validation and fallback installer remain stdlib scripts.",
    no_args_is_help=True,
)
profile_app = typer.Typer(help="Manage saved Cortex install profiles.", no_args_is_help=True)
team_app = typer.Typer(help="Use the committed team deployment profile.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")
app.add_typer(team_app, name="team")


def profile_path(name: str) -> Path:
    clean = "".join(ch.lower() if ch.isalnum() or ch in "-_" else "-" for ch in name).strip("-")
    if not clean:
        console.print("[red]Profile name must contain at least one letter or number.[/red]")
        raise typer.Exit(1)
    return PROFILE_DIR / f"{clean}.json"


def team_profile_path() -> Path:
    return ROOT / "profiles" / "team-codex-claude.json"


def load_profile(name: Optional[str]) -> dict[str, str]:
    if not name:
        return {}
    path = profile_path(name)
    if not path.exists():
        console.print(f"[red]Profile not found:[/red] {path}")
        raise typer.Exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile_file(path: Optional[Path]) -> dict[str, str]:
    if path is None:
        return {}
    resolved = path if path.is_absolute() else ROOT / path
    if not resolved.exists():
        console.print(f"[red]Profile file not found:[/red] {resolved}")
        raise typer.Exit(1)
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        console.print(f"[red]Profile file must contain a JSON object:[/red] {resolved}")
        raise typer.Exit(1)
    return {str(key): str(value) for key, value in data.items() if value is not None}


def write_profile(name: str, data: dict[str, str]) -> Path:
    path = profile_path(name)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def write_profile_file(path: Path, data: dict[str, str]) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return resolved


def merge_profile(
    profile: Optional[str],
    profile_file: Optional[Path],
    skills: Optional[str],
    categories: Optional[str],
    agents: Optional[str],
    scope: Optional[str],
    mode: Optional[str],
    project: Optional[Path],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[Path]]:
    data = {**load_profile_file(profile_file), **load_profile(profile)}
    skills = skills or data.get("skills")
    categories = categories or data.get("categories")
    agents = agents or data.get("agents")
    scope = scope or data.get("scope")
    mode = mode or data.get("mode")
    if project is None and data.get("project"):
        project = Path(data["project"])
    return skills, categories, agents, scope, mode, project


def read_key() -> str:
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key == "\xe0":
            arrow = msvcrt.getwch()
            return {"H": "up", "P": "down"}.get(arrow, "")
        return {"\r": "enter", " ": "space"}.get(key, key.lower())

    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        key = sys.stdin.read(1)
        if key == "\x1b" and sys.stdin.read(1) == "[":
            arrow = sys.stdin.read(1)
            return {"A": "up", "B": "down"}.get(arrow, "")
        return {"\n": "enter", " ": "space"}.get(key, key.lower())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def multi_select(title: str, options: list[str], selected: set[int] | None = None) -> set[int]:
    if not sys.stdin.isatty():
        console.print(f"[red]{title} requires a TTY. Use flags or --profile instead.[/red]")
        raise typer.Exit(1)
    selected = set(selected or set())
    cursor = 0
    while True:
        console.clear()
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print("[dim]Use Up/Down, Space to toggle, Enter to continue, q to cancel.[/dim]\n")
        for index, option in enumerate(options):
            style = "bold reverse" if index == cursor else ""
            console.print(format_multi_select_row(option, active=index == cursor, selected=index in selected), style=style)
        key = read_key()
        if key == "enter":
            console.clear()
            return selected
        if key == "q":
            console.clear()
            raise typer.Exit(1)
        if key == "space":
            if cursor in selected:
                selected.remove(cursor)
            else:
                selected.add(cursor)
        elif key == "up":
            cursor = (cursor - 1) % len(options)
        elif key == "down":
            cursor = (cursor + 1) % len(options)


def format_multi_select_row(option: str, active: bool, selected: bool) -> str:
    pointer = ">" if active else " "
    mark = "*" if selected else " "
    return f"{pointer} {mark} {option}"


def single_select(title: str, options: list[str], default: str) -> str:
    default_index = options.index(default) if default in options else 0
    cursor = default_index
    if not sys.stdin.isatty():
        console.print(f"[red]{title} requires a TTY. Use flags or --profile instead.[/red]")
        raise typer.Exit(1)
    while True:
        console.clear()
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print("[dim]Use Up/Down, Enter to continue, q to cancel.[/dim]\n")
        for index, option in enumerate(options):
            pointer = ">" if index == cursor else " "
            mark = "(*) " if index == cursor else "( ) "
            style = "bold reverse" if index == cursor else ""
            console.print(f"{pointer} {mark}{option}", style=style)
        key = read_key()
        if key == "enter":
            console.clear()
            return options[cursor]
        if key == "q":
            console.clear()
            raise typer.Exit(1)
        if key == "up":
            cursor = (cursor - 1) % len(options)
        elif key == "down":
            cursor = (cursor + 1) % len(options)


def skill_records() -> list[dict[str, str]]:
    sys.path.insert(0, str(ROOT / "skills" / "meta" / "scripts"))
    import lint_skill  # type: ignore

    records: list[dict[str, str]] = []
    for path in lint_skill.discover_skill_files(ROOT):
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = lint_skill.parse_frontmatter(text)
        skill_id = str(frontmatter.get("skill_id", ""))
        records.append(
            {
                "skill_id": skill_id,
                "domain": skill_id.split("/", 1)[0],
                "summary": str(frontmatter.get("summary", "")),
            }
        )
    return sorted(records, key=lambda item: item["skill_id"])


def guided_selectable_skills(
    records: list[dict[str, str]],
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    selectable = [record for record in records if record["domain"] != CORE_DOMAIN]
    domains = sorted({record["domain"] for record in selectable})
    skill_options = [f"{record['skill_id']} - {record['summary']}" for record in selectable]
    return domains, skill_options, selectable


def guided_selection_values(
    categories: list[str],
    selected_skill_ids: list[str],
    agents: list[str],
    scope: str,
    mode: str,
    project: str,
) -> dict[str, str]:
    values = {
        "agents": ",".join(agents),
        "scope": scope,
        "mode": mode,
    }
    if categories:
        values["categories"] = "all" if "all" in categories else ",".join(sorted(categories))
    if selected_skill_ids:
        values["skills"] = ",".join(selected_skill_ids)
    if project:
        values["project"] = project
    return values


def run_command(args: list[str]) -> None:
    console.print(f"[dim]$ {' '.join(args)}[/dim]")
    result = subprocess.run(args, cwd=ROOT)
    raise typer.Exit(result.returncode)


def run_command_capture(args: list[str]) -> subprocess.CompletedProcess[str]:
    console.print(f"[dim]$ {' '.join(args)}[/dim]")
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


STATUS_STATES = {"current", "stale", "missing", "unmanaged", "unsupported"}
DRIFT_STATES = {"stale", "missing"}


def parse_status_rows(output: str) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for line in output.splitlines():
        if " -> " not in line:
            continue
        left, target = line.split(" -> ", 1)
        parts = left.split(maxsplit=3)
        if len(parts) != 4 or parts[0] not in STATUS_STATES:
            continue
        rows.append((parts[0], parts[1], parts[2], parts[3], target))
    return rows


def render_status_table(output: str) -> bool:
    rows = parse_status_rows(output)
    if not rows:
        return False

    table = Table(title="Cortex Native Skill Status", box=box.SIMPLE_HEAVY)
    table.add_column("State", style="bold")
    table.add_column("Agent")
    table.add_column("Scope")
    table.add_column("Skill")
    table.add_column("Target", overflow="fold")
    state_styles = {
        "current": "green",
        "stale": "yellow",
        "missing": "red",
        "unmanaged": "magenta",
        "unsupported": "dim",
    }
    for state, agent, scope, skill, target in rows:
        table.add_row(f"[{state_styles[state]}]{state}[/{state_styles[state]}]", agent, scope, skill, target)
    console.print(table)
    return True


def installer_args(
    action: str,
    skills: Optional[str],
    categories: Optional[str],
    agents: Optional[str],
    scope: Optional[str],
    mode: Optional[str],
    project: Optional[Path],
    dry_run: bool,
    yes: bool,
    hide_missing: bool = False,
) -> list[str]:
    args = [sys.executable, str(INSTALLER), "--action", action]
    if skills:
        args.extend(["--skills", skills])
    if categories:
        args.extend(["--categories", categories])
    if agents:
        args.extend(["--agents", agents])
    if scope:
        args.extend(["--scope", scope])
    if mode:
        args.extend(["--mode", mode])
    if project:
        args.extend(["--project", str(project)])
    if dry_run:
        args.append("--dry-run")
    if yes:
        args.append("--yes")
    if action == "status" and hide_missing:
        args.append("--hide-missing")
    return args


def apply_agent_flags(
    agents: Optional[str],
    codex: bool = False,
    claude: bool = False,
    cursor: bool = False,
) -> Optional[str]:
    selected = [name for name, enabled in (("codex", codex), ("claude", claude), ("cursor", cursor)) if enabled]
    if not selected:
        return agents
    if not agents:
        return ",".join(selected)
    existing = [part.strip() for part in agents.split(",") if part.strip()]
    for name in selected:
        if name not in existing:
            existing.append(name)
    return ",".join(existing)


def run_installer(
    action: str,
    skills: Optional[str],
    categories: Optional[str],
    agents: Optional[str],
    scope: Optional[str],
    mode: Optional[str],
    project: Optional[Path],
    dry_run: bool,
    yes: bool,
    profile: Optional[str] = None,
    profile_file: Optional[Path] = None,
    hide_missing: bool = False,
) -> int:
    skills, categories, agents, scope, mode, project = merge_profile(
        profile, profile_file, skills, categories, agents, scope, mode, project
    )
    console.print(f"[bold cyan]Cortex {action}[/bold cyan]")
    args = installer_args(action, skills, categories, agents, scope, mode, project, dry_run, yes, hide_missing)
    console.print(f"[dim]$ {' '.join(args)}[/dim]")
    return subprocess.run(args, cwd=ROOT).returncode


def dispatch_installer(
    action: str,
    skills: Optional[str],
    categories: Optional[str],
    agents: Optional[str],
    scope: Optional[str],
    mode: Optional[str],
    project: Optional[Path],
    dry_run: bool,
    yes: bool,
    profile: Optional[str] = None,
    profile_file: Optional[Path] = None,
    hide_missing: bool = False,
) -> None:
    raise typer.Exit(
        run_installer(action, skills, categories, agents, scope, mode, project, dry_run, yes, profile, profile_file, hide_missing)
    )


def run_status_with_profile_file(profile_file: Path, raw: bool, agents_override: Optional[str] = None, show_missing: bool = False) -> None:
    skills, categories, agents, scope, mode, project = merge_profile(
        None, profile_file, None, None, None, None, None, None
    )
    agents = agents_override or agents
    console.print("[bold cyan]Cortex status[/bold cyan]")
    args = installer_args("status", skills, categories, agents, scope, mode, project, False, True, hide_missing=not show_missing)
    result = run_command_capture(args)
    if result.returncode != 0:
        console.print(result.stdout)
        console.print(result.stderr, style="red")
        raise typer.Exit(result.returncode)
    if raw or not render_status_table(result.stdout):
        console.print(result.stdout)


def run_finish_with_profile_file(profile_file: Path, dry_run: bool, yes: bool, raw: bool) -> None:
    skills, categories, agents, scope, mode, project = merge_profile(
        None, profile_file, None, None, None, None, None, None
    )
    run_finish_lifecycle(skills, categories, agents, scope, mode, project, dry_run, yes, raw)


def run_finish_lifecycle(
    skills: Optional[str],
    categories: Optional[str],
    agents: Optional[str],
    scope: Optional[str],
    mode: Optional[str],
    project: Optional[Path],
    dry_run: bool,
    yes: bool,
    raw: bool,
) -> None:
    console.print("[bold cyan]Cortex finish[/bold cyan]")

    validate_result = subprocess.run(
        [sys.executable, str(VALIDATE), "--fix-generated"],
        cwd=ROOT,
    )
    if validate_result.returncode != 0:
        raise typer.Exit(validate_result.returncode)

    console.print("[bold cyan]Native package status[/bold cyan]")
    status_args = installer_args("status", skills, categories, agents, scope, mode, project, False, True)
    status_result = run_command_capture(status_args)
    if status_result.returncode != 0:
        console.print(status_result.stdout)
        console.print(status_result.stderr, style="red")
        raise typer.Exit(status_result.returncode)
    if raw or not render_status_table(status_result.stdout):
        console.print(status_result.stdout)

    drifted_skills = sorted(
        {skill for state, _agent, _scope, skill, _target in parse_status_rows(status_result.stdout) if state in DRIFT_STATES}
    )
    if not drifted_skills:
        console.print("[green]No stale or missing managed packages found.[/green]")
        return

    console.print("[bold cyan]Native package sync[/bold cyan]")
    console.print(f"[yellow]Drift detected:[/yellow] {', '.join(drifted_skills)}")
    if dry_run:
        console.print("[yellow]Preview complete. Review the drift before writing managed packages.[/yellow]")
    sync_args = installer_args("sync", ",".join(drifted_skills), None, agents, scope, mode, project, dry_run, yes)
    sync_result = subprocess.run(sync_args, cwd=ROOT)
    if sync_result.returncode != 0:
        raise typer.Exit(sync_result.returncode)

    if dry_run:
        if yes or not Confirm.ask("Apply this sync now?", default=False):
            return
        write_args = installer_args("sync", ",".join(drifted_skills), None, agents, scope, mode, project, False, True)
        write_result = subprocess.run(write_args, cwd=ROOT)
        if write_result.returncode != 0:
            raise typer.Exit(write_result.returncode)

    console.print("[bold cyan]Native package status after sync[/bold cyan]")
    final_status = run_command_capture(status_args)
    if final_status.returncode != 0:
        console.print(final_status.stdout)
        console.print(final_status.stderr, style="red")
        raise typer.Exit(final_status.returncode)
    if raw or not render_status_table(final_status.stdout):
        console.print(final_status.stdout)


@app.command()
def about() -> None:
    """Show the Cortex identity banner and local tool paths."""
    console.print(BANNER, style="bold cyan")
    console.print("[bold]Cortex[/bold] compounds agent skills in a markdown/git vault.")
    console.print(f"[dim]vault:[/dim] {ROOT}")
    console.print(f"[dim]validate:[/dim] {VALIDATE}")
    console.print(f"[dim]installer:[/dim] {INSTALLER}")


@app.command()
def install(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: Optional[str] = typer.Option(None, help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(False, help="Print planned writes without changing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation in scripted mode."),
) -> None:
    """Install selected Cortex skills into native agent targets."""
    dispatch_installer("install", skills, categories, agents, scope, mode, project, dry_run, yes, profile, profile_file)


@app.command()
def status(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    codex: bool = typer.Option(False, "--codex", help="Show Codex targets."),
    claude: bool = typer.Option(False, "--claude", help="Show Claude targets."),
    cursor: bool = typer.Option(False, "--cursor", help="Show Cursor targets."),
    scope: Optional[str] = typer.Option(None, help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    show_missing: bool = typer.Option(False, help="Include missing packages in status output."),
    raw: bool = typer.Option(False, help="Print raw stdlib installer output instead of a Rich table."),
) -> None:
    """Show whether selected native installs are current, stale, missing, or unmanaged."""
    agents = apply_agent_flags(agents, codex, claude, cursor)
    skills, categories, agents, scope, mode, project = merge_profile(
        profile, profile_file, skills, categories, agents, scope, mode, project
    )
    console.print("[bold cyan]Cortex status[/bold cyan]")
    args = installer_args("status", skills, categories, agents, scope, mode, project, False, True, hide_missing=not show_missing)
    result = run_command_capture(args)
    if result.returncode != 0:
        console.print(result.stdout)
        console.print(result.stderr, style="red")
        raise typer.Exit(result.returncode)
    if raw or not render_status_table(result.stdout):
        console.print(result.stdout)


@app.command()
def sync(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: Optional[str] = typer.Option(None, help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(False, help="Print planned writes without changing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation in scripted mode."),
) -> None:
    """Regenerate selected managed native packages from current Cortex source."""
    dispatch_installer("sync", skills, categories, agents, scope, mode, project, dry_run, yes, profile, profile_file)


@app.command()
def repair(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: Optional[str] = typer.Option(None, help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(False, help="Print planned writes without changing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation in scripted mode."),
) -> None:
    """Repair selected managed native packages."""
    dispatch_installer("repair", skills, categories, agents, scope, mode, project, dry_run, yes, profile, profile_file)


@app.command()
def uninstall(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: Optional[str] = typer.Option(None, help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(False, help="Print planned writes without changing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation in scripted mode."),
) -> None:
    """Remove selected Cortex-managed native packages."""
    dispatch_installer("uninstall", skills, categories, agents, scope, mode, project, dry_run, yes, profile, profile_file)


@app.command()
def cleanup(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids. Defaults to all Cortex skills."),
    categories: Optional[str] = typer.Option("all", help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'. Defaults to codex,claude."),
    codex: bool = typer.Option(False, "--codex", help="Clean Codex targets."),
    claude: bool = typer.Option(False, "--claude", help="Clean Claude targets."),
    cursor: bool = typer.Option(False, "--cursor", help="Clean Cursor targets."),
    scope: Optional[str] = typer.Option("global", help="Install scope: global or project."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped cleanup."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(True, help="Preview removals first; interactive runs can approve the cleanup after review."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation when writing."),
) -> None:
    """Remove Cortex-managed native packages selected by skill, category, agent, and scope."""
    agents = apply_agent_flags(agents, codex, claude, cursor)
    if agents is None:
        agents = "codex,claude"
    exit_code = run_installer("cleanup", skills, categories, agents, scope, None, project, dry_run, True, profile, profile_file)
    if exit_code != 0:
        raise typer.Exit(exit_code)
    if dry_run and not yes:
        if not Confirm.ask("Apply this cleanup now?", default=False):
            return
        exit_code = run_installer("cleanup", skills, categories, agents, scope, None, project, False, True, profile, profile_file)
        if exit_code != 0:
            raise typer.Exit(exit_code)


@profile_app.command("list")
def list_profiles() -> None:
    """List saved install profiles."""
    if not PROFILE_DIR.exists():
        console.print("[dim]No profiles saved yet.[/dim]")
        return
    table = Table(title="Cortex Profiles", box=box.SIMPLE)
    table.add_column("Name", style="bold cyan")
    table.add_column("Categories")
    table.add_column("Skills")
    table.add_column("Agents")
    table.add_column("Scope")
    table.add_column("Mode")
    for path in sorted(PROFILE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        table.add_row(
            path.stem,
            data.get("categories", "-"),
            data.get("skills", "-"),
            data.get("agents", "-"),
            data.get("scope", "-"),
            data.get("mode", "-"),
        )
    console.print(table)


@profile_app.command("show")
def show_profile(name: str) -> None:
    """Show one saved install profile."""
    data = load_profile(name)
    table = Table(title=f"Profile: {name}", box=box.SIMPLE)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    for key in ("categories", "skills", "agents", "scope", "mode", "project"):
        table.add_row(key, data.get(key, "-"))
    console.print(table)


@profile_app.command("delete")
def delete_profile(
    name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation."),
) -> None:
    """Delete one saved install profile."""
    path = profile_path(name)
    if not path.exists():
        console.print(f"[red]Profile not found:[/red] {path}")
        raise typer.Exit(1)
    if not yes and not Confirm.ask(f"Delete profile '{path.stem}'?", default=False):
        raise typer.Exit(0)
    path.unlink()
    console.print(f"[green]Deleted profile:[/green] {path}")


@profile_app.command("save")
def save_profile(
    name: str,
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option(None, help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option(None, help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: str = typer.Option("global", help="Install scope: global or project."),
    mode: str = typer.Option("wrapper", help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile_file: Optional[Path] = typer.Option(None, help="Also write this profile to an explicit JSON path."),
) -> None:
    """Save a profile without opening the interactive wizard."""
    if not skills and not categories:
        console.print("[red]Provide --skills, --categories, or both.[/red]")
        raise typer.Exit(1)
    if scope not in SCOPES:
        console.print(f"[red]Scope must be one of: {', '.join(SCOPES)}[/red]")
        raise typer.Exit(1)
    if mode not in MODES:
        console.print(f"[red]Mode must be one of: {', '.join(MODES)}[/red]")
        raise typer.Exit(1)
    data = {
        "scope": scope,
        "mode": mode,
    }
    if skills:
        data["skills"] = skills
    if categories:
        data["categories"] = categories
    if agents:
        data["agents"] = agents
    if project:
        data["project"] = str(project)
    path = write_profile(name, data)
    console.print(f"[green]Saved profile:[/green] {path}")
    if profile_file:
        shared_path = write_profile_file(profile_file, data)
        console.print(f"[green]Saved shared profile:[/green] {shared_path}")


@profile_app.command("validate-file")
def validate_profile_file(path: Path) -> None:
    """Validate a shared profile JSON file."""
    data = load_profile_file(path)
    missing_selection = not data.get("skills") and not data.get("categories")
    errors: list[str] = []
    if missing_selection:
        errors.append("provide 'skills', 'categories', or both")
    if data.get("scope") and data["scope"] not in SCOPES:
        errors.append(f"scope must be one of: {', '.join(SCOPES)}")
    if data.get("mode") and data["mode"] not in MODES:
        errors.append(f"mode must be one of: {', '.join(MODES)}")
    if data.get("agents"):
        requested = {part.strip() for part in data["agents"].split(",") if part.strip()}
        unknown = sorted(agent for agent in requested if agent not in AGENTS and agent != "all")
        if unknown:
            errors.append(f"unknown agents: {', '.join(unknown)}")
    if errors:
        for error in errors:
            console.print(f"[red]ERROR:[/red] {error}")
        raise typer.Exit(1)
    console.print(f"[green]OK:[/green] {path}")


@team_app.command("status")
def team_status(
    agents: Optional[str] = typer.Option(None, help="Override profile agents with codex,claude,cursor, or all."),
    codex: bool = typer.Option(False, "--codex", help="Show Codex targets."),
    claude: bool = typer.Option(False, "--claude", help="Show Claude targets."),
    cursor: bool = typer.Option(False, "--cursor", help="Show Cursor targets."),
    show_missing: bool = typer.Option(False, help="Include missing packages in status output."),
    raw: bool = typer.Option(False, help="Print raw installer output instead of a Rich table."),
) -> None:
    """Show status using profiles/team-codex-claude.json."""
    run_status_with_profile_file(team_profile_path(), raw, apply_agent_flags(agents, codex, claude, cursor), show_missing)


@team_app.command("finish")
def team_finish(
    dry_run: bool = typer.Option(True, help="Preview package sync first; interactive runs can approve the write after review."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation when writing."),
    raw: bool = typer.Option(False, help="Print raw installer output instead of a Rich table."),
) -> None:
    """Daily command after committing: validate (--fix-generated), inspect native packages, sync drift, and inspect again using the team profile."""
    run_finish_with_profile_file(team_profile_path(), dry_run, yes, raw)


@team_app.command("sync")
def team_sync(
    dry_run: bool = typer.Option(True, help="Preview planned writes. Use --no-dry-run for non-interactive writes."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation when writing."),
) -> None:
    """Sync managed native packages selected by the team profile."""
    dispatch_installer("sync", None, None, None, None, None, None, dry_run, yes, None, team_profile_path())


@team_app.command("profile")
def team_profile() -> None:
    """Show the committed team deployment profile path and contents."""
    path = team_profile_path()
    data = load_profile_file(path)
    table = Table(title=f"Team Profile: {path.relative_to(ROOT)}", box=box.SIMPLE)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    for key in ("categories", "skills", "agents", "scope", "mode", "project"):
        table.add_row(key, data.get(key, "-"))
    console.print(table)


def guided_values() -> dict[str, str]:
    records = skill_records()
    domains, skill_options, selectable_records = guided_selectable_skills(records)

    category_options = ["all", *domains, "individual skills only"]
    category_indexes = multi_select("Select skill categories", category_options, {0})
    selected_categories = {category_options[index] for index in category_indexes}
    individual_only = "individual skills only" in selected_categories
    if individual_only:
        categories = []
    elif "all" in selected_categories:
        categories = ["all"]
    else:
        categories = sorted(selected_categories)

    skill_ids: list[str] = []
    if "all" not in categories:
        skill_indexes = multi_select("Select individual skills to include, or press Enter to skip", skill_options)
        skill_ids = [selectable_records[index]["skill_id"] for index in sorted(skill_indexes)]
    if not categories and not skill_ids:
        console.print("[red]Select at least one category or individual skill.[/red]")
        raise typer.Exit(1)

    agent_indexes = multi_select("Select target agents", list(AGENTS), {0, 1})
    agents = ",".join(AGENTS[index] for index in sorted(agent_indexes))
    if not agents:
        console.print("[red]Select at least one agent.[/red]")
        raise typer.Exit(1)

    scope = single_select("Select install scope", list(SCOPES), "global")
    mode = single_select("Select install mode", list(MODES), "wrapper")
    project = ""
    if scope == "project":
        project = Prompt.ask("Project root", default=str(ROOT))

    console.print("[dim]Cortex core meta skills are included automatically.[/dim]")
    return guided_selection_values(categories, skill_ids, agents.split(","), scope, mode, project)


@app.command("first-run")
def first_run(
    action: str = typer.Option("install", help="Installer action to run after selection."),
    save_profile: Optional[str] = typer.Option(None, help="Profile name to save selections under (e.g. 'default')."),
    save_profile_file: Optional[Path] = typer.Option(None, help="Path to save selections as a shared profile JSON file."),
    dry_run: bool = typer.Option(True, help="Preview planned writes first; interactive runs can approve the install after review."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip final confirmation prompt."),
) -> None:
    """Guided first-run setup for selecting skills, agents, scope, and mode."""
    if action not in INSTALLER_ACTIONS:
        console.print(f"[red]Action must be one of: {', '.join(INSTALLER_ACTIONS)}[/red]")
        raise typer.Exit(1)

    console.print(BANNER, style="bold cyan")
    console.print("[bold]Cortex first-run setup[/bold]")
    console.print("[dim]The stdlib installer remains available for scripted or dependency-free use.[/dim]\n")
    values = guided_values()
    if save_profile is None and Confirm.ask(
        "Save these choices as a reusable local profile?", default=False
    ):
        # The answer is a profile name (a filename under .cortex/profiles), not yes/no,
        # so show a default name and let an empty entry fall back to it.
        save_profile = Prompt.ask("Profile name", default=DEFAULT_PROFILE_NAME).strip() or DEFAULT_PROFILE_NAME
    if save_profile_file is None and Confirm.ask(
        "Also save to a shared profile file for committing or sharing?", default=False
    ):
        default_shared = str(ROOT / "profiles" / f"{save_profile or DEFAULT_PROFILE_NAME}.json")
        shared_path = Prompt.ask("Shared profile file path", default=default_shared).strip()
        save_profile_file = Path(shared_path) if shared_path else None

    if save_profile:
        path = write_profile(save_profile, values)
        console.print(f"[green]Saved profile:[/green] {path}")
    if save_profile_file:
        path = write_profile_file(save_profile_file, values)
        console.print(f"[green]Saved shared profile:[/green] {path}")

    summary = Table(title="Planned Selection", box=box.SIMPLE)
    summary.add_column("Field", style="bold cyan")
    summary.add_column("Value")
    for key, value in values.items():
        summary.add_row(key, value)
    summary.add_row("action", action)
    summary.add_row("dry_run", str(dry_run))
    console.print(summary)

    if not yes and not Confirm.ask("Run this command now?", default=dry_run):
        raise typer.Exit(0)

    exit_code = run_installer(
        action,
        values.get("skills"),
        values.get("categories"),
        values.get("agents"),
        values.get("scope"),
        values.get("mode"),
        Path(values["project"]) if values.get("project") else None,
        dry_run,
        True,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)

    if dry_run and action in {"install", "sync", "repair"} and not yes:
        if Confirm.ask("Apply this same selection now?", default=False):
            exit_code = run_installer(
                action,
                values.get("skills"),
                values.get("categories"),
                values.get("agents"),
                values.get("scope"),
                values.get("mode"),
                Path(values["project"]) if values.get("project") else None,
                False,
                True,
            )
            if exit_code != 0:
                raise typer.Exit(exit_code)


@app.command()
def validate(
    fix_generated: bool = typer.Option(False, help="Rebuild generated catalogs before validating."),
) -> None:
    """Run the stdlib Cortex validation contract."""
    args = [sys.executable, str(VALIDATE)]
    if fix_generated:
        args.append("--fix-generated")
    console.print("[bold cyan]Cortex validate[/bold cyan]")
    run_command(args)


@app.command()
def finish(
    skills: Optional[str] = typer.Option(None, help="Comma-separated skill ids, or 'all'."),
    categories: Optional[str] = typer.Option("all", help="Comma-separated domains/categories, or 'all'."),
    agents: Optional[str] = typer.Option("codex,claude", help="Comma-separated agents: codex,claude,cursor, or 'all'."),
    scope: Optional[str] = typer.Option("global", help="Install scope: global or project."),
    mode: Optional[str] = typer.Option(None, help="Install mode: wrapper, symlink, or copy."),
    project: Optional[Path] = typer.Option(None, help="Project root for project-scoped installs."),
    profile: Optional[str] = typer.Option(None, help="Saved profile name to use as defaults."),
    profile_file: Optional[Path] = typer.Option(None, help="Shared profile JSON file to use as defaults."),
    dry_run: bool = typer.Option(True, help="Preview package sync first; interactive runs can approve the write after review."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation in scripted mode."),
    raw: bool = typer.Option(False, help="Print raw stdlib installer status output instead of a Rich table."),
) -> None:
    """Daily command after committing: validate (--fix-generated), inspect native packages, sync managed drift, and inspect again."""
    skills, categories, agents, scope, mode, project = merge_profile(
        profile, profile_file, skills, categories, agents, scope, mode, project
    )
    run_finish_lifecycle(skills, categories, agents, scope, mode, project, dry_run, yes, raw)


@app.command()
def completion(
    shell: str = typer.Argument("powershell", help="Shell: powershell, bash, zsh, or fish."),
    install: bool = typer.Option(False, help="Show the Typer install command for this shell."),
) -> None:
    """Show first-party shell completion setup for Cortex."""
    if shell not in COMPLETION_SHELLS:
        console.print(f"[red]Shell must be one of: {', '.join(COMPLETION_SHELLS)}[/red]")
        raise typer.Exit(1)

    if install:
        console.print(f"[bold cyan]Install completion for {shell}[/bold cyan]")
        console.print(f"uv run cortex --install-completion {shell}")
        console.print("cortex --install-completion " + shell)
        return

    snippets = {
        "powershell": [
            "Preview for this session:",
            "uv run cortex --show-completion powershell | Out-String | Invoke-Expression",
            "",
            "Install through Typer:",
            "uv run cortex --install-completion powershell",
            "",
            "If you use a wrapper function named cortex, add the completion line after the wrapper in $PROFILE.",
        ],
        "bash": [
            "Preview for this session:",
            'eval "$(uv run cortex --show-completion bash)"',
            "",
            "Install through Typer:",
            "uv run cortex --install-completion bash",
            "",
            "Common manual install:",
            "mkdir -p ~/.local/share/bash-completion/completions",
            "uv run cortex --show-completion bash > ~/.local/share/bash-completion/completions/cortex",
        ],
        "zsh": [
            "Preview for this session:",
            'eval "$(uv run cortex --show-completion zsh)"',
            "",
            "Install through Typer:",
            "uv run cortex --install-completion zsh",
            "",
            "Common manual install:",
            "mkdir -p ~/.zfunc",
            "uv run cortex --show-completion zsh > ~/.zfunc/_cortex",
            "Add `fpath=(~/.zfunc $fpath)` and `autoload -Uz compinit && compinit` to ~/.zshrc if needed.",
        ],
        "fish": [
            "Preview for this session:",
            "uv run cortex --show-completion fish | source",
            "",
            "Install through Typer:",
            "uv run cortex --install-completion fish",
        ],
    }
    console.print(f"[bold cyan]Cortex completion for {shell}[/bold cyan]")
    console.print("\n".join(snippets[shell]))


@app.command()
def expertise(
    skill: Optional[str] = typer.Argument(None, help="Skill id such as forensics/pcap."),
    claim: Optional[str] = typer.Option(None, help="Concrete expertise claim to capture."),
    details: Optional[str] = typer.Option(None, help="Optional supporting context or caveat."),
    reviewer: Optional[str] = typer.Option(None, help="Human name, handle, role, or team."),
    domain: Optional[str] = typer.Option(None, help="Comma-separated expertise domains."),
    status: str = typer.Option("human-noted", help="human-noted, reviewed, disputed, or needs-refresh."),
    confidence: str = typer.Option("medium", help="low, medium, or high."),
    kind: str = typer.Option("domain-expertise", help="preference, operational-experience, or domain-expertise."),
    validate_after: bool = typer.Option(True, help="Run Cortex validation after capturing."),
) -> None:
    """Capture human expertise against a skill without hand-editing markdown."""
    guided = sys.stdin.isatty() and (skill is None or claim is None)
    if guided:
        console.print(BANNER, style="bold cyan")
        console.print("[bold]Cortex expertise capture[/bold]")
        console.print("[dim]Record durable human knowledge against an existing skill.[/dim]\n")
        records = skill_records()
        if skill is None:
            options = [f"{record['skill_id']} - {record['summary']}" for record in records]
            selected = single_select("Select skill", options, options[0])
            skill = selected.split(" - ", 1)[0]
        if claim is None:
            claim = Prompt.ask("Durable claim")
        details = details if details is not None else Prompt.ask("Details or caveat", default="")
        reviewer = reviewer if reviewer is not None else Prompt.ask("Reviewer, role, or team", default="")
        domain = domain if domain is not None else Prompt.ask("Expertise domain", default="")
        status = single_select(
            "Review status",
            ["human-noted", "reviewed", "disputed", "needs-refresh"],
            status,
        )
        confidence = single_select("Confidence", ["low", "medium", "high"], confidence)
        kind = single_select(
            "Contribution kind",
            ["domain-expertise", "operational-experience", "preference"],
            kind,
        )

    if not skill or not claim:
        console.print("[red]Provide a skill id and --claim, or run interactively in a TTY.[/red]")
        raise typer.Exit(1)

    args = [
        sys.executable,
        str(CAPTURE_EXPERTISE),
        skill,
        "--claim",
        claim,
        "--status",
        status,
        "--confidence",
        confidence,
        "--kind",
        kind,
    ]
    if details:
        args.extend(["--details", details])
    if reviewer:
        args.extend(["--reviewer", reviewer])
    if domain:
        args.extend(["--domain", domain])
    console.print("[bold cyan]Cortex expertise capture[/bold cyan]")
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)
    if validate_after:
        run_command([sys.executable, str(VALIDATE), "--fix-generated"])


def prompt_if_missing(label: str, value: Optional[str], default: str = "", enabled: bool = True) -> str:
    if value is not None:
        return value
    if not enabled or not sys.stdin.isatty():
        return default
    return Prompt.ask(label, default=default)


@app.command("skill-brief")
def skill_brief(
    title: Optional[str] = typer.Option(None, help="Short name for the skill idea."),
    domain: Optional[str] = typer.Option(None, help="Domain or category, such as forensics or sql."),
    task: Optional[str] = typer.Option(None, help="Task or capability the skill should teach."),
    triggers: Optional[str] = typer.Option(None, help="User phrases or situations that should trigger the skill."),
    expertise: Optional[str] = typer.Option(None, help="Domain knowledge the expert wants preserved."),
    examples: Optional[str] = typer.Option(None, help="Concrete examples or scenarios."),
    caveats: Optional[str] = typer.Option(None, help="Caveats, failure modes, or dangerous assumptions."),
    outputs: Optional[str] = typer.Option(None, help="Expected output, artifact, or completion criteria."),
    reviewer: Optional[str] = typer.Option(None, help="Human name, handle, role, or team."),
    path: Optional[Path] = typer.Option(None, help="Output path. Defaults to .cortex/skill-briefs/."),
    print_only: bool = typer.Option(False, help="Print the brief instead of writing a file."),
) -> None:
    """Create a local domain-expert brief for building or updating a Cortex skill."""
    console.print(BANNER, style="bold cyan")
    console.print("[bold]Cortex skill brief[/bold]")
    console.print("[dim]Create local input for an agent to triage through Cortex skill authoring.[/dim]\n")

    guided = sys.stdin.isatty() and title is None and domain is None
    title = prompt_if_missing("Skill idea title", title)
    domain = prompt_if_missing("Domain/category", domain)
    if not title or not domain:
        console.print("[red]Provide --title and --domain, or run interactively in a TTY.[/red]")
        raise typer.Exit(1)

    values = {
        "task": prompt_if_missing("Task or capability", task, enabled=guided),
        "triggers": prompt_if_missing("Trigger phrases or situations", triggers, enabled=guided),
        "expertise": prompt_if_missing("Domain expertise to preserve", expertise, enabled=guided),
        "examples": prompt_if_missing("Concrete examples", examples, enabled=guided),
        "caveats": prompt_if_missing("Caveats or failure modes", caveats, enabled=guided),
        "outputs": prompt_if_missing("Expected output or completion criteria", outputs, enabled=guided),
        "reviewer": prompt_if_missing("Reviewer/role", reviewer, enabled=guided),
    }

    summary = Table(title="Skill Brief", box=box.SIMPLE)
    summary.add_column("Field", style="bold cyan")
    summary.add_column("Value")
    summary.add_row("title", title)
    summary.add_row("domain", domain)
    for key, value in values.items():
        summary.add_row(key, value or "-")
    if path:
        summary.add_row("path", str(path))
    summary.add_row("print_only", str(print_only))
    console.print(summary)

    args = [sys.executable, str(SKILL_BRIEF), "--title", title, "--domain", domain]
    for key, value in values.items():
        if value:
            args.extend([f"--{key}", value])
    if path:
        args.extend(["--path", str(path)])
    if print_only:
        args.append("--print-only")
    run_command(args)


if __name__ == "__main__":
    app()
