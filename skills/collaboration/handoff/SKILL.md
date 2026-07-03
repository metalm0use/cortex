---
schema_version: 1
tags:
  - collaboration
  - continuity
  - handoff
topics:
  - project handoff
  - session handoff
  - context compaction
  - agent continuity
status: seed
created: 2026-05-31
updated: 2026-06-02
sources:
  - https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md
source_count: 1
aliases:
  - handoff
  - session handoff
  - handoff document
argument_hint: What will the next session be used for?
skill_id: collaboration/handoff
summary: Write a redacted project handoff so a fresh agent or developer can continue without duplicating existing artifacts.
model_role: thinking
depends_on: []
related:
  - collaboration/grill-me
  - meta/contributing
---

# Handoff

<!-- learned: 2026-05 | project: cortex-bootstrap | model: thinking-model -->

Use this skill when the user asks for a handoff, wants another agent to
continue the work, or needs the current conversation compacted into a
continuation document.

By default, write the handoff into the current project as
`docs/HANDOFF.md` and commit it alongside the project work. A project
handoff is durable working memory for the next person or agent. It should
capture the thinking that is not already obvious from code, commits,
issues, or other durable artifacts.

## Output Location

Default to a durable project handoff:

```text
docs/HANDOFF.md
```

Create `docs/` if it does not exist. Commit the handoff with the project
changes when the user has asked for committed work or when the handoff is
part of the project deliverable.

Use a temporary handoff only when the user explicitly asks for a private
or ephemeral handoff, the content should not enter the repository, or the
handoff contains sensitive operational context that must be redacted so
heavily that a committed file would be misleading.

For temporary handoffs, use the platform's standard temp location:

- POSIX shell: `${TMPDIR:-/tmp}`
- PowerShell: `$env:TEMP`
- Python: `tempfile.gettempdir()`

Name temporary files predictably, for example:

```text
cortex-handoff-YYYYMMDD-HHMMSS.md
```

After writing any handoff, tell the user the path and whether it was
committed, staged, or left untracked.

## Inputs

If the user passes an argument or focus description, treat it as the next
session's intended purpose. Tailor the handoff toward that future work
instead of writing a generic transcript summary.

Examples:

- "next session is for deployment" means emphasize deployment status,
  credentials that are not secret, pending deploy commands, and risks.
- "next session is for review" means emphasize design decisions,
  unresolved questions, validation evidence, and likely review areas.

## Redaction Rules

Redact sensitive information before writing the handoff. Replace secrets
with `[REDACTED]` and explain the type of information removed when useful.

Always redact:

- API keys, access tokens, passwords, private keys, cookies, and session
  identifiers.
- Personal addresses, phone numbers, government identifiers, and private
  account details.
- Private URLs or credentials that grant access unless the user
  explicitly instructs otherwise.

Do not invent missing details. If a future agent needs secret material,
say where the user must provide it again rather than copying it.

## Avoid Duplication

Do not duplicate content already captured in durable artifacts such as
product requirement documents, plans, architecture decision records,
issues, commits, diffs, or generated vault files.

Reference existing artifacts by path, commit, branch, pull request, issue,
or URL.

Prefer:

```text
See `skills/meta/contributing/SKILL.md` for the vault update protocol.
See commit `674923c` for question-fidelity changes.
```

Avoid pasting whole file contents or long diffs into the handoff.

## Context Budget

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

A handoff should save the next agent context, not spend more of it. Lead
with what the next session must know to act. Omit generic Cortex
instructions unless they are unusually relevant to the next task; use
the "Suggested Skills" section for skill pointers instead.

Prefer concise references over copied content:

- Link to commits, files, issues, generated catalogs, or plans.
- Summarize command results in one line unless the exact output matters.
- Include only decisions, risks, and next actions that change what the
  next agent should do.
- Do not preserve chat chronology for its own sake.

## Suggested Structure

Use this structure unless the next-session focus requires a better one:

```markdown
# Handoff

## Next Session Focus

[User-provided focus or inferred purpose.]

## Current State

[Concise status of the project or task.]

## Decisions Made

- [Decision and reason.]

## Open Questions

- [Question, owner if known, and why it matters.]

## Suggested Skills

- `[skill_id]`: [why the next agent should use it.]

## Artifacts To Read

- `[path or URL]`: [why it matters.]

## Commands Already Run

- `[command]`: [result summary.]

## Risks And Watchouts

- [Concrete risk.]

## Next Actions

1. [First action.]
2. [Second action.]
```

## Suggested Skills Section

Always include a "Suggested Skills" section. Suggest skill identifiers
from the vault when possible, not vague capabilities.

Examples:

```markdown
## Suggested Skills

- `meta/contributing`: Use if the next session learns something
  vault-worthy.
- `collaboration/grill-me`: Use if the next session needs to stress-test
  an unresolved plan before implementation.
```

If no current skill applies, write "No specific vault skill applies yet"
and briefly explain why.

## Completion Criteria

The handoff is complete when:

- It is saved to `docs/HANDOFF.md` by default, or to the OS temp
  directory only when the handoff is intentionally private or ephemeral.
- It is concise enough for a fresh agent to read quickly.
- It references existing artifacts instead of duplicating them.
- It redacts sensitive information.
- It names suggested skills for the next agent.
- It ends with clear next actions.
- The user is told whether the handoff was committed, staged, or left
  untracked.
