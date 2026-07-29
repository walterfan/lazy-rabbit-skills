# Python Pitfalls Catalog + Triage Map

A field guide to the Python mistakes that most often ship as bugs, plus a
symptom -> trap triage map and a performance cheat sheet. Cite the trap number
in the review comment.

Source: "Python 编程的常见陷阱与奇巧淫技" (Walter Fan).

## Symptom -> trap triage map

| Symptom you see in the diff | Trap | Fix |
|-----------------------------|------|-----|
| `def f(x, acc=[])` / `={}` / `=set()` | 1 Mutable default arg | default `None`, init inside |
| `lambda`/def in a loop using the loop var | 2 Closure late binding | `lambda i=i:` or `functools.partial` |
| `x == None`, or `is` for value compare | 3 `is` vs `==` | `is None`; `==` for values |
| `.copy()`/`[:]`/`dict(x)` on nested data | 4 Shallow copy | `copy.deepcopy(x)` |
| `[[0]*3]*3`, `[{}]*n` | 5 Multiplication aliasing | `[[0]*3 for _ in range(3)]` |
| `for k in d: del d[k]` | 6 Mutate while iterating | collect-then-delete / rebuild |
| `result += s` in a loop | 7 String concat O(n^2) | `"".join(parts)` |
| `float` amounts, `0.1+0.2==0.3` | 8 Float precision | `Decimal` / int cents / `math.isclose` |
| bare `except:` / `except Exception: pass` | 9 Over-broad except | catch specific exceptions |
| `threading` for CPU work; `counter += 1` shared | 10 GIL / non-atomic | multiprocessing (CPU), `Lock`/asyncio (IO) |

## The 10 traps (detail)

### Trap 1 — Mutable default argument
Default values are evaluated **once at def time**, not per call. A `list`/`dict`/
`set` default is shared across all calls.
```python
def append_to(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target
```
Rule: never use a mutable object as a default; use `None`.

### Trap 2 — Closure late binding
A `lambda`/nested function captures the **variable**, not its value at creation.
After a loop, all closures see the final value.
```python
funcs = [lambda i=i: i for i in range(3)]   # 0,1,2 (captured)
# or: [partial(lambda x: x, i) for i in range(3)]
```

### Trap 3 — `is` vs `==`
`==` compares value; `is` compares identity (address). Small ints (-5..256) and
some strings are interned, so `is` sometimes "works" by accident.
```python
if x is None: ...      # correct singleton check
if a == b: ...         # value comparison
```

### Trap 4 — Shallow vs deep copy
`.copy()`, `[:]`, `list(x)`, `dict(x)` copy one level; nested objects stay
shared. Use `copy.deepcopy` for fully independent nested copies.

### Trap 5 — Multiplication creates references
`[[0]*3]*3` is three references to the **same** inner list. Use a comprehension
so each row is a new list: `[[0]*3 for _ in range(3)]`.

### Trap 6 — Mutating a container during iteration
`del d[k]` / `d[k]=...` while iterating raises `RuntimeError: dictionary changed
size during iteration` (or silently skips list items). Collect keys first, then
delete, or build a new dict/list.

### Trap 7 — String concatenation in a loop
`+=` on immutable strings creates a new object each time (O(n^2)). Use
`"".join(list_of_strings)` (O(n)).

### Trap 8 — Float precision
`0.1 + 0.2 == 0.3` is `False`. For money use `decimal.Decimal` or integer cents;
for comparisons use `math.isclose`. Never use `float` for currency.

### Trap 9 — Over-broad exception handling
Bare `except:` also catches `KeyboardInterrupt`/`SystemExit`; `except Exception:`
hides real bugs. Catch only what you can handle:
```python
try:
    do_something()
except (ValueError, KeyError) as e:
    handle(e)
```

### Trap 10 — GIL and threads
CPython's GIL serializes bytecode, so `threading` does not speed up CPU-bound
work, and `counter += 1` is not atomic (read/add/write -> races). Use
`multiprocessing`/`ProcessPoolExecutor` for CPU-bound work; `Lock` or `Queue`
for shared state; threads or `asyncio` remain effective for IO-bound work.

## Useful idioms (suggest, don't force)

- Walrus `:=` (3.8+) for assign-and-test in `while`/`if`
- `dict1 | dict2` merge (3.9+); `dict1 |= dict2` in-place
- `collections`: `defaultdict`, `Counter`, `namedtuple`, `deque(maxlen=...)`
- `itertools`: `chain`, `groupby` (sort first!), `islice`, `combinations`
- `contextlib.contextmanager` for lightweight `with` resources
- `__slots__` for millions of small objects (~40-50% memory saved)
- `functools`: `lru_cache`/`cache`, `partial`, `reduce`
- Unpacking: `a, *mid, b = seq`; swap `a, b = b, a`; chained `0 < x < 10`
- `dataclasses.dataclass` (use `field(default_factory=list)` for mutable defaults)
- f-strings: `f"{x=}"` debug, `f"{score:.2f}"`, alignment `f"{s:>10}"`

## Performance cheat sheet

| Scenario | Slow | Fast |
|----------|------|------|
| String join | `+=` in loop | `"".join(list)` |
| Membership test | `x in list` | `x in set` |
| Counting | hand-rolled dict | `Counter` |
| Repeated pure compute | recompute | `@lru_cache` / `@cache` |
| Many small objects | plain class | `__slots__` / `namedtuple` / `dataclass(slots=True)` |
| Large file read | `readlines()` | `for line in f:` |

## Engineering checklist (from the article)

- Format: `black`, `isort`; Lint: `ruff`/`flake8`; Types: `mypy`/`pyright`
- Type hints on public functions; avoid `Any`/bare `dict`
- Tests with `pytest` — core logic, edges (`None`/empty/huge), known traps
- Logging on key paths (`logger.exception` in `except`)
- Locked dependencies (`poetry.lock` / `requirements.txt`), virtualenv
- Wire `lint + type-check + test` into one `make check`, in pre-commit AND CI
