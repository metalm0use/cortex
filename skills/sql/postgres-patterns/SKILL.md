---
schema_version: 1
tags:
  - "sql"
  - "postgres"
  - "database"
  - "performance"
  - "security"
topics:
  - "postgresql schema design"
  - "query optimization"
  - "postgres indexes"
  - "row level security"
status: seed
created: 2026-06-07
updated: 2026-06-07
sources:
  - "https://github.com/affaan-m/ECC/blob/main/skills/postgres-patterns/SKILL.md"
source_count: 1
aliases:
  - "postgres"
  - "postgresql"
  - "postgres indexes"
  - "row level security"
  - "database schema"
skill_id: sql/postgres-patterns
summary: "Apply PostgreSQL patterns for schema design, indexes, query optimization, RLS, connection safety, and operational diagnostics."
model_role: reference
depends_on:
  - sql/injection
related:
  - devops/docker-patterns
  - devops/redis-patterns
  - programming/python-patterns
  - meta/contributing
---

# PostgreSQL Patterns

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when designing PostgreSQL schemas, writing migrations,
reviewing SQL queries, troubleshooting slow queries, choosing indexes,
implementing Row Level Security (RLS), using PostgreSQL as a queue, or
setting safe database defaults.

## Core Rule

Start from the query shape and data lifecycle. Choose types, constraints,
indexes, policies, and timeouts that make the intended access path clear,
then verify with `EXPLAIN` and production-like row counts instead of
assuming the planner will rescue vague schema design.

## Workflow

1. Identify the workload: OLTP CRUD, reporting, queue processing,
   time-series lookup, full-text search, JSONB search, multi-tenant
   access, or administrative maintenance.
2. Design tables with durable types and constraints before adding
   indexes. Prefer database-enforced correctness for IDs, foreign keys,
   uniqueness, nullability, and timestamps.
3. Choose indexes from the exact `WHERE`, `JOIN`, `ORDER BY`, and
   uniqueness requirements. Avoid adding indexes that no query uses.
4. For untrusted inputs, follow `sql/injection`: use parameterized
   queries and never string-build SQL values.
5. For multi-tenant tables, design RLS policies and test both allowed
   and denied access paths.
6. Check query plans with `EXPLAIN (ANALYZE, BUFFERS)` on representative
   data before declaring a query or index good.
7. Add operational guardrails: statement timeouts, idle transaction
   timeouts, monitoring, migration rollback strategy, and connection
   pool sizing.

## Types And Constraints

Prefer types that encode intent:

| Use Case | Prefer | Avoid |
| --- | --- | --- |
| Internal numeric IDs | `bigint generated ... as identity` | Small `int` counters |
| External stable IDs | UUID or text by product need | Random type drift |
| Free-form strings | `text` | Arbitrary `varchar(255)` |
| Timestamps | `timestamptz` | `timestamp` without time zone |
| Money | `numeric(precision, scale)` | Floating-point types |
| Flags | `boolean` | String or integer flags |
| Structured flexible data | `jsonb` with clear access paths | Untyped JSON dumping |

Use constraints before application-only checks when the rule must always
hold:

```sql
alter table orders
  add constraint orders_total_nonnegative check (total_cents >= 0),
  add constraint orders_user_fk foreign key (user_id) references users (id);
```

## Index Selection

Choose the index type from the access pattern:

| Query Pattern | Index Type | Example |
| --- | --- | --- |
| `where col = value` | B-tree | `create index on users (email);` |
| `where col > value` | B-tree | `create index on orders (created_at);` |
| `where a = x and b > y` | Composite B-tree | `create index on orders (status, created_at);` |
| `where jsonb_col @> ...` | GIN | `create index on events using gin (payload);` |
| Full-text search | GIN | `create index on docs using gin (search_vector);` |
| Large append-only time ranges | BRIN | `create index on readings using brin (created_at);` |

For composite indexes, put equality columns before range columns:

```sql
create index orders_status_created_at_idx
  on orders (status, created_at);
```

Use partial indexes when most queries target a subset:

```sql
create index users_active_email_idx
  on users (email)
  where deleted_at is null;
```

Use covering indexes when a hot query can avoid table lookups:

```sql
create index users_email_cover_idx
  on users (email)
  include (name, created_at);
```

Every index has write and maintenance cost. Remove or avoid indexes that
do not serve reads, constraints, ordering, or uniqueness.

## Query Patterns

Prefer cursor pagination over large offsets on growing tables:

```sql
select *
from products
where id > $1
order by id
limit 20;
```

Use `ON CONFLICT` for atomic upserts:

```sql
insert into settings (user_id, key, value)
values ($1, $2, $3)
on conflict (user_id, key)
do update set value = excluded.value;
```

Use `FOR UPDATE SKIP LOCKED` for simple queue workers that can tolerate
database-backed queue tradeoffs:

```sql
update jobs
set status = 'processing', started_at = now()
where id = (
  select id
  from jobs
  where status = 'pending'
  order by created_at
  limit 1
  for update skip locked
)
returning *;
```

Keep transactions short. Never leave a request or worker idle inside a
transaction while waiting on network calls, user input, or long external
work.

## Row Level Security

For multi-tenant or user-scoped data, enable RLS and test policies from
the application's database role, not only as an owner or admin:

```sql
alter table orders enable row level security;

create policy orders_user_select
  on orders
  for select
  using ((select auth.uid()) = user_id);
```

When using Supabase-style helper functions such as `auth.uid()`, wrapping
the call in a scalar `select` can avoid repeated per-row function
evaluation in policy checks. Confirm the plan in the target environment
because policy behavior depends on the helper, role, and query shape.

## Diagnostics

Use `pg_stat_statements` for workload-level query visibility:

```sql
create extension if not exists pg_stat_statements;

select query, mean_exec_time, calls
from pg_stat_statements
where mean_exec_time > 100
order by mean_exec_time desc;
```

Find foreign keys that may need supporting indexes:

```sql
select conrelid::regclass as table_name, a.attname as column_name
from pg_constraint c
join pg_attribute a
  on a.attrelid = c.conrelid
 and a.attnum = any(c.conkey)
where c.contype = 'f'
  and not exists (
    select 1
    from pg_index i
    where i.indrelid = c.conrelid
      and a.attnum = any(i.indkey)
  );
```

Watch table churn and vacuum health:

```sql
select relname, n_dead_tup, last_vacuum, last_autovacuum
from pg_stat_user_tables
where n_dead_tup > 1000
order by n_dead_tup desc;
```

## Operational Defaults

Set guardrails deliberately, then tune for the actual environment:

```sql
alter system set idle_in_transaction_session_timeout = '30s';
alter system set statement_timeout = '30s';
select pg_reload_conf();
```

Use connection pooling instead of letting application replicas multiply
direct database connections until `max_connections` becomes the bottleneck.
Size pools from database capacity and workload behavior, not from a
default copied from another project.

When PostgreSQL runs through Compose, follow `devops/docker-patterns`:
use `compose.yaml`, `env_file`, explicit `${VAR}` wiring, and a
first-party named volume for database data.

## Anti-Patterns

- Using `varchar(255)` by habit instead of `text` or a meaningful
  constrained type.
- Storing money in floating-point columns.
- Large `OFFSET` pagination on tables that keep growing.
- String-built SQL with untrusted values.
- RLS policies that were only tested as an owner or admin role.
- Long idle transactions that hold locks and block vacuum.
- Indexes added without checking the query shape or write cost.
- JSONB dumping that becomes a hidden schema with no constraints or
  planned indexes.
- Raising `max_connections` instead of fixing pooling and connection
  lifecycle.

## Completion Criteria

The PostgreSQL change is ready when schema rules are enforced by types
and constraints, SQL values are parameterized, indexes match real query
shapes, important queries have representative `EXPLAIN` evidence,
multi-tenant access is protected and tested through RLS where applicable,
transactions are short, and operational guardrails exist for timeouts,
monitoring, pooling, and maintenance.
