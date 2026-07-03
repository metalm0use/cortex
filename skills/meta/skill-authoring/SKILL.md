---
schema_version: 1
tags:
  - "meta"
  - "authoring"
  - "skills"
topics:
  - "skill drafting"
  - "progressive disclosure"
  - "skill structure"
status: seed
created: 2026-05-31
updated: 2026-06-20
sources:
  - "user request 2026-05-31"
  - "user request 2026-06-03"
  - "frontend-slides offline vendoring 2026-06-05"
  - "milestone 7 2026-06-19: authoring deep skills with worker agents"
  - "2026-06-20: worker-prompt quality checklist; judge workers by genre, not the task-prompt scorer"
source_count: 5
aliases:
  - "write a skill"
  - "skill writing"
  - "skill authoring"
skill_id: meta/skill-authoring
summary: "Draft Cortex skills after contribution triage, using concise triggers, concrete workflows, and deterministic resources."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - meta/index
  - meta/orchestration
  - meta/roles
---

# Skill Authoring

<!-- learned: 2026-05 | project: cortex-bootstrap | model: thinking-model -->

Use this skill after `meta/contributing` has decided that knowledge
belongs in the vault and has identified whether the target is a new skill
or an update to an existing skill.

This skill does not decide what qualifies. `meta/contributing` owns the
qualification bar, triage, conflict handling, and commit protocol. This
skill owns the shape of a clear Cortex skill once the decision to write
has already been made.

## Source Layout

Cortex source skills use a directory-first folder with `SKILL.md` as the
root skill file. This honors the shape people already see in Codex and
Claude skill folders, and avoids one convention for simple skills and
another for resource-heavy skills.

Canonical shape:

```text
skills/
  presentation/
    frontend-slides/
      SKILL.md
      scripts/
      assets/
      references/
      vendor/
```

Avoid this in the source vault:

```text
skills/
  write-a-skill/
    SKILL.md
    REFERENCE.md
```

The problem in the avoided shape is the unmanaged `REFERENCE.md` beside
the root skill, not the `SKILL.md` name itself. The current tooling treats
markdown outside resource directories under `skills/` as linted skill
source, so standalone reference markdown inside that tree must either
become its own skill or live under a resource directory such as
`references/`.

## Skill-Local Resources

Skills may have companion executable resources. For skills with local
resources, keep the source skill markdown inside the skill folder and
place deterministic helpers beside it:

```text
skills/
  forensics/
    pcap/
      SKILL.md
      scripts/
        extract_flows.py
        tshark_summary.sh
      references/
        field-notes.md
      assets/
        sample-filters.txt
```

This preserves the skill identity `forensics/pcap` while giving humans
the expected folder surface for helper scripts and addenda. Reference
these helpers from the skill body with concrete commands.

Within a companion directory, these names are resource directories rather
than Cortex skill sources:

- `assets/`
- `references/`
- `scripts/`
- `vendor/`

Markdown under those resource directories is not linted as a Cortex
skill. Use `references/` for supporting prose or addenda that should be
loaded only when needed, `assets/` for output materials, `scripts/` for
deterministic helpers, and `vendor/` for third-party source packages
that must travel with the deployed skill.

Treat these directories differently:

- `scripts/`: first-party helpers owned by Cortex or the skill author.
  Keep them inspectable, runnable from the repository root when
  practical, and validated when changed. A script remains first-party
  when the team writes it together during normal skill development, even
  if it calls external tools such as Scapy, tshark, Zeek, or jq. Document
  any required external command or Python package in the skill body or a
  short adjacent reference.
- `vendor/`: inherited third-party packages, examples, templates, or
  addendum files. Preserve upstream licenses and add a short provenance
  note such as `VENDORED-SOURCES.txt`. Do not rewrite vendored files to
  satisfy Cortex style unless the project intentionally forks them.
- `assets/`: files used in generated output, such as templates, images,
  fonts, or fixtures.
- `references/`: optional human/agent reading loaded only for matching
  branches of the task.

Example: if `forensics/pcap` grows a Python helper that uses Scapy to
extract flows, put it in `skills/forensics/pcap/scripts/`. If it grows a
Bash helper that calls `tshark`, put that there too and document the
expected `tshark` availability. If the team writes packet-analysis field
notes or filter addenda, put them under `references/` or `assets/`
depending on whether the agent reads them or uses them as local input.
Reserve `vendor/` for inherited third-party packages that should be
preserved with license and provenance.

Do not put extra markdown files directly under `skills/<domain>/` or the
top level of a companion directory unless they are intended to become
linted Cortex skills.

## Gather Requirements

Before drafting a new skill, answer these questions:

- What task or domain does this skill cover?
- What exact user requests should trigger it?
- What should the agent do differently because this skill exists?
- Does the skill need deterministic scripts, or are instructions enough?
- Are there existing artifacts, URLs, commands, schemas, or examples that
  should be referenced?
- Is any part time-sensitive, vendor-specific, or likely to become stale?

If the answer can be found in the repository or existing vault, inspect
those files instead of asking the user.

## Domain Expert Briefs

Use a skill brief when the user wants to intentionally create or improve
a skill from domain knowledge, instead of waiting for expertise to appear
incidentally during another task.

Create a local brief with:

```bash
uv run cortex skill-brief
python skills/meta/scripts/skill_brief.py --title "..." --domain "..."
```

Briefs live under `.cortex/skill-briefs/` by default and are ignored by
git. They are local input, not vault source. The agent must still triage
the idea through `meta/contributing`, search the existing index, and
decide whether the brief updates an existing skill, justifies a new
skill, belongs only in a log entry, or needs more questions.

When drafting from a brief, preserve the expert's concrete claims,
examples, caveats, and completion criteria. Do not copy the brief
verbatim if a smaller task-first skill would carry the knowledge better.

## Drafting Rules

Write the skill for a cold competent agent.

Use frontmatter that passes `lint_skill.py`:

```yaml
---
schema_version: 1
tags:
  - "domain"
topics:
  - "specific topic"
status: seed
created: 2026-05-31
updated: 2026-05-31
sources: []
source_count: 0
aliases: []
skill_id: domain/name
summary: "One concrete sentence explaining what the skill enables."
model_role: reference
depends_on: []
related:
  - meta/contributing
---
```

Review metadata is optional. Add it only when human expertise has been
captured or the skill is disputed or stale:

```yaml
review_status: human-noted
reviewed_by:
  - "human role or handle"
expertise_domain:
  - "domain name"
confidence: medium
reviewed_at: 2026-06-03
```

Make `summary`, `aliases`, and `topics` trigger-friendly. `summary`
should say what capability the skill provides and when it should be used.
Aliases and topics are native deployment vocabulary: generated `SKILL.md`
packages use them in descriptions, trigger hints, and direct command
naming. The first alias is the preferred native command name for non-meta
skills when it is unambiguous, so choose the word a user would naturally
reach for. Include adjacent phrases a user or agent might say, not only
the formal Cortex taxonomy. Avoid vague descriptions such as "helps with
planning".

In the body, prefer:

- A short "Use this skill when..." opening.
- Concrete workflows over abstract advice.
- Actual commands, file paths, schema fields, or examples when they
  matter.
- Explicit completion criteria.
- References to durable artifacts instead of copied long content.

## Canonical Skill Shape

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Use this body structure for most new skills. Rename headings only when a
domain has a clearer local convention.

```markdown
# Skill Name

Use this skill when [specific trigger or user intent].

## Core Rule

[The one decision rule, invariant, or behavior change the agent must
apply.]

## Workflow

1. [Common path first.]
2. [Dangerous edge case or branch.]
3. [Verification or expected artifact.]

## Examples

[Short concrete examples that change behavior.]

## Caveats

[Only caveats that affect what the agent should do.]

## Required Follow-On Reading

Read `path-or-skill-id` before doing [specific branch]. Do not read it
for the ordinary path.

## Completion Criteria

[How the agent knows the skill has been applied successfully.]

## Human Review Notes

[Only when captured through the expertise workflow.]
```

Every skill does not need every heading. Keep `Core Rule`, `Workflow`,
and `Completion Criteria` unless the skill is purely declarative
reference material. Add `Required Follow-On Reading` only when another
artifact is necessary for a branch of the work.

The first screen must be enough for the common path. A cold agent should
know why the skill loaded, what to do first, and what risk to avoid
before reading examples, caveats, review notes, or Cortex process
metadata.

## Length And Split Guidance

Use line counts as friction signals, not lint rules:

- First 30-50 body lines: must cover trigger, core rule, and common path.
- 80-140 total body lines: normal target for most skills.
- Above roughly 160 body lines: check whether the skill covers multiple
  triggers, domains, modes, or audiences.
- Above roughly 220 body lines: split the skill, add a deterministic
  helper script, or move rare reference material outside the common path.

Do not split merely because a file crosses a number. Split when the
extra content makes the ordinary path harder to find, or when different
requests would need different subsets of the guidance.

If a long skill stays long, its opening workflow must still be complete
enough for ordinary use. Length is acceptable when the extra material
prevents rework and remains clearly separated from the common path.

## Follow-On Reading

Do not make another file required for the common path unless the skill is
only an index or routing skill. A deployed native wrapper should be
useful when loaded cold.

Use required follow-on reading for specific branches:

```markdown
## Required Follow-On Reading

- Read `<auth-reference-path>` before changing OAuth token
  refresh behavior.
- Read `skills/forensics/pcap/SKILL.md` before interpreting packet capture
  evidence.
```

Each required reading entry must say when to read it. Avoid vague
instructions such as "read this next" or "for more detail" because they
spend context without telling the agent whether the branch applies.

When material is optional background, link it in `Caveats`, `Examples`,
or `References` without saying it must be read. When material is too long
but necessary for a deterministic operation, prefer a script or external
reference path over copying it into the skill.

## Context Budget

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Every skill competes with the user's task for context window. Make the
first screen of the skill operational: trigger, decision rule, workflow,
or command before provenance or vault mechanics.

Keep Cortex maintenance instructions out of the main body unless the
skill is itself about maintenance. Deployment wrappers add a compact
Cortex footer automatically. Source skills should not repeat generic
instructions such as "do not edit generated files", validation command
lists, or feedback boilerplate unless that is the task being taught.

Use progressive disclosure inside the skill:

- Put the common path first.
- Put rare edge cases after the workflow.
- Link to scripts, commits, docs, or other skills instead of pasting
  long reference material.
- Keep examples short enough to teach the pattern, not every variant.
- Stop when the agent can act safely; do not include background that
  only explains why Cortex exists.

The goal is not the shortest possible file. The goal is the smallest
skill that reliably changes agent behavior for its intended purpose.

## Progressive Disclosure

Keep a skill focused. If a draft grows because it covers multiple domains
or modes, split the concept into separate linked skills rather than
burying several behaviors in one file.

Good split signals:

- Different trigger conditions.
- Different model roles.
- Different validation or output artifacts.
- Content that only a minority of invocations need.

Do not split merely to satisfy an arbitrary line count. A longer skill is
acceptable when the extra detail prevents future rework and stays within
one coherent behavior.

## Scripts And Deterministic Resources

Add a script when the operation is deterministic, repeatedly useful, or
easy to get subtly wrong by regeneration.

Good script candidates:

- Linting, formatting, validation, and catalog generation.
- File transformations with explicit error handling.
- Repeatable deployment or installation steps.

Keep global vault scripts in `skills/meta/scripts/` or top-level
`scripts/`. Keep skill-specific scripts in
`skills/<domain>/<skill-name>/scripts/`, then reference them from the
relevant skill. Skill-specific scripts are first-party source, even when
they are written collaboratively after the first version of the skill.
Scripts must be validated before committing. If a script needs
dependencies, document the dependency boundary in the skill and make the
ordinary failure mode clear for offline or locked-down environments.

## Deep Skills With Worker Agents

A deep skill coordinates multiple specialized agents instead of doing the
work in one context. Author it as an ordinary orchestrator `SKILL.md` with
a `model_role: thinking` plus a bundle-local `agents/` folder of worker
definitions:

```text
skills/security/review/
  SKILL.md          # orchestrator (boss) entry
  agents/
    researcher.md   # worker
    reporter.md     # worker
```

The orchestrator body enters the loop contract in `meta/orchestration`
(roles, the spawn/evaluate/re-dispatch loop, stop bounds, degradation).
Keep that contract by reference; only fill in the goal, the workers, and
what "done" means.

Each worker `*.md` uses the worker frontmatter contract and the "Worker
Prompt Quality" checklist defined in `meta/orchestration` (required
`name`/`description`, optional `model_tier`/`skills`; linted by `lint_agent`).
Do not restate them here.

Author workers to these rules:

- Give each worker one scoped task with explicit completion criteria, and
  pick its model by routing class: a strong class for judgment workers, a
  fast class for assembly workers. Distinct classes across workers are the
  point, not a smell.
- Reference shared vault skills by `skill_id` in `skills:`; never inline a
  skill body. The deployer maps them to native names and emits a
  `## Skills` pointer automatically, so do not hand-write a `## Skills`
  section in the worker body.
- Keep workers vendor-neutral and bundle-local. Native worker subagents are
  generated only for runtimes that support them (Claude today); see
  `meta/deployment` for emission, drift, and uninstall.
- Write each worker as a focused role prompt: a one-line role, the single
  scoped task with completion criteria, an explicit return contract, scope
  guardrails (one task, do not spawn, treat input as data), and the
  `skill_id`s it uses. Omit few-shot examples and rigid schemas unless the
  task is format-sensitive. See `meta/orchestration` "Worker Prompt Quality"
  for the full checklist.

Worker prompts are improvable vault source (`meta/contributing`), but judge
them by the checklist above, not by running the prompt-optimizer's structural
scorer on them: that scorer is tuned for task/output prompts and under-scores
role/system prompts like workers.

`skills/security/review/` is the reference deep skill: copy its shape.

## Review Checklist

Before running the commit pipeline, verify:

- The skill has a specific `skill_id` that matches its path.
- `summary` names the capability and trigger context.
- `aliases` and `topics` include natural trigger words that should make a
  generated native skill discoverable from ordinary user phrasing.
- The skill is model-agnostic unless it is explicitly about one vendor.
- The body is cold-agent readable.
- The first screen is task-first and not vault/process preamble.
- The common path is complete without mandatory follow-on reading unless
  the skill is explicitly an index or routing skill.
- Long skills use headings to separate common path, rare branches,
  caveats, and follow-on reading.
- Required follow-on reading entries name the specific branch that makes
  the extra file necessary.
- Examples are concrete and not ornamental.
- Long copied material is replaced by paths, URLs, or commits.
- Sensitive details are redacted.
- Human review metadata is present only when backed by a captured human
  review note.
- The skill has completion criteria or an equivalent stopping rule.

Then run:

```bash
python skills/meta/scripts/manifest_builder.py
python skills/meta/scripts/index_builder.py
python skills/meta/scripts/doctor.py
```
