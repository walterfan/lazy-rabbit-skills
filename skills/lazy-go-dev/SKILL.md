---
name: lazy-go-dev
description: >-
  Use when implementing, refactoring, reviewing, explaining, or testing Go code
  in a repo, diff, file, or snippet where idiomatic APIs, concurrency safety,
  nil/interface behavior, slice or channel semantics, SQL safety, or HTTP
  boundaries matter. Applies especially when the user mentions Go services,
  handlers, repositories, goroutines, race conditions, common Go pitfalls,
  GORM, `database/sql`, Resty, or request/response flow.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - go
  - gin
  - gorm
  - resty
  - concurrency
  - api
  - testing
  - security
  - pkb
category: dev-tools
use_cases:
  - "implement a Go handler/service/repository change with tests"
  - "review a Go diff for races, leaks, SQL safety, and API correctness"
  - "write Go unit tests with table-driven cases and testify"
  - "explain how this Go code works across handler, service, and repo layers"
platforms: [claude-code, cursor, codex]
visibility: public
---

# lazy-go-dev

Practical **idiomatic Go development** with a **pitfall-first** review mindset:
keep diffs small, pass `context.Context` explicitly, validate at boundaries,
avoid leaking secrets, and verify with `go test` (plus `-race` when concurrency
is involved) before claiming done.

**Progressive detail:** [references/go-service-stack.md](references/go-service-stack.md)
(web/API/data/Resty/security defaults),
[references/go-concurrency-review.md](references/go-concurrency-review.md)
(goroutines, pitfalls, review heuristics), and
[references/go-testing.md](references/go-testing.md) only when the user opts in
or the task needs that depth.

## Pitfall hotspots

Prioritize these Go-specific bug patterns during implementation and review:

- `:=` shadowing and narrow scope in `if` / `for` / `switch`
- typed `nil` inside interfaces, nil receivers, pointer vs value method sets
- `for range` capture, taking the address of iteration variables, and closures
  or goroutines closing over loop state
- slice aliasing, shared backing arrays, `append` capacity surprises, map
  iteration order, and byte-vs-rune string assumptions
- goroutine leaks, channel ownership/close rules, deadlocks, and shared-state
  races
- hidden `init()` side effects, package-level initialization order, and import
  cycles

## When to use

- User has a Go repo, diff, file, stack trace, or code snippet and wants
  code-focused help rather than general language discussion
- Go repo mentions `go.mod`, `go test`, `gofmt`, `golangci-lint`, Gin, Echo,
  GORM, `database/sql`, Resty, middleware, handlers, repositories, or
  goroutines
- User wants to implement, fix, refactor, explain, test, or review Go while
  preserving idiomatic APIs and minimum diff
- User mentions race conditions, deadlocks, nil interface weirdness, range
  capture bugs, slice/map surprises, or other "why does Go do this" behavior
- Repo has `AGENTS.md`, PKB docs, `man/`, or conventions that should steer the
  change
- Change touches HTTP boundaries, persistence, auth, concurrency, or other
  areas where correctness matters more than style alone

## When not to use

- Non-Go primary work
- Main task is deploy, infra, Jira/GitLab workflow, or product-specific ops
- User explicitly wants a non-idiomatic experiment and accepts the tradeoff
- Task is general Go education, language history, ecosystem comparison, or
  blog/tutorial writing without concrete code work
- Task is mostly architecture/design doc generation rather than code or code
  review

## Contract

- **scope_in**: Go code and config in repos that use `go.mod`;
  handler/service/repository flows; Gin/Echo HTTP layers; GORM or
  `database/sql`; Resty-based HTTP clients; goroutines, channels, mutexes, and
  worker pools; nil/interface/pointer semantics; slice, map, string, switch,
  closure, and package-init pitfalls; unit tests, table-driven tests, mocks,
  code review, and explanation of Go behavior; reading `AGENTS.md` or `man/`
  conventions when present
- **scope_out**: Deployment runbooks; Terraform/Kubernetes work; non-Go primary
  code; forcing a framework switch (for example Gin to Echo, GORM to sqlc)
  unless the user asks; deep product-specific semantics better owned by a
  repo-specific skill; general Go history/comparison/tutorial content without a
  concrete code artifact
- **Preconditions**: Repo, diff, or snippet is available; Go version is read
  from `go.mod` or CI rather than assumed; existing test or lint entry points
  are discovered before new commands are invented
- **Postconditions**: Recommendations keep `context.Context` explicit, errors
  handled and wrapped, exported items documented when created, request
  boundaries validated, secrets excluded from logs/examples, and verification
  states exactly what did and did not run

## Execution

### Phase 0: Detect context

- **Entry**: User asks to implement, fix, review, explain, or test Go
- **Steps**:
  1. Read `go.mod`, `Makefile`, `justfile`, `Taskfile.yml`, or CI config to
     detect Go version and project commands
  2. If `AGENTS.md`, `man/`, or repo conventions exist, skim them for danger
     zones, API stability rules, and testing expectations
  3. Identify the active stack: web framework, data layer, logger, test libs,
     and whether Resty/concurrency patterns are in play
- **Exit**: Tooling path and project conventions are grounded in repo evidence
- **On fail**: Name the missing file or gap and continue from idiomatic Go
  defaults, clearly labeled as fallback guidance

### Phase 1: Classify the task

- **Entry**: Phase 0 complete
- **Steps**:
  1. Pick one primary mode:
     - **Implement**: write or modify Go code
     - **Review**: assess a diff/file/snippet for correctness, risk, and
       missing tests
     - **Test**: add or improve unit tests
     - **Explain**: describe code structure, flow, and tradeoffs
     - **Tooling**: adjust formatting, lint, or test wiring
  2. Keep the task in one mode unless the user clearly asked for both code and
     review
- **Exit**: One primary mode is chosen
- **On fail**: Ask one short question combining scope and mode, for example:
  `Do you want me to implement the change, review the diff, or write tests for it?`

### Phase 2: Apply Go defaults and pitfall checks

- **Entry**: Phase 1 complete
- **Steps**:
  1. **Core Go shape**
     - Keep `context.Context` as the first parameter for request-scoped or
       blocking work
     - Return `error` last; wrap with `%w`; do not ignore errors without reason
     - Use idiomatic naming: no `I` prefix on interfaces, no `Get` prefix for
       simple getters, short consistent receiver names, lowercase singular
       package names
     - Add godoc comments for new exported types/functions
  2. **Pitfall checklist**
     - Watch for `:=` shadowing, especially `err` or state variables inside
       `if`, `for`, and `switch`
     - Treat interfaces, pointers, and receivers carefully: a typed `nil`
       inside an interface is not the same as a nil interface; pointer receiver
       method sets differ from value receiver method sets; nil receiver methods
       may or may not panic depending on the method body
     - For loops, closures, and goroutines, check whether iteration state is
       captured safely; prefer explicit parameters or index-based access when
       taking addresses or launching work per item
     - For slices, maps, and strings, check shared backing arrays, `append`
       reallocation effects, random map iteration order, delete-during-iterate
       behavior, and byte-vs-rune assumptions
     - For channels and goroutines, define ownership, close rules, cancellation,
       wait paths, and timeout behavior; nil channels block forever and sends to
       closed channels panic
     - For package setup, avoid hidden `init()` work and fragile package-level
       variable dependencies unless the repo already depends on them
  3. **Implement**
     - Prefer small, reviewable diffs over broad cleanup
     - Follow handler/service/repository boundaries already present in the repo
     - Validate input at boundaries and keep internal domain structs separate
       from request/response DTOs when HTTP APIs are involved
     - Prefer explicit control flow over clever `fallthrough`, label jumps, or
       hidden side effects unless the surrounding code already uses them well
  4. **Web/API**
     - Version routes explicitly, use middleware for cross-cutting concerns,
       map errors to consistent HTTP responses, and propagate
       `c.Request.Context()`
     - Include health/readiness or graceful shutdown changes only when the
       surrounding code already uses those patterns or the user asks
  5. **Data layer**
     - Use parameterized queries; never build SQL with user input
     - Handle `gorm.ErrRecordNotFound` distinctly when relevant
     - Use transactions for multi-step mutations, pagination for lists, and
       `Preload`/`Joins` to avoid N+1 queries
  6. **Resty/client code**
     - Treat `resty.Client` as long-lived, set explicit timeouts, propagate
       context, retry only idempotent operations, and check non-2xx responses
  7. **Concurrency**
     - Give goroutines a lifecycle, cancellation path, and wait mechanism
     - Only senders close channels; size buffers intentionally; use `select`
       with `ctx.Done()` for long-running flows
     - Protect shared state with `sync.Mutex`/`sync.RWMutex` or justified
       atomics; unlock with `defer` immediately after locking
     - Use `sync.WaitGroup` or equivalent joining instead of sleep-based
       "waiting"
  8. **Security**
     - Never log secrets, tokens, raw JWTs, or sensitive PII
     - Use `crypto/rand` for security-sensitive randomness
     - Avoid `os/exec` with user input; validate uploads, params, regex, and
       pagination inputs
  9. **Review**
     - Lead with behavioral bugs, race/leak risks, API compatibility, security
       issues, and missing tests before style nits
     - Use [go-concurrency-review.md](references/go-concurrency-review.md) as
       the semantic checklist when goroutines, shared state, HTTP handlers, or
       DB access are involved
     - Also scan for language pitfalls before concluding "looks fine":
       shadowing, typed nil, receiver/method-set mismatch, range capture,
       slice aliasing, map order assumptions, and package init surprises
- **Exit**: Code or review notes align with idiomatic Go plus the repo's actual
  stack
- **On fail**: If the repo's conventions conflict with these defaults, follow
  the repo and call out the exception explicitly

### Phase 3: Test and verify

- **Entry**: Code change exists or the user asked for test/review guidance
- **Steps**:
  1. Prefer repo commands first: `just test`, `make test`, `go test ./...`,
     `golangci-lint run`, `gofmt -w`
  2. For targeted behavior changes, run nearby package tests before the whole
     tree when that materially speeds feedback
  3. Use `go test -race ./...` when shared state, goroutines, channels,
     background workers, or caches changed
  4. For security-sensitive or dependency-sensitive work, consider
     `go mod verify` and `govulncheck ./...` when available
- **Exit**: Verification section states exactly which commands ran, what passed
  or failed, and what was not run
- **On fail**: Report failing commands or environment gaps plainly; do not imply
  green status without evidence

### Phase 4: Shape the response

- **Entry**: Draft code, review findings, or guidance is ready
- **Steps**:
  1. Use this response shape for non-trivial work:
     - `summary`: what changed or what was reviewed
     - `assumptions`: missing repo context or decisions that affected the answer
     - `changes` or `findings`: file-level or risk-level substance
     - `risks`: compatibility, security, performance, or test gaps
     - `verification`: what actually ran
     - `next_step`: only if there is a clear follow-up
  2. For review tasks, present findings first, ordered by severity
  3. For explain tasks, cover purpose, key components, flow, dependencies,
     concurrency, and important risks
- **Exit**: Response is evidence-first and easy to scan
- **On fail**: Fall back to a shorter response, but still state assumptions and
  verification limits

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| No secrets in output | No real tokens, credentials, raw JWTs, or sensitive PII in code blocks, logs, or examples | Redact and replace with placeholders |
| Idiomatic Go API shape | New blocking/request-scoped functions use `context.Context` appropriately and return `error` last | Rework signature or explain why the repo differs |
| Error handling present | Errors are checked, wrapped, or intentionally propagated; no silent `_` discard without reason | Add handling or justify the discard |
| Pitfall-sensitive semantics | No newly introduced typed-nil confusion, loop capture bug, channel misuse, or obvious shadowing hazard in changed code | Rework the code or call out the remaining risk explicitly |
| Boundary safety | Handler/data/client code validates inputs, uses parameterized queries, and avoids unsafe logging/command execution | Fix the unsafe path before delivery |
| Evidence-first closeout | Verification says what actually ran | Remove unsupported `done/passing` claims |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Tests tied to change | Behavior changes mention a test file or test case | Note the coverage gap |
| Race awareness | Concurrency work ran `-race` or explicitly notes the missing check | Call out the residual risk |
| Pitfall coverage | Reviews or explanations mention the relevant Go pitfall class when semantics are the real risk | Call out the unchecked pitfall category |
| Exported docs | New exported items have godoc comments | Suggest or add the comments |
| HTTP/data shape | DTOs, errors, pagination, and transaction boundaries are consistent when relevant | Note the mismatch |
| Review depth | Reviews cover behavior and correctness before naming/style | Reorder and elevate the real risks |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Code compiled but used the wrong `err` / state value | `:=` shadowed an outer variable inside a nested scope | Reuse `=` when appropriate or rename the inner variable to make scope explicit |
| `if v == nil` failed unexpectedly | Returned or stored a typed `nil` inside an interface | Check the concrete type path, avoid returning typed nil interfaces, and document nil semantics |
| Goroutines or closures all saw the wrong loop value | Iteration state was captured unsafely | Pass the value as a parameter or take the address from the indexed source element |
| Editing one slice unexpectedly changed another | Two slices shared the same backing array | Copy before mutation when aliasing is not intended; reason about `len` vs `cap` before `append` |
| Behavior depended on map iteration order or delete-while-ranging quirks | Treated map traversal as stable and mutation-safe | Sort keys first when order matters; stage deletes outside the loop when clarity matters |
| String indexing broke non-ASCII text | Treated bytes as runes | Use `for range`, `[]rune`, or `utf8` helpers when character semantics matter |
| Generated `GetX` getters and `IService` interfaces everywhere | Imported non-Go naming habits | Re-read the naming rules; keep interfaces small and names idiomatic |
| New Resty client created per request | Treated client like disposable request state | Reuse a long-lived client per service or config profile |
| Retried POST/command calls blindly | Missed idempotency boundary | Restrict retries to safe operations or add idempotency handling |
| Logged tokens or raw response bodies | Debugging convenience overrode security | Redact, disable production debug, and log metadata only |
| Review missed the real bug | Focused on style before races, leaks, typed nil, aliasing, or error flow | Use the concurrency and pitfall checklist first |
| Claimed tests passed without running them | No evidence-first verification step | State exactly which commands ran and what did not |
| Startup behavior was surprising or flaky | Relied on `init()` side effects or package-level initialization order | Move setup into explicit constructors or bootstrapping code when possible |

### Boundary examples

- **User**: `add a Gin handler for user lookup` -> implement
  handler/service/repo flow, validate params, map errors, and keep DTOs
  separate from entities
- **User**: `review this goroutine fan-out code` -> focus first on
  cancellation, loop variable capture, channel ownership, and `-race` risk
- **User**: `why is this interface nil check failing` -> inspect typed `nil`,
  receiver types, and whether an interface holds a nil concrete pointer
- **User**: `why did changing this slice mutate another value` -> inspect shared
  backing arrays, reslicing, and `append` capacity behavior before blaming
  concurrency
- **User**: `write tests for this service` -> add table-driven tests, mock
  external interfaces, cover happy path, error path, and edge cases
- **User**: `explain this Go file` -> use the explain shape: purpose, key
  components, flow, dependencies, concurrency, and security/performance notes,
  plus any likely Go-specific footguns
- **User**: `convert the whole repo from GORM to sqlc` -> out of scope unless
  they explicitly ask for a migration plan or implementation

### Improvement triggers

- Repo conventions consistently prefer a different HTTP/data stack (for example
  `chi`, `sqlc`, `ent`) -> expand references and narrow the default description
- Users often ask for benchmarking, profiling, or memory analysis -> add a
  performance-focused reference
- The upstream Go rules or commands change materially -> refresh the
  progressive-detail references and hard-gate language

## Additional resources

- Web/API/data/Resty/security defaults:
  [references/go-service-stack.md](references/go-service-stack.md)
- Concurrency pitfalls and review heuristics:
  [references/go-concurrency-review.md](references/go-concurrency-review.md)
- Unit test patterns and checklists:
  [references/go-testing.md](references/go-testing.md)
