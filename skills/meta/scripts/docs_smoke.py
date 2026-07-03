#!/usr/bin/env python3
"""Smoke-test Cortex human-facing docs and shared profile files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import lint_skill


REQUIRED_DOCS = (
    "README.md",
    "docs/FIRST_10_MINUTES.md",
    "docs/TEAM_ROLLOUT.md",
    "docs/CLI_REFERENCE.md",
    "docs/ROADMAP.md",
    "docs/HANDOFF.md",
    "AGENTS.md",
)
README_REQUIRED_LINKS = (
    "docs/FIRST_10_MINUTES.md",
    "docs/TEAM_ROLLOUT.md",
    "docs/CLI_REFERENCE.md",
    "docs/HANDOFF.md",
    "docs/ROADMAP.md",
    "skills/meta/contributing/SKILL.md",
)
CLI_REFERENCE_TERMS = (
    "uv run cortex team profile",
    "uv run cortex team status",
    "uv run cortex team finish",
    "uv run cortex first-run",
    "uv run cortex validate --fix-generated",
    "uv run cortex completion <shell>",
    "uv run cortex expertise",
    "uv run cortex skill-brief",
    "python scripts/install-skills.py",
    "--profile-file",
    "--dry-run",
    "--no-dry-run",
    "--yes",
    "--raw",
    "current",
    "stale",
    "missing",
    "unmanaged",
    "unsupported",
)
PROFILE_KEYS = {"skills", "categories", "agents", "scope", "mode", "project"}
VALID_AGENTS = {"codex", "claude", "cursor", "all"}
VALID_SCOPES = {"global", "project"}
VALID_MODES = {"wrapper", "symlink", "copy"}
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTEND_SLIDES_REQUIRED = (
    "skills/presentation/frontend-slides/SKILL.md",
    "skills/presentation/frontend-slides/vendor/VENDORED-SOURCES.txt",
    "skills/presentation/frontend-slides/vendor/frontend-slides/LICENSE",
    "skills/presentation/frontend-slides/vendor/frontend-slides/SKILL.md",
    "skills/presentation/frontend-slides/vendor/frontend-slides/viewport-base.css",
    "skills/presentation/frontend-slides/vendor/frontend-slides/scripts/extract-pptx.py",
    "skills/presentation/frontend-slides/vendor/frontend-slides/bold-template-pack/selection-index.json",
    "skills/presentation/frontend-slides/vendor/frontend-slides/bold-template-pack/deck-stage.js",
    "skills/presentation/frontend-slides/vendor/beautiful-html-templates/LICENSE",
    "skills/presentation/frontend-slides/vendor/beautiful-html-templates/AGENTS.md",
    "skills/presentation/frontend-slides/vendor/beautiful-html-templates/index.json",
    "skills/presentation/frontend-slides/vendor/beautiful-html-templates/templates",
    "skills/presentation/frontend-slides/vendor/beautiful-html-templates/screenshots",
    "skills/presentation/frontend-slides/assets/fonts/google-fonts.json",
    "skills/presentation/frontend-slides/assets/fonts/google-fonts.css",
    "skills/presentation/frontend-slides/assets/fonts/FONT-SOURCES.md",
    "skills/presentation/frontend-slides/assets/fonts/files/archivo-black",
    "skills/presentation/frontend-slides/assets/fonts/files/space-grotesk",
    "skills/presentation/frontend-slides/assets/fonts/files/jetbrains-mono",
    "skills/presentation/frontend-slides/assets/fonts/files/noto-sans-sc",
    "skills/presentation/frontend-slides/assets/fonts/files/noto-serif-sc",
)


def normalize_link(raw: str) -> str | None:
    target = raw.strip()
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    if "://" in target:
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    return target.replace("\\", "/")


def check_links(root: Path, rel: str) -> list[str]:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for match in MARKDOWN_LINK.finditer(text):
        target = normalize_link(match.group(1))
        if target is None:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{rel}: link points outside repo: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{rel}: broken local link: {target}")
    return errors


def check_shared_profiles(root: Path) -> list[str]:
    profile_root = root / "profiles"
    if not profile_root.exists():
        return []
    errors: list[str] = []
    for path in sorted(profile_root.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: profile must be a JSON object")
            continue
        unknown = sorted(set(data) - PROFILE_KEYS)
        if unknown:
            errors.append(f"{rel}: unknown profile keys: {', '.join(unknown)}")
        if not data.get("skills") and not data.get("categories"):
            errors.append(f"{rel}: provide skills, categories, or both")
        if data.get("agents"):
            agents = {part.strip() for part in str(data["agents"]).split(",") if part.strip()}
            unknown_agents = sorted(agents - VALID_AGENTS)
            if unknown_agents:
                errors.append(f"{rel}: unknown agents: {', '.join(unknown_agents)}")
        if data.get("scope") and data["scope"] not in VALID_SCOPES:
            errors.append(f"{rel}: scope must be one of: {', '.join(sorted(VALID_SCOPES))}")
        if data.get("mode") and data["mode"] not in VALID_MODES:
            errors.append(f"{rel}: mode must be one of: {', '.join(sorted(VALID_MODES))}")
    return errors


def check_frontend_slides_vendor(root: Path) -> list[str]:
    errors: list[str] = []
    skill_path = root / "skills" / "presentation" / "frontend-slides" / "SKILL.md"
    vendor_root = root / "skills" / "presentation" / "frontend-slides" / "vendor"
    if not skill_path.exists() and not vendor_root.exists():
        return errors
    for rel in FRONTEND_SLIDES_REQUIRED:
        if not (root / rel).exists():
            errors.append(f"frontend-slides offline payload missing: {rel}")
    duplicate_plugin = vendor_root / "frontend-slides" / "plugins" / "frontend-slides"
    if duplicate_plugin.exists():
        errors.append(f"frontend-slides duplicate plugin payload should be pruned: {duplicate_plugin.relative_to(root)}")
    templates = vendor_root / "beautiful-html-templates" / "templates"
    if templates.exists():
        count = sum(1 for path in templates.iterdir() if path.is_dir())
        if count < 30:
            errors.append(f"frontend-slides template payload looks incomplete: {count} templates")
    fonts = vendor_root.parent / "assets" / "fonts" / "files"
    if fonts.exists():
        count = sum(1 for path in fonts.rglob("*.woff2"))
        if count < 500:
            errors.append(f"frontend-slides font payload looks incomplete: {count} font files")
    font_script = vendor_root.parent / "scripts" / "vendor_google_fonts.py"
    if font_script.exists():
        result = subprocess.run(
            [sys.executable, str(font_script), "--check-template-fonts"],
            cwd=root,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            detail = (result.stdout + result.stderr).strip()
            errors.append(f"frontend-slides font manifest does not cover templates:\n{detail}")
    return errors


def main() -> int:
    root = lint_skill.repo_root(Path.cwd())
    errors: list[str] = []

    for rel in REQUIRED_DOCS:
        if not (root / rel).is_file():
            errors.append(f"missing required human-facing doc: {rel}")

    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for rel in README_REQUIRED_LINKS:
        if rel not in readme:
            errors.append(f"README.md does not reference {rel}")

    cli_reference = root / "docs" / "CLI_REFERENCE.md"
    if cli_reference.exists():
        cli_text = cli_reference.read_text(encoding="utf-8")
        for term in CLI_REFERENCE_TERMS:
            if term not in cli_text:
                errors.append(f"docs/CLI_REFERENCE.md does not document {term}")

    for rel in REQUIRED_DOCS:
        if (root / rel).is_file():
            errors.extend(check_links(root, rel))

    errors.extend(check_shared_profiles(root))
    errors.extend(check_frontend_slides_vendor(root))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: docs smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
