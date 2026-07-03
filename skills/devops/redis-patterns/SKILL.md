---
schema_version: 1
tags:
  - "devops"
  - "redis"
  - "cache"
  - "queues"
  - "security"
topics:
  - "redis caching"
  - "rate limiting"
  - "distributed locks"
  - "redis streams"
status: seed
created: 2026-06-07
updated: 2026-06-07
sources:
  - "https://github.com/affaan-m/ECC/blob/main/skills/redis-patterns/SKILL.md"
source_count: 1
aliases:
  - "redis"
  - "redis cache"
  - "redis streams"
  - "rate limiting"
  - "distributed locks"
skill_id: devops/redis-patterns
summary: "Apply Redis patterns for caching, rate limiting, locks, sessions, messaging, and production connection management."
model_role: reference
depends_on: []
related:
  - devops/docker-patterns
  - sql/injection
  - meta/contributing
---

# Redis Patterns

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when adding or reviewing Redis for application caching,
session or token storage, rate limiting, distributed coordination,
Pub/Sub, Redis Streams, leaderboards, or production Redis configuration.

## Core Rule

Redis is fast because it is in-memory and single-command operations are
atomic, not because every workflow is automatically safe. Pick the data
structure that matches the access pattern, give ephemeral data a TTL,
and make multi-step workflows atomic with a pipeline, transaction, Lua
script, or explicit lock.

## Workflow

1. Name the use case first: cache, session store, counter, lock,
   leaderboard, queue, broadcast channel, or approximate analytics. Do
   not put unrelated duties in the same Redis instance without an
   isolation reason.
2. Choose the smallest fitting data structure: strings for simple cache
   values and counters, hashes for session-like records, sets for
   membership, sorted sets for ranked data, lists for simple feeds,
   streams for durable event processing, and HyperLogLog for approximate
   unique counts.
3. Design keys as `namespace:resource:id[:field]`, with enough prefix
   structure to scan, observe, and delete narrowly.
4. Set TTLs for cache entries, sessions, tokens, rate-limit windows, and
   temporary coordination keys. Intentionally persistent keys should be
   documented as persistent.
5. Protect multi-command logic. Use `pipeline(transaction=True)` for
   grouped operations, Lua scripts for check-and-update logic, and token
   based locks for coordination.
6. Configure clients with connection pools, connect timeouts, operation
   timeouts, and bounded retry behavior. Avoid opening a new TCP
   connection per request.
7. Verify behavior under the failure mode: cache miss, Redis unavailable,
   lock timeout, rate-limit boundary, consumer restart, or eviction.

## Data Structures

| Use Case | Structure | Key Example |
| --- | --- | --- |
| Simple cache | String | `cache:product:123` |
| Session | Hash | `session:abc123` |
| Counter or fixed window limit | String with `INCR` | `ratelimit:user:123:29230000` |
| Membership or uniqueness | Set | `visitors:2026-06-07` |
| Leaderboard | Sorted set | `scores:weekly` |
| Activity feed | List | `feed:user:456` |
| Durable event queue | Stream | `stream:orders` |
| Approximate unique count | HyperLogLog | `hll:pageviews` |

## Caching

Use cache-aside when the database remains the source of truth and slight
staleness is acceptable:

```python
def get_product(product_id: int):
    key = f"cache:product:{product_id}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    product = load_product_from_db(product_id)
    redis_client.setex(key, 300, json.dumps(product))
    return product
```

Use write-through when the application must update the cache as part of
the write path:

```python
def update_product(product_id: int, data: dict):
    save_product_to_db(product_id, data)
    redis_client.setex(f"cache:product:{product_id}", 300, json.dumps(data))
```

For invalidation groups, record cached keys in a tag set and expire the
tag alongside its members:

```python
pipe = redis_client.pipeline(transaction=True)
pipe.setex(product_key, 300, json.dumps(product))
pipe.sadd(category_tag_key, product_key)
pipe.expire(category_tag_key, 300)
pipe.execute()
```

Prevent cache stampedes on expensive misses by using request coalescing,
short distributed locks, stale-while-revalidate, or probabilistic early
refresh. Do not let every worker rebuild the same cold key at once.

## Rate Limiting

Fixed-window limits are simple and good enough for many low-risk paths:

```python
def allow_fixed_window(user_id: str, limit: int, window_seconds: int) -> bool:
    bucket = int(time.time()) // window_seconds
    key = f"ratelimit:user:{user_id}:{bucket}"
    pipe = redis_client.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    count, _ = pipe.execute()
    return count <= limit
```

Use a Lua script with a sorted set for accurate sliding-window limits.
The script should remove old members, count remaining requests, add a
unique member for the new request, and set the key expiry as one atomic
operation.

## Locks

For a single Redis primary, acquire locks with `SET key token NX PX ttl`
and release only if the stored token matches the caller's token:

```python
def acquire_lock(resource: str, ttl_ms: int = 5000) -> str | None:
    token = str(uuid.uuid4())
    ok = redis_client.set(f"lock:{resource}", token, nx=True, px=ttl_ms)
    return token if ok else None
```

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
end
return 0
```

Always choose a TTL longer than the expected critical section but short
enough to recover from a crashed worker. Release in a `finally` block.
For multi-primary or cross-region coordination, do not casually invent a
locking algorithm; use a well-reviewed library or a stronger coordination
system when correctness is critical.

## Messaging

Use Pub/Sub only for fire-and-forget broadcast where missed messages are
acceptable. Subscribers that are offline do not receive past messages.

Use Redis Streams when the workflow needs persistence, consumer groups,
acknowledgement, retry, or replay:

```python
redis_client.xadd("stream:orders", {"order_id": order_id}, maxlen=10000)
messages = redis_client.xreadgroup(
    "order-processors",
    consumer_name,
    {"stream:orders": ">"},
    count=10,
    block=2000,
)
```

After processing a stream message, acknowledge it with `XACK`. Plan for
pending entries and retries; at-least-once delivery means handlers must
be idempotent.

## Production Checks

- Configure connection pools with maximum connections and operation
  timeouts.
- Pick an eviction policy that matches the role: `allkeys-lru` or
  `allkeys-lfu` for general cache, `noeviction` for queues or critical
  coordination data, and TTL-focused policies only when expirations are
  consistently set.
- Separate cache, queue, lock, and session workloads by instance or
  logical boundary when eviction, persistence, or blast radius differs.
- Avoid `KEYS *` in production; use `SCAN` with a cursor and bounded
  batches.
- Avoid large serialized blobs. Store bulky payloads in object storage or
  the primary database and cache references or compact projections.
- Decide persistence deliberately. RDB snapshots, append-only file (AOF),
  replicas, Sentinel, and Cluster solve different durability and
  availability problems.
- When running Redis through Compose, follow `devops/docker-patterns`:
  use `compose.yaml`, `env_file`, explicit `${VAR}` wiring, and a
  first-party named volume for Redis data.

## Anti-Patterns

- Cache keys with no TTL unless the persistence is intentional and
  documented.
- `FLUSHALL` or broad pattern deletes in a shared environment.
- One Redis instance used for every cache, queue, lock, and session
  responsibility without isolation.
- Locks without unique tokens, TTLs, or compare-before-delete release.
- Streams consumers that process messages but never acknowledge them.
- Rate limits that lose expiry or allow race conditions around the
  increment.
- Connection creation on every request instead of pooled clients.

## Completion Criteria

The Redis design is ready when the use case is explicit, the data
structure matches the access pattern, keys have a predictable namespace,
ephemeral data has a TTL, multi-step operations are atomic, client
connections are pooled and bounded, failure modes are tested, and
operational settings match the workload's durability and eviction needs.
