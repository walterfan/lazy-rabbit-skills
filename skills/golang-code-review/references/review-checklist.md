# Go Code Review Checklist

Fast, focus-scoped checklist for reviewing local Go code. Run one focus per
round. Mistake numbers reference *100 Go Mistakes and How to Avoid Them*; see
[go-mistakes-catalog.md](go-mistakes-catalog.md) for the full catalog and
[go-common-traps.md](go-common-traps.md) for code-level fixes.

## Review order (severity-first)

1. Correctness / behavior
2. Concurrency safety and leaks
3. Security and data exposure
4. Performance (with evidence)
5. Idiomatic / maintainability
6. Testing coverage

## Correctness

- [ ] No `:=` shadowing of `err`/state in nested scopes (#1)
- [ ] No typed nil returned/stored in an interface (#48)
- [ ] Errors compared with `errors.Is`/`errors.As`, not `==` (#52/#53)
- [ ] Loop-variable capture safe for the target Go version (#33/#77)
- [ ] No unintended slice aliasing / shared backing array (#21/#25)
- [ ] No reliance on map iteration order; no delete-during-range hazard (#34)
- [ ] Byte-vs-rune handled for non-ASCII strings (#37)
- [ ] `defer` argument timing understood (#36)
- [ ] Edge/empty/nil inputs and boundaries handled
- [ ] `return` after `http.Error`; errors not silently ignored (#90/#55)

## Concurrency

- [ ] Every goroutine has a stop condition and wait path (#76/#81)
- [ ] Shared state guarded (mutex/atomic) or owned by one goroutine (#60/#69)
- [ ] Channels: sender closes; buffer size intentional; no nil-channel hang (#66/#67)
- [ ] `WaitGroup.Add` before launching goroutines (#62)
- [ ] `context` cancellation threaded through blocking work (#80)
- [ ] No copied `sync` types (#74)
- [ ] `defer mu.Unlock()` right after `Lock`; consistent lock order
- [ ] No `time.After` timer leak in loops (#83)
- [ ] `go test -race` considered/run

## Security

- [ ] Parameterized queries only; no SQL string building
- [ ] No `os/exec` with unsanitized input
- [ ] No secrets/tokens/PII in logs or errors
- [ ] Input validated at trust boundaries (params, uploads, paths, redirects)
- [ ] `crypto/rand` for security-sensitive randomness
- [ ] Authz checks present and correct
- [ ] HTTP client/server has timeouts (#91)
- [ ] JWT/TLS validation correct; no insecure defaults

## Performance (require evidence)

- [ ] Slices/maps preallocated when size known (#21/#22/#27)
- [ ] `strings.Builder` for loop concatenation (#42)
- [ ] No needless `[]byte`/`string` copies (#43)
- [ ] No large-backing-array retention (#25/#44)
- [ ] No N+1 queries; pagination present
- [ ] Hot-path allocations minimized (escape analysis) (#95/#96)
- [ ] No `defer`/`time.After` overhead in tight loops (#49/#83)
- [ ] Range does not copy large structs by value (#30)

## Idiomatic / maintainability

- [ ] Accept interfaces, return structs; no interface pollution (#5/#6/#7)
- [ ] No `I`-prefix interfaces or `GetX` getters
- [ ] `context.Context` first; `error` last; wrapped with `%w`
- [ ] No double error handling; no swallowed errors (#54/#55)
- [ ] `any` avoided where a concrete type/generic fits (#8)
- [ ] No error-prone `init()`; explicit constructors (#3)
- [ ] Early returns over deep nesting (#2)
- [ ] Consistent receiver kind per type (#45)
- [ ] No `utils`/`common` dumping-ground packages (#12)
- [ ] New exported identifiers have godoc

## Testing

- [ ] Table-driven tests for multi-scenario logic (#94)
- [ ] Error paths, edge cases, boundaries covered
- [ ] `-race` for concurrent code (#93)
- [ ] No `time.Sleep`-based flakiness (#95)
- [ ] Clock injected, not `time.Now()` directly (#96)
- [ ] `httptest`/`iotest` for HTTP/IO boundaries (#97)
- [ ] Not-found vs internal-error branches tested
- [ ] Context cancellation/timeout tested
- [ ] Benchmarks reset timer / report allocs (#98)
- [ ] External deps mocked via small interfaces

## Finding format

For each finding, state:

- **Severity**: blocker / major / minor (or critical/high for security)
- **What can go wrong**: the concrete failure/race/exploit/cost
- **Evidence**: file + rough location from the reviewed payload
- **Fix**: concrete suggestion
- **Mistake #**: the matching *100 Go Mistakes* number when applicable

Do not invent findings. If a focus area is clean, say so briefly and note any
residual risk (e.g. "no data race found in shown code, but run `go test -race`").
