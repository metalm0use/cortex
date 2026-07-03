#!/usr/bin/env python3
"""Rebuild skills/meta/index/SKILL.md from skill frontmatter."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from lint_skill import discover_skill_files, expected_skill_id, index_path, parse_frontmatter, repo_root


def yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "\n" + "\n".join(f'  - "{item}"' for item in items)


def mermaid_id(skill_id: str) -> str:
    return "s_" + re.sub(r"[^A-Za-z0-9_]", "_", skill_id)


def read_skill(path: Path, root: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(text)
    rel_id = expected_skill_id(path, root) or path.relative_to(root / "skills").with_suffix("").as_posix()
    frontmatter.setdefault("skill_id", rel_id)
    frontmatter["_path"] = path
    return frontmatter


def max_updated(skills: list[dict]) -> str:
    dates = [str(skill.get("updated", "")) for skill in skills if skill.get("updated")]
    return max(dates) if dates else "2026-05-31"


def discover_skills(root: Path) -> list[dict]:
    found = []
    for path in discover_skill_files(root):
        rel = path.relative_to(root / "skills").as_posix()
        if rel == "meta/index/SKILL.md":
            continue
        found.append(read_skill(path, root))
    return sorted(found, key=lambda item: item["skill_id"])


def grouped(skills: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for skill in skills:
        domain = str(skill["skill_id"]).split("/", 1)[0]
        groups.setdefault(domain, []).append(skill)
    return dict(sorted(groups.items()))


def row_for(skill: dict, index_path: Path) -> str:
    skill_id = skill["skill_id"]
    path = skill.get("_path")
    if path:
        link = Path(os.path.relpath(path, index_path.parent)).as_posix()
    else:
        link = skill_id.split("/", 1)[1] + ".md" if skill_id.startswith("meta/") else "../" + skill_id + ".md"
    tags = ", ".join(skill.get("tags", []))
    model_role = skill.get("model_role", "-")
    review_status = skill.get("review_status", "unreviewed")
    confidence = skill.get("confidence", "-")
    review = f"{review_status} / {confidence}"
    related = ", ".join(f"`{item}`" for item in skill.get("related", [])) or "-"
    return (
        f"| [`{skill_id}`]({link}) | {skill.get('status', '')} | {model_role} | {review} | "
        f"{skill.get('summary', '')} | {tags} | {related} |"
    )


def build_index(root: Path) -> str:
    discovered = discover_skills(root)
    updated = max_updated(discovered)
    learned_month = updated[:7]
    index_skill = {
        "schema_version": 1,
        "tags": ["meta", "index"],
        "topics": ["skill graph"],
        "status": "seed",
        "created": "2026-05-31",
        "updated": updated,
        "sources": [],
        "source_count": 0,
        "aliases": ["skill graph"],
        "skill_id": "meta/index",
        "summary": "Generated map of vault skills, domains, summaries, and relationships.",
        "model_role": "reference",
        "depends_on": ["meta/contributing"],
        "related": ["meta/roles"],
    }
    path = index_path(root)
    index_skill["_path"] = path
    skills = sorted([index_skill, *discovered], key=lambda item: item["skill_id"])
    all_tags = sorted({tag for skill in skills for tag in skill.get("tags", [])})

    lines = [
        "---",
        "schema_version: 1",
        'tags:',
        '  - "meta"',
        '  - "index"',
        'topics:',
        '  - "skill graph"',
        "status: seed",
        "created: 2026-05-31",
        f"updated: {updated}",
        "sources: []",
        "source_count: 0",
        "aliases:",
        '  - "skill graph"',
        "skill_id: meta/index",
        'summary: "Generated map of vault skills, domains, summaries, and relationships."',
        "model_role: reference",
        "depends_on:",
        '  - "meta/contributing"',
        "related:",
        '  - "meta/roles"',
        "---",
        "",
        "# Skill Graph",
        "",
        f"<!-- learned: {learned_month} | project: cortex-bootstrap | model: index-builder -->",
        "",
        "Generated from skill frontmatter. Do not hand-edit skill entries;",
        "update the source skill files and rerun `skills/meta/scripts/index_builder.py`.",
        "",
        "## Domains",
        "",
    ]

    for domain, items in grouped(skills).items():
        lines.append(f"- `{domain}`: {len(items)} skill(s)")

    lines.extend(
        [
            "",
            "## Tags",
            "",
            ", ".join(f"`{tag}`" for tag in all_tags) if all_tags else "_No tags yet._",
            "",
            "## Skills",
            "",
            "| Skill | Status | Model Role | Review | Summary | Tags | Related |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for skill in skills:
        lines.append(row_for(skill, path))

    lines.extend(["", "## Relationship Graph", "", "```mermaid", "flowchart LR"])
    for skill in skills:
        node = mermaid_id(skill["skill_id"])
        lines.append(f'  {node}["{skill["skill_id"]}"]')
    for skill in skills:
        source = mermaid_id(skill["skill_id"])
        for target in skill.get("depends_on", []):
            lines.append(f"  {source} --> {mermaid_id(target)}")
        for target in skill.get("related", []):
            lines.append(f"  {source} -.-> {mermaid_id(target)}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit non-zero if skills/meta/index/SKILL.md is stale")
    args = parser.parse_args()

    root = repo_root(Path.cwd())
    path = index_path(root)
    expected = build_index(root)
    if args.check:
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual != expected:
            print(f"ERROR: stale index: {path}", file=sys.stderr)
            print("Run: python skills/meta/scripts/index_builder.py", file=sys.stderr)
            return 1
        print(f"OK: {path}")
        return 0

    path.write_text(expected, encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
