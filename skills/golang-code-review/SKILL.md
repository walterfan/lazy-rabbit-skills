---
name: golang-code-review
description: >-
  Review local Go code — files, directories, or a git diff — for correctness,
  concurrency safety, security, performance, idiomatic style, or testing, one
  focus per round. Grounded in "100 Go Mistakes and How to Avoid Them" and a
  curated common-traps guide. Use when a user wants a Go code review, wants to
  check Go changes before committing, or mentions Go races, goroutine leaks,
  typed nil, slice aliasing, SQL safety, or common Go pitfalls. Works entirely
  on the local filesystem and never calls GitLab or GitHub APIs.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - go
  - golang
  - code-review
  - concurrency
  - security
  - testing
  - 100-go-mistakes
category: dev-tools
use_cases:
  - "review local Go changes before committing (git diff)"
  - "review specific Go files or a package directory"
  - "run a focused concurrency/security/performance review round"
  - "catch common Go mistakes from the 100 Go Mistakes catalog"
platforms: [claude-code, cursor, codex]
visibility: public
license: Apache-2.0
compatibility: Python 3.8+ and git. No network access or VCS server tokens required.
allowed-tools: Bash(python3:*) Bash(git:*) Read Write Grep Glob
---

# golang-code-review

Focused **local Go code review**. This skill reviews Go code that already exists
on your machine — a set of files, a package directory, or your working-tree
`git diff` — and produces one severity-ordered review pass per run. It is a
review companion to `lazy-go-dev`; use `lazy-go-dev` to write or fix Go, use this
to review it.

It is **local-only**: it never fetches merge requests or pull requests and needs
no GitLab/GitHub token. For GitLab MR review over the API, use `gitlab-mr-review`
instead.

The review criteria are grounded in *100 Go Mistakes and How to Avoid Them*
(Teiva Harsanyi) plus a 15-point common-traps field guide. Reviews cite the
concrete mistake number so the author can look it up.

## Progressive detail

- [references/review-checklist.md](references/review-checklist.md) — fast,
  focus-scoped checklist and finding format
- [references/go-mistakes-catalog.md](references/go-mistakes-catalog.md) — full
  *100 Go Mistakes* catalog by chapter, with a symptom -> mistake triage map
- [references/go-common-traps.md](references/go-common-traps.md) — 15 code-level
  traps with fixes, cross-referenced to the book

## When to use

- User has local Go code (files, a directory, or uncommitted changes) and wants
  a review rather than an implementation
- User wants a pre-commit sanity check on a Go diff
- User asks for a specific angle: correctness, concurrency/races, security,
  performance, idiomatic style, or test coverage
- User mentions Go pitfalls: typed nil, loop-variable capture, slice aliasing,
  goroutine leaks, SQL safety, error wrapping

## When not to use

- Reviewing a remote GitLab MR or GitHub PR by URL -> use `gitlab-mr-review`
- Writing, fixing, or refactoring Go -> use `lazy-go-dev`
- Non-Go code
- Design-doc or architecture review rather than code review

## Contract

- **scope_in**: Review local Go source obtained from file/dir paths or
  `git diff`/`git diff --cached`; one review focus per round; findings grounded
  in the shown code and cited to *100 Go Mistakes* where applicable.
- **scope_out**: GitLab/GitHub API calls; writing or fixing code; multi-focus
  "review everything" in a single pass; non-Go review; posting comments to any
  server.
- **Preconditions**: `python3` and `git` available; the target Go code is on the
  local filesystem; for `--diff`/`--staged` the repo has a valid `HEAD`.
- **Postconditions**: One coherent, severity-ordered review pass for the chosen
  focus; scope (included/omitted files) stated; no invented findings; any budget
  trimming noted.

## Execution

### Phase 1: Resolve the review target and focus

- **Entry**: User asks to review Go code.
- **Steps**:
  1. Determine the source:
     - working-tree changes -> `--diff [REV]` (default `HEAD`)
     - staged changes -> `--staged`
     - specific code -> one or more file/dir `paths`
  2. Pick exactly one focus for this round. Default to `correctness` if the user
     does not specify. Supported: `correctness`, `concurrency`, `security`,
     `performance`, `idiomatic`, `testing`.
- **Exit**: One resolvable target and one explicit focus.
- **On fail**: Ask for the missing path/mode or focus instead of guessing.

### Phase 2: Render the review prompt

- **Entry**: Phase 1 complete.
- **Steps**:
  1. Run the collector to build the focused prompt (see Workflow).
  2. Read the rendered prompt, which embeds the code/diff, repo context
     (module, Go version, frameworks), and the focus-specific rubric.
  3. Note the detected Go version — it changes loop-variable-capture reasoning
     (pre-1.22 shares the loop variable; 1.22+ scopes it per iteration).
- **Exit**: A rendered prompt (or code/context section) is available.
- **On fail**: Apply the error table below; if unmapped, surface stderr and stop.

### Phase 3: Deliver the focused review

- **Entry**: Phase 2 complete.
- **Steps**:
  1. Walk the relevant section of
     [references/review-checklist.md](references/review-checklist.md) and the
     matching chapters of
     [references/go-mistakes-catalog.md](references/go-mistakes-catalog.md).
  2. Produce findings only for the chosen focus, ordered by severity.
  3. Cite the concrete mistake number (e.g. "typed nil in interface, #48").
  4. If the user wants another angle, run a separate round with a new focus.
- **Exit**: One coherent review pass, no mixed scopes unless explicitly asked.
- **On fail**: Report insufficient evidence rather than speculating.

## Workflow

Review uncommitted working-tree changes (default focus = correctness):

```bash
python3 skills/golang-code-review/scripts/collect_target.py --diff \
  --project-root /absolute/path/to/go-project
```

Review staged changes with a concurrency focus:

```bash
python3 skills/golang-code-review/scripts/collect_target.py --staged \
  --focus concurrency \
  --project-root /absolute/path/to/go-project
```

Review specific files or a package directory:

```bash
python3 skills/golang-code-review/scripts/collect_target.py \
  internal/service/user.go internal/repo \
  --focus security \
  --project-root /absolute/path/to/go-project
```

Compare against a base branch/commit:

```bash
python3 skills/golang-code-review/scripts/collect_target.py --diff origin/main \
  --focus performance \
  --project-root /absolute/path/to/go-project
```

Run another angle as a separate round instead of asking for a broad review:

```bash
python3 skills/golang-code-review/scripts/collect_target.py --diff \
  --focus idiomatic --project-root /absolute/path/to/go-project
```

Use a fully custom one-aspect rubric:

```bash
python3 skills/golang-code-review/scripts/collect_target.py --diff \
  --prompt-file /absolute/path/to/custom-review.md
```

Then read the rendered prompt and produce findings only for that focus. Do not
mix correctness, concurrency, security, performance, idiomatic, and testing
feedback in the same round unless the user explicitly asks for a combined review.

### Error handling

| Error pattern | Cause | Action |
|---------------|-------|--------|
| `No Go changes found` | `--diff`/`--staged` found no `.go` changes | Ask user to stage/commit changes or pass file paths |
| `No .go files found` | Paths had no Go files | Ask for correct paths or a directory containing Go code |
| `unsupported focus` | Bad `--focus` value | Use one of correctness/concurrency/security/performance/idiomatic/testing |
| `git command failed` | Not a git repo or bad revision | Pass `--project-root` to the repo, or use file paths instead of `--diff` |
| `does not have a valid HEAD` | No commits yet | Use file paths, or make an initial commit |

## Script options

`scripts/collect_target.py`:

- Modes: `--diff [REV]` (default `HEAD`), `--staged`, or positional `paths`
- `--focus` — correctness | concurrency | security | performance | idiomatic |
  testing (aliases like `race`, `perf`, `style`, `tests` are accepted)
- `--prompt-file` — custom markdown template (overrides `--focus`)
- `--project-root` — repo root for module/framework/Go-version context
- `--include-tests` — include `*_test.go` when scanning directories
- `--max-files` (default 25), `--max-chars` (default 60000) — review budget
- `--format` — `prompt` (default), `code`, or `context`
- `--output-file` — write the result to a file instead of stdout

The collector auto-detects the module path, Go version, and common frameworks
(Gin, Echo, chi, GORM, sqlx, Resty, gRPC, Redis, Kafka, testify) from `go.mod`,
and skips `vendor/`, `node_modules/`, `.git/`, and `testdata/`.

Custom prompt files may use these placeholders: `{{language}}`, `{{code}}`,
`{{review_focus}}`, `{{review_scope}}`, `{{project_context}}`, `{{go_version}}`,
`{{project_frameworks}}`.

## Built-in review focuses

- **correctness** — logic errors, edge cases, typed nil, shadowing, slice
  aliasing, map order, error handling, `http.Error` return.
- **concurrency** — goroutine leaks, races, channel/close rules, `WaitGroup`
  misuse, context cancellation, timer leaks, `-race` awareness.
- **security** — SQL/command injection, secret logging, input validation, weak
  randomness, authz, HTTP timeouts, JWT/TLS validation.
- **performance** — prealloc, `strings.Builder`, conversions, backing-array
  retention, N+1 queries, escape analysis (evidence-first).
- **idiomatic** — interface pollution, naming, `context`/`error` shape, error
  wrapping, `init()` misuse, receiver consistency, package boundaries, godoc.
- **testing** — table-driven tests, error/edge coverage, `-race`, flaky
  `time.Sleep`, clock injection, `httptest`, benchmarks, mocking.

Run these as separate rounds. The skill is biased toward depth over breadth.

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| Local-only | No GitLab/GitHub API call; no token required | Route API MR review to `gitlab-mr-review` |
| Single focus | Output stays within one focus unless a combined pass was requested | Split into separate rounds |
| Evidence-based | Every finding cites shown code | Report insufficient evidence instead of speculating |
| No invented findings | Clean areas are stated as clean, not padded | Remove speculative findings |
| Go-version aware | Loop-capture findings account for the detected Go version | Recheck against `go.mod` before flagging |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Mistake citations | Findings reference the matching *100 Go Mistakes* number when applicable | Add the number or note it is not in the catalog |
| Budget transparency | Note when `--max-files`/`--max-chars` trimmed coverage | State what was omitted |
| Race awareness | Concurrency reviews mention `go test -race` | Call out the residual risk |
| Severity ordering | Findings ordered blocker -> minor | Reorder before delivery |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Review mixes many concerns | Ran all focuses in one pass | Run one focus per round |
| Flagged loop-capture bug that is not real | Ignored Go 1.22+ per-iteration scoping | Read `go_version` from project context first |
| Findings not grounded in code | Speculated beyond the payload | Restrict to shown code; note omitted files |
| "No token" or API errors | Tried to use a remote MR flow | This skill is local-only; use `gitlab-mr-review` for API MRs |
| Empty review | Diff had no Go changes | Stage changes or pass file paths |

### Boundary examples

- **User**: `review my Go changes before I commit` -> `--diff`, correctness first
- **User**: `check this handler for races` -> `--focus concurrency` on the file
- **User**: `is this repo's SQL safe?` -> `--focus security` on the repo/dir
- **User**: `review this GitLab MR <url>` -> out of scope; use `gitlab-mr-review`
- **User**: `write this function for me` -> out of scope; use `lazy-go-dev`

### Improvement triggers

- New Go pitfalls or updated mistake numbering -> refresh
  `references/go-mistakes-catalog.md`
- A recurring focus need not covered by the six built-ins -> add a prompt
  template under `assets/prompts/` and register it in `collect_target.py`
