# Python Code Review Checklist

Fast, focus-scoped checklist for reviewing local Python code. Run one focus per
round. Trap numbers reference [python-pitfalls-catalog.md](python-pitfalls-catalog.md);
Pydantic items reference [pydantic-best-practices.md](pydantic-best-practices.md).

## Review order (severity-first)

1. Correctness / behavior
2. Classic Python pitfalls (the 10 traps)
3. Concurrency & async safety (GIL-aware)
4. Security and data exposure
5. Performance (with evidence)
6. Typing & tooling (static-checkability)
7. Pydantic / boundary validation
8. Testing coverage

## Correctness

- [ ] No mutable default argument (Trap 1)
- [ ] Loop closures capture value, not variable (Trap 2)
- [ ] `is`/`is not` only for singletons; `==` for values; `is None` (Trap 3)
- [ ] Nested data copied with `deepcopy` when independence needed (Trap 4)
- [ ] No `[[...]]*n` aliasing (Trap 5)
- [ ] No container mutated during iteration (Trap 6)
- [ ] `Decimal`/int cents for money, not `float` (Trap 8)
- [ ] Empty/`None`/boundary inputs handled; truthiness vs `is not None`
- [ ] Return values used; no missing `return`; generator not re-consumed

## Pitfalls sweep

- [ ] All 10 traps swept (see catalog)
- [ ] `+=` string building replaced by `"".join` (Trap 7)
- [ ] Broad `except` narrowed (Trap 9)
- [ ] CPU-bound `threading` -> multiprocessing; shared state locked (Trap 10)

## Concurrency / async

- [ ] `threading` not used for CPU-bound speedup (GIL)
- [ ] Shared mutable state guarded by `Lock`/`Queue`; no `counter += 1` race
- [ ] `with lock:`; consistent lock order; no lock leak on exception
- [ ] No blocking calls (sync I/O, `time.sleep`, `requests`) inside `async def`
- [ ] Every coroutine awaited; `create_task` results tracked/awaited
- [ ] No `asyncio.run` inside a running loop; bounded concurrency (semaphore)
- [ ] `if __name__ == "__main__":` guard for multiprocessing spawn

## Security

- [ ] No `eval`/`exec`/`pickle.loads`/`yaml.load` on untrusted data
- [ ] SQL parameterized; no `shell=True`/`os.system` with input
- [ ] No path traversal / unsafe archive extraction (Zip Slip)
- [ ] `secrets` (not `random`) for tokens; KDF for passwords; no hardcoded keys
- [ ] No secrets/PII in logs/errors; `SecretStr` for config secrets
- [ ] `verify=False` not used; XML via `defusedxml`; no SSTI
- [ ] `assert` not used for security checks (stripped under `-O`)

## Performance (require evidence)

- [ ] `"".join` for loop string building (Trap 7)
- [ ] `set`/`dict` for membership, `Counter` for counting
- [ ] `@lru_cache`/`@cache` for pure repeated compute
- [ ] `__slots__`/`namedtuple`/`dataclass(slots=True)` for many objects
- [ ] Iterate files/generators instead of loading all into memory
- [ ] No N+1 queries / per-item network calls in loops
- [ ] Vectorized numpy/pandas instead of element-wise Python loops

## Typing & tooling

- [ ] Public functions have parameter + return annotations
- [ ] No stray `Any`/bare `dict`/`list`; precise types / `TypedDict`
- [ ] `Optional`/`None` narrowed before attribute access
- [ ] `# type: ignore[code]` is specific, with a reason
- [ ] Project has ruff/flake8 + mypy/pyright + black/isort + pytest
- [ ] A single `make check` gate wired into pre-commit AND CI

## Pydantic / boundaries

- [ ] Every external input (HTTP/MQ/API/LLM/config) has a model
- [ ] Key fields strict; money is `Decimal`; string/list length limits
- [ ] `extra="forbid"` on requests/commands (or a stated reason)
- [ ] Validators are pure (no DB/network/side effects)
- [ ] Config in `BaseSettings`; `SecretStr` for secrets; validated at startup
- [ ] Output models + `model_dump(mode="json")`; internal fields excluded
- [ ] v2 APIs (`model_validate`/`model_dump`); no mixed v1/v2

## Testing

- [ ] Core logic + error/exception paths tested
- [ ] Edge cases: empty/`None`/huge/unicode/boundaries
- [ ] Known traps tested (fresh default, closure value, deepcopy, money math)
- [ ] `@pytest.mark.parametrize` instead of copy-paste
- [ ] Strong assertions (`== expected`), not just `assert result`
- [ ] No `sleep`/wall-clock/network flakiness; deps mocked/monkeypatched
- [ ] Pydantic success AND `ValidationError` paths tested
- [ ] async tests properly awaited

## Finding format

For each finding, state:

- **Severity**: blocker / major / minor (or critical/high for security)
- **What can go wrong**: the concrete wrong result / crash / race / exploit / cost
- **Evidence**: file + rough location from the reviewed payload
- **Fix**: concrete suggestion
- **Trap #/best-practice**: the matching catalog trap or Pydantic practice, or CWE

Do not invent findings. If a focus area is clean, say so briefly and note any
residual risk (e.g. "no data race in shown code, but confirm under load").
