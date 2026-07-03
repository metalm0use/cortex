#!/usr/bin/env python3
"""Run the portable Cortex validation contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import lint_skill


SCRIPT_DIR = Path(__file__).resolve().parent


def run_section(title: str, cmd: list[str], root: Path) -> int:
    print(f"\n== {title} ==", flush=True)
    print(" ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=root)
    if result.returncode == 0:
        print(f"OK: {title}")
    else:
        print(f"FAILED: {title}", file=sys.stderr)
    return result.returncode


def script(name: str) -> str:
    return str(SCRIPT_DIR / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix-generated",
        action="store_true",
        help="Rebuild generated manifest and index before validating",
    )
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    python = sys.executable
    failures = 0

    if args.fix_generated:
        failures += run_section(
            "rebuild source manifest",
            [python, script("manifest_builder.py")],
            root,
        )
        failures += run_section(
            "rebuild skill index",
            [python, script("index_builder.py")],
            root,
        )

    checks = [
        ("lint all skills", [python, script("lint_skill.py"), "--all"]),
        ("check source manifest", [python, script("manifest_builder.py"), "--check"]),
        ("check skill index", [python, script("index_builder.py"), "--check"]),
        ("docs smoke check", [python, script("docs_smoke.py")]),
        ("doctor report", [python, script("doctor.py"), "--report"]),
    ]

    for title, cmd in checks:
        failures += run_section(title, cmd, root)

    if failures:
        print("\nFAILED: Cortex validation contract did not pass", file=sys.stderr)
        return 1

    print("\nOK: Cortex validation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
