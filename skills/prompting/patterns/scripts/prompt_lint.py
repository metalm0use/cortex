#!/usr/bin/env python3
"""Deterministic structural scorer for prompts.

Checks for the presence of the components a strong prompt usually has. This is
an objective, repeatable structural signal, not a judgement of quality: it
reports which components are present, not whether they are good. Pair it with
the anchored rubric in `prompting/patterns` for the qualitative layer.

Usage:
    python prompt_lint.py PROMPT_FILE
    python prompt_lint.py --stdin < prompt.txt
    python prompt_lint.py PROMPT_FILE --min 5   # exit 1 if score < 5

Output is JSON: {"score", "max", "present", "missing", "word_count"}.
"""

from __future__ import annotations

import argparse
import json
import re
import sys


# Each component maps to case-insensitive signals. Presence is heuristic and
# deliberately simple so the score is deterministic and explainable.
COMPONENTS: dict[str, list[str]] = {
    "role": [
        r"\byou are\b", r"\byour role\b", r"\bact as\b", r"^role\s*:", r"\bas an?\b\s+\w+\s+(assistant|expert|engineer|analyst|writer|reviewer)",
    ],
    "task": [
        r"\byour task\b", r"^task\s*:", r"^goal\s*:", r"^objective\s*:", r"\byou will\b", r"\byou should\b",
        r"^\s*(summari[sz]e|analy[sz]e|write|generate|classify|extract|translate|review|explain|draft|rewrite)\b",
    ],
    "output_format": [
        r"\bformat\b", r"\bjson\b", r"\bmarkdown\b", r"\byaml\b", r"\brespond with\b", r"^output\s*:",
        r"\breturn (a|the|only)\b", r"\bschema\b", r"\bbullet", r"\btable\b", r"\bheadings?\b",
    ],
    "examples": [
        r"\bexample\b", r"\bfor example\b", r"\be\.g\.", r"^input\s*:", r"^output\s*:", r"\bfew-?shot\b", r"\bsample\b",
    ],
    "constraints": [
        r"\bmust\b", r"\bdo not\b", r"\bdon't\b", r"\bat most\b", r"\bno more than\b", r"\bconcise\b",
        r"\bonly\b", r"\bavoid\b", r"\bnever\b", r"\balways\b", r"\blimit\b",
    ],
    "guardrails": [
        r"\bignore[^.\n]{0,40}\b(previous|prior|instructions?)\b", r"\binstructions?\b[^.\n]{0,30}\b(in|inside|within|embedded|contained)\b",
        r"\bout of scope\b", r"\bdo not reveal\b", r"\bif asked\b", r"\bonly as (data|evidence)\b", r"\bas (data|evidence) only\b",
        r"\brefuse\b", r"\bprompt injection\b", r"\bstay on\b", r"\bdecline\b", r"\bif the request\b", r"\bdo not follow\b",
    ],
}


def score_prompt(text: str) -> dict:
    """Return the structural scorecard for a prompt string."""
    present: dict[str, bool] = {}
    for component, signals in COMPONENTS.items():
        present[component] = any(
            re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in signals
        )
    missing = sorted(name for name, ok in present.items() if not ok)
    return {
        "score": sum(present.values()),
        "max": len(COMPONENTS),
        "present": present,
        "missing": missing,
        "word_count": len(text.split()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_file", nargs="?", help="File containing the prompt to score")
    parser.add_argument("--stdin", action="store_true", help="Read the prompt from standard input")
    parser.add_argument("--min", type=int, default=None, help="Exit 1 if the score is below this threshold")
    args = parser.parse_args(argv)

    if args.stdin:
        text = sys.stdin.read()
    elif args.prompt_file:
        try:
            with open(args.prompt_file, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(f"ERROR: could not read {args.prompt_file}: {exc}", file=sys.stderr)
            return 2
    else:
        parser.error("provide PROMPT_FILE or --stdin")

    result = score_prompt(text)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.min is not None and result["score"] < args.min:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
