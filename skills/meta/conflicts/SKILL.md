---
schema_version: 1
tags:
  - "meta"
  - "conflicts"
topics:
  - "conflict log"
status: seed
created: 2026-05-31
updated: 2026-05-31
sources: []
source_count: 0
aliases:
  - "conflict register"
skill_id: meta/conflicts
summary: "Append-only log for unresolved contradictions found while updating vault skills."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - meta/index
  - meta/roles
---

# Conflict Log

<!-- learned: 2026-05 | project: cortex-bootstrap | model: seed -->

Use this file for conflicts that cannot be resolved during an execution
pass. Do not delete resolved conflicts; mark them closed with date,
reviewing model role, and the skill section that was updated.

## Entry Template

```markdown
## 2026-05 - short conflict title

Status: unresolved
Skills:
- `skills/<domain>/<name>.md`

Observed contradiction:
[Concrete description of what contradicted the existing skill.]

Resolution notes:
[Leave blank until a thinking model resolves it.]
```
