# Go Common Traps (15-point field guide)

Curated pitfalls from Walter Fan's field notes
(<https://www.fanyamin.com/blog/2025-03-25-go.html>), cross-referenced to the
matching mistakes in *100 Go Mistakes and How to Avoid Them*. Use as a
practical, code-level companion to `go-100-mistakes.md`. Each entry: the trap,
the concrete fix, and the book mistake number(s).

## 1. Short variable declaration (`:=`)

- **Trap**: `:=` in a nested `if`/`for`/`switch` scope shadows an outer variable
  instead of reusing it; `:=` must declare at least one new name.
- **Fix**: Avoid reusing names across nested scopes; use `var` or `=` to make
  intent explicit; let `gofmt`/vet flag shadowing.
- **Book**: unintended variable shadowing (#1).

## 2. Pointers

- **Trap**: Pointer-receiver vs value-receiver behavior differs; forgetting to
  dereference; nil-pointer method calls only panic if the body touches fields.
  (Returning `&localVar` is safe in Go—escape analysis heap-promotes it.)
- **Fix**: Use pointer receivers to mutate; check for nil before field access;
  keep receiver kind consistent per type; run `go vet`.
- **Book**: value vs pointer receiver (#45); nil receiver / typed nil (#48).

## 3. nil semantics

- **Trap**: A nil concrete pointer stored in an interface makes `iface == nil`
  false. nil slice (safe `len`), nil map (panic on write), nil channel (blocks
  forever) all behave differently. Different nil types are not comparable.
- **Fix**: Guard with `if i == nil || reflect.ValueOf(i).IsNil()` when needed;
  initialize maps/channels before use; document nilable return values; prefer
  not returning typed-nil interfaces.
- **Book**: returning nil receiver in interface (#48); nil vs empty slice (#23);
  nil channels (#66).

## 4. `for range` loops

- **Trap**: Taking `&v` of the range value captures one reused variable
  (pre–Go 1.22); map iteration order is random; deleting map entries mid-range
  is unreliable; appending during range does not affect the current pass.
- **Fix**: Index the source (`&s[i]`) or pass the value as a parameter; sort keys
  when order matters; stage deletes; verify the Go version in `go.mod` (1.22+
  scopes the loop var per iteration).
- **Book**: range loop variable capture (#33/#77); map iteration order (#34);
  range copies element (#30).

## 5. Slices

- **Trap**: Slices share backing arrays, so `s2 := s[1:3]; s2[0]=x` mutates `s`;
  `append` may or may not reallocate depending on `cap`; length vs capacity
  confusion; repeated `append` reallocates.
- **Fix**: `copy()` when you need independence; reason about `len` vs `cap`
  before `append`; preallocate `make([]T, 0, n)` when size is known; use
  three-index slices `s[a:b:c]` to bound capacity.
- **Book**: slice length/capacity (#21); slice memory leaks (#25); inefficient
  init (#22).

## 6. Strings

- **Trap**: Strings are immutable; `s[i]` returns a byte not a rune;
  `len(s)` is bytes not characters; conversions copy; `+=` in a loop is O(n^2).
- **Fix**: Convert via `[]byte`/`[]rune` to modify; iterate with `for range`;
  count with `utf8.RuneCountInString`; build with `strings.Builder`; avoid
  needless `[]byte(...)`/`string(...)` round-trips.
- **Book**: rune vs byte (#37/#39); concatenation (#42); substring leak (#44).

## 7. `switch`

- **Trap**: No implicit fallthrough (unlike C); `fallthrough` forces the next
  case unconditionally; multi-value cases; type-switch variable has a different
  type per case.
- **Fix**: Rely on default no-fallthrough; use `fallthrough` deliberately; group
  values with commas; remember the bound variable's per-case type.
- **Book**: break/switch/label behavior (#35).

## 8. Goroutines

- **Trap**: A goroutine may never run before `main` exits; loop-variable capture
  prints the last value; leaks when there is no stop signal; unsynchronized
  shared state races.
- **Fix**: `sync.WaitGroup` to join; pass loop values as params or shadow;
  control lifecycle with `context`/`done` channels; protect state with mutex or
  atomics; run `go test -race`.
- **Book**: goroutine lifecycle (#76); loop-var capture (#77); data races (#60).

## 9. Channels

- **Trap**: Send on a closed channel panics; receive on a closed channel returns
  the zero value immediately; closing a nil channel panics; circular waits
  deadlock.
- **Fix**: Only the sender closes; use `v, ok := <-ch`; use `select` with a
  timeout/`ctx.Done()`; size buffers deliberately; use `context` for
  cancellation.
- **Book**: channel buffer/size (#67); nil channels (#66); select behavior (#64).

## 10. Methods with receivers

- **Trap**: `T` value can call `*T` methods only when addressable; `T` may not
  satisfy an interface that `*T` does; nil receivers; method value vs method
  expression.
- **Fix**: Keep receiver kind consistent; store `&c` in interfaces needing
  pointer methods; nil-check inside methods; know `c.M` (bound) vs `(*T).M`
  (unbound) forms.
- **Book**: value vs pointer receiver (#45); method sets.

## 11. `break`

- **Trap**: Bare `break` exits only the innermost loop/switch/select; inside a
  `select`/`switch` within a loop it breaks the switch, not the loop; `break`
  after each case is usually redundant.
- **Fix**: Use labeled `break outer` to exit outer loops; drop redundant breaks;
  consider `return` for clarity.
- **Book**: break/continue with labels & switch (#35).

## 12. Closures

- **Trap**: Closures capture variables by reference; loop-created closures share
  the loop var; capturing large objects leaks memory; `defer` closures see the
  final value of captured variables.
- **Fix**: Shadow per iteration or pass params; avoid capturing large state you
  do not need; pass `defer` args by value when you want a snapshot.
- **Book**: loop var capture (#33/#77); defer argument evaluation (#36).

## 13. Error handling

- **Trap**: Ignoring errors with `_`; handling the same error twice (log AND
  return); wrapping that drops the original; comparing wrapped errors with `==`.
- **Fix**: Always handle or propagate; wrap with `fmt.Errorf("...: %w", err)`;
  match with `errors.Is`/`errors.As`; either log or return, not both.
- **Book**: ignoring errors (#55); handling twice (#54); wrap vs `%w`
  (#51); `Is`/`As` (#52/#53).

## 14. Concurrency safety

- **Trap**: Unsynchronized shared counters race; inconsistent lock ordering
  deadlocks; forgetting to unlock (early return/panic) blocks forever;
  coarse-grained locks hurt throughput.
- **Fix**: Protect with mutex/RWMutex/atomics; `defer mu.Unlock()` right after
  `Lock`; keep a consistent lock order; narrow critical sections; prefer
  channels for ownership transfer; `go test -race`.
- **Book**: channels vs mutexes (#59); data races (#60); copying sync types
  (#74).

## 15. Imports and initialization

- **Trap**: Circular imports fail to compile; `init` ordering is subtle;
  unused imports error (use `_` for side effects only); package-level variable
  init order depends on dependency graph.
- **Fix**: Break cycles with interfaces/refactoring; avoid error-prone `init`
  logic (prefer explicit constructors); don't rely on `init` order; run
  `go mod tidy`.
- **Book**: misusing init (#3); project/package organization (#12–13).

## Usage

1. When a diff touches one of these 15 areas, walk that entry's fix list.
2. Cite the trap number and the matching book mistake (e.g. "trap 8 / #77") so
   the author can dig deeper.
3. For deeper/library and performance categories not covered here, fall back to
   `go-100-mistakes.md`.
