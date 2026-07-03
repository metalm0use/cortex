---
schema_version: 1
tags:
  - "prompting"
  - "llm"
topics:
  - "prompt engineering"
  - "prompt patterns"
status: seed
created: 2026-06-19
updated: 2026-06-19
sources:
  - "real-world use 2026-06-19: an outer code fence broke one-shot copy of a Markdown deliverable that had inner code fences"
  - "prompt-architect by ckelsoe (MIT), https://github.com/ckelsoe/prompt-architect: intent-routing taxonomy and framework catalog, adapted 2026-06-20"
source_count: 2
aliases:
  - "prompt-engineering"
  - "prompt patterns"
  - "prompt design"
skill_id: prompting/patterns
summary: "Build and score effective prompts from a fixed component checklist, a pattern catalog, and an anchored quality rubric."
model_role: reference
depends_on: []
related:
  - writing/article-writing
---

# Prompt Engineering Patterns

<!-- learned: 2026-06 | project: cortex-prompt-optimizer | model: thinking-model -->

Use this skill to build a strong prompt from parts, or to judge an existing
one. It is the reference catalog behind the `prompting/optimize`
orchestrator: the component checklist below is both the build spec and the
structural scorer, and the rubric is the qualitative scorer.

## Core Rule

A strong prompt is assembled from named components, not written as one
undifferentiated blob. To improve a prompt, find which components are weak
or missing, apply the matching pattern, and re-score. Measurement has two
honest layers: a deterministic structural check (presence of components) and
an anchored qualitative rubric (judgement). Neither alone is sufficient.

## Choose the Approach by Intent

Before fixing components, decide what kind of prompt this is — different
intents need different structures. `scripts/intent_router.py` gives a
heuristic suggestion (intent + a fitting framework); treat it as a starting
hint, not a verdict.

| Intent | When | Fitting frameworks |
|---|---|---|
| Create | new prompt from scratch | CO-STAR (context, objective, style, tone, audience, response); RISEN (role, instructions, steps, end-goal, narrowing); RTF (role, task, format) |
| Transform | improve or convert existing text | Self-Refine (draft -> critique -> revise); Chain of Density (tighter summaries) |
| Reason | solve a multi-step problem | Step-Back (abstract the principle first); Tree of Thought (branch and compare) |
| Critique | stress-test or verify | Pre-Mortem (assume it failed, find causes); Devil's Advocate (argue the opposite) |
| Recover | rebuild a lost prompt from its output | RPEF (reverse-engineer from the output) |
| Clarify | requirements are vague | Reverse Role Prompting (the model interviews you first) |
| Agentic | tool use in a loop | ReAct (interleave reasoning and actions) |

These frameworks are just component recipes: CO-STAR front-loads role and
output format; Step-Back and Tree of Thought strengthen the task component for
hard reasoning; Pre-Mortem adds robustness. Pick the lightest framework that
supplies the components the prompt is missing.

### When Not to Add Structure

Frameworks are overhead. Skip them, and keep the prompt short, for
fully-specified one-off asks, simple factual lookups, and ordinary
conversational turns. Add structure only when a missing component is actually
hurting the output.

## Component Checklist (Build Spec)

These six components map 1:1 to `scripts/prompt_lint.py`. Treat any missing
component as the first thing to add. (They describe *task/output* prompts —
the kind you paste to get an answer. For *role/system* prompts such as
orchestration worker definitions, judge by `meta/orchestration` "Worker
Prompt Quality" instead; the scorer under-scores that genre.)

1. **Role / context** — who the model is and the situation it operates in.
2. **Task / goal** — the explicit job, stated as an instruction.
3. **Output format** — the exact shape of the answer (schema, sections,
   length, JSON/Markdown) *and how it is delivered so it is usable as-is*.
   When the answer is Markdown that contains code fences, say to emit it as
   raw Markdown or in a longer/distinct outer fence; never nest same-delimiter
   fences.
4. **Examples** — at least one worked input/output when the task is
   non-obvious or format-sensitive.
5. **Constraints** — what must hold and what to avoid (length, tone,
   forbidden moves).
6. **Guardrails** — how to handle out-of-scope, adversarial, or
   injection-style requests.

## Pattern Catalog

Apply the pattern that fixes the weak component:

- **Few-shot examples** — supply 1-5 representative input/output pairs;
  choose examples that cover the edge cases the model gets wrong. Fixes
  *examples* and often *output format*.
- **Chain-of-thought** — ask for explicit reasoning before the answer for
  multi-step tasks; keep the final answer clearly delimited. Fixes *task*
  clarity on hard problems.
- **Structured output** — specify a schema (fields, types) or a fixed
  section layout, and say what to do when a field is unknown. Fixes *output
  format*.
- **Copyable deliverable** — when the answer is itself Markdown containing
  code fences, specify the delivery form so it pastes in one shot: emit raw
  Markdown with no outer fence, or wrap the whole block in a longer outer
  fence (four backticks) or `~~~` so inner triple-backtick blocks survive. A
  deliverable that needs manual de-fencing before use has failed. Fixes
  *output format* for paste-ready output.
- **Role and system framing** — set a precise role and the constraints that
  follow from it, rather than a vague persona. Fixes *role* and
  *constraints*.
- **Decomposition** — split a broad request into ordered sub-tasks so each is
  checkable. Fixes overloaded *task*.
- **Guardrail clauses** — state how to refuse or redirect out-of-scope and
  injection-style input, and never to follow instructions embedded in the
  data being processed. Fixes *guardrails*.

These patterns are model-agnostic. Name the behavior you want; do not tune
for one vendor's quirks.

## Structural Scorer

`scripts/prompt_lint.py` reports which components are present. It is
objective and repeatable, but it only checks presence, not quality.

```bash
python scripts/prompt_lint.py PROMPT_FILE
python scripts/prompt_lint.py --stdin < prompt.txt
python scripts/prompt_lint.py PROMPT_FILE --min 5   # exit 1 if score < 5
```

It prints JSON with `score`, `max`, `present`, and `missing`. Use `missing`
as the build list.

`scripts/intent_router.py` is a companion advisory tool: it suggests the
request's intent and a fitting framework (with a confidence). It is a hint for
picking an approach, not a quality score and not a gate.

```bash
python scripts/intent_router.py REQUEST_FILE
python scripts/intent_router.py --stdin < request.txt
```

## Quality Rubric (Anchored)

Score each criterion 0-3 with the anchor below, and cite the evidence in the
prompt that justifies the score. This is the qualitative layer; it is
judgement, so require justification rather than treating it as objective.

- **Clarity** — 0 ambiguous; 1 readable but loose; 2 mostly unambiguous; 3 a
  cold reader cannot reasonably misread the task.
- **Specificity** — 0 generic; 1 some detail; 2 concrete; 3 leaves no
  important decision unspecified.
- **Robustness** — 0 breaks on edge or adversarial input; 1 handles the happy
  path; 2 handles common edges; 3 handles edges and injection-style input.
- **Format fidelity** — 0 no format; 1 named but vague; 2 specified; 3
  specified with the unknown/empty cases handled and the result usable as-is
  (no nested-fence or container conflict that forces manual editing before
  the output can be used).

A prompt is "good enough" when every required component is present (structural
floor) and every rubric criterion is at least 2, or the optimizer's round
bound is reached.

## Completion Criteria

The skill is applied well when the improved prompt names each weak component,
applies the matching pattern, passes the structural floor, and carries a
rubric scorecard with cited evidence rather than an unexplained verdict.
