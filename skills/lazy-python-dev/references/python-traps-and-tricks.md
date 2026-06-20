# Python traps and tricks

This reference distills reusable guidance on common Python traps and tricks into review and implementation checks for `lazy-python-dev`.

Use this file for **code review**, **bug triage**, and **small implementation decisions**. Keep the repo's toolchain rules from [python-library.md](python-library.md) as the default; this file is about Python behavior, not replacing the project's Poetry + Ruff + pytest workflow.

## Top traps to scan for

| Trap | Bad pattern | Safer pattern | Why it matters |
|------|-------------|---------------|----------------|
| Mutable default argument | `def f(x, items=[]):` | `def f(x, items=None): ...` | Default mutable objects are shared across calls |
| Late-bound closure in loops | `lambda: i` inside loop | `lambda i=i: i` or `functools.partial(...)` | Closures capture variables by reference, not snapshot |
| `is` vs `==` misuse | `x is 3`, `x == None` | `x == value`, `x is None` | Identity and value checks are different |
| Shallow copy surprise | `copy = nested.copy()` | `copy.deepcopy(nested)` when independence is required | Nested structures still share children |
| List multiplication aliasing | `rows = [[0] * 3] * 3` | `rows = [[0] * 3 for _ in range(3)]` | Repeats references, not independent inner lists |
| Mutating during iteration | delete from dict while iterating | collect keys first or build a new dict | Can raise at runtime or produce confusing behavior |
| String concat in loops | `result += chunk` in big loop | `"".join(parts)` | Repeated allocation hurts performance |
| Float for money | `0.1 + 0.2 == 0.3` | `Decimal`, integer cents, or `math.isclose` | Binary float precision is often unsuitable |
| Over-broad exception | `except:` or `except Exception: pass` | catch specific exceptions you can handle | Broad handlers hide bugs and operational signals |
| Wrong concurrency model | CPU-heavy threads in CPython | multiprocessing for CPU, threads/asyncio for I/O | GIL and non-atomic updates cause surprises |

## Review checklist

- Check defaults for `[]`, `{}`, or `set()` in function signatures and dataclass fields.
- Check loops that create callbacks, lambdas, or closures for late binding bugs.
- Check nested copies and "matrix" initialization for shared inner references.
- Check money, percentages, or precise comparisons for float misuse.
- Check `except` clauses for precision and whether the handler actually recovers.
- Check concurrency code for shared mutable state, locks, and CPU-vs-I/O mismatch.
- Check large string assembly or membership tests for obvious algorithmic hot spots.

## Useful standard-library patterns

| Need | Prefer |
|------|--------|
| Counting | `collections.Counter` |
| Grouping with default values | `collections.defaultdict` |
| Fast queue / rolling buffer | `collections.deque` |
| Flattening and iterator slicing | `itertools.chain`, `itertools.islice` |
| Reusable partial arguments | `functools.partial` |
| Memoizing pure functions | `functools.lru_cache` |
| Lightweight records | `dataclasses.dataclass` or project-approved model types |
| Resource cleanup / timing | `with` and `contextlib.contextmanager` |

## Dataclass note

For dataclasses, mutable fields need factories:

```python
from dataclasses import dataclass, field


@dataclass
class User:
    tags: list[str] = field(default_factory=list)
```

This is the dataclass version of the "mutable default argument" rule.

## Performance heuristics

- Prefer `"".join(parts)` over repeated string concatenation in large loops.
- Prefer `set` membership over repeated `x in list` checks on large collections.
- Use iterator-based processing for large inputs instead of materializing everything.
- Consider caching only for **pure** or effectively pure functions.
- Reach for `__slots__` only when object count is very large and the tradeoff is understood.

## Scope guard

These are **review heuristics**, not rigid rewrite rules:

- Do not force `Decimal`, `lru_cache`, `__slots__`, or `dataclass` everywhere.
- Prefer the simplest correct change that matches the repo's style and public API constraints.
- When a project already uses Pydantic models heavily, do not replace them with dataclasses just because dataclasses are convenient.
