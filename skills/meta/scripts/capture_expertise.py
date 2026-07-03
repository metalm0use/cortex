#!/usr/bin/env python3
"""Capture human expertise against a Cortex skill without hand-editing."""

from __future__ import annotations

import argparse
import datetime as dt
import textwrap
from pathlib import Path

import lint_skill


VALID_REVIEW_STATUS = ("human-noted", "reviewed", "disputed", "needs-refresh")
VALID_CONFIDENCE = ("low", "medium", "high")
VALID_INPUT_KIND = ("preference", "operational-experience", "domain-expertise")


def skill_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    if candidate.suffix != ".md":
        candidate = root / "skills" / f"{value}.md"
    if candidate.exists():
        return candidate
    raise SystemExit(f"Skill not found: {value}")


def split_frontmatter(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SystemExit("Skill is missing frontmatter")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[: index + 1], lines[index + 1 :]
    raise SystemExit("Skill is missing closing frontmatter delimiter")


def list_lines(key: str, values: list[str]) -> list[str]:
    if not values:
        return [f"{key}: []"]
    return [f"{key}:"] + [f'  - "{value}"' for value in values]


def replace_key(frontmatter: list[str], key: str, lines: list[str]) -> list[str]:
    start = None
    end = None
    for index, line in enumerate(frontmatter):
        if line.startswith(f"{key}:"):
            start = index
            end = index + 1
            while end < len(frontmatter) and frontmatter[end].startswith("  - "):
                end += 1
            break
    if start is None:
        return [*frontmatter[:-1], *lines, frontmatter[-1]]
    return [*frontmatter[:start], *lines, *frontmatter[end:]]


def merge_list(existing: list[str], additions: list[str]) -> list[str]:
    merged = list(existing)
    seen = set(existing)
    for addition in additions:
        if addition and addition not in seen:
            merged.append(addition)
            seen.add(addition)
    return merged


def csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def update_frontmatter(
    frontmatter_lines: list[str],
    frontmatter: dict,
    *,
    review_status: str,
    reviewer: str,
    domains: list[str],
    confidence: str,
    today: str,
) -> list[str]:
    reviewed_by = merge_list(list(frontmatter.get("reviewed_by", [])), [reviewer] if reviewer else [])
    expertise_domain = merge_list(list(frontmatter.get("expertise_domain", [])), domains)
    updated = today

    replacements = {
        "updated": [f"updated: {updated}"],
        "review_status": [f"review_status: {review_status}"],
        "reviewed_by": list_lines("reviewed_by", reviewed_by),
        "expertise_domain": list_lines("expertise_domain", expertise_domain),
        "confidence": [f"confidence: {confidence}"],
        "reviewed_at": [f"reviewed_at: {today}"],
    }
    for key, lines in replacements.items():
        frontmatter_lines = replace_key(frontmatter_lines, key, lines)
    return frontmatter_lines


def note_block(
    *,
    today: str,
    review_status: str,
    confidence: str,
    input_kind: str,
    reviewer: str,
    domains: list[str],
    claim: str,
    details: str,
) -> str:
    header = "## Human Review Notes"
    metadata = [
        f"status: {review_status}",
        f"confidence: {confidence}",
        f"kind: {input_kind}",
    ]
    if reviewer:
        metadata.append(f"reviewer: {reviewer}")
    if domains:
        metadata.append("domain: " + ", ".join(domains))
    wrapped_claim = textwrap.fill(claim.strip(), width=88, subsequent_indent="  ")
    lines = [
        header,
        "",
        f"<!-- learned: {today[:7]} | project: human-expertise-capture | model: human-mediated -->",
        "",
        f"- {today} | " + " | ".join(metadata),
        f"  {wrapped_claim}",
    ]
    if details:
        wrapped_details = textwrap.fill(details.strip(), width=88, subsequent_indent="  ")
        lines.append(f"  Details: {wrapped_details}")
    return "\n".join(lines)


def append_note(body_lines: list[str], block: str) -> list[str]:
    body = "\n".join(body_lines).rstrip()
    lines = body.splitlines()
    if "## Human Review Notes" not in lines:
        return [*(body.splitlines() if body else []), "", *block.splitlines()]

    section_index = lines.index("## Human Review Notes")
    insert_at = len(lines)
    for index in range(section_index + 1, len(lines)):
        if lines[index].startswith("## ") and lines[index] != "## Human Review Notes":
            insert_at = index
            break
    note_lines = block.splitlines()[4:]
    return [*lines[:insert_at], "", *note_lines, *lines[insert_at:]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="Skill id such as forensics/pcap, or a path to a skill markdown file")
    parser.add_argument("--claim", required=True, help="Concrete expertise claim to record")
    parser.add_argument("--details", default="", help="Optional supporting context or caveat")
    parser.add_argument("--reviewer", default="", help="Human name, handle, role, or team")
    parser.add_argument("--domain", default="", help="Comma-separated expertise domains")
    parser.add_argument("--status", choices=VALID_REVIEW_STATUS, default="human-noted")
    parser.add_argument("--confidence", choices=VALID_CONFIDENCE, default="medium")
    parser.add_argument("--kind", choices=VALID_INPUT_KIND, default="domain-expertise")
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    path = skill_path(root, args.skill)
    text = path.read_text(encoding="utf-8")
    parsed_frontmatter, _ = lint_skill.parse_frontmatter(text)
    frontmatter_lines, body_lines = split_frontmatter(text)
    today = dt.date.today().isoformat()
    domains = csv(args.domain)

    frontmatter_lines = update_frontmatter(
        frontmatter_lines,
        parsed_frontmatter,
        review_status=args.status,
        reviewer=args.reviewer,
        domains=domains,
        confidence=args.confidence,
        today=today,
    )
    block = note_block(
        today=today,
        review_status=args.status,
        confidence=args.confidence,
        input_kind=args.kind,
        reviewer=args.reviewer,
        domains=domains,
        claim=args.claim,
        details=args.details,
    )
    body_lines = append_note(body_lines, block)
    path.write_text("\n".join([*frontmatter_lines, *body_lines, ""]), encoding="utf-8", newline="\n")
    print(f"captured expertise in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
