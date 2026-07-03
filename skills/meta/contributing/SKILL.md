---
schema_version: 1
tags:
  - "meta"
  - "protocol"
topics:
  - "vault maintenance"
  - "skill updates"
status: active
created: 2026-05-31
updated: 2026-06-19
sources:
  - "initial user-provided seed document, incorporated 2026-05-31"
  - "user product rule 2026-06-05: first-party the happy human path; keep flags as the automation contract"
source_count: 2
aliases:
  - "update protocol"
skill_id: meta/contributing
summary: "Protocol for deciding what belongs in the vault, how to update it, and how model roles are separated."
model_role: thinking
depends_on: []
related:
  - meta/index
  - meta/roles
  - meta/conflicts
  - meta/deployment
  - meta/source-manifest
  - meta/skill-authoring
review_status: human-noted
reviewed_by:
  - "project owner"
expertise_domain:
  - "cortex"
  - "human-in-the-loop"
confidence: high
reviewed_at: 2026-06-02
---

# Contributing to Cortex

<!-- learned: 2026-05 | project: cortex-bootstrap | model: seed -->

This document is the invariant layer. It does not belong to any project
or vendor. It lives in the vault and is read by whatever agent is
working, regardless of model provider.

If you are reading this after a session, decide whether the vault should
be different because of what just happened.

## 1. Qualification Bar

Before writing anything, ask one question:

> Would a cold agent, with no session context and no memory, be
> meaningfully better on a similar problem with this knowledge?

If yes, it qualifies. If maybe, it qualifies. If the learning only
applies to one repository, one file, or one bug, it usually does not.

Things that almost always qualify:

- A pattern that caused avoidable rework.
- An edge case the documentation did not make obvious.
- A decision that should be pre-reasoned for future sessions.
- A tool behavior that surprised the agent.
- A security gotcha with a specific bypass or failure mode.
- A file format quirk that is not obvious from the extension.

Things that rarely qualify:

- Fixing a typo in a specific file.
- A workaround for a one-project dependency conflict.
- Anything likely to be obsolete within a week.
- General advice any competent agent would already know.

## 2. Triage

Before writing, read `skills/meta/index/SKILL.md`.

Search for exact and adjacent matches. When in doubt, update an existing
skill instead of creating a new file. The vault should stay flat and
navigable, and each new file should earn its place.

After triage decides that a new skill or substantial skill update is
needed, follow `skills/meta/skill-authoring/SKILL.md` for Cortex-native drafting
rules. Resource-bearing skills should look like native skill folders with
a root `SKILL.md`, but the file must use Cortex frontmatter and
validation rather than being copied unmanaged from a vendor package.

```text
New knowledge -> read meta/index/SKILL.md ->
  fits existing skill     -> update that file
  adjacent to existing    -> update that file with a new section
  contradicts existing    -> flag and log a conflict
  genuinely novel         -> create a new skill file
```

## 3. Writing Contract

Everything written to the vault must obey these rules.

Each skill must include `schema_version: 1`. The schema version is the
contract between the markdown files and the enforcement scripts. When
frontmatter requirements change, update the schema deliberately and
teach the linter how to read it.

Each skill may include a `model_role` frontmatter hint. Use `thinking`
for skills that require judgment, conflict resolution, or high-fidelity
drafting; use `execution` for skills that primarily format, lint,
generate, or commit; use `reference` for ordinary domain knowledge.
Agents that cannot enforce model routing should treat the field as
guidance and keep working.

Model-agnostic language:
Write for "the agent", "the thinking model", "the execution model", or
use imperative second person. Do not bind instructions to one vendor or
one product unless the skill is specifically about that product.

Cold-agent readability:
Assume the reader is competent in general but knows nothing about the
session that produced the insight. Define acronyms on first use. Spell
out the gotcha fully.

Concrete over abstract:
Include the actual pattern, command, file structure, or failure mode.
When an unsafe and safe version both clarify the point, show both.

Context-frugal writing:
Every vault note should earn the context it consumes. Put the useful
behavior first and move provenance, caveats, and maintenance mechanics
after the workflow. Do not paste generic Cortex process text into domain
skills. If the knowledge only matters during contribution, deployment,
or validation, put it in the relevant meta skill instead of every skill.

Human-facing command surfaces:
When Cortex exposes both a guided command and explicit flags, put the
guided command first in human-facing docs. The CLI should carry the
complexity: ask questions, preview risky writes, show understandable
status, and prompt before mutating local agent homes. Keep flags
documented and first-class for scripts, agents, debugging, and
standard-library parity, but do not make ordinary readers start by
assembling long flag strings. Use Markdown `<details>` blocks or a
separate reference document for fallback and non-interactive forms.

Human expertise capture:
Humans should not need to edit skill markdown directly to improve the
vault. When a user contributes domain knowledge in conversation, the
agent should extract the durable claim, ask only for missing essentials,
and capture it through the expertise workflow. Distinguish:

- `preference`: a user wants Cortex or an agent to behave a certain way.
- `operational-experience`: the user has seen a pattern work or fail in
  a real environment.
- `domain-expertise`: the user is contributing field knowledge that
  should change how future agents reason or act.

Only operational experience and domain expertise should raise confidence
in a skill. Preference may shape workflow or wording, but it should not
be treated as evidence that a technical claim is true.

Skills may include optional review frontmatter:

```yaml
review_status: human-noted
reviewed_by:
  - "name, handle, role, or team"
expertise_domain:
  - "packet forensics"
confidence: medium
reviewed_at: 2026-06-03
```

Allowed `review_status` values are `unreviewed`, `human-noted`,
`reviewed`, `disputed`, and `needs-refresh`. Allowed `confidence` values
are `low`, `medium`, and `high`.

Use `human-noted` when a human has contributed useful review context but
the skill has not been fully certified. Use `reviewed` only when the
human is explicitly comfortable marking the skill as reviewed for the
named domain. Use `disputed` when human input contradicts current skill
guidance. Use `needs-refresh` when human input says the skill is likely
stale.

Capture the nuance in the body under `## Human Review Notes`, not only
in frontmatter. Frontmatter is for index visibility; the body note is
where future agents learn what the human actually said.

Timestamped provenance:
Every appended section gets a comment block:

```markdown
<!-- learned: 2026-05 | project: network-forensics-lab | model: thinking-model -->
```

No opinions without basis:
If a section says to prefer one approach over another, give the reason
in the same paragraph. Unsupported preferences rot the vault.

Worker prompts are source too:
A deep skill's worker definitions in its `agents/` folder are vault source,
not generated output. Improve a worker prompt through this same loop: it
qualifies, triages, and commits like a skill, carries timestamped
provenance, and may carry the optional review metadata
(`review_status`, `reviewed_by`, `confidence`) once a human has validated
it. `lint_agent` enforces the worker contract. Edit the source worker, then
re-sync native packages; never edit a generated subagent file in an agent
home.

## 4. Roles

The thinking model and execution model have strictly separate jobs.
Neither does the other's work.

Thinking model responsibilities:

- Decide whether knowledge qualifies.
- Resolve triage against the index.
- Draft the full insight in plain language.
- Resolve conflicts when they exist.
- Avoid touching the file system.
- Avoid formatting or committing.

Execution model responsibilities:

- Take the thinking model's structured output.
- Format it to the vault standard.
- Run `skills/meta/scripts/lint_skill.py` and fix violations.
- Run `skills/meta/scripts/index_builder.py` when the graph may change.
- Commit with a structured message such as
  `skill(sql/injection): add parameterized query pattern`.
- Avoid making judgment calls about content.
- Avoid rewriting the insight.

If the thinking model output is ambiguous, the execution model stops and
asks. It does not interpret.

## 5. Conflict Resolution

If new learning contradicts something already in the vault, do not
overwrite silently. Insert a conflict block in the existing file:

```markdown
> WARNING: CONFLICT - 2026-05
> Session `network-forensics-lab` found behavior contradicting the
> pattern below. Specifically: [one sentence description].
> Unresolved. Requires thinking model review before next use.
> See: `skills/meta/conflicts/SKILL.md` for full context.
```

Log the full conflict detail in `skills/meta/conflicts/SKILL.md`.

The vault is not resolved until a thinking model session explicitly
closes the conflict and removes the block. Speed is not worth
incoherence.

## 6. Deprecation

Do not delete outdated content. Mark it:

```markdown
> WARNING: DEPRECATED - 2026-05
> This pattern applied to [tool] before version X. It may be incorrect
> for current versions. Retained for historical context.
```

The history of why something was believed, and why it stopped being
trusted, is itself knowledge.

## 7. Python Enforcement

Run scripts from the repository root:

```bash
python skills/meta/scripts/lint_skill.py skills/sql/injection/SKILL.md
python skills/meta/scripts/lint_skill.py --all
python skills/meta/scripts/validate.py
python skills/meta/scripts/validate.py --fix-generated
python skills/meta/scripts/manifest_builder.py
python skills/meta/scripts/manifest_builder.py --check
python skills/meta/scripts/index_builder.py
python skills/meta/scripts/index_builder.py --check
python skills/meta/scripts/doctor.py
python skills/meta/scripts/doctor.py --report
python skills/meta/scripts/commit_skill.py skills/sql/injection/SKILL.md "skill(sql/injection): add parameterized query pattern"
python skills/meta/scripts/capture_expertise.py skills/forensics/pcap/SKILL.md --claim "Encrypted traffic workflows should prioritize metadata before payload assumptions." --reviewer "packet analyst" --domain "packet forensics" --confidence high
```

`lint_skill.py` checks frontmatter, provenance, vendor-neutral language,
cross-references, and index coverage. `--all` is the minimum check before
any vault commit because a single broken skill weakens the whole vault.

`validate.py` is the portable validation contract. By default it runs
vault-wide lint, manifest check, index check, and `doctor.py --report`
without mutating repository files. Use `validate.py --fix-generated` to
rebuild the generated manifest and index before running the same checks.
This command is the local contract that optional hooks or hosted
automation should wrap.

`index_builder.py` rebuilds `skills/meta/index/SKILL.md` from skill
frontmatter. `--check` must pass before committing; a stale graph is a
broken graph even when every individual skill lints cleanly.

`manifest_builder.py` rebuilds `skills/meta/source-manifest/SKILL.md`, the
generated catalog of vault notes, scripts, root files, logs, and basic
counts. `--check` must pass before committing.

`doctor.py` is the minimum vault health check. It verifies required
folders and files, Python version, current source manifest, current
index, vault-wide lint, unique skill identifiers, and `git diff --check`
when the vault is inside a git repository. Use `doctor.py --report` for
non-mutating counts. Use `doctor.py --fix-manifest --fix-index` when
generated files are stale.

`commit_skill.py` rebuilds the index, refuses to commit without a clean
vault-wide lint pass, requires the commit message scope to match the
target `skill_id`, stages the target skill plus the index, and commits
with a structured message. Use `--include <path>` for companion script or
documentation changes that belong in the same skill commit.

`capture_expertise.py` records a human claim against a skill without
requiring the human to edit markdown. It updates optional review
frontmatter, appends a `Human Review Notes` entry, and leaves normal
validation and commit steps to the agent.

## 8. Portability First

<!-- learned: 2026-06 | project: cortex-roadmap | model: thinking-model -->

Cortex must not depend on hosted runners, vendor services, editor
integrations, local hooks, or native agent skill folders for its core
correctness. The portable repository scripts are the validation contract.

Automation may wrap the local contract, but it must not replace it. A
hosted continuous integration job is useful when available because it
catches stale indexes, broken lint, or whitespace failures before changes
spread. It is not required infrastructure. Any hosted job should run the
same commands a user can run locally from a fresh clone.

If an environment has no network access and no hosted runner, the vault
should still be operable with:

- The markdown files in the repository.
- Python for deterministic scripts.
- Git for source control.
- Optional native skill deployment adapters.

Core validation scripts must avoid third-party Python dependencies. A
fresh clone with a reasonably modern Python interpreter should be able to
run `validate.py`, inspect the vault, and commit skill changes without
installing packages.

Third-party libraries are acceptable for optional ergonomics when they
materially improve the experience, such as a richer terminal installer.
If Cortex adds libraries such as Typer, Rich, or prompt-tooling, declare
them in a project dependency file, document an install command, and keep
a clear boundary between optional user-interface features and the
stdlib-only validation contract. Prefer a modern, reproducible installer
such as `uv` when dependency installation becomes necessary.

Minimum update lifecycle:

```text
draft/update skill -> validate --fix-generated -> commit_skill -> status deployed wrappers -> sync stale managed wrappers -> status current
```

Deployment impact is part of the lifecycle when native packages exist.
Changing a source skill changes its source hash. Changing the native
package generator, package shape, or deployment metadata may make many
installed packages stale at once. After committing either kind of change,
inspect deployed state with `uv run cortex status ...` or
`python scripts/install-skills.py --action status ...`, sync managed
stale packages, and verify status again. Do not silently leave generated
Codex or Claude packages stale when the session has access to those
targets.

This lifecycle is an agent instruction first. Do not rely on git hooks
as the only enforcement layer, because many agents, web editors, or
repository APIs may bypass local hooks. A compliant agent runs the
pipeline explicitly and stops when checks fail.

Failure handling:

- If `validate.py --fix-generated` changes only generated catalogs, rerun
  validation and include the generated files with the source change.
- If lint fails, fix the source skill or metadata. Do not weaken the
  linter to make the current draft pass unless the rule itself is wrong.
- If manifest or index checks fail after a non-mutating validation run,
  run `validate.py --fix-generated`, inspect the generated diff, and
  rerun validation.
- If `doctor.py` reports missing folders, duplicate skill IDs,
  unresolved references, or whitespace errors, fix the reported cause
  before committing.
- If native package status fails, reports unmanaged targets, or cannot
  write to an agent home, do not force overwrite. Record the exact status
  and sync command in the handoff or log so a user with access can finish
  deployment.
- If validation still fails after one direct fix attempt, stop and report
  the failing command, the error summary, and the files touched. Do not
  commit a red validation state.

Optional helpers:

- `log_entry.py --title "..." --details "..."` appends a short entry to
  `logs/YYYY-MM.md`. Logs explain change context; they do not replace
  skill updates.
- `install_hooks.py` configures git to use `.githooks/pre-commit`. Use
  it as optional local enforcement for normal `git commit` workflows. The
  hook runs `validate.py --fix-generated`, stages generated manifest and
  index updates, and blocks the commit if health checks fail.

## 9. Self-Improvement

This document is a skill. It follows the same protocol it defines.

If a session reveals a better triage rule, writing rule, role boundary,
or enforcement check, propose an update to this file through the same
process. The vault improves itself through the mechanism it teaches.

## Human Review Notes

<!-- learned: 2026-06 | project: human-expertise-capture | model: human-mediated -->

- 2026-06-02 | status: human-noted | confidence: high | kind: domain-expertise | reviewer: project owner | domain: cortex, human-in-the-loop
  Domain experts should be able to contribute durable expertise through normal prompting
  and discussion; the agent should capture the durable claim, update review metadata,
  append a human review note, validate, and leave the skill source as the editable
  artifact.
  Details: This lowers friction because the human already prompts and discusses work while using
  skills, and it preserves Cortex as the persistence layer rather than making experts
  learn the markdown schema.
