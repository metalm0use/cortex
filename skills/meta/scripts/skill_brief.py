#!/usr/bin/env python3
"""Create a local domain-expert brief for building or updating a Cortex skill."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import textwrap
from pathlib import Path

import lint_skill


def slug(value: str) -> str:
    clean = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")
    return clean or "skill-brief"


def section(title: str, value: str, fallback: str = "_Not provided._") -> list[str]:
    body = value.strip() or fallback
    return [f"## {title}", "", body, ""]


def build_prompt(path: str) -> str:
    return textwrap.dedent(
        f"""
        Use Cortex to build or update a skill from this domain-expert brief:

        {path}

        Before drafting, read:
        - skills/meta/index/SKILL.md
        - skills/meta/contributing/SKILL.md
        - skills/meta/skill-authoring/SKILL.md

        Triage whether this updates an existing skill or earns a new skill.
        Ask only for missing information that materially changes the skill.
        Keep the common path task-first, use required follow-on reading only
        for specific branches, then run:

        python skills/meta/scripts/validate.py --fix-generated
        """
    ).strip()


def build_brief(args: argparse.Namespace, output_path: Path | None) -> str:
    today = dt.date.today().isoformat()
    path_text = output_path.as_posix() if output_path else "<brief-path>"
    lines = [
        "# Cortex Skill Brief",
        "",
        f"Created: {today}",
        f"Title: {args.title}",
        f"Domain: {args.domain}",
        f"Reviewer: {args.reviewer or 'Not provided'}",
        "",
        "## Agent Prompt",
        "",
        "```text",
        build_prompt(path_text),
        "```",
        "",
        *section("Task Or Capability", args.task),
        *section("Trigger Phrases Or Situations", args.triggers),
        *section("Domain Expertise", args.expertise),
        *section("Concrete Examples", args.examples),
        *section("Caveats And Failure Modes", args.caveats),
        *section("Expected Output Or Completion Criteria", args.outputs),
        "## Cortex Notes",
        "",
        "- This brief is local input, not a skill source file.",
        "- A future agent should triage it through `meta/contributing`.",
        "- If accepted, draft or update a Cortex source skill through `meta/skill-authoring`.",
        "- If the expert claim reviews an existing skill, capture it with `capture_expertise.py`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Short name for the skill idea")
    parser.add_argument("--domain", required=True, help="Domain or category, such as forensics or sql")
    parser.add_argument("--task", default="", help="Task or capability the skill should teach")
    parser.add_argument("--triggers", default="", help="User phrases or situations that should trigger the skill")
    parser.add_argument("--expertise", default="", help="Domain knowledge the expert wants preserved")
    parser.add_argument("--examples", default="", help="Concrete examples or scenarios")
    parser.add_argument("--caveats", default="", help="Caveats, failure modes, or dangerous assumptions")
    parser.add_argument("--outputs", default="", help="Expected output, artifact, or completion criteria")
    parser.add_argument("--reviewer", default="", help="Human name, handle, role, or team")
    parser.add_argument("--path", help="Output path. Defaults to .cortex/skill-briefs/<date>-<slug>.md")
    parser.add_argument("--print-only", action="store_true", help="Print the brief instead of writing a file")
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    output_path = None
    if not args.print_only:
        output_path = (
            Path(args.path)
            if args.path
            else root / ".cortex" / "skill-briefs" / f"{dt.date.today().isoformat()}-{slug(args.title)}.md"
        )
        if not output_path.is_absolute():
            output_path = root / output_path

    brief = build_brief(args, output_path)
    if args.print_only:
        print(brief)
        return 0

    assert output_path is not None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(brief, encoding="utf-8", newline="\n")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
