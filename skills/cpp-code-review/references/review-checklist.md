# C++ Code Review Checklist

Fast, focus-scoped checklist for reviewing local C++ code. Run one focus per
round. Rule ids reference the ISO C++ Core Guidelines; see
[cpp-pitfalls-catalog.md](cpp-pitfalls-catalog.md) for the symptom -> pitfall
triage map, and [core-guidelines/01-iron_rules.md](core-guidelines/01-iron_rules.md)
for the crash/UB/OOB/leak-level rules to check first.

## Review order (severity-first)

1. Correctness / undefined behavior
2. Memory safety, ownership, and RAII
3. Concurrency safety and lifetime across threads
4. Security and data exposure
5. Performance (with evidence)
6. API / interface / lifetime design and maintainability
7. Testing coverage

## Correctness / UB

- [ ] No use-after-move; moved-from object not read before reassignment (ES.56, C.64)
- [ ] No returned/kept reference/pointer/`string_view`/`span` to a local or
      expired temporary (F.43, ES.65)
- [ ] Every variable and member initialized before use (ES.20)
- [ ] No narrowing / signed-unsigned mixing / integer overflow (ES.100, ES.103)
- [ ] No reliance on argument evaluation order or unsequenced side effects (ES.43)
- [ ] No out-of-bounds array/container/pointer access (SL.con.3, ES.62)
- [ ] No object slicing on copy through a base value (C.67, ES.63)
- [ ] Polymorphic base has a `virtual` (or protected non-virtual) destructor (C.35)
- [ ] No iterator/pointer/reference use after container mutation
- [ ] No missing `return`, wrong `switch` fallthrough, or ignored result
- [ ] No float `==`, div-by-zero, or unhandled `NaN` (ES.105)

## Memory / ownership / RAII

- [ ] No naked `new`/`delete`; ownership via `unique_ptr`/`shared_ptr`/value (R.11, R.20)
- [ ] No leak on any early-return / exception / error path (P.8, R.1)
- [ ] `new`/`delete` and `new[]`/`delete[]` forms match (ES.61)
- [ ] No double-free / use-after-free / dangling after owner destroyed
- [ ] Rule of Five/Zero consistent; move ops `noexcept` (C.20, C.21, C.66)
- [ ] Copy/move assignment self-assignment-safe (C.62, C.65)
- [ ] No `shared_ptr` reference cycles (use `weak_ptr` to break) 
- [ ] Smart pointers not passed by value where a reference/raw ptr fits (R.30, R.34)
- [ ] No `memset`/`memcpy` on non-trivially-copyable types (C.90)
- [ ] Destructor releases all resources and does not throw (C.31, C.33, C.36)

## Concurrency

- [ ] Shared mutable state guarded by mutex/atomic or single-owner (CP.2, CP.3)
- [ ] RAII locks (`lock_guard`/`scoped_lock`/`unique_lock`), never naked lock/unlock (CP.20)
- [ ] Multiple mutexes taken via `std::scoped_lock`; consistent lock order (CP.21)
- [ ] No `volatile` used for synchronization (CP.8)
- [ ] No lock held across callback / blocking call / `co_await` / I/O (CP.52)
- [ ] Threads joined or detached deliberately; no detached thread touching
      soon-dead data (CP.26)
- [ ] `condition_variable` waits use a predicate; no lost/spurious wakeup bug
- [ ] Correct `std::atomic` memory ordering; no relaxed where acq/rel needed
- [ ] No `this`/reference captured by a lambda outliving the object on another thread (F.53)
- [ ] `go test -race`-equivalent: TSan run considered

## Security

- [ ] No `strcpy`/`strcat`/`sprintf`/`gets`/unbounded `scanf`
- [ ] `memcpy`/`memset` lengths validated; no attacker-controlled sizes
- [ ] No user data used as a format string
- [ ] No `system`/`popen`/`exec*` with unsanitized input
- [ ] Input validated at trust boundaries; size/index arithmetic overflow-safe
- [ ] No secrets/tokens/JWTs/PII logged or retained; sensitive buffers zeroized
- [ ] Strong crypto/randomness; no `rand()` for security; no hardcoded keys
- [ ] Untrusted parsing/deserialization bounded; no unchecked `reinterpret_cast`

## Performance (require evidence)

- [ ] Large objects passed by `const&`; sinks by value + `move` (F.16)
- [ ] `reserve()` before known-size `push_back` loops
- [ ] Range-for uses `const auto&`, not `auto` copy, for big elements
- [ ] `'\n'` not `std::endl` in loops
- [ ] No redundant heap allocations / `shared_ptr` churn on hot paths
- [ ] Right container for the access pattern; no `map::operator[]` misuse
- [ ] No virtual/`std::function`/type-erasure overhead in tight loops
- [ ] Loop-invariant work hoisted; no false sharing of hot fields
- [ ] `emplace_back`/`emplace` where a temporary would be copied

## API / lifetime / maintainability

- [ ] Ownership clear in signatures; return `unique_ptr` not raw owning ptr (I.11, R.3)
- [ ] Idiomatic parameter passing (F.15–F.17)
- [ ] No leaked reference/view whose lifetime is not tied to an owner (I.13)
- [ ] `[[nodiscard]]` on must-check results; `explicit` on 1-arg ctors (C.46)
- [ ] Rule of Zero preferred; no needless special members (C.20)
- [ ] `const`-correct methods, params, locals (Con.1, Con.2)
- [ ] Preconditions expressed via types/`Expects`/assert, not comments (I.5, I.6)
- [ ] `enum class` over plain enum; no magic numbers (Enum.3)
- [ ] Header hygiene: `#pragma once`/guards; no `using namespace` in headers (SF.7)

## Testing

- [ ] Error/exception/failure paths tested
- [ ] Edge/boundary inputs tested (empty, max, null, overflow)
- [ ] Move-from and self-assignment tested for value types
- [ ] Concurrency exercised under contention / TSan
- [ ] CI runs tests under ASan/UBSan/TSan
- [ ] No `sleep`/wall-clock/timing flakiness; clock injected
- [ ] Parameterized tests instead of copy-paste
- [ ] `EXPECT_EQ` over `EXPECT_TRUE(a==b)`; correct `ASSERT` vs `EXPECT`
- [ ] External deps mocked/faked via a seam

## Finding format

For each finding, state:

- **Severity**: blocker / major / minor (or critical/high for security)
- **What can go wrong**: the concrete UB / leak / race / exploit / cost
- **Evidence**: file + rough location from the reviewed payload
- **Fix**: concrete suggestion (prefer RAII, value semantics, safe types)
- **Rule id**: the matching Core Guidelines rule id when applicable
- **Sanitizer**: which of ASan/UBSan/TSan/LeakSan would likely catch it

Do not invent findings. If a focus area is clean, say so briefly and note any
residual risk (e.g. "no data race found in shown code, but run under TSan").
