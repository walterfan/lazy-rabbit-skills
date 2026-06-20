# Go Concurrency and Review

Use this note when a task touches goroutines, channels, caches, HTTP handlers,
database access, or any code that could hide semantic bugs behind clean syntax.

## Concurrency defaults

- Every goroutine needs an owner, a stop condition, and a wait path
- Pass loop variables into goroutines explicitly
- Use `context.Context` to cancel long-running work
- Use `sync.WaitGroup`, channels, or both to coordinate completion
- Only senders close channels
- Use `select` with `ctx.Done()` for cancellable send/receive loops
- Protect shared maps and slices with `sync.Mutex`, `sync.RWMutex`, or a
  justified `sync.Map`
- Unlock mutexes with `defer` immediately after locking
- Prefer worker pools over unbounded goroutine fan-out

## Common pitfalls

- Goroutine leaks from background work with no cancellation
- Loop variable capture in goroutines
- Nil interface surprises and unchecked nil pointers
- Race conditions on maps, slices, and cached state
- `defer` inside loops keeping resources open too long
- Ignored errors that hide partial failure
- HTTP response bodies not being closed
- Inconsistent pointer vs value receiver choices
- Blocking channel sends with no receiver or undersized buffering

## Review order

1. Behavior and correctness
2. Security and data exposure
3. Concurrency safety and leak risk
4. API compatibility and error flow
5. Missing tests
6. Naming/style nits

## Focused review checklist

- Are all errors handled or intentionally propagated?
- Does the code wrap errors with enough context?
- Is `context.Context` passed through blocking layers?
- Could any goroutine outlive its caller without reason?
- Are channels closed by the sender only?
- Could shared state race under load?
- Should `go test -race` be run for this change?
- Are response bodies, files, rows, and transactions closed correctly?
- Is user input validated before it reaches SQL, regex, or command execution?
- Are sensitive values omitted from logs and error messages?
- Does the diff preserve handler/service/repo boundaries already in the repo?

## Good review comments

- `The goroutine launched here has no cancellation path; if the request exits early, this worker can outlive its owner. Thread the request context through and stop on ctx.Done().`
- `This raw SQL string interpolates user input. Switch to placeholders so the query remains parameterized.`
- `The change adds shared map writes from multiple goroutines. Guard it with a mutex or replace the pattern with a worker-owned map.`
- `This handler returns 200 even when the dependency reports not found. Map the domain error to a stable HTTP status and response body.`

## Verification defaults

- `go test ./...`
- `go test -race ./...` for concurrency or cache work
- Package-targeted tests first when feedback speed matters
