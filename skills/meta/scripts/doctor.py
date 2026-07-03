#!/usr/bin/env python3
"""Run the minimum Cortex vault health checks."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import index_builder
import lint_skill
import manifest_builder


MIN_PYTHON = (3, 10)
REQUIRED_DIRS = (
    "skills",
    "skills/meta",
    "skills/meta/scripts",
    "scripts",
    "src",
    "src/cortex_cli",
    "logs",
)
REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    "skills/meta/contributing/SKILL.md",
    "skills/meta/index/SKILL.md",
    "skills/meta/source-manifest/SKILL.md",
    "skills/meta/roles/SKILL.md",
    "skills/meta/conflicts/SKILL.md",
    "skills/meta/deployment/SKILL.md",
    "skills/meta/scripts/lint_skill.py",
    "skills/meta/scripts/index_builder.py",
    "skills/meta/scripts/manifest_builder.py",
    "skills/meta/scripts/doctor.py",
    "skills/meta/scripts/validate.py",
    "skills/meta/scripts/docs_smoke.py",
    "skills/meta/scripts/commit_skill.py",
    "skills/meta/scripts/capture_expertise.py",
    "skills/meta/scripts/log_entry.py",
    "skills/meta/scripts/skill_brief.py",
    "skills/meta/scripts/install_hooks.py",
    "scripts/deploy-skills.ps1",
    "scripts/deploy-skills.sh",
    "src/cortex_cli/__init__.py",
    "src/cortex_cli/main.py",
    ".githooks/pre-commit",
)


def run_git_diff_check(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    git = shutil.which("git")
    if git is None:
        for candidate in (
            Path("C:/Program Files/Git/cmd/git.exe"),
            Path("C:/Program Files/Git/bin/git.exe"),
        ):
            if candidate.exists():
                git = str(candidate)
                break
    if git is None:
        return ["git diff --check could not run because git was not found on PATH"]
    result = subprocess.run(
        [git, "diff", "--check"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return []
    output = "\n".join(part for part in [result.stdout, result.stderr] if part)
    return [f"git diff --check failed:\n{output.strip()}"]


def unique_skill_ids(root: Path) -> list[str]:
    seen: dict[str, Path] = {}
    errors: list[str] = []
    for path in lint_skill.discover_skill_files(root):
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = lint_skill.parse_frontmatter(text)
        skill_id = frontmatter.get("skill_id")
        if skill_id in seen:
            errors.append(
                f"duplicate skill_id {skill_id!r}: "
                f"{seen[skill_id].relative_to(root)} and {path.relative_to(root)}"
            )
        else:
            seen[skill_id] = path
    return errors


def structural_checks(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_DIRS:
        if not (root / rel).is_dir():
            errors.append(f"missing required directory: {rel}")
    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")
    if sys.version_info < MIN_PYTHON:
        errors.append(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required; "
            f"running {sys.version_info.major}.{sys.version_info.minor}"
        )
    return errors


def count_report(root: Path) -> list[str]:
    skills = []
    for path in lint_skill.discover_skill_files(root):
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = lint_skill.parse_frontmatter(text)
        skills.append(frontmatter)

    domains = Counter(str(skill.get("skill_id", "")).split("/", 1)[0] for skill in skills)
    roles = Counter(str(skill.get("model_role", "")) for skill in skills)
    statuses = Counter(str(skill.get("status", "")) for skill in skills)
    reviews = Counter(str(skill.get("review_status", "unreviewed")) for skill in skills)
    scripts = [path for path in (root / "skills").glob("**/scripts/*") if path.is_file()]
    logs = list((root / "logs").glob("*.md")) if (root / "logs").exists() else []

    lines = [
        f"Skill notes: {len(skills)}",
        f"Skill scripts: {len(scripts)}",
        f"Log markdown files: {len(logs)}",
        "Domains: " + ", ".join(f"{key}={value}" for key, value in sorted(domains.items())),
        "Model roles: " + ", ".join(f"{key}={value}" for key, value in sorted(roles.items())),
        "Statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(statuses.items())),
        "Review statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(reviews.items())),
    ]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix-index", action="store_true", help="Rewrite skills/meta/index/SKILL.md before checking")
    parser.add_argument(
        "--fix-manifest",
        action="store_true",
        help="Rewrite skills/meta/source-manifest/SKILL.md before checking",
    )
    parser.add_argument("--report", action="store_true", help="Print non-mutating vault counts")
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    index_path = lint_skill.index_path(root)
    manifest_path = lint_skill.source_manifest_path(root)
    expected_manifest = manifest_builder.build_manifest(root)
    expected_index = index_builder.build_index(root)

    if args.fix_manifest:
        manifest_path.write_text(expected_manifest, encoding="utf-8")
        print(f"wrote {manifest_path}")
        expected_index = index_builder.build_index(root)

    if args.fix_index:
        index_path.write_text(expected_index, encoding="utf-8")
        print(f"wrote {index_path}")

    errors: list[str] = []
    errors.extend(structural_checks(root))

    actual_manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
    if actual_manifest != expected_manifest:
        errors.append("skills/meta/source-manifest/SKILL.md is stale; run manifest_builder.py or doctor.py --fix-manifest")

    actual_index = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    if actual_index != expected_index:
        errors.append("skills/meta/index/SKILL.md is stale; run index_builder.py or doctor.py --fix-index")

    for path in lint_skill.discover_skill_files(root):
        for error in lint_skill.lint(path):
            errors.append(f"{path.relative_to(root)}: {error}")

    errors.extend(unique_skill_ids(root))
    errors.extend(run_git_diff_check(root))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.report:
        for line in count_report(root):
            print(line)
    print("OK: vault health checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
