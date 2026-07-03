# Handoff

## Next Session Focus

No in-flight work. Both deep-skill milestones are complete: Milestone 7
(multi-agent orchestration) and the prompt-optimizer capability built on top
of it. The next session should pick from `docs/ROADMAP.md` (Near-Term Order)
or take a carry-over below. Full build records live in
`docs/MILESTONE_7_PLAN.md` and `docs/PROMPT_OPTIMIZER_PLAN.md` (both COMPLETE);
do not re-derive them here.

## Current State

Cortex is locally production-ready on Claude Code 2.1.183. All native packages
report `current` (resync with `uv run cortex team finish --no-dry-run --yes`).

What exists for orchestration / prompting:

- Deep skills: a `SKILL.md` orchestrator plus a bundle-local `agents/` folder
  of worker definitions, compiled to native Claude subagents
  (`<install_name>__<worker>.md`) with per-worker `model:` and a `## Skills`
  pointer. Contract and loop in `meta/orchestration`; emission/drift/uninstall
  in `meta/deployment`; authoring in `meta/skill-authoring`; workers are
  improvable source per `meta/contributing`.
- Two live deep-skill fixtures: `skills/security/review/`
  (researcher->opus, reporter->haiku) and `skills/prompting/optimize/`
  (critic/evaluator->opus, rewriter->haiku).
- Prompt engineering: `skills/prompting/patterns/` owns the six-component
  checklist, the intent->framework catalog, the deterministic
  `scripts/prompt_lint.py` (structural floor) and `scripts/intent_router.py`
  (advisory), the anchored rubric, and the copyable-deliverable rule.
  `skills/prompting/optimize/` runs the critic->rewriter->evaluator loop;
  `references/worked-example.md` has two real traces.

Model routing, the `model:` mechanism, and `GENERATOR_VERSION` (currently 8)
are documented in `meta/roles`, `meta/deployment`, and `config/README.md` —
not duplicated here.

## Open Questions / Carry-overs

- Codex orchestration: Codex deploys the orchestrator and degrades to
  sequential roles; native Codex worker emission is a future adapter, unscoped.
- Team expertise merge protocol is still undocumented.
- Whether `docs/AGENTIC_AI_INTRO_V2.html` replaces the original deck.
- A worker-genre `worker_lint` is intentionally deferred (over-engineering);
  workers are judged by the `meta/orchestration` checklist, not by running the
  task-prompt scorer on them.

## Suggested Skills

- `collaboration/grill-me`: stress-test the next milestone before building.
- `meta/skill-authoring` + `meta/orchestration`: author any new deep skill.
- `meta/deployment` + `meta/roles`: deployment mechanics and model routing.
- `meta/contributing`: when a session yields reusable knowledge.

## Artifacts To Read

- `docs/ROADMAP.md`: Near-Term Order and milestone history.
- `docs/MILESTONE_7_PLAN.md`, `docs/PROMPT_OPTIMIZER_PLAN.md`: build records.
- `skills/prompting/optimize/references/worked-example.md`: loop traces.
- `config/model-routing.json` + `config/README.md`: the team routing map.

## Risks And Watchouts

- Sub-agent and skill `model:` support is version-dependent (verified on
  2.1.183); re-verify before relying on it elsewhere.
- Changing `config/model-routing.json`, a skill's routing class, a worker, or
  a skill body marks affected packages stale. Resync with
  `uv run cortex team finish --no-dry-run --yes` and confirm `current`.
- Importing a skill-companion script can drop a `__pycache__` in its
  `scripts/`; `resource_files` now ignores `__pycache__`/`*.pyc`, but keep
  bytecode out of source dirs.
- Commit/push only when asked.

## Next Actions

1. Both deep-skill milestones are COMPLETE; do not redo. All work is committed,
   pushed, and `current`.
2. Pick the next item from `docs/ROADMAP.md` Near-Term Order; grill it first if
   the scope is not sharp.
3. Carry-overs above are lower priority.
