# 100 Go Mistakes Checklist

Actionable review and implementation checklist distilled from *100 Go Mistakes
and How to Avoid Them* (Teiva Harsanyi). Grouped by the book's chapters. Use it
as a semantic scan: for changed code, walk the relevant category and confirm the
mistake is not present. Numbers below reference the mistake grouping, not exact
book pagination.

## 1. Code and project organization

- **Unintended variable shadowing** (#1): `:=` in a nested scope silently
  shadows an outer variable, especially `err`. Reuse `=` or rename.
- **Unnecessary nested code** (#2): keep the happy path left-aligned; return
  early instead of deep `else` nesting.
- **Misusing init functions** (#3): avoid `init()` for error-prone setup,
  ordering-sensitive work, or anything that should be an explicit constructor.
- **Overusing getters/setters** (#4): only add them when they earn their keep;
  prefer direct field access for plain data.
- **Interface pollution** (#5): define interfaces on the consumer side, keep
  them small, and do not create them speculatively ("abstractions should be
  discovered, not created").
- **Interface on the producer side** (#6): return concrete types; let callers
  define the interfaces they need.
- **Returning interfaces** (#7): return structs, accept interfaces.
- **`any` says nothing** (#8): avoid `any`/`interface{}` when a concrete type or
  generic constraint expresses intent.
- **Misusing generics** (#9): use generics for real type-parameterized reuse,
  not to over-abstract simple code.
- **Type embedding pitfalls** (#10): embedding promotes methods/fields and can
  leak internals or break encapsulation—embed intentionally.
- **Not using the functional options pattern** (#11) for flexible, backward
  compatible constructors instead of many overloads or config structs.
- **Project misorganization / utility packages** (#12–13): avoid `utils`,
  `common`, `shared`, `base` dumping grounds; name packages by what they
  provide.
- **Ignoring package name collisions and missing godoc** (#14–15): document
  exported items; avoid shadowing built-ins/imports with local names.

## 2. Data types

- **Octal literal confusion** (#17): a leading `0` means octal.
- **Integer overflow ignored** (#18): detect/guard overflow on arithmetic near
  type limits.
- **Float comparison / accuracy** (#19–20): never compare floats with `==`;
  understand accumulation error and operation ordering.
- **Slice length vs capacity confusion** (#21) and inefficient initialization
  (#22): preallocate with `make([]T, 0, n)` when size is known.
- **Confusing nil vs empty slice** (#23): a nil slice and an empty slice differ
  in JSON and reflection; be deliberate.
- **Not checking empty slice properly** (#24): use `len(s) == 0`.
- **Slices and memory leaks** (#25): reslicing keeps the full backing array
  alive; copy when retaining a small window of a large slice, and nil out
  removed pointer elements.
- **Inefficient map initialization** (#27) and **map memory not shrinking**
  (#28): maps do not release buckets after deletes—recreate if needed.
- **Comparing values incorrectly** (#29): `==` fails or panics on slices/maps/
  functions; use `reflect.DeepEqual` or explicit comparison.

## 3. Control structures

- **Range copies the element** (#30): `for _, v := range s` copies each element;
  index for large structs or when mutating.
- **Range over array copy** (#31): ranging over an array (not slice) copies it;
  the range expression is evaluated once.
- **Ignoring how index/value behave with pointers/maps/channels** (#32).
- **Range loop variable capture** (#33): pre–Go 1.22, closures/goroutines share
  one loop variable. Pass by parameter or shadow per iteration. In Go 1.22+ the
  loop variable is per-iteration—still verify the target Go version in `go.mod`.
- **Range over map iteration order** (#34): unspecified and randomized; sort
  keys when order matters.
- **Break/continue with labels and switch** (#35): a bare `break` inside a
  `select`/`switch` in a loop breaks the switch, not the loop—use a label.
- **`defer` argument evaluation** (#36): arguments are evaluated when `defer`
  runs, not when it executes; capture the intended value or use a closure.

## 4. Strings

- **Rune vs byte confusion** (#37–38): a string indexes bytes; iterate runes
  with `for range`, convert with `[]rune`, use `utf8` helpers.
- **Inaccurate string iteration** (#39): `s[i]` yields a byte, not a rune.
- **Misusing `TrimRight`/`TrimSuffix`, `Trim` cutsets** (#40–41).
- **Inefficient concatenation** (#42): use `strings.Builder` in loops, not `+=`.
- **Useless `[]byte`/`string` conversions** (#43): avoid round-trip copies.
- **Substring and memory leaks** (#44): slicing a string retains the backing
  storage; copy when keeping a small piece of a huge string.

## 5. Functions and methods

- **Wrong receiver type (value vs pointer)** (#45): mutation, large structs,
  and consistency drive pointer receivers; do not mix on one type.
- **Named result parameters misuse** (#46): use for docs/deferred error wrap,
  but beware unintended zero-value returns.
- **Unintended side effects with named results** (#47).
- **Returning a nil receiver inside an interface** (#48): produces a non-nil
  interface—the typed-nil trap.
- **Ignoring how defer affects performance/args/return values** (#49).

## 6. Error management

- **Panicking instead of returning errors** (#50): reserve `panic` for truly
  unrecoverable programmer errors.
- **Ignoring when to wrap** (#51): wrap with `%w` to add context and preserve
  the chain; use `%v` only to intentionally hide the source.
- **Comparing errors by string / type inaccurately** (#52–53): use
  `errors.Is` for sentinels and `errors.As` for typed errors, not `==` on
  wrapped errors.
- **Handling an error twice** (#54): either handle or return, not both (e.g.
  log-and-return duplicates noise).
- **Ignoring errors** (#55): never `_ =` an error without an explicit reason.
- **Not handling `defer` errors** (#56): e.g. `defer f.Close()` can drop a write
  error—capture it via named return when it matters.

## 7. Concurrency: foundations

- **Confusing concurrency with parallelism** (#57) and thinking concurrency is
  always faster (#58): benchmark; goroutines have cost.
- **Channels vs mutexes confusion** (#59): channels for coordination/ownership
  transfer, mutexes for protecting shared state.
- **Not understanding race problems** (#60): data races and race conditions are
  distinct; `-race` finds data races, not all logic races.
- **Not knowing which concurrency approach fits the workload type** (#61):
  CPU-bound vs I/O-bound changes the design.
- **Misusing `sync.WaitGroup`** (#62): call `Add` before launching, not inside
  the goroutine.
- **Forgetting `select` with a single channel is pointless** / **`select`
  behavior with multiple ready cases is random** (#64).
- **Not using notification channels / `chan struct{}`** (#65) for signals.
- **Not using nil channels** (#66): a nil channel blocks forever—useful to
  disable a `select` case.
- **Wrong channel buffer size assumptions** (#67).
- **String formatting side effects in concurrent code** (#68): `String()` that
  touches shared state can deadlock/race.
- **Appending to a shared slice concurrently** (#69): data race.
- **Using mutexes inaccurately with slices/maps copies** (#70).
- **Misusing `sync.WaitGroup`, `sync.Cond`, `errgroup`, `sync.Once`** (#71–73):
  pick the right primitive; use `errgroup` for fan-out with error/cancel.
- **Forgetting `sync.Cond`/atomic where appropriate** and copying a
  `sync` type (#74): never copy a `sync.Mutex`/`WaitGroup` after use.

## 8. Concurrency: practice

- **Propagating an inappropriate context** (#75): do not pass a request context
  into work that must outlive the request; detach when needed.
- **Starting a goroutine without knowing when it stops** (#76): every goroutine
  needs a stop condition and a wait path.
- **Not being careful with goroutines and loop variables** (#77): see #33.
- **Expecting deterministic behavior using `select` + channels** (#78).
- **Not using notification channels vs data channels** correctly (#79).
- **Not using `context.Context` for cancellation/timeout/values** (#80).
- **Goroutine leaks from unbuffered/unread channels** (#81).
- **`context.Value` misuse** (#82): only request-scoped data, not optional
  parameters.
- **Not stopping `time.After` in loops** (#83): `time.After` in a hot loop leaks
  timers until they fire—use `time.NewTimer`/`NewTicker` and `Stop()`.
- **Ignoring `sync/atomic` for simple counters; misusing atomics** (#84).

## 9. Standard library

- **Wrong time duration** (#85): `time` APIs expect `time.Duration`, not raw
  ints—`5 * time.Second`, not `5`.
- **`time.After` memory leaks** (#86): see #83.
- **JSON handling pitfalls** (#87): type embedding + `MarshalJSON` recursion,
  `any` decoding to `float64`, monotonic clock in `time.Time` equality.
- **Common SQL/`database/sql` mistakes** (#88): forgetting `rows.Err()`, not
  closing `rows`/statements, not using prepared statements, ignoring
  `sql.NullXxx`, connection pool misconfiguration.
- **Not closing transient resources** (#89): HTTP response bodies, files, rows,
  `http.Response.Body`—`defer resp.Body.Close()` and drain it.
- **Forgetting the `return` after `http.Error`** (#90): the handler continues
  otherwise.
- **Using the default HTTP client/server (no timeouts)** (#91): set explicit
  `Timeout`, `ReadHeaderTimeout`, etc.

## 10. Testing

- **Not categorizing tests** (build tags, short mode) (#92).
- **Not enabling the race flag** (#93): run `go test -race` for concurrent code.
- **Not using table-driven tests** (#94).
- **Sleeping in tests / flaky timing** (#95): synchronize with channels/wait
  groups, not `time.Sleep`.
- **Not dealing with time in tests** (#96): inject a clock instead of calling
  `time.Now()` directly.
- **Not using `httptest`/`iotest`** (#97).
- **Inaccurate benchmarks** (#98): reset timer, avoid compiler elimination, use
  `b.ReportAllocs()`.
- **Not exploring all Go test features** (#99): sub-tests, setup/teardown,
  fuzzing, coverage.

## 11. Optimizations (measure first)

- **Not understanding CPU caches / data alignment / false sharing** (#91–94 in
  the perf chapter): struct field ordering and padding affect memory/cache.
- **Relying on premature optimization**: profile with `pprof` and benchmarks
  before restructuring.
- **Not understanding stack vs heap / escape analysis** (#95–96): reduce
  allocations that escape to the heap when it matters; verify with
  `go build -gcflags="-m"`.
- **Not using `sync.Pool`, prealloc, or inlining awareness** (#97–98) where a
  benchmark justifies it.
- **Ignoring GC / `GOGC` behavior and Linux/container CPU-throttling
  (`GOMAXPROCS`)** (#99–100): set `GOMAXPROCS` sensibly in containers.

## Fast triage map (symptom -> mistake)

| Symptom | Likely mistake |
|---------|----------------|
| `err` looks handled but wrong value used | shadowing (#1) |
| `if v == nil` false for a nil pointer | typed nil in interface (#48) |
| `errors.Is`/target check fails | comparing wrapped errors with `==` (#52) |
| Goroutines/closures all see last loop value | loop var capture (#33/#77) — check Go version |
| Editing one slice mutates another | shared backing array (#21/#25) |
| High memory after trimming a big slice/string | retained backing array (#25/#44) |
| Timers pile up in a loop | `time.After` in loop (#83/#86) |
| Handler keeps running after error response | missing `return` after `http.Error` (#90) |
| Intermittent hangs under load | goroutine leak / unread channel (#76/#81) |
| Client hangs forever | default HTTP client without timeout (#91) |
| Flaky test | `time.Sleep` instead of synchronization (#95) |
| Concurrency bug not caught | `-race` not run (#93) |
| Duration off by 1e9 | passing int where `time.Duration` expected (#85) |
| Non-ASCII string breaks | byte vs rune (#37) |

## How to use in review

1. Identify which chapters the diff touches (data types, control structures,
   error management, concurrency, stdlib, testing, perf).
2. Walk only those categories; confirm each listed mistake is absent.
3. Prefer citing the concrete mistake (e.g. "typed nil in interface, #48") so
   the author can look it up.
4. For performance claims, require a benchmark or profile before restructuring.
