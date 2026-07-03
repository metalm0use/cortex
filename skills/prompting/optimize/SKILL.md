---
schema_version: 1
tags:
  - "prompting"
  - "orchestration"
topics:
  - "prompt optimization"
  - "prompt improvement loop"
status: seed
created: 2026-06-19
updated: 2026-06-19
sources: []
source_count: 0
aliases:
  - "prompt-optimizer"
  - "optimize prompt"
  - "improve prompt"
skill_id: prompting/optimize
summary: "Orchestrate a critic, rewriter, and evaluator to turn a draft prompt into a measurably stronger one against a fixed checklist and rubric."
model_role: thinking
depends_on:
  - meta/orchestration
  - prompting/patterns
related:
  - meta/orchestration
  - prompting/patterns
  - writing/article-writing
---

# Prompt Optimizer

<!-- learned: 2026-06 | project: cortex-prompt-optimizer | model: thinking-model -->

Use this skill to improve a draft prompt. It is a deep skill: it coordinates
three specialized workers in a diagnose -> build -> verify loop, scoring each
round against the fixed checklist and rubric in `prompting/patterns`. Read
`meta/orchestration` for the loop contract; this skill fills in the goal, the
workers, and what "done" means.

## Core Rule

Coordinate; do not rewrite the prompt in this context. The boss takes a draft
prompt plus its intended use, runs the loop, and stops when the prompt clears
the structural floor and the rubric threshold, or the round bound is hit. The
measurement has two honest layers: deterministic structure
(`prompting/patterns` `scripts/prompt_lint.py`) and an anchored judgement
rubric. The boss never reports a prompt as improved without the scorecard.

## Entry

The user provides a draft prompt and a sentence on its intended use (the task
it should accomplish and any audience or format needs). The boss passes both,
verbatim, into every worker dispatch, because worker contexts are isolated.

## Workers

Three workers live in `agents/` beside this skill:

- `critic` (judgment, strong model): runs the structural scorer, reads the
  rubric, and returns a concrete improvement plan naming each weak or missing
  component and the pattern to apply. One scoped task: produce the plan.
- `rewriter` (assembly, fast model): rebuilds the prompt by applying the
  critic's plan using the `prompting/patterns` catalog and
  `writing/article-writing` for clear prose. One scoped task: produce the
  revised prompt, changing only what the plan calls for.
- `evaluator` (judgment, strong model): re-runs the structural scorer, scores
  the anchored rubric with cited evidence, red-teams for misread and
  injection, and returns a scorecard plus a pass/fail decision.

The critic and evaluator are distinct: the critic diagnoses the incoming
draft, the evaluator verifies the rewritten candidate. Each worker's model
comes from its `model_tier` via `config/model-routing.json` (see
`meta/roles`) — here the two judgment workers route to a strong model and the
rewriter to a fast one.

## Workflow

1. Score the draft: dispatch `critic` with the draft and intended use.
   Completion criteria: a plan that names every weak/missing component (by the
   six-part checklist) and the pattern to apply to each.
2. Build: dispatch `rewriter` with the draft, the intended use, and the
   critic's plan. Completion criteria: a revised prompt that addresses each
   plan item and changes nothing the plan did not call for.
3. Verify: dispatch `evaluator` with the revised prompt and intended use.
   Completion criteria: a scorecard with the structural score, a 0-3 rubric
   score per criterion with cited evidence, and pass/fail.
4. If the evaluator fails the candidate, re-dispatch `rewriter` with the
   evaluator's specific gaps. Re-verify.
5. Stop when the candidate clears the structural floor (all required
   components present) and every rubric criterion is at least 2, or the round
   bound is hit. Return the best candidate with its scorecard.

## Stop Conditions

- Done-signal: structural floor met and every rubric criterion >= 2.
- Max rounds: cap the build/verify cycle at 3 so a stuck rewrite cannot loop
  forever.
- Failure: if the candidate cannot clear the bar within the rounds, return the
  best candidate and name the criteria still unmet rather than looping.

## Degradation

On a runtime without isolated subagents, run the three roles sequentially in
this context: critique using `prompting/patterns` and the scorer, rewrite,
then evaluate. The loop contract and the two-layer measurement are unchanged;
the work is simply less parallel.

## Completion Criteria

The optimization is complete when the returned prompt clears the structural
floor, carries a rubric scorecard with cited evidence (not an unexplained
verdict), and either meets the threshold on every criterion or names the ones
it could not, with the draft and final scores both reported.

## Required Follow-On Reading

Read `references/worked-example.md` to see a full run end to end (a
chat-handoff seed prompt taken from 1/6 to 6/6, including a failed verify
round that the loop closes). Read it when you want a concrete trace of the
loop or a ready-made handoff prompt; skip it for the ordinary path.
