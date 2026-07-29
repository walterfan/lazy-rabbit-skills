# C++ Pitfalls Catalog + Triage Map

A field guide to the C++ mistakes that most often ship as bugs, mapped to the
matching ISO C++ Core Guidelines rule ids and the reference chapter that holds
the full reasoning, examples, and enforcement notes.

Use the **symptom -> pitfall** triage map to jump straight to the right chapter,
then cite the concrete rule id in the review comment.

Reference chapters live under [core-guidelines/](core-guidelines/):

| File | Chapter |
|------|---------|
| `01-iron_rules.md` | Iron Rules — crash / UB / OOB / leak (**start here**) |
| `02-p-philosophy.md` | P — Philosophy |
| `03-i-interfaces.md` | I — Interfaces |
| `04-f-functions.md` | F — Functions |
| `05-c-classes-and-hierarchies.md` | C — Classes and hierarchies |
| `06-enum-enumerations.md` | Enum — Enumerations |
| `07-r-resource-management.md` | R — Resource management |
| `08-es-expressions-and-statements.md` | ES — Expressions and statements |
| `09-per-performance.md` | Per — Performance |
| `10-cp-concurrency-and-parallelism.md` | CP — Concurrency and parallelism |
| `11-e-error-handling.md` | E — Error handling |
| `12-con-constants-and-immutability.md` | Con — Constants and immutability |
| `13-t-templates-and-generic-programming.md` | T — Templates |
| `14-cpl-c-style-programming.md` | CPL — C-style programming |
| `15-sf-source-files.md` | SF — Source files |
| `16-sl-standard-library.md` | SL — Standard library |
| `17-a-architectural-ideas.md` | A — Architecture |
| `18-nr-non-rules-and-myths.md` | NR — Non-rules and myths |
| `19-nl-naming-and-layout.md` | NL — Naming and layout |

## Symptom -> pitfall triage map

| Symptom you see in the diff | Likely pitfall | Rule id(s) | Chapter |
|-----------------------------|----------------|-----------|---------|
| `new`/`delete`, owning raw pointer | Manual memory mgmt instead of RAII | R.11, R.12 | 07, 01 |
| Leak on error/early return | No RAII owner for a resource | P.8, R.1 | 07, 01 |
| `delete` on `new[]` (or vice versa) | Mismatched alloc/free form | ES.61 | 08, 01 |
| Returns `&local` / view of local | Dangling reference/pointer | F.43, ES.65 | 04, 01 |
| `string_view`/`span` outlives source | Dangling view | ES.65 | 08, 01 |
| Reads object after `std::move` | Use-after-move | ES.56, C.64 | 08, 05 |
| Custom dtor, no copy/move defined | Rule-of-Five gap | C.21 | 05 |
| Move ctor/assign not `noexcept` | Slow/incorrect move | C.66 | 05 |
| `base b = derived;` | Object slicing | C.67, ES.63 | 05, 08 |
| `delete base_ptr;` non-virtual dtor | Missing virtual destructor | C.35, C.127 | 05, 01 |
| Virtual call in ctor/dtor | Wrong dispatch / UB | C.82 | 05, 01 |
| Uninitialized member/variable | Indeterminate value read | ES.20 | 08, 01 |
| `int i` vs `size_t` comparison | Signed/unsigned mix | ES.100, ES.106 | 08, 01 |
| `a[i] + a[i++]` | Unsequenced side effects | ES.43, ES.44 | 08, 01 |
| `arr[n]`, off-by-one | Out-of-bounds access | SL.con.3, ES.62 | 16, 01 |
| Pointer to `push_back`'d element | Iterator/pointer invalidation | ES.65 | 08, 01 |
| Shared var, no mutex/atomic | Data race | CP.2, CP.3 | 10, 01 |
| `mtx.lock()` / `mtx.unlock()` | Naked lock, leaks on throw | CP.20 | 10, 01 |
| Two `lock_guard`s in sequence | Deadlock / lock-order inversion | CP.21 | 10, 01 |
| `volatile bool ready` as flag | volatile is not synchronization | CP.8 | 10, 01 |
| `t.detach()` | Detached thread lifetime hazard | CP.26 | 10, 01 |
| Lock held across `co_await`/callback | Suspension/re-entrancy deadlock | CP.52 | 10, 01 |
| `cv.wait(lk)` no predicate | Spurious/lost wakeup | — | 10 |
| `memcpy(&obj, ...)` non-POD | Type-punning UB | C.90, SL.con.4 | 05, 01 |
| `strcpy`/`sprintf`/`gets` | Buffer overflow | SL.str, CPL | 16, 14 |
| `printf(user_input)` | Format-string injection | — (CWE-134) | 14 |
| `system(user_input)` | Command injection | — (CWE-78) | 14 |
| `(T)x` C-style cast | Unsafe cast | ES.48, ES.49 | 08, 01 |
| `const_cast` to mutate | Casting away const | ES.50 | 08, 01 |
| Pass-by-value big object | Needless copy | F.16 | 04, 09 |
| `for (auto x : bigvec)` | Copy per iteration | ES.71 | 08, 09 |
| `push_back` in loop, no reserve | Repeated realloc | Per.11 | 09 |
| `std::endl` in loop | Forced flush per line | — | 09 |
| `map[k]` to read | Accidental insert | — | 16 |
| `shared_ptr` by value in hot path | Refcount churn | R.34, R.37 | 07, 09 |
| Raw ptr param, unclear owner | Ambiguous ownership | I.11, R.3 | 03, 07 |
| `enum Color { Red }` at namespace scope | Unscoped enum leak | Enum.3 | 06 |
| `using namespace` in a header | Namespace pollution | SF.7 | 15 |
| Missing include guard | Double inclusion | SF.8 | 15 |
| Result ignored (e.g. `error_code`) | Missing `[[nodiscard]]` | — | 03 |
| 1-arg ctor not `explicit` | Implicit conversion surprise | C.46 | 05 |

## Core pitfall groups

### 1. Ownership and lifetime (highest bug density)
Prefer RAII and value semantics. Every resource has exactly one owner. Never
return or store a reference/pointer/`string_view`/`span`/iterator that can
outlive its source. See `07-r-resource-management.md`, `01-iron_rules.md`.

### 2. Special members (Rule of Five / Rule of Zero)
If you write a destructor, copy ctor, copy assign, move ctor, or move assign,
you almost certainly need to reason about all five. Prefer Rule of Zero — let
the compiler generate them by using RAII members. Make move ops `noexcept`.
See `05-c-classes-and-hierarchies.md`.

### 3. Undefined behavior in expressions
Uninitialized reads, signed overflow, unsequenced side effects, OOB access,
invalid downcasts, and type punning are UB. UBSan catches many at runtime.
See `08-es-expressions-and-statements.md`, `01-iron_rules.md`.

### 4. Concurrency
Guard shared mutable state, use RAII locks, take multiple mutexes with
`scoped_lock`, keep a consistent lock order, never use `volatile` for
synchronization, and never hold a lock across a callback or `co_await`. Run
under TSan. See `10-cp-concurrency-and-parallelism.md`.

### 5. Performance (evidence-first)
Kill needless copies and allocations, `reserve` before known-size loops, pick
the right container, avoid `std::endl` in loops, and avoid virtual/type-erasure
overhead on hot paths. Profiling is the source of truth. See
`09-per-performance.md`.

### 6. C interop and security
Ban `strcpy`/`sprintf`/`gets`/unbounded `scanf`; never pass user data as a
format string or into `system()`; validate all sizes and indices; never log
secrets/PII. See `14-cpl-c-style-programming.md`, `16-sl-standard-library.md`.

## How to cite

Cite the concrete rule id in each finding, e.g.:
`dangling string_view returned from getName() (ES.65)` or
`data race on cache_ read from worker thread (CP.2)`. If a mistake is not covered
by a specific Core Guidelines rule, cite the CWE (for security) or say "not in
the catalog" and explain the concrete C++ risk.
