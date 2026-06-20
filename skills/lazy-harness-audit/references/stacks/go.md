# Go Stack Checklist

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

**Markers**: `go.mod`, `go.sum`, `cmd/`, `internal/`, `pkg/`, `Makefile` targets, `.golangci.yml`.

**Verification surfaces** (rubric §2):
- `go test ./...`, `go test -race ./...`, `go vet ./...`, `gofmt -l`, `goimports -l`.
- `golangci-lint run`, `staticcheck`.
- `go build ./...` and module hygiene: `go mod tidy -check` or equivalent.

**Architecture fitness** (rubric §3):
- `internal/` package boundaries enforced by the compiler.
- Custom analyzers (`go/analysis`), `depguard`, `forbidigo` rules in `golangci-lint`.

**Behavior harness** (rubric §4):
- `testdata/` fixtures, golden files, table-driven tests, `httptest`-based integration tests.
- `go test -race` and `-count=1` discipline documented for agents.

**Safety tooling** (rubric §5):
- `govulncheck`, `gosec`, secret scanning.
- `GOFLAGS`, build tag boundaries for production vs test code.

**Priority notes**:
- Reward repos that wire `-race` and `govulncheck` into CI; their absence is a common gap.
