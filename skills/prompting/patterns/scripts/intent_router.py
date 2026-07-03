#!/usr/bin/env python3
"""Advisory intent router for prompt requests.

Suggests the prompt's primary intent and a couple of frameworks that fit it,
by counting keyword signals. This is a heuristic hint to start from, NOT a gate
and NOT a quality score: confidence is low when signals are weak or tied, and
the default is "create". Use it to pick a building approach; the judgement
layer (the critic) decides what actually fits.

Usage:
    python intent_router.py REQUEST_FILE
    python intent_router.py --stdin < request.txt

Output is JSON: {"intent", "confidence", "frameworks", "signals", "scores"}.

Adapted from the intent taxonomy of prompt-architect (MIT, ckelsoe):
https://github.com/ckelsoe/prompt-architect
"""

from __future__ import annotations

import argparse
import json
import sys


# Keyword signals per intent. Lowercased substring match; deliberately small.
INTENT_SIGNALS: dict[str, list[str]] = {
    "recover": ["reconstruct", "reverse engineer", "recover the prompt", "what prompt", "from this output", "infer the prompt"],
    "clarify": ["not sure", "unclear", "vague", "help me figure out", "don't know what", "interview me", "ask me questions"],
    "create": ["write", "create", "draft", "generate", "compose", "build", "make", "produce", "design a prompt"],
    "transform": ["rewrite", "refactor", "convert", "improve", "edit", "revise", "summarize", "translate", "rephrase", "shorten"],
    "reason": ["calculate", "solve", "figure out", "reason", "evaluate", "prove", "derive", "step by step", "work out"],
    "critique": ["critique", "review", "stress-test", "find flaws", "red-team", "red team", "verify", "attack", "pre-mortem", "devil's advocate"],
    "agentic": ["use tools", "tool use", "agent", "multi-step", "iterate until", "act and observe", "react", "loop until"],
}

# A curated framework or two per intent (the catalog lives in the skill body).
FRAMEWORKS: dict[str, list[str]] = {
    "recover": ["RPEF (reverse-engineer the prompt from its output)"],
    "clarify": ["Reverse Role Prompting (let the model interview you first)"],
    "create": ["CO-STAR (context, objective, style, tone, audience, response)", "RISEN (role, instructions, steps, end-goal, narrowing)"],
    "transform": ["Self-Refine (draft, critique, revise)", "Chain of Density (for tighter summaries)"],
    "reason": ["Step-Back (abstract the principle first)", "Tree of Thought (branch and compare)"],
    "critique": ["Pre-Mortem (assume it failed; why?)", "Devil's Advocate (argue the opposite)"],
    "agentic": ["ReAct (interleave reasoning and tool actions)"],
}


def detect_intent(text: str) -> dict:
    """Return {intent, confidence, frameworks, signals, scores} for a request."""
    lowered = text.lower()
    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}
    for intent, signals in INTENT_SIGNALS.items():
        hits = [s for s in signals if s in lowered]
        if hits:
            scores[intent] = len(hits)
            matched[intent] = hits

    if not scores:
        intent, confidence = "create", "low"
    else:
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        intent = ranked[0][0]
        top = ranked[0][1]
        runner = ranked[1][1] if len(ranked) > 1 else 0
        confidence = "high" if top >= 2 and top > runner else "medium" if top > runner else "low"

    return {
        "intent": intent,
        "confidence": confidence,
        "frameworks": FRAMEWORKS.get(intent, []),
        "signals": matched.get(intent, []),
        "scores": scores,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_file", nargs="?", help="File containing the prompt request to route")
    parser.add_argument("--stdin", action="store_true", help="Read the request from standard input")
    args = parser.parse_args(argv)

    if args.stdin:
        text = sys.stdin.read()
    elif args.request_file:
        try:
            with open(args.request_file, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(f"ERROR: could not read {args.request_file}: {exc}", file=sys.stderr)
            return 2
    else:
        parser.error("provide REQUEST_FILE or --stdin")

    print(json.dumps(detect_intent(text), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
