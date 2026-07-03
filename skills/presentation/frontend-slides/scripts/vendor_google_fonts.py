#!/usr/bin/env python3
"""Vendor selected Google Fonts CSS and WOFF2 files for offline decks."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
FONT_ROOT = SKILL_DIR / "assets" / "fonts"
VENDOR_ROOT = SKILL_DIR / "vendor"
URL_RE = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+)\)")
FONT_ATTR_RE = re.compile(r"(?i)font-family\s*=\s*[\"']([^\"']+)[\"']")
FONT_CSS_RE = re.compile(r"(?i)font-family\s*:\s*([^;`\r\n}]+)")
FONT_FAMILY_RE = re.compile(r"(?i)fontFamily\s*:\s*([^`\r\n]+)")
FONT_VAR_RE = re.compile(r"(?i)--f-[\w-]+\s*:\s*([^;\r\n}]+)")
GOOGLE_FAMILY_RE = re.compile(r"[?&]family=([^&\"')]+)")
SYSTEM_FAMILIES = {
    "-apple-system",
    "Arial",
    "BlinkMacSystemFont",
    "Consolas",
    "Courier New",
    "cursive",
    "fantasy",
    "Garamond",
    "Geneva",
    "Georgia",
    "Helvetica",
    "Helvetica Neue",
    "Impact",
    "inherit",
    "Menlo",
    "monospace",
    "MS Sans Serif",
    "sans-serif",
    "Segoe UI",
    "serif",
    "SF Mono",
    "system-ui",
    "Tahoma",
    "Times New Roman",
    "ui-monospace",
    "ui-sans-serif",
    "ui-serif",
    "Verdana",
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def css_url(base: str, query: str) -> str:
    return f"{base}?family={query}&display=swap"


def family_from_query(query: str) -> str:
    family = urllib.parse.unquote_plus(query.split(":", 1)[0])
    return family.strip()


def split_font_stack(value: str) -> list[str]:
    cleaned = value.strip().strip("`")
    if cleaned.startswith("var(") or cleaned.startswith("{"):
        return []
    families: list[str] = []
    for part in cleaned.split(","):
        name = part.split("`", 1)[0].strip().strip("\"'").strip()
        if not name or name.startswith("var(") or name.startswith("{"):
            continue
        if name in SYSTEM_FAMILIES:
            continue
        families.append(name)
    return families


def extract_template_fonts(paths: list[Path]) -> set[str]:
    families: set[str] = set()
    for root in paths:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".css", ".html", ".js", ".json", ".md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in (FONT_ATTR_RE, FONT_CSS_RE, FONT_FAMILY_RE):
                for match in pattern.finditer(text):
                    families.update(split_font_stack(match.group(1)))
            for match in FONT_VAR_RE.finditer(text):
                families.update(split_font_stack(match.group(1)))
            for match in GOOGLE_FAMILY_RE.finditer(text):
                families.add(family_from_query(match.group(1)))
    return families


def template_roots() -> list[Path]:
    return [
        VENDOR_ROOT / "beautiful-html-templates" / "templates",
        VENDOR_ROOT / "frontend-slides" / "bold-template-pack" / "templates",
    ]


def check_template_fonts(manifest: dict) -> int:
    referenced = extract_template_fonts(template_roots())
    vendored = {family["family"] for family in manifest["families"]}
    for family in manifest["families"]:
        vendored.update(family.get("aliases", []))
    ignored = set(manifest.get("ignored_template_families", []))
    missing = sorted(referenced - vendored - ignored)
    extra = sorted(vendored - referenced)

    print("Referenced template families:")
    for family in sorted(referenced):
        marker = "vendored" if family in vendored else "ignored" if family in ignored else "missing"
        print(f"- {family}: {marker}")

    if extra:
        print("\nVendored but not currently referenced:")
        for family in extra:
            print(f"- {family}")

    if missing:
        print("\nMissing template font coverage:")
        for family in missing:
            print(f"- {family}")
        return 1

    print("\nOK: all referenced template font families are vendored or explicitly ignored")
    return 0


def local_font_path(url: str, family_slug: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix or ".woff2"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return FONT_ROOT / "files" / family_slug / f"{digest}{suffix}"


def vendor_family(base_url: str, family: dict, dry_run: bool) -> tuple[str, list[dict]]:
    name = family["family"]
    family_slug = slug(name)
    url = css_url(base_url, family["query"])
    css = fetch(url).decode("utf-8")
    records: list[dict] = []

    def replace_url(match: re.Match[str]) -> str:
        remote = match.group(1)
        local = local_font_path(remote, family_slug)
        rel = local.relative_to(FONT_ROOT).as_posix()
        records.append({"family": name, "url": remote, "path": rel})
        if not dry_run and not local.exists():
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(fetch(remote))
        return f"url({rel})"

    local_css = URL_RE.sub(replace_url, css)
    for alias in family.get("aliases", []):
        alias_css = re.sub(
            r"font-family:\s*(['\"])" + re.escape(name) + r"\1",
            "font-family: " + repr(alias),
            local_css,
        )
        local_css += "\n" + alias_css
    header = f"/* {name} | source: {url} */\n"
    return header + local_css.strip() + "\n", records


def unique_records(records: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for record in records:
        key = str(record["path"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def write_sources(manifest: dict, records: list[dict], dry_run: bool) -> None:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Vendored Font Sources",
        "",
        "These fonts are vendored for offline Frontend Slides decks.",
        "",
        f"Generated: {now}",
        f"CSS source: {manifest['source']}",
        "",
        "Licensing:",
        "Downloaded families are fetched through the Google Fonts CSS API, which serves open-source web fonts.",
        "Do not add non-Google or CDN-only families until their license and provenance are verified.",
        "Check upstream metadata before adding non-Google or CDN-only families.",
        "",
        "Families:",
    ]
    for family in manifest["families"]:
        aliases = family.get("aliases", [])
        suffix = f" (aliases: {', '.join(aliases)})" if aliases else ""
        lines.append(f"- {family['family']}{suffix}: `{css_url(manifest['source'], family['query'])}`")
    ignored = manifest.get("ignored_template_family_notes", {})
    if ignored:
        lines.extend(["", "Referenced But Not Vendored:"])
        for family, reason in sorted(ignored.items()):
            lines.append(f"- {family}: {reason}")
    lines.extend(["", "Files:"])
    for record in unique_records(records):
        lines.append(f"- `{record['path']}` from {record['url']}")
    text = "\n".join(lines) + "\n"
    if dry_run:
        print(text)
    else:
        (FONT_ROOT / "FONT-SOURCES.md").write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(FONT_ROOT / "google-fonts.json"),
        help="Font manifest JSON path",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch CSS and print manifest without writing")
    parser.add_argument(
        "--check-template-fonts",
        action="store_true",
        help="Check vendored font manifest against referenced template font families",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = Path.cwd() / manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.check_template_fonts:
        return check_template_fonts(manifest)

    css_parts: list[str] = []
    records: list[dict] = []
    for family in manifest["families"]:
        css, family_records = vendor_family(manifest["source"], family, args.dry_run)
        css_parts.append(css)
        records.extend(family_records)
        print(f"{family['family']}: {len(family_records)} font file(s)")

    if not args.dry_run:
        FONT_ROOT.mkdir(parents=True, exist_ok=True)
        (FONT_ROOT / manifest["output_css"]).write_text("\n".join(css_parts), encoding="utf-8", newline="\n")
    write_sources(manifest, records, args.dry_run)
    print(f"font references: {len(records)}")
    print(f"unique font files: {len(unique_records(records))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
