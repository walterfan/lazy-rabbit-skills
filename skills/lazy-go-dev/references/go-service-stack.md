# Go Service Stack

Concise defaults for Go services derived from the upstream Go rules and
commands this skill was built from.

## Core shape

- Keep packages lowercase and singular
- Use PascalCase for exported names and camelCase for unexported ones
- Do not prefix interfaces with `I`
- Avoid `Get` for simple getters; prefer `Name()` over `GetName()`
- Add godoc comments for exported items
- Keep `context.Context` first for request-scoped or blocking work
- Return `error` last and wrap with `%w`

## Common project layout

- `api/` or `handlers/` for HTTP handlers
- `service/` or `services/` for business logic
- `repository/` or `repo/` for persistence
- `models/` or `domain/` for entities and domain types
- `internal/` or `pkg/` for helper packages

Follow the repo's existing layout before inventing a new one.

## Web and API defaults

- Version routes explicitly, for example `/api/v1`
- Use middleware for cross-cutting concerns: recovery, CORS, request ID,
  logging, auth, authz, rate limiting
- Validate request input at the handler boundary
- Keep request and response DTOs separate from internal entities when the repo
  already does that
- Map errors to consistent HTTP responses; do not leak internal errors directly
- Propagate `c.Request.Context()` through handler -> service -> repository
- Prefer health/readiness endpoints and graceful shutdown in production services

## Data and persistence

- Use parameterized queries only; never interpolate user input into SQL
- In GORM, prefer `Where("field = ?", value)` over `fmt.Sprintf(...)`
- Treat `gorm.ErrRecordNotFound` separately when not-found is meaningful
- Use transactions for multi-step mutations that must succeed or fail together
- Add pagination to list endpoints and avoid loading large tables by default
- Prevent N+1 patterns with `Preload` or `Joins`
- Configure connection pools intentionally for production services
- Mark sensitive fields with `json:"-"` when they must never be serialized

## Resty client defaults

- Reuse one long-lived `resty.Client` per target service or config profile
- Always set explicit timeouts
- Always propagate context with `SetContext(ctx)`
- Retry only idempotent operations or use explicit idempotency controls
- Check `resp.IsError()` because non-2xx is not an error automatically
- Use hooks for auth, tracing, and metrics; avoid hiding business logic there
- Never leave `SetDebug(true)` on in production paths

## Security defaults

- Never log secrets, passwords, tokens, raw JWTs, or sensitive PII
- Never include credentials in error messages
- Use `crypto/rand` for security-sensitive randomness
- Validate params, pagination bounds, regex, file uploads, and redirect targets
- Avoid `os/exec` with user input; use allowlists when execution is unavoidable
- Use HTTPS in production and validate JWT claims/signatures properly
- Consider `go mod verify` and `govulncheck ./...` for dependency-sensitive work

## Commands to prefer

- Format: `gofmt -w`
- Test: `go test ./...`
- Race check: `go test -race ./...`
- Vulnerability scan: `govulncheck ./...`

If the repo already has `just`, `make`, or CI recipes, prefer those entry
points over raw commands.
