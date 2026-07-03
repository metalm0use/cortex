---
schema_version: 1
tags:
  - collaboration
  - planning
  - review
topics:
  - plan interrogation
  - design review
  - question fidelity
status: seed
created: 2026-05-31
updated: 2026-06-02
sources:
  - https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md
source_count: 1
aliases:
  - grill me
  - plan grilling
skill_id: collaboration/grill-me
summary: Interview the user one question at a time, starting low fidelity, to stress-test a plan until the design tree is resolved.
model_role: thinking
depends_on: []
related:
  - meta/contributing
  - meta/roles
---

# Grill Me

<!-- learned: 2026-05 | project: cortex-bootstrap | model: thinking-model -->

Use this skill when the user wants to stress-test a plan, design, or
proposal; asks to be grilled; or needs help reaching shared
understanding before implementation.

The agent interviews the user relentlessly but constructively. Walk down
the decision tree one branch at a time. Resolve dependencies between
decisions before moving to downstream choices.

## Core Rules

Ask exactly one question at a time.

For each question, include the recommended answer before waiting for the
user. The recommendation should be concrete enough that the user can
accept, reject, or modify it.

If a question can be answered by inspecting the codebase, files, logs, or
existing documentation, inspect those sources instead of asking the user.
Report the discovered answer and only ask the next unresolved question.

Do not ask broad bundles such as "What are the requirements, constraints,
timeline, and risks?" Split them into one decision at a time.

Do not move to implementation until the important branches have either
been resolved or explicitly marked as assumptions.

## Question Economy

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Relentless does not mean exhaustive. Ask the next question that most
reduces uncertainty about the plan. Skip questions whose answers are
already implied by repository evidence, prior decisions, or the user's
stated constraints.

Keep each turn small:

- One question.
- One recommended answer.
- One reason the recommendation matters.

Stop when more questioning would mostly add detail without changing the
decision. Summarize the remaining assumptions instead of spending the
user's and agent's context on low-leverage branches.

## Question Shape

Use this format:

```text
Question: [one precise question]

Recommended answer: [the answer the agent would choose, with the reason]
```

After the user answers, briefly confirm the decision and ask the next
highest-leverage question.

## Question Fidelity

<!-- learned: 2026-05 | project: cortex-bootstrap | model: thinking-model -->

Prefer low-fidelity questions early. A low-fidelity question tests the
shape of the plan before details harden. These questions are more
grillable because the answer can redirect the design cheaply.

Examples:

```text
Question: Is this primarily a user-experience problem or a correctness problem?

Recommended answer: Treat it as a correctness problem first, because a
polished workflow still fails if the underlying state can drift.
```

```text
Question: Should this be a reusable protocol or a one-off project note?

Recommended answer: Make it reusable only if a cold agent would apply it
in a future session; otherwise keep it out of the vault.
```

Use high-fidelity questions after the major branch is chosen. A
high-fidelity question tests a concrete implementation detail, exact
wording, threshold, filename, schema field, command, or UI behavior.
These questions are still useful, but they are less grillable early
because they assume upstream decisions are already settled.

Examples:

```text
Question: Should the generated file be named `source-manifest.md` or `catalog.md`?

Recommended answer: Use `source-manifest.md`, because it describes a
generated inventory rather than a manually curated navigation page.
```

```text
Question: Should the linter require `model_role` in frontmatter?

Recommended answer: Yes, because routing hints should be visible and
consistent across every skill instead of being optional folklore.
```

When the user proposes a detailed implementation, step back and ask the
lowest-fidelity unresolved question that could invalidate it. Move back
to high-fidelity questions only after that answer is stable.

## Decision Tree Order

Prefer this order unless the user's plan makes another dependency more
urgent:

1. Goal: what outcome must this plan achieve?
2. Users: who is affected, and who decides success?
3. Constraints: what cannot change?
4. Existing state: what is already true in the repo, system, or process?
5. Interfaces: what inputs, outputs, files, APIs, or people are touched?
6. Failure modes: what would make the plan unsafe, confusing, or wasted?
7. Tradeoffs: what is being optimized, and what is intentionally not?
8. Validation: how will the agent know the plan worked?
9. Rollback: how can the change be undone or contained?

## Codebase Exploration Rule

Before asking about repository facts, search or inspect locally.

Examples:

```bash
rg "feature_flag|migration|TODO"
rg --files
```

Ask the user only for intent, priorities, private context, or decisions
that cannot be inferred from available artifacts.

## Exit Criteria

Stop grilling when the agent and user have a shared understanding of:

- The intended outcome.
- The key constraints and non-goals.
- The chosen path and rejected alternatives.
- The validation plan.
- Any unresolved assumptions.

End with a short decision summary and the next action.
