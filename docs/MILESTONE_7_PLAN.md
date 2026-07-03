# Milestone 7 Implementation Plan: Multi-Agent Orchestration Skills

Status: ALL STEPS 0-8 DONE — Milestone 7 complete (2026-06-19, Claude Code
2.1.183). Worker generation is fully wired into install/status/uninstall;
worker-to-skill wiring emits native `skills:` plus invokable body-pointers;
the `security/review` reference deep skill is built, deployed, and serving
as the live validation fixture; docs (`meta/deployment`,
`meta/skill-authoring`, `docs/TEAM_ROLLOUT.md`) are updated; and the
lifecycle resync left all 50 packages `current`. See the Step 3 sub-step
status below. This plan is the recallable contract for the work. See
`docs/ROADMAP.md` Milestone 7 for goal and rationale, and `docs/HANDOFF.md`
for current state.

## Decisions This Plan Implements

Grilled and locked (see ROADMAP Milestone 7 for context):

1. Cortex is a definition + deployment layer. The runtime LLM executes the
   spawn/loop. Cortex ships no execution engine.
2. Workers are bundle-local: an `agents/` folder beside `SKILL.md`. Workers
   reference shared vault skills for expertise. No shared-worker registry yet.
3. The loop is a reusable `meta/orchestration` protocol. Per-skill entry into
   orchestration stays flexible.
4. Worker-to-skill wiring uses body-pointers as the portable default for
   access (Step 0 confirmed workers reach globally-installed skills via the
   Skill tool), plus `skills:` frontmatter for scoping and intent. Never
   inline or copy a skill body.
5. Claude-only native worker emission, enforced. Other runtimes deploy the
   orchestrator and degrade: the boss body encourages worker-spawning where
   possible and otherwise runs the roles sequentially in-context.

Non-goals (first cut): Codex-native orchestration, a shared worker registry, a
deterministic Cortex harness, inlining skill content.

## Step 0: Verification Probes (Gate)

Mirror the `model:` probe that de-risked routing. Do not build past this until
both pass on the installed Claude Code version; record results in
`docs/HANDOFF.md` and ICM.

- Probe A — subagent spawn + model + isolation: define a throwaway
  `~/.claude/agents/*.md` worker with a set `model:`, have a boss invoke it via
  the Task/Agent tool, and confirm it runs on that model in an isolated context
  and returns a result.
- Probe B — subagent `skills:` loading: give a throwaway subagent a `skills:`
  field naming an installed skill and confirm the skill loads into its context.
  If unsupported, the worker-to-skill wiring uses body-pointers only (decision
  4 fallback), and the rest of the plan is unchanged.

Clean up throwaway agents after probing.

### Result (2026-06-19, Claude Code 2.1.183)

Both probes ran headless via `claude -p "...Task tool...subagent_type..."
--model claude-haiku-4-5-20251001 --output-format json --allowedTools Task
[Skill]`. Note: `--dangerously-skip-permissions` is blocked by the sandbox
classifier; use `--allowedTools` to grant exactly the Task (and Skill)
tools instead.

- Probe A PASSED cleanly. A boss pinned to haiku spawned a worker
  declaring `model: opus`; `modelUsage` reported both `claude-haiku-4-5`
  (boss) and `claude-opus-4-8` (worker), and the worker returned its
  sentinel. Native subagent spawn, per-unit model selection, and isolated
  context all work.
- Probe B PASSED with a nuance. A worker with `skills: [cortex-probe-fact]`
  returned the skill-only codeword, but a control worker with no `skills:`
  field returned it too. Globally-installed skills are reachable by any
  subagent via the Skill tool, and Cortex already deploys all skills to
  `~/.claude/skills/`. So the `skills:` field is accepted and useful for
  scoping and intent, but it is not required for access.

Design impact: decision 4's body-pointer path is sufficient for access and
is the portable default; emit `skills:` for scoping but never treat it as
load-bearing; still never inline. Whether `skills:` also restricts a
worker to only the listed skills is an open refinement for Step 2 or 4,
not a gate blocker.

## Step 1: `meta/orchestration` Protocol Skill — DONE

Done in commit `7e7d4df`. `skills/meta/orchestration/SKILL.md` defines the
loop contract (roles, the spawn/scope/wait/evaluate/re-dispatch/aggregate
loop, stop conditions, worker definition shape, entry flexibility, and
sequential degradation). Deployed; its Claude wrapper carries `model:
opus` via the routing map, confirming routing applies to new skills. The
section below is the original spec for reference.

Author `skills/meta/orchestration/SKILL.md` (model_role: thinking). It defines
the loop contract once so deep skills inherit it:

- Roles: boss vs workers; what each may and may not do.
- Loop: spawn workers, give each a scoped task, wait, evaluate output against
  explicit completion criteria, re-dispatch unfinished work, aggregate, stop.
- Stop conditions: done-signal, max rounds, and failure handling so "until
  done" cannot loop forever.
- Entry flexibility: how an orchestrator `SKILL.md` calls into the protocol,
  with the boss naming its workers by their deployed native subagent names.
- Degradation: on runtimes without subagents, run roles sequentially in-context
  using the referenced skills.

Link from `meta/index` (automatic via frontmatter) and relate to `meta/roles`,
`meta/deployment`, `meta/skill-authoring`.

## Step 2: Worker Source Schema + Linter — DONE

Done in commit `4f21498`. `agents/` is excluded from skill discovery and
linted separately by `lint_agent` (required `name`/`description`, name
matches file stem, optional `model_tier`/`model_role`, optional `skills:`
list whose ids must resolve, unknown-key rejection, bundle-local check,
provenance, vendor-neutral language). `lint_skill.py --all` lints workers
too, so `validate.py` covers them. Worker contract documented in
`meta/orchestration`; tests in `tests/test_agent_lint.py`. Decision on
index/manifest: workers are excluded from both for now (bundle-local
implementation detail of their orchestrator); counting can be added later.
The section below is the original spec for reference.

Define Cortex-native worker frontmatter for `agents/*.md` files. Reuse routing
semantics rather than inventing parallel concepts:

- `name`, `description` (required).
- `model_tier` / `model_role` for model selection (same map as skills).
- `skills:` — list of vault skill ids the worker loads as domain knowledge.
- Optional `tools` / `allowed-tools` if the runtime supports scoping.

Extend `skills/meta/scripts/lint_skill.py` (or a sibling `lint_agent.py`) to
validate worker files: known fields, valid `model_tier`/`model_role`, and that
every referenced `skills:` id resolves to a real vault skill. Decide whether
workers appear in the generated index/manifest (recommend: count them, do not
treat them as standalone skills).

## Step 3: `agents/` Companion Handling + Native Emission

Sub-step status (decomposed under token pressure):

- 3a DONE (commit pending in this batch): pure generation, no filesystem
  writes. `install-skills.py` now has `discover_agents(skill)` (parses
  `agents/*.md`), `worker_agent_text(worker, agent, skill_names, routing)`
  (emits native subagent text: `model:` from the worker's routing class via
  the refactored `model_for_class`, a `skills:` scoping list mapped to
  native names, and a body-pointer that always names the referenced
  skill_ids; never inlines). `resolve_model` was refactored to delegate to
  `model_for_class`. Tested in `tests/test_install_model_routing.py`
  (WorkerGenerationTests).
- 3b DONE — wiring: `agents_home(agent, scope, project)` returns the Claude
  agents home (`~/.claude/agents/` global, `<project>/.cortex/claude/agents/`
  project; None for non-Claude). `write_skill_wrapper` now calls
  `sync_worker_agents` for Claude orchestrators, passing `skill_names` (the
  full-vault `skill_id -> install_name` map) so worker `skills:` use deployed
  names. Worker filenames are namespaced `<install_name>__<worker>.md`.
  Foreign (non-Cortex) files at a target are skipped, not clobbered.
- 3c DONE — drift/status: the orchestrator's metadata carries a
  `worker_agents` manifest (per-worker target path + content sha256 of the
  generated text). `workers_current` recomputes the expected manifest and
  compares it to the stored set (catches changed worker source or routing
  map) and to on-disk files (catches manual edits / deletions);
  `status_for_metadata` returns stale on mismatch. `GENERATOR_VERSION`
  bumped 7 -> 8.
- 3d DONE — uninstall/cleanup: `remove_worker_agents` deletes worker files
  recorded in metadata on uninstall/cleanup, and `sync_worker_agents` prunes
  previously-generated workers a skill no longer defines, so no orphans
  remain in the agents home.

Original spec follows.

Source discovery and deployment already handle companion dirs (`scripts/`,
`references/`, `assets/`, `vendor/`). Add `agents/`:

- Discovery: associate an `agents/` folder with its parent skill.
- Claude adapter (`scripts/install-skills.py`): generate one native subagent
  file per worker into the Claude agents home (`~/.claude/agents/`), setting
  `model:` from `config/model-routing.json` via the existing `resolve_model` /
  `model_routing` path. Reuse `VALID_MODEL_ALIASES` and the routing map.
- Resource manifest + drift: include generated worker subagents so status
  reports stale when a worker source or the routing map changes.
- Non-Claude adapters: do not emit native worker files; deploy the orchestrator
  skill only.
- Bump `GENERATOR_VERSION` when wrapper/agent output shape changes.

## Step 4: Worker-to-Skill Wiring — DONE

Done in commit (this batch). `worker_agent_text` emits the worker's `skills:`
ids as native subagent `skills:` frontmatter mapped to deployed install names,
and a `## Skills` body pointer that names the invokable handle plus source id
for each, e.g. `/article-writing (writing/article-writing)`. The pointer is the
portable path and the fallback when `skills:` is not load-bearing (Probe B
showed it is advisory, not required for access). Skill bodies are never
inlined. Tested in `WorkerGenerationTests` (native-handle pointer +
skill-id fallback). The section below is the original spec for reference.

- If Probe B passed: emit the worker's `skills:` ids as the native subagent
  `skills:` frontmatter, mapped to the installed native skill names.
- Always also write body-pointers in the worker `.md` so the worker knows it can
  reach for the referenced skills (e.g. "use `/article-writing`, `/humanizer`").
  This is the portable path and the fallback when `skills:` is unsupported.
- Never inline skill bodies.

## Step 5: Orchestrator Entry + Reference Example — DONE

Done in commit (this batch). `skills/security/review/` is the reference deep
skill: `SKILL.md` (model_role: thinking) enters the `meta/orchestration` loop
with two bundle-local workers in `agents/`. `researcher` (model_tier:
thinking -> opus) uses `forensics/pcap` + `forensics/ja4`; `reporter`
(model_tier: execution -> haiku) uses `writing/article-writing`. The two
distinct model tiers demonstrate routing diversity. Deployed live: both
workers land in `~/.claude/agents/` as `security-review__<worker>.md` with
the right `model:` and native `skills:`. The worker bodies do not repeat the
generated `## Skills` pointer (the generator emits it from frontmatter). The
original spec follows.

- Define how a deep skill's `SKILL.md` enters orchestration (flexible per
  skill, but pointing at `meta/orchestration` for the loop contract).
- Build one reference deep skill end to end to prove the path, e.g. a
  security-review orchestrator with a cyber-research worker
  (`forensics/pcap`, `forensics/ja4`) and a report-writer worker
  (`writing/article-writing`). This doubles as the validation fixture.

## Step 6: Validation Strategy — DONE

Done in commit (this batch). Lint covers workers via `lint_agent` under
`validate.py`. Generator coverage: `ReferenceDeepSkillTests` loads the real
`security/review` skill and asserts the workers emit `model: opus` /
`model: haiku` and reference the real skills by native name; `WorkerWiringTests`
covers write/prune/foreign-skip/drift/uninstall on a synthetic vault. Drift
was exercised live (editing a worker marked `security/review` claude-stale
while codex stayed current). `validate.py --fix-generated` stays green; 44
unit tests pass. The original spec follows.

Test artifacts and structure, not live multi-agent loops (expensive,
nondeterministic):

- Lint: worker schema, resolvable skill references, valid model classes.
- Generator: native worker files land in the Claude agents home with the
  expected `model:` and `skills:`/body-pointers; non-Claude targets omit them.
- Drift: editing a worker or the routing map marks packages stale; re-sync
  returns to current.
- Full `validate.py --fix-generated` stays green; add unit tests beside
  `tests/test_install_model_routing.py`.
- Live loop behavior is covered by the Step 0 probes and the Step 5 reference
  skill, not by CI.

## Step 7: Docs — DONE

Done in commit (this batch). `meta/orchestration` already carried the loop
protocol. `meta/deployment` gained a "Worker Subagents For Deep Skills"
section (agents/ is not a copied resource; Claude agents-home target,
filename namespacing, model/skills emission, drift, uninstall, foreign-file
safety, degradation) and a `meta/orchestration` relation.
`meta/skill-authoring` gained a "Deep Skills With Worker Agents" section
(orchestrator + agents/ layout, worker frontmatter example, model-class
guidance, the never-inline / no-hand-written-`## Skills` rules, and a
pointer to `skills/security/review/` as the reference). `docs/TEAM_ROLLOUT.md`
gained a "Deep Skills" note: Claude-native with automatic sequential
degradation elsewhere.

## Step 8: Lifecycle — DONE

Done in commit (this batch). `validate.py --fix-generated` green; 44 unit
tests pass; `uv run cortex team finish --no-dry-run --yes` resynced after
the meta-skill edits and all 50 packages report `current`. Committed per
the contributing protocol and pushed to `main`.

## Suggested Skills For The Build

- `collaboration/grill-me`: re-grill any high-fidelity branch that hardens
  unexpectedly.
- `meta/skill-authoring`: drafting `meta/orchestration` and the reference skill.
- `meta/deployment`: extending companion-resource deployment and drift.
- `meta/roles`: the model-routing semantics workers reuse.
- `meta/contributing`: validation-failure handling and commit discipline.
