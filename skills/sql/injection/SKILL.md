---
schema_version: 1
tags:
  - "sql"
  - "security"
topics:
  - "injection prevention"
status: seed
created: 2026-05-31
updated: 2026-05-31
sources: []
source_count: 0
aliases:
  - "sql"
  - "sql injection"
  - "parameterized queries"
skill_id: sql/injection
summary: "Use parameterized SQL query patterns and avoid string-built query text for untrusted values."
model_role: reference
depends_on: []
related:
  - meta/contributing
---

# SQL Injection Patterns

<!-- learned: 2026-05 | project: cortex-bootstrap | model: seed -->

Never build SQL text by concatenating or interpolating untrusted values.
Use driver-supported parameters so the database receives query structure
and values separately.

Unsafe pattern:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)
```

Safer pattern:

```python
cursor.execute(
    "SELECT * FROM users WHERE email = ?",
    (email,),
)
```

Placeholder syntax differs by driver. Confirm whether the driver expects
`?`, `%s`, `$1`, or named placeholders such as `:email`; do not translate
placeholder style by guesswork.
