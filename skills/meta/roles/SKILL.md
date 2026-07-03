---
schema_version: 1
tags:
  - "meta"
  - "roles"
topics:
  - "model responsibilities"
status: seed
created: 2026-05-31
updated: 2026-06-19
sources: []
source_count: 0
aliases:
  - "role split"
skill_id: meta/roles
summary: "Defines the strict split between thinking models that decide and execution models that format, lint, and commit."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - meta/index
  - meta/conflicts
  - meta/deployment
  - meta/source-manifest
---

# Model Role Split

<!-- learned: 2026-05 | project: cortex-bootstrap | model: seed -->

Use two roles when updating the vault.

The thinking model decides whether knowledge belongs in the vault,
chooses the target skill, resolves conflicts, and drafts the insight at
full fidelity. The thinking model does not edit files or commit.

The execution model formats the accepted insight, applies the frontmatter
contract, runs linting, rebuilds the index when needed, and commits. The
execution model does not decide whether the knowledge qualifies or alter
the substance of the drafted insight.

If the drafted insight is ambiguous, the execution model asks for a
clarification before writing. It should not infer missing judgment.

## Frontmatter Routing

Use `model_role` in skill frontmatter as an advisory routing hint:

```yaml
model_role: thinking
```

Valid values:

- `thinking`: use a strong reasoning model for judgment, triage,
  conflict resolution, and drafting.
- `execution`: use a fast execution model for formatting, linting,
  indexing, and committing after a thinking model has decided.
- `reference`: no special model class is required; the skill is ordinary
  domain guidance.

This field must stay model-agnostic. Prefer capability classes such as
`thinking` and `execution` over vendor names. If a runtime supports
automatic model routing, it may map those values to local model choices.
If it does not, the agent reads the hint and proceeds with the available
model.

Codex can read this metadata and follow it as an instruction. It cannot
guarantee an automatic model switch inside a session unless the host
environment exposes a routing tool.

## Runtime Model Routing

<!-- learned: 2026-06 | project: cortex-model-routing | model: thinking-model -->

`model_role` describes a skill's role in vault contribution: who decides,
who formats, who supplies domain knowledge. That is not always the same
as which model tier the skill's task deserves when it is actually
invoked. To separate those two axes, a skill may set an optional
`model_tier`:

```yaml
model_tier: thinking
```

Valid values are `thinking`, `execution`, `reference`, and `inherit`.
`model_tier` is the runtime routing override. When present it wins; when
absent, routing falls back to `model_role`. Use `inherit` to explicitly
opt a skill out of any model change. This lets a hard `reference` skill
bump itself up (`model_tier: thinking`) or a light `thinking` skill stay
cheap (`model_tier: execution`) without lying about its contribution
role.

The mapping from a routing class to a concrete model is vendor-specific,
so it lives in the deployment adapter, not in skill frontmatter. Skill
files stay model-agnostic. The map is a team decision in the committed
`config/model-routing.json` file; the Claude adapter
(`scripts/install-skills.py`) reads it and falls back to a built-in
upgrade-only default when the file is absent:

| Routing class | Claude model | Rationale |
| --- | --- | --- |
| `thinking` | `opus` | Judgment, drafting, and conflict work earn the strongest model. |
| `execution` | `haiku` | Formatting, linting, and committing are mechanical and high volume. |
| `reference` | inherit | Ordinary domain skills keep the session model so they never silently downgrade mid-task. |

The Claude adapter emits the resolved choice as a `model:` line in the
generated `SKILL.md` wrapper. Claude Code honors that as a per-invocation
override: the skill's turn runs on the mapped model and the session
reverts afterward. `inherit` emits no line. Agents without per-skill
model selection ignore the field and read it as advisory, consistent with
the portability contract. Because the wrapper output changes, adjusting
this map or a skill's routing class makes installed native packages stale
until the next sync.

To change the team decision, edit `config/model-routing.json` and
re-sync. Values must be `opus`, `sonnet`, `haiku`, `fable`, `inherit`, or
`null`; partial files keep the default for unspecified agents and
classes. The file is keyed by agent, but only the Claude adapter consumes
it today.
