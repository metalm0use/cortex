---
schema_version: 1
tags:
  - "programming"
  - "python"
  - "typing"
  - "testing"
  - "tooling"
topics:
  - "python idioms"
  - "type hints"
  - "error handling"
  - "package layout"
status: seed
created: 2026-06-07
updated: 2026-06-07
sources:
  - "https://github.com/affaan-m/ECC/blob/main/skills/python-patterns/SKILL.md"
source_count: 1
aliases:
  - "python"
  - "python patterns"
  - "python typing"
  - "python packaging"
  - "python review"
skill_id: programming/python-patterns
summary: "Apply idiomatic Python patterns for readable code, type hints, error handling, package layout, tooling, and performance."
model_role: reference
depends_on: []
related:
  - sql/injection
  - meta/contributing
---

# Python Patterns

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when writing, reviewing, refactoring, or organizing Python
code, especially when the task touches type hints, error handling,
package boundaries, resource management, concurrency, performance, or
tooling.

## Core Rule

Prefer clear, explicit, typed Python that follows the principle of least
surprise. Use Python idioms when they improve readability; expand the
code when an idiom becomes clever enough to hide behavior.

## Workflow

1. Match the repository's existing Python version, formatter, linter,
   test runner, package manager, and layout before introducing new tools.
2. Write public function signatures with type hints. Use modern built-in
   generics such as `list[str]` and unions such as `str | None` when the
   supported Python version allows them.
3. Keep functions small enough to name one behavior. Prefer explicit
   intermediate variables over dense one-line transformations.
4. Handle errors narrowly. Catch specific exceptions, add context, and
   chain with `raise ... from exc` when translating exception types.
5. Use context managers for files, locks, network clients, database
   transactions, and temporary resources.
6. Use comprehensions for simple mapping or filtering. Use loops or
   generator functions when conditions, branches, or side effects make a
   comprehension hard to read.
7. Verify with the local contract: tests first, then formatting, linting,
   and type checks when the project has them.

## Type Hints

Annotate boundaries that other code calls:

```python
def get_active_users(users: list[User]) -> list[User]:
    return [user for user in users if user.is_active]
```

Use type aliases to make repeated complex shapes readable:

```python
type JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
```

Use `Protocol` when callers only need a behavior, not a concrete base
class:

```python
class Renderable(Protocol):
    def render(self) -> str: ...

def render_all(items: Iterable[Renderable]) -> str:
    return "\n".join(item.render() for item in items)
```

Do not use `Any` to silence uncertainty. Use it at boundaries where the
data is genuinely dynamic, then validate or narrow it as soon as
practical.

## Errors

Catch the failure mode you can handle:

```python
def load_config(path: Path) -> Config:
    try:
        data = path.read_text(encoding="utf-8")
        return Config.model_validate_json(data)
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except ValueError as exc:
        raise ConfigError(f"Invalid config JSON: {path}") from exc
```

Avoid bare `except`, silent `pass`, and returning `None` for every error.
If an error is expected and part of the API, document it in the return
type or raise a domain-specific exception.

## Data And Resources

Use dataclasses for simple in-process data containers:

```python
@dataclass(frozen=True)
class UserProfile:
    user_id: str
    email: str
    created_at: datetime
```

Use `default_factory` for mutable defaults:

```python
@dataclass
class Batch:
    items: list[str] = field(default_factory=list)
```

Use context managers for resource lifetime:

```python
with path.open(encoding="utf-8") as handle:
    text = handle.read()
```

Create a custom context manager when setup and cleanup must stay paired:

```python
@contextmanager
def transaction(connection: Connection):
    connection.begin()
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
```

## Iteration And Performance

Use generator expressions for large or streaming inputs:

```python
total = sum(item.price for item in orders if item.is_billable)
```

Use generator functions when the transformation needs names, branches,
or cleanup:

```python
def read_nonempty_lines(path: Path) -> Iterator[str]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield line
```

Avoid repeated string concatenation in loops; use `"".join(...)` or
`io.StringIO` when building larger strings.

Use `__slots__` only when many instances make memory a measured concern.
Do not add it reflexively to ordinary domain objects where flexibility
and simple debugging matter more.

## Concurrency

Pick the concurrency model that matches the bottleneck:

- Use `asyncio` for high-concurrency I/O when the libraries are async.
- Use `ThreadPoolExecutor` for blocking I/O when async libraries are not
  available.
- Use `ProcessPoolExecutor` or native/vectorized libraries for CPU-bound
  work.

Bound concurrency and timeouts. Do not create an unbounded task per input
item or a new client connection per request.

## Package Layout

Prefer a `src/` layout for reusable packages unless the repository
already has a strong local convention:

```text
project/
  pyproject.toml
  src/
    package_name/
      __init__.py
      py.typed
  tests/
    conftest.py
```

Keep imports explicit and sorted as standard library, third-party, then
local imports. Use `__init__.py` for intentional package exports; do not
hide expensive imports or runtime side effects there.

## Tooling

Use project-local tooling before adding new commands. Common checks are:

```bash
python -m pytest
python -m ruff check .
python -m ruff format .
python -m mypy .
```

Prefer `pyproject.toml` as the shared configuration surface for package
metadata, Python version, formatter, linter, type checker, and pytest
settings. Keep `requires-python` honest so type syntax and runtime
features match the supported interpreter.

## Anti-Patterns

- Mutable default arguments such as `items=[]`.
- Bare `except` or broad `except Exception` without a narrow recovery
  plan.
- `from module import *` outside rare compatibility modules.
- `type(obj) == SomeClass` when `isinstance` is intended.
- `value == None` instead of `value is None`.
- Hidden import-time side effects.
- Dense comprehensions with multiple filters, nested loops, or side
  effects.
- New formatting, linting, or typing tools added without checking local
  repository conventions first.

## Completion Criteria

The Python change is ready when the code is readable, public boundaries
are typed, errors preserve useful context, resources are managed with
clear lifetimes, package structure follows local convention, performance
choices match measured or obvious bottlenecks, and the repository's
Python tests plus relevant formatter, linter, or type-checker commands
pass.
