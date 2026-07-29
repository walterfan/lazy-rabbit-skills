---
name: python-code-review
description: >-
  Review local Python code — files, directories, or a git diff — for the
  mistakes Python developers most commonly ship, one focus per round:
  correctness, pitfalls (the 10 classic traps), concurrency (GIL/async),
  performance, security, typing-tooling, pydantic, or testing. Grounded in
  "Python 编程的常见陷阱与奇巧淫技" and "Pydantic 用法与最佳实践", it catches
  mutable default args, closure late binding, is-vs-==, shallow copy, list
  multiplication aliasing, dict-mutation-during-iteration, string += in loops,
  float money, over-broad except, and GIL/threading misuse; it checks
  typing/tooling posture (ruff/flake8/mypy/pyright/black/isort/pytest) and
  Pydantic v2 boundary validation. It asks or detects the target Python version
  and only suggests version-appropriate syntax. Use when a user wants a Python
  code review, wants to check Python changes before committing, wants to review
  Pydantic models, or mentions Python traps/gotchas, type hints, mypy, asyncio,
  the GIL, or boundary validation. Works entirely on the local filesystem and
  never calls GitLab or GitHub APIs.
version: 0.1.0
author: walterfan@ustc.edu
source: "fanyamin.com — Python coding traps & Pydantic best practices"
tags:
  - python
  - code-review
  - pitfalls
  - pydantic
  - typing
  - mypy
  - asyncio
  - gil
  - performance
  - security
category: dev-tools
use_cases:
  - "review local Python changes before committing (git diff)"
  - "sweep code for the 10 classic Python traps"
  - "review Pydantic v2 boundary validation and models"
  - "check typing/tooling posture (ruff/mypy/pyright/black/pytest)"
  - "run a focused concurrency (GIL/async) / performance / security round"
platforms: [claude-code, cursor, codex]
visibility: public
license: Apache-2.0
compatibility: Python 3.8+ and git. No network access or VCS server tokens required.
allowed-tools: Bash(python3:*) Bash(git:*) Read Write Grep Glob
---

# python-code-review

Focused **local Python code review**. This skill reviews Python code that
already exists on your machine — a set of files, a directory, or your
working-tree `git diff` — and produces one severity-ordered review pass per run.
It is the review companion to `lazy-python-dev`; use `lazy-python-dev` to write
or fix Python, use this to review it.

It is **local-only**: it never fetches merge requests or pull requests and needs
no GitLab/GitHub token. For GitLab MR review over the API, use `gitlab-mr-review`
instead.

The review criteria are grounded in two field guides — the **10 classic Python
traps** (mutable defaults, closure late binding, `is`/`==`, shallow copy, list
multiplication, dict mutation while iterating, string `+=`, float money, broad
`except`, GIL/threads) and **Pydantic v2 best practices** (validate all external
input, strict key fields, `extra="forbid"`, pure validators, `BaseSettings`,
output models, `TypeAdapter`, schema-as-contract). It also enforces a
static-checkability + tooling posture (ruff/flake8, mypy/pyright, black/isort,
pytest, one `make check` gate). Every finding cites the concrete trap number or
best-practice.

## Progressive detail

- [references/review-checklist.md](references/review-checklist.md) — fast,
  focus-scoped checklist and finding format
- [references/python-pitfalls-catalog.md](references/python-pitfalls-catalog.md) —
  the 10 traps, a symptom->trap triage map, idioms, and a performance cheat sheet
- [references/pydantic-best-practices.md](references/pydantic-best-practices.md) —
  Pydantic v2 boundary-validation practices, common traps, and v1->v2 migration

## When to use

- User has local Python code (files, a directory, or uncommitted changes) and
  wants a review rather than an implementation
- User wants a pre-commit sanity check on a Python diff
- User asks for a specific angle: correctness, pitfalls, concurrency,
  performance, security, typing-tooling, pydantic, or testing
- User mentions Python pitfalls (mutable defaults, closures, `is` vs `==`,
  shallow copy, GIL), type hints/mypy/pyright, asyncio, or Pydantic models

## When not to use

- Reviewing a remote GitLab MR or GitHub PR by URL -> use `gitlab-mr-review`
- Writing, fixing, or refactoring Python -> use `lazy-python-dev`
- Non-Python code (Go -> `golang-code-review`, C++ -> `cpp-code-review`)
- Design-doc or architecture review rather than code review

## Contract

- **scope_in**: Review local Python source obtained from file/dir paths or
  `git diff`/`git diff --cached`; one review focus per round; findings grounded
  in the shown code and cited to the trap/best-practice where applicable.
- **scope_out**: GitLab/GitHub API calls; writing or fixing code; multi-focus
  "review everything" in a single pass; non-Python review; posting comments to
  any server.
- **Preconditions**: `python3` and `git` available; the target Python code is on
  the local filesystem; for `--diff`/`--staged` the repo has a valid `HEAD`.
- **Postconditions**: One coherent, severity-ordered review pass for the chosen
  focus; scope (included/omitted files) stated; no invented findings; any budget
  trimming noted.

## Execution

### Phase 1: Resolve the review target, focus, and Python version

- **Entry**: User asks to review Python code.
- **Steps**:
  1. Determine the source:
     - working-tree changes -> `--diff [REV]` (default `HEAD`)
     - staged changes -> `--staged`
     - specific code -> one or more file/dir `paths`
  2. Pick exactly one focus for this round. Default to `correctness` if the user
     does not specify. Supported: `correctness`, `pitfalls`, `concurrency`,
     `performance`, `security`, `typing-tooling`, `pydantic`, `testing`.
  3. Establish the target **Python version**. Run the collector once and read the
     `Python version` line in the rendered project context. If it says `unknown`
     (no `requires-python`/`target-version`/`python_version` in the manifests),
     **ask the user which version they target** (e.g. 3.9 / 3.10 / 3.11 / 3.12)
     and re-run with `--py 3.NN`. The version gates syntax suggestions
     (walrus `:=`, `dict |`, `match`/`case`, `X | None`, builtins-as-generics).
  4. If the collector reports Pydantic usage, offer a `--focus pydantic` round.
     If it reports `MIXED v1/v2 (risk)`, flag it and confirm the version.
- **Exit**: One resolvable target, one explicit focus, and a known Python version
  (or an explicit ask for it).
- **On fail**: Ask for the missing path/mode, focus, or Python version instead of
  guessing.

### Phase 2: Render the review prompt

- **Entry**: Phase 1 complete.
- **Steps**:
  1. Run the collector to build the focused prompt (see Workflow).
  2. Read the rendered prompt, which embeds the code/diff, repo context
     (Python version, tooling, libraries, Pydantic usage), and the
     focus-specific rubric.
  3. Never suggest syntax newer than the target Python version. If the version is
     `unknown`, ask the user before making version-specific recommendations.
- **Exit**: A rendered prompt (or code/context section) is available.
- **On fail**: Apply the error table below; if unmapped, surface stderr and stop.

### Phase 3: Deliver the focused review

- **Entry**: Phase 2 complete.
- **Steps**:
  1. Walk the relevant section of
     [references/review-checklist.md](references/review-checklist.md) and the
     matching entries in
     [references/python-pitfalls-catalog.md](references/python-pitfalls-catalog.md)
     (and [references/pydantic-best-practices.md](references/pydantic-best-practices.md)
     for the `pydantic` focus).
  2. Regardless of focus, do a quick sweep for the highest-severity traps
     (mutable defaults, dict mutation while iterating, float money, broad
     `except`, GIL races) since they cause real production bugs.
  3. Produce findings only for the chosen focus, ordered by severity.
  4. Cite the concrete trap number (e.g. "mutable default arg, Trap 1") or
     Pydantic best-practice.
  5. Note which tool would catch it when relevant (mypy/pyright, ruff, black).
  6. If the user wants another angle, run a separate round with a new focus.
- **Exit**: One coherent review pass, no mixed scopes unless explicitly asked.
- **On fail**: Report insufficient evidence rather than speculating.

## Workflow

Review uncommitted working-tree changes (default focus = correctness):

```bash
python3 skills/python-code-review/scripts/collect_target.py --diff \
  --project-root /absolute/path/to/py-project
```

Sweep the classic traps on staged changes:

```bash
python3 skills/python-code-review/scripts/collect_target.py --staged \
  --focus pitfalls \
  --project-root /absolute/path/to/py-project
```

Review specific files or a package with a concurrency focus:

```bash
python3 skills/python-code-review/scripts/collect_target.py \
  app/worker.py app/tasks \
  --focus concurrency \
  --project-root /absolute/path/to/py-project
```

Pydantic boundary-validation review:

```bash
python3 skills/python-code-review/scripts/collect_target.py --diff \
  --focus pydantic \
  --project-root /absolute/path/to/py-project
```

Typing & tooling pass — pass the Python version when it cannot be detected:

```bash
python3 skills/python-code-review/scripts/collect_target.py --diff \
  --focus typing-tooling --py 3.11 \
  --project-root /absolute/path/to/py-project
```

Compare against a base branch/commit for a performance pass:

```bash
python3 skills/python-code-review/scripts/collect_target.py --diff origin/main \
  --focus performance \
  --project-root /absolute/path/to/py-project
```

Use a fully custom one-aspect rubric:

```bash
python3 skills/python-code-review/scripts/collect_target.py --diff \
  --prompt-file /absolute/path/to/custom-review.md
```

Then read the rendered prompt and produce findings only for that focus. Do not
mix focuses in the same round unless the user explicitly asks for a combined
review.

### Error handling

| Error pattern | Cause | Action |
|---------------|-------|--------|
| `No Python changes found` | `--diff`/`--staged` found no `.py` changes | Ask user to stage/commit changes or pass file paths |
| `No Python files found` | Paths had no Python files | Ask for correct paths or a directory containing Python code |
| `unsupported focus` | Bad `--focus` value | Use one of correctness/pitfalls/concurrency/performance/security/typing-tooling/pydantic/testing |
| `git command failed` | Not a git repo or bad revision | Pass `--project-root` to the repo, or use file paths instead of `--diff` |
| `does not have a valid HEAD` | No commits yet | Use file paths, or make an initial commit |

## Script options

`scripts/collect_target.py`:

- Modes: `--diff [REV]` (default `HEAD`), `--staged`, or positional `paths`
- `--focus` — correctness | pitfalls | concurrency | performance | security |
  typing-tooling | pydantic | testing (aliases like `traps`, `async`, `gil`,
  `perf`, `sec`, `typing`, `mypy`, `lint`, `validation`, `tests` are accepted)
- `--py` — target Python version (e.g. `3.11`); overrides auto-detection. Set
  this from the user's answer when the version is `unknown`
- `--prompt-file` — custom markdown template (overrides `--focus`)
- `--project-root` — repo root for version/tooling/library/Pydantic context
- `--include-tests` — include `test_*.py`/`*_test.py`/`tests/` when scanning dirs
- `--max-files` (default 25), `--max-chars` (default 60000) — review budget
- `--format` — `prompt` (default), `code`, or `context`
- `--output-file` — write the result to a file instead of stdout

The collector auto-detects the Python version (`pyproject.toml`, `setup.cfg`,
`setup.py`, `tox.ini`), tooling (ruff, flake8, mypy, pyright, black, isort,
pylint, pytest, poetry, uv), libraries (FastAPI, Flask, Django, SQLAlchemy,
Celery, httpx, pandas, numpy, ...), and **Pydantic usage** (v1 vs v2 vs mixed)
from manifests and from the reviewed code's imports. It skips `.venv/`, `venv/`,
`__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `build/`, `dist/`, and `.git/`.

When the Python version cannot be detected, the project context prints an
explicit `NOTE: Python version unknown — ASK THE USER ...`. Ask, then re-run
with `--py`.

Custom prompt files may use these placeholders: `{{language}}`, `{{code}}`,
`{{review_focus}}`, `{{review_scope}}`, `{{project_context}}`, `{{py_version}}`,
`{{project_frameworks}}`, `{{tooling}}`, `{{pydantic_usage}}`.

## Built-in review focuses

- **correctness** — logic errors: mutable defaults, closure late binding,
  `is`/`==`, shallow copy, aliasing, dict mutation while iterating, float money,
  truthiness, boundaries.
- **pitfalls** — a targeted sweep for the 10 classic traps plus common
  near-misses (manual loops, `dict[k]` vs `.get`, `readlines`).
- **concurrency** — GIL-aware: `threading` for CPU-bound work, non-atomic shared
  mutation, locks/deadlocks, blocking calls in `async def`, un-awaited
  coroutines, discarded tasks, unbounded concurrency, multiprocessing guards.
- **performance** — string `+=`, membership in lists, `Counter`, `lru_cache`,
  `__slots__`, streaming files/generators, N+1, vectorization (evidence-first).
- **security** — injection (SQL/command/`eval`/`pickle`/`yaml.load`), unsafe
  deserialization, path traversal/Zip Slip, weak crypto/`random`, secrets/PII in
  logs, `verify=False`, SSTI/XXE, `assert` for security.
- **typing-tooling** — precise types over `Any`/bare `dict`, annotations on
  public functions, `Optional` narrowing, specific `type: ignore`, and the
  ruff/mypy/pyright/black/isort/pytest + `make check` posture.
- **pydantic** — validate all external input, strict key fields, `extra="forbid"`,
  pure validators, `BaseSettings`/`SecretStr`, output models, `TypeAdapter`,
  schema-as-contract, layer separation, v1->v2 migration.
- **testing** — error/edge/boundary coverage, known-trap tests, parameterization,
  strong assertions, flakiness/mocking, async awaits, Pydantic success+failure.

Run these as separate rounds. The skill is biased toward depth over breadth, and
toward the classic traps, Pydantic boundaries, and typing posture in particular.

**Python version awareness.** The `typing-tooling` and `pydantic` rounds (and any
idiom suggestion) only recommend syntax available in the target version. If the
version is unknown, ask the user (3.9/3.10/3.11/3.12) and pass `--py 3.NN`.

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| Local-only | No GitLab/GitHub API call; no token required | Route API MR review to `gitlab-mr-review` |
| Single focus | Output stays within one focus unless a combined pass was requested | Split into separate rounds |
| Traps swept | High-severity traps surfaced regardless of the chosen focus | Re-scan against the pitfalls catalog |
| Evidence-based | Every finding cites shown code | Report insufficient evidence instead of speculating |
| No invented findings | Clean areas are stated as clean, not padded | Remove speculative findings |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Trap/practice citations | Findings reference the matching trap number or Pydantic best-practice (or CWE for security) | Add the reference or note it is not in the catalog |
| Version-aware | Syntax suggestions fit the target Python version; unknown version triggers a question | Recheck the version, or ask, before recommending newer syntax |
| Pydantic v2-aware | Pydantic findings use v2 APIs; v1 usage flagged with the v2 equivalent | Add the migration note |
| Tool hint | Typing/style findings note which tool catches them (mypy/pyright/ruff/black) | Add the tool guidance |
| Budget transparency | Note when `--max-files`/`--max-chars` trimmed coverage | State what was omitted |
| Severity ordering | Findings ordered blocker -> minor | Reorder before delivery |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Review mixes many concerns | Ran all focuses in one pass | Run one focus per round |
| Recommends `match`/`X\|None` on an older Python | Ignored detected version | Read `py_version` from project context first |
| Gives v1 Pydantic advice on a v2 codebase | Ignored `pydantic_usage` | Assume v2; flag v1; warn on mixed |
| Findings not grounded in code | Speculated beyond the payload | Restrict to shown code; note omitted files |
| "No token" or API errors | Tried to use a remote MR flow | This skill is local-only; use `gitlab-mr-review` for API MRs |
| Empty review | Diff had no Python changes | Stage changes or pass file paths |
| Missed a mutable-default / GIL bug | Only ran a style focus | Always sweep the top traps; run `pitfalls` + `concurrency` rounds |

### Boundary examples

- **User**: `review my Python changes before I commit` -> `--diff`, correctness first
- **User**: `any classic Python gotchas here?` -> `--focus pitfalls`
- **User**: `is this asyncio code safe?` -> `--focus concurrency`
- **User**: `review my Pydantic models` -> `--focus pydantic`
- **User**: `will this pass mypy?` -> `--focus typing-tooling` (ask version if unknown)
- **User**: `review this GitLab MR <url>` -> out of scope; use `gitlab-mr-review`
- **User**: `write / fix this function for me` -> out of scope; use `lazy-python-dev`
- **User**: (version undetectable) -> ask "which Python version do you target —
  3.9/3.10/3.11/3.12?" before version-specific suggestions

### Improvement triggers

- New Python version or common pitfall not covered -> refresh
  `references/python-pitfalls-catalog.md`
- New Pydantic guidance -> refresh `references/pydantic-best-practices.md`
- A recurring focus need not covered by the eight built-ins -> add a prompt
  template under `assets/prompts/` and register it in `collect_target.py`
