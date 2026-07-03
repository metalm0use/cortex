#!/usr/bin/env python3
"""Install Cortex git hooks by setting core.hooksPath to .githooks."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import lint_skill


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
    raise SystemExit("ERROR: git was not found")


def main() -> int:
    root = lint_skill.repo_root(Path.cwd())
    hooks = root / ".githooks"
    pre_commit = hooks / "pre-commit"
    if not pre_commit.exists():
        raise SystemExit(f"ERROR: missing hook template: {pre_commit}")

    git = git_command()
    result = subprocess.run(
        [git, "config", "core.hooksPath", ".githooks"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    print("OK: git core.hooksPath set to .githooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
