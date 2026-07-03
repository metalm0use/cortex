# Prompt Optimizer Plan: Meaningful Deep-Skill Demonstration

Status: COMPLETE (2026-06-19). The prompt-engineering capability is built,
deployed, and is the meaningful Milestone 7 demonstration. All steps done:
reference skill + deterministic scorer, orchestrator + three workers
(opus/haiku/opus, verified live in `~/.claude/agents/`), `lint_agent`
review metadata, the `meta/contributing` worker-prompts-are-source note,
deploy/sync (54 packages current), and tests (57 green). A latent
resource-manifest bug (pycache leaking into the manifest) was fixed in
passing. See `docs/MILESTONE_7_PLAN.md` for the orchestration mechanics this
exercises.

## Decisions (grilled and locked)

1. Build a deep-skill **orchestrator on top of a thin reference skill**, not a
   standalone teaching skill. The reference skill carries the patterns; the
   orchestrator is the meaningful, runnable M7 test case.
2. The done-signal is **two layers**: a deterministic structural lint
   (`prompt_lint.py`, objective + unit-testable) plus an anchored 0-3
   LLM-judge rubric. Combined, with a 3-round bound. The lint and rubric are
   also the **build spec** the rewriter works from, so the loop constructs
   better prompts, not just grades them. Prompt quality is not fully
   objective; we are honest about which layer is which.
3. Three workers mirror diagnose -> build -> verify:
   - `critic` (`model_tier: thinking` -> opus): run the lint, diagnose weak
     or missing rubric components, return a concrete improvement plan.
   - `rewriter` (`model_tier: execution` -> haiku): implement the plan using
     the reference patterns. Execution-class because it assembles a concrete
     plan, not open-ended reasoning.
   - `evaluator` (`model_tier: thinking` -> opus): re-run the lint, score the
     anchored rubric with cited evidence, red-team for misread/injection,
     emit a scorecard and pass/fail.
4. Workers are **self-learning Cortex files**: keep required provenance and
   add optional review metadata (`review_status`, `reviewed_by`,
   `expertise_domain`, `confidence`, `reviewed_at`) so a worker prompt can be
   human-reviewed and improved through `meta/contributing` like any skill.
5. Naming: a new `prompting` domain. `prompting/patterns` (reference,
   model_role: reference) and `prompting/optimize` (orchestrator, model_role:
   thinking). Workers deploy as `prompt-optimizer__<worker>.md`.

Non-goals: a new middle routing tier for sonnet (that is a config-map
decision, not per-worker); live multi-agent CI (covered by the deterministic
script plus structural fixture tests); vendor-coupled code samples.

## Steps

1. Reference skill `prompting/patterns` + `scripts/prompt_lint.py`
   (deterministic component scorer) + unit tests for the scorer.
2. Orchestrator `prompting/optimize/SKILL.md` + `agents/{critic,rewriter,
   evaluator}.md`. Workers reference `prompting/patterns`; rewriter also
   reaches `writing/article-writing` for prose.
3. Teach `lint_agent` to accept the optional review-metadata block (mirror
   the skill review keys + shape checks). Add agent tests.
4. Add a short note to `meta/contributing` that worker prompts are vault
   source subject to the same triage/commit loop.
5. Validate (`validate.py --fix-generated`), deploy/sync
   (`uv run cortex team finish --no-dry-run --yes`), confirm workers land in
   `~/.claude/agents/` with the right models, confirm `current`.
6. Tests: `prompt_lint.py` scorer (weak vs strong prompt), reference-skill
   fixture (workers emit opus/haiku and reference the real skills), drift.
7. Docs: the orchestrator body documents entry; `meta/skill-authoring`
   already covers deep skills. Update `docs/HANDOFF.md`.

## Validation Strategy

The deterministic `prompt_lint.py` scorer is the objective, CI-testable core:
crafted weak/strong prompts assert the score. The orchestrator + workers are
covered structurally (lint, generation, drift) like `security/review`. Live
loop behavior is demonstrated, not CI-gated.
