#!/usr/bin/env python3
"""Build or check the generated Cortex source manifest."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import lint_skill


ROOT_FILES = ("README.md", "AGENTS.md", ".gitignore", "pyproject.toml", "uv.lock")
SCRIPT_GLOBS = (
    "skills/**/scripts/*",
    "scripts/*",
    "src/**/*.py",
    ".githooks/*",
)
RESOURCE_DIR_NAMES = {"assets", "references", "vendor"}


def skill_records(root: Path) -> list[dict]:
    records = []
    for path in lint_skill.discover_skill_files(root):
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = lint_skill.parse_frontmatter(text)
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "skill_id": frontmatter.get("skill_id", ""),
                "status": frontmatter.get("status", ""),
                "model_role": frontmatter.get("model_role", ""),
                "review_status": frontmatter.get("review_status", "unreviewed"),
                "confidence": frontmatter.get("confidence", "-"),
                "summary": frontmatter.get("summary", ""),
                "updated": frontmatter.get("updated", ""),
            }
        )
    if not any(record["skill_id"] == "meta/source-manifest" for record in records):
        records.append(
            {
                "path": "skills/meta/source-manifest/SKILL.md",
                "skill_id": "meta/source-manifest",
                "status": "seed",
                "model_role": "reference",
                "review_status": "unreviewed",
                "confidence": "-",
                "summary": "Generated manifest of vault notes, scripts, root files, logs, and basic counts.",
                "updated": max_updated(records),
            }
        )
    return sorted(records, key=lambda item: item["path"])


def script_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    for pattern in SCRIPT_GLOBS:
        for path in root.glob(pattern):
            if path.is_file() and not any(part in RESOURCE_DIR_NAMES for part in path.relative_to(root).parts):
                paths.add(path.relative_to(root).as_posix())
    return sorted(paths)


def root_paths(root: Path) -> list[str]:
    return [path for path in ROOT_FILES if (root / path).exists()]


def log_paths(root: Path) -> list[str]:
    logs_root = root / "logs"
    if not logs_root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in logs_root.rglob("*.md"))


def max_updated(records: list[dict]) -> str:
    dates = [str(record["updated"]) for record in records if record.get("updated")]
    return max(dates) if dates else "2026-05-31"


def build_manifest(root: Path) -> str:
    records = skill_records(root)
    scripts = script_paths(root)
    roots = root_paths(root)
    logs = log_paths(root)
    updated = max_updated([record for record in records if record["skill_id"] != "meta/source-manifest"])
    learned_month = updated[:7]
    domains = Counter(record["skill_id"].split("/", 1)[0] for record in records if record["skill_id"])
    statuses = Counter(record["status"] for record in records if record["status"])
    roles = Counter(record["model_role"] for record in records if record["model_role"])
    review_statuses = Counter(record["review_status"] for record in records if record["review_status"])

    lines = [
        "---",
        "schema_version: 1",
        'tags:',
        '  - "meta"',
        '  - "manifest"',
        'topics:',
        '  - "source catalog"',
        "status: seed",
        "created: 2026-05-31",
        f"updated: {updated}",
        "sources: []",
        "source_count: 0",
        "aliases:",
        '  - "source manifest"',
        "skill_id: meta/source-manifest",
        'summary: "Generated manifest of vault notes, scripts, root files, logs, and basic counts."',
        "model_role: reference",
        "depends_on:",
        '  - "meta/contributing"',
        "related:",
        '  - "meta/index"',
        "---",
        "",
        "# Source Manifest",
        "",
        f"<!-- learned: {learned_month} | project: cortex-bootstrap | model: manifest-builder -->",
        "",
        "Generated from repository files. Do not hand-edit counts or tables;",
        "rerun `skills/meta/scripts/manifest_builder.py`.",
        "",
        "## Counts",
        "",
        f"- Skill notes: {len(records)}",
        f"- Script files: {len(scripts)}",
        f"- Root files: {len(roots)}",
        f"- Log markdown files: {len(logs)}",
        "",
        "## Domains",
        "",
    ]

    for domain, count in sorted(domains.items()):
        lines.append(f"- `{domain}`: {count}")

    lines.extend(["", "## Statuses", ""])
    for status, count in sorted(statuses.items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Model Roles", ""])
    for role, count in sorted(roles.items()):
        lines.append(f"- `{role}`: {count}")

    lines.extend(["", "## Review Statuses", ""])
    for review_status, count in sorted(review_statuses.items()):
        lines.append(f"- `{review_status}`: {count}")

    lines.extend(
        [
            "",
            "## Skill Notes",
            "",
            "| Path | Skill ID | Status | Model Role | Review | Summary |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        review = f"{record['review_status']} / {record['confidence']}"
        lines.append(
            f"| `{record['path']}` | `{record['skill_id']}` | {record['status']} | "
            f"{record['model_role']} | {review} | {record['summary']} |"
        )

    lines.extend(["", "## Scripts", ""])
    if scripts:
        lines.extend(f"- `{path}`" for path in scripts)
    else:
        lines.append("_No scripts found._")

    lines.extend(["", "## Root Files", ""])
    if roots:
        lines.extend(f"- `{path}`" for path in roots)
    else:
        lines.append("_No root files found._")

    lines.extend(["", "## Logs", ""])
    if logs:
        lines.extend(f"- `{path}`" for path in logs)
    else:
        lines.append("_No log markdown files found._")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit non-zero if source manifest is stale")
    args = parser.parse_args()

    root = lint_skill.repo_root(Path.cwd())
    manifest_path = lint_skill.source_manifest_path(root)
    expected = build_manifest(root)
    if args.check:
        actual = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        if actual != expected:
            print(f"ERROR: stale source manifest: {manifest_path}", file=sys.stderr)
            print("Run: python skills/meta/scripts/manifest_builder.py", file=sys.stderr)
            return 1
        print(f"OK: {manifest_path}")
        return 0

    manifest_path.write_text(expected, encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
