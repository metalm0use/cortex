# Cortex Roadmap

## Design Principle

Cortex must be portable first and automation-friendly second.

The source of truth is the repository plus deterministic local scripts.
Hosted CI, local git hooks, editor integrations, and native agent skill
folders are adapters around that core. They may improve enforcement, but
they must never become required infrastructure.

Windows and Linux are first-class platforms. Codex and Claude are the
minimum supported native skill targets; additional runtimes are welcome
only when they remain adapters around the same Cortex source files.

Core validation should stay standard-library only. Optional user
experience improvements may use third-party Python libraries when they
materially improve the terminal application, but those dependencies must
be declared, documented, and kept out of the minimum validation path.

## First Production Deployment Gate

Status: local production completed on 2026-06-05 for global Codex and
Claude native packages in the maintainer environment. The latest CLI
deployment UX fixes have been validated locally, including dry-run apply
prompting, quieter focused status, managed cleanup, and first-run
selector display polish. Team rollout still needs a first-audience
walkthrough and an explicit expertise-merge protocol so multiple humans
can improve the same skill without blocking each other or silently
flattening disagreement.

This gate defines the first production cutover for Cortex. It is separate
from ordinary feature milestones because production readiness depends on
repository health, native package state, and user-facing onboarding all
being true at the same time.

Required before calling the first deployment complete:

- `python skills/meta/scripts/validate.py --fix-generated` passes.
- The working tree is clean except for intentional ignored local runtime
  artifacts such as `.venv/`, `.cortex/`, Obsidian workspace state, and
  Smart Environment data.
- `docs/HANDOFF.md` names the current deployment state, last relevant
  commits, known local environment repairs, and the exact next commands.
- `docs/FIRST_10_MINUTES.md` has been walked with a fresh-clone mindset.
- `docs/TEAM_ROLLOUT.md` has been checked against the intended first
  audience, even if the first deployment remains local-only.
- Native package status has been inspected for the intended targets.
- Managed Codex and Claude packages selected for the deployment are
  synced and then reported as `current`.
- Any unmanaged native target is left untouched and called out in the
  handoff or rollout notes.
- No secrets, local profiles, editor workspace state, or generated
  virtualenv/cache artifacts are committed.

Recommended command path:

```bash
uv run cortex validate --fix-generated
uv run cortex finish --categories all --agents codex,claude --scope global
uv run cortex finish --categories all --agents codex,claude --scope global --no-dry-run --yes
uv run cortex status --categories all --agents codex,claude --scope global
```

Standard-library fallback:

```bash
python skills/meta/scripts/validate.py --fix-generated
python scripts/install-skills.py --action status --categories all --agents codex,claude --scope global
python scripts/install-skills.py --action sync --categories all --agents codex,claude --scope global --yes
python scripts/install-skills.py --action status --categories all --agents codex,claude --scope global
```

Success means a fresh agent or teammate can clone Cortex, validate it,
install or sync selected native packages, point an agent at the vault,
and understand how to feed reusable learning back into source skills.

## Post-Production Polish Tasks

These are not blockers for local production. They are the next
development tasks that make team rollout less dependent on maintainer
memory.

- Add a lightweight docs smoke check that verifies key human-facing docs
  exist, checks important cross-links, and confirms the README points
  readers through the intended journey. Completed locally in the portable
  validation contract.
- Validate `docs/FIRST_10_MINUTES.md` from a fresh clone or clean
  worktree, recording any missing assumptions in the guide.
- Validate `docs/TEAM_ROLLOUT.md` against the first real project or
  teammate audience.
- Decide whether saved profiles need a team-shareable `--profile-file`
  path in addition to local `.cortex/profiles/` preferences. Completed
  for the enhanced CLI with committed JSON profile support.
- Turn shell completion from a one-off local profile repair into a
  documented or CLI-supported setup path. Completed with
  `uv run cortex completion <shell>`.
- Document the enhanced CLI and stdlib fallback as a command contract
  with expected inputs, outputs, mutating behavior, flag meanings, and
  profile schema. Completed in `docs/CLI_REFERENCE.md`.
- Add optional hosted CI templates later if the team wants hosted
  feedback. Deferred for now; local validation remains the production
  contract.
- Decide whether skill maturity needs a field separate from human review
  metadata before broader team rollout.
- Review whether `docs/AGENTIC_AI_INTRO_V2.html` should replace the
  original intro deck or remain as a separate review variant.
- Define the low-friction expertise merge protocol for teams: how
  attributed claims land, how agreeing claims are synthesized, and how
  contradictory claims become visible conflicts instead of stalled work.
- Complete the offline-validation CLI follow-up. Done in the enhanced
  CLI and stdlib installer: dry-run previews can be applied from the same
  first-run flow, status hides missing packages by default while offering
  focused agent filters, cleanup removes only Cortex-managed artifacts,
  and the first-run selector uses stable ASCII markers for selected rows.

## Milestone 0: Stabilize The Local Contract

Status: completed in `34a37b7`.

Goal: any user on a normal machine can validate and operate Cortex
without hosted runners, paid services, embeddings, or vendor-specific
memory.

Deliverables:

- Keep `doctor.py` as the minimum non-mutating health check.
- Keep `lint_skill.py --all`, `manifest_builder.py --check`, and
  `index_builder.py --check` runnable from the repository root.
- Add a single command or wrapper for the full local validation contract.
- Document the validation contract in the README and handoff.

Success means a fresh clone can answer: "Is this vault healthy?" without
network access.

## Milestone 1: Native Install Status And Sync

Status: completed in `ec5ff6e`.

Goal: installed native packages can be inspected, repaired, updated, and
removed without guessing.

Deliverables:

- Add generated metadata to each native package:
  source skill ID, source path, source hash, generated timestamp, Cortex
  commit, target agent, scope, and install mode.
- Add installer commands or flags for `status`, `sync`, `repair`, and
  `uninstall`.
- Detect stale native packages when Cortex source files change.
- Refuse to overwrite unmarked native packages.
- Preserve Windows and Linux support for Codex and Claude native
  `SKILL.md` packages.

Success means the user can ask: "Are my Codex, Claude, and Cursor skills
current with Cortex?" and get a deterministic answer.

## Milestone 1.5: Installer UX And Dependency Packaging

Status: completed in `633e5ac`.

Goal: make native skill deployment pleasant enough to use regularly
without making optional Python dependencies part of the core validation
contract.

Deliverables:

- Add a declared dependency path using `pyproject.toml` and `uv`.
- Build an optional richer terminal UI with Typer or an equivalent
  command framework, plus Rich or another display library if it
  materially improves selection and status output.
- Add guided first-run setup with checkbox multi-select for categories,
  individual skills, and target agents.
- Add saved local install profiles so common deployment selections can
  be reused without re-answering the wizard.
- Prefer subcommands such as `install`, `status`, `sync`, `repair`, and
  `uninstall` for the enhanced CLI.
- Keep `skills/meta/scripts/validate.py` and core vault health scripts
  standard-library only.
- Keep the current stdlib installer path as the fallback for fresh clones
  and agents that do not install optional dependencies.
- Ensure every interactive workflow has a complete noninteractive input
  path through flags or an input file. No deployment or future creation
  workflow may require a terminal wizard only.
- Document the dependency boundary clearly: users can validate and
  script Cortex without installing packages, but can opt into enhanced
  deployment UX.

Success means deployment feels like a real terminal application for
humans, while agents and fresh clones still have a simple stdlib path.

First slice:

- Add `pyproject.toml` with optional Typer and Rich dependencies.
- Add the `cortex` console entry point under `src/cortex_cli/`.
- Delegate enhanced `install`, `status`, `sync`, `repair`, and
  `uninstall` subcommands to `scripts/install-skills.py`.
- Render enhanced status output as a Rich table, with raw output still
  available for troubleshooting.
- Add `cortex first-run` for guided dry-run-first setup.
- Add `cortex profile` commands for saved local deployment selections.
- Delegate `cortex validate` to `skills/meta/scripts/validate.py`.
- Keep the enhanced CLI as Tier 2; Tier 0 validation and Tier 1 install
  behavior remain runnable with Python's standard library.

Follow-up fix:

- `8161865` fixed first-run selection drift so meta skills no longer
  appear as optional user choices and individual-only selection no
  longer accidentally keeps `categories=all`.
- `39a946a` fixed offline validation feedback for the deployment CLI:
  first-run no longer exits after dry-run preview, status supports
  focused agent filters and quiet defaults, and cleanup can remove
  Cortex-managed native packages without touching unmanaged local skills.
- The current selector-display polish keeps selected first-run rows
  visually stable with `*` markers, including the default `all`
  selection.

## Milestone 2: Human Expertise Review

Status: completed in `6cb6d81`.

Goal: Cortex compounds agent learning and human domain expertise without
pretending they are the same signal.

Deliverables:

- Add optional frontmatter for review and confidence:
  `review_status`, `reviewed_by`, `expertise_domain`, and `confidence`.
- Add a low-friction command for agent-mediated expertise capture so
  humans can contribute through normal prompting instead of editing
  markdown directly.
- Update the linter to validate those fields when present.
- Define review meanings:
  `unreviewed`, `reviewed`, `disputed`, and `needs-refresh`.
- Make conflicts and deprecations visible in generated indexes.

Success means a domain expert can improve trust in a skill without
rewriting the whole vault protocol.

## Milestone 3: Skill Maturity Lifecycle

Status: open design checkpoint; not the next implementation milestone.

Goal: distinguish seed ideas from battle-tested knowledge.

Deliverables:

- Decide whether current `status` values need expansion beyond
  `seed`, `active`, `draft`, `deprecated`, and `conflict`.
- Consider a maturity field such as:
  `trial`, `active`, `canonical`, `deprecated`, and `conflict`.
- Teach the index to expose maturity or status clearly.
- Define what evidence promotes a skill to canonical.

Success means future agents can tell whether a skill is experimental,
trusted, or historically retained.

## Milestone 4: First 10 Minutes Onboarding

Status: local production-ready; guide exists and still needs independent
fresh-clone validation before team rollout.

Goal: make Cortex obvious and useful before the user understands all of
the philosophy.

Deliverables:

- Add a concise first-run path:
  clone, run doctor, install selected skills, use `AGENTS.md`, add a
  log entry, add or update a skill, validate, commit, reinstall.
- Add OS-specific notes only where behavior differs.
- If optional Python dependencies are introduced for terminal UX, provide
  a clear install path such as `uv sync` while preserving stdlib-only
  validation.
- Keep examples small and copyable.

Success means a new user can get value from Cortex before reading every
meta skill.

First slice:

- Add `docs/FIRST_10_MINUTES.md` as the shortest end-to-end path.
- Link the guide from the README without turning the README back into an
  agent-only structure.
- Include both enhanced `uv run cortex ...` commands and stdlib
  fallbacks.
- Add `uv run cortex finish` as a thin enhanced wrapper around the
  validate/status/sync/status lifecycle so native package drift is harder
  to forget without adding another stdlib script.
- Use task-shaped native names for non-meta packages where safe, preferring
  the first source alias so examples include `/pcap`, `/humanizer`,
  `/handoff`, and `/sql`, while keeping meta packages prefixed as
  `/cortex-meta-*`.
- Keep the broad "why agentic AI feels different" material separate
  from the first-run path.

Stretch goal:

- Add a beginner-friendly agentic AI introduction that explains tokens,
  tokenization, context windows, compaction, memory, `AGENTS.md`,
  `CLAUDE.md`, `CODEX.md`, and "dumb in the middle" failures so new and
  experienced users can understand why Cortex exists. Completed with
  `docs/AGENTIC_AI_INTRO.html`.
- Build that introduction as an offline-capable HTML slide deck using
  `presentation/frontend-slides`. The skill vendors `frontend-slides`
  and `beautiful-html-templates` so enterprise Codex and Claude
  environments without internet access can still generate and revise the
  deck. The first deck uses the vendored Creative Mode template language
  as a fixed-stage, self-contained HTML presentation.
- A V2 review variant exists at `docs/AGENTIC_AI_INTRO_V2.html`. It
  keeps the Creative Mode and `deck-stage.js` structure, tightens the
  title-card tagline, expands the instruction-files slide with
  `MEMORY.md`, and fixes the final slide stamp overlap. Decide whether
  V2 replaces the original deck after review.

## Milestone 4.5: Team Rollout Hardening

Status: local production-ready; guide exists and needs first-audience
validation plus explicit expertise-merge guidance before broader rollout.

Goal: make Cortex safe and unsurprising when more than one person or
project starts using it.

Deliverables:

- Add a concise `docs/TEAM_ROLLOUT.md`.
- Add a production checklist for validation, deployment, secrets, and
  native package sync.
- Enforce useful alias/topic trigger metadata for non-meta skills.
- Add explicit validation failure handling to the contribution protocol.
- Keep guardrails in `meta/contributing` and mechanical checks in scripts
  instead of turning onboarding docs into policy manuals.
- Add a docs smoke check so README, onboarding, rollout, roadmap, and
  handoff links do not drift from each other.
- Support a shareable profile file for repeatable installs across
  machines.
- Document and implement shell completion setup for the enhanced CLI.
- Add an "intellectual merge" protocol for domain expertise:
  contributions should land as attributed, confidence-marked claims;
  compatible claims should be synthesized into clearer guidance; true
  contradictions should be marked with conflict blocks and logged for
  later review instead of blocking every update.
- Decide whether the first expertise-merge workflow can use existing
  pieces (`capture_expertise.py`, skill edits, logs, and
  `meta/conflicts`) or needs a small helper for propose/synthesize/
  dispute/resolve.

Success means a team can adopt Cortex without relying on one maintainer's
session memory, and experts can improve shared skills without waiting on
perfect consensus for every useful claim.

## Milestone 5: Optional Automation Templates

Goal: make continuous validation easy for people who have automation,
without requiring it.

Deliverables:

- Add optional hosted CI templates only after the local contract is
  stable.
- Ensure every automation command is just a wrapper around local scripts.
- Document that local validation remains authoritative.
- Keep hooks optional and generated from scripts, not hand-maintained as
  the only enforcement layer.
- Include a docs smoke check if Milestone 4.5 adds one.

Success means users with runners can catch regressions automatically,
while users without runners lose no core capability.

## Milestone 6: Feedback And Change History

Goal: make Cortex's learning over time easy to inspect.

Deliverables:

- Keep lightweight monthly logs for operational context.
- Decide whether logs should be indexed more deeply or remain plain
  chronological notes.
- Add a way to link log entries to skill IDs when useful.
- Avoid turning logs into noisy transcripts.

Success means the repository shows not only what Cortex knows, but why
that knowledge changed.

## Milestone 7: Multi-Agent Orchestration Skills

Status: COMPLETE (2026-06-19, Claude Code 2.1.183). All Steps 0-8 of
`docs/MILESTONE_7_PLAN.md` are done: orchestration protocol, worker schema +
linter, worker subagent generation wired into install/status/uninstall,
worker-to-skill wiring, the `security/review` reference deep skill, docs,
and lifecycle. The full record, including the resolved design questions,
lives in `docs/MILESTONE_7_PLAN.md`.

Goal: let a Cortex skill kick off an orchestrator agent that spawns
specialized sub-agents, each with its own model, isolated context, and
domain skills, and drives them in a loop until the work is done. The
orchestrator is the "boss": it spawns workers, hands each a scoped task,
waits, and keeps them working until completion criteria are met. Example:
a security-review orchestrator spawns a cyber-research worker (with
`forensics/pcap` and `forensics/ja4`) and a report-writer worker (with
`writing/article-writing`), then assembles their output.

This milestone builds directly on the model-routing work completed in
this cycle. Claude Code sub-agents (`~/.claude/agents/<name>.md`) support
per-unit `model:` selection and isolated context windows; that was
empirically verified, and the `config/model-routing.json` capability
class-to-model map already exists to drive sub-agent model choice.

Architecture sketch:

- Add an `agents/` companion folder to folder-native skills, beside
  `SKILL.md`, `scripts/`, `references/`, `assets/`, and `vendor/`.
- Each source agent file is Cortex-native and model-agnostic: it declares
  a routing class (reuse `model_tier`/`model_role` capability classes), a
  description, and the Cortex skill ids it should load as domain
  knowledge.
- The orchestrator `SKILL.md` is the entry point. When invoked it spawns
  the declared sub-agents, scopes each task, waits, and loops until done.
- Deployment generates native sub-agent packages into the agent home's
  agents directory, setting `model:` from the routing config and wiring
  each sub-agent's loadable skills.

Deliverables:

- Define Cortex-native source agent frontmatter and teach the linter to
  validate it.
- Add `agents/` to companion resource handling, resource manifests, and
  drift detection in deployment.
- Generate native Claude sub-agent files with model selection from
  `config/model-routing.json`.
- Define how a sub-agent declares the Cortex skills it loads.
- Author an orchestration pattern or meta-skill for the boss loop: spawn,
  scope, wait, retry-until-done, aggregate, and stop conditions.
- Decide Codex and other adapter behavior: native equivalent where the
  runtime supports it, advisory otherwise, keeping source vendor-neutral.

Resolved design questions (see `docs/MILESTONE_7_PLAN.md` for detail):

- Source agent files use a dedicated worker frontmatter schema linted by
  `lint_agent`; workers are bundle-local and excluded from the index and
  manifest (an orchestrator implementation detail).
- The orchestrator decides "done" by explicit per-worker completion
  criteria plus a max-round bound and recorded-gap failure handling, per
  `meta/orchestration`.
- Sub-agents receive domain skills by `skill_id` reference (emitted as
  native `skills:` mapped to deployed names, plus a body pointer); skill
  bodies are never inlined.
- Claude is the first and only native target; Codex and others deploy the
  orchestrator and degrade to sequential roles. Native Codex worker
  emission is a future adapter.

Success means a maintainer can define an orchestrator plus its workers as
Cortex source, deploy them, and have the boss agent coordinate
model-appropriate workers to completion without manual babysitting.

## Near-Term Order

1. Define and document the team expertise merge protocol for first
   rollout.
2. Review `docs/AGENTIC_AI_INTRO.html` and
   `docs/AGENTIC_AI_INTRO_V2.html`; decide whether V2 replaces the
   original or remains a variant.
3. Decide whether skill maturity needs a field separate from review
   status.
4. Revisit optional automation templates after first real team use.
5. Consider a native Codex orchestration adapter once Claude deep skills
   see real team use.

Completed this cycle: Milestone 7 (multi-agent orchestration deep skills,
Steps 0-8); the prompt-optimizer capability built on it (`prompting/patterns`
reference skill with a deterministic scorer + advisory intent router and an
intent->framework catalog adapted from prompt-architect (MIT); the
`prompting/optimize` critic/rewriter/evaluator deep skill; a worker-prompt
quality checklist in `meta/orchestration`); `docs/FIRST_10_MINUTES.md` and
`docs/TEAM_ROLLOUT.md` validation passes; first-run profile-save prompt fix;
the daily-command callout; and model-tier routing with a team-editable
`config/model-routing.json`. See `docs/PROMPT_OPTIMIZER_PLAN.md`.
