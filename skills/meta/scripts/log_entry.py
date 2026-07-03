#!/usr/bin/env python3
"""Append a short timestamped entry to the Cortex log directory."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import lint_skill


def append_log(root: Path, title: str, details: str, actor: str) -> Path:
    now = dt.datetime.now(dt.UTC).replace(microsecond=0)
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{now:%Y-%m}.md"

    if not log_path.exists():
        log_path.write_text(
            "\n".join(
                [
                    "---",
                    'tags:',
                    '  - "log"',
                    '  - "cortex"',
                    f"created: {now:%Y-%m-%d}",
                    f"updated: {now:%Y-%m-%d}",
                    "---",
                    "",
                    f"# Cortex Log - {now:%Y-%m}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    entry = "\n".join(
        [
            f"## {now.isoformat().replace('+00:00', 'Z')} - {title}",
            "",
            f"Actor: {actor}",
            "",
            details.strip(),
            "",
        ]
    )
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(entry)
    return log_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Short log title")
    parser.add_argument("--details", required=True, help="Concrete detail to append")
    parser.add_argument("--actor", default="agent", help="Actor label, default: agent")
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    log_path = append_log(root, args.title, args.details, args.actor)
    print(f"wrote {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
