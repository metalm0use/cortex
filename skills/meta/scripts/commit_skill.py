#!/usr/bin/env python3
"""Lint, catalog, stage, and commit a vault skill update."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import index_builder
import lint_skill
import manifest_builder


COMMIT_RE = re.compile(r"^skill\([a-z0-9_./-]+\): .{8,}$")


def git_command() -> str:
    git = shutil.which("git")
    if git:
        return git
    for candidate in (
        Path("C:/Program Files/Git/cmd/git.exe"),
        Path("C:/Program Files/Git/bin/git.exe"),
    ):
        if candidate.exists():
            return str(candidate)
    raise SystemExit("ERROR: git was not found on PATH or in the default Windows install paths")


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)


def git_root(start: Path) -> Path:
    git = git_command()
    result = subprocess.run(
        [git, "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise SystemExit("ERROR: not inside a git repository")
    return Path(result.stdout.strip()).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Skill file to commit")
    parser.add_argument("message", help='Structured commit message, for example "skill(sql/injection): add pattern"')
    parser.add_argument("--include", action="append", default=[], help="Additional path to stage after lint passes")
    args = parser.parse_args()

    if not COMMIT_RE.match(args.message):
        raise SystemExit("ERROR: commit message must match: skill(scope/path): short description")

    root = git_root(Path.cwd())
    git = git_command()
    target = (root / args.target).resolve() if not Path(args.target).is_absolute() else Path(args.target).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise SystemExit("ERROR: target must live inside the repository")
    if not target.exists():
        raise SystemExit(f"ERROR: target does not exist: {target}")
    if target.suffix.lower() != ".md":
        raise SystemExit("ERROR: target must be a markdown skill file")

    manifest_path = lint_skill.source_manifest_path(root)
    manifest_path.write_text(manifest_builder.build_manifest(root), encoding="utf-8")
    index_path = lint_skill.index_path(root)
    index_path.write_text(index_builder.build_index(root), encoding="utf-8")

    try:
        target_text = target.read_text(encoding="utf-8")
        target_frontmatter, _ = lint_skill.parse_frontmatter(target_text)
    except Exception as exc:
        raise SystemExit(f"ERROR: cannot read target frontmatter: {exc}")
    target_skill_id = target_frontmatter.get("skill_id")
    expected_prefix = f"skill({target_skill_id}):"
    if not args.message.startswith(expected_prefix):
        raise SystemExit(f"ERROR: commit message scope must match target skill_id: {expected_prefix}")

    errors = []
    for skill_file in lint_skill.discover_skill_files(root):
        errors.extend(f"{skill_file.relative_to(root)}: {error}" for error in lint_skill.lint(skill_file))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    stage_paths = [
        str(target.relative_to(root)),
        str(manifest_path.relative_to(root)),
        str(index_path.relative_to(root)),
    ]
    for included in args.include:
        include_path = (root / included).resolve() if not Path(included).is_absolute() else Path(included).resolve()
        try:
            stage_paths.append(str(include_path.relative_to(root)))
        except ValueError:
            raise SystemExit(f"ERROR: include path must live inside the repository: {included}")

    run([git, "add", *dict.fromkeys(stage_paths)], root)
    run([git, "commit", "-m", args.message], root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
