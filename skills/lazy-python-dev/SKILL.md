---
name: lazy-python-dev
description: >-
  Use when working in a Python repo that uses or should use Poetry, Ruff,
  pytest, `pyproject.toml`, and library-style conventions; when the task is to
  implement, refactor, review, or debug Python while preserving API stability,
  typed models, small diffs, and safe logging. Applies especially to library-style
  repos with `AGENTS.md`, `justfile`, or `man/07-conventions.md`.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - python
  - poetry
  - ruff
  - pytest
  - library
  - pyproject
  - type-hints
  - pkb
  - just
category: dev-tools
use_cases:
  - "add a feature in our Python SDK with tests"
  - "set up ruff and pytest the way the repo does"
  - "review this Python change for style and security"
  - "should I use poetry add or edit pyproject by hand"
platforms: [claude-code, cursor, codex]
visibility: public
---

# lazy-python-dev

Practical **Poetry-first** Python development: match the project’s `pyproject.toml` and `justfile`, keep changes small, and verify with **Ruff + pytest** before claiming done.

**Progressive detail:** [references/python-library.md](references/python-library.md) (library defaults), [references/python-traps-and-tricks.md](references/python-traps-and-tricks.md) (review heuristics from common Python pitfalls), and [references/modern-tooling.md](references/modern-tooling.md) only when the user opts in.

## When to use

- Python repo mentions `pyproject.toml`, `poetry.lock`, `poetry`, `ruff`, `pytest`, or `just`
- User wants to implement, fix, refactor, or review Python with **minimum diff**
- Repo looks like a reusable library or SDK where API stability matters
- Project has `AGENTS.md`, PKB docs, or conventions files that should steer the change

## When not to use

- Non-Python primary work
- Team has explicitly chosen a non-Poetry stack for the current task
- Task is mainly deployment, Jira/GitLab workflow, or product-specific secrets-manager usage guidance

## Contract

- **scope_in**: Python code or config in repos that use (or should use) **Poetry**, **Ruff**, **pytest**, and optionally **just**; library/service modules; `pyproject.toml` edits *via* Poetry commands; type hints and validated models; test and mock strategy; logging that must not leak secrets; reading **AGENTS.md** / `man/07-conventions` style rules when present
- **scope_out**: Non-Python primary work; replacing Poetry with **uv** without the user asking; production deploy runbooks (use your deployment platform/team skills); JIRA/GitLab process (use other skills); **secrets manager SDK API semantics** in depth (use your project's secret-management documentation)
- **Preconditions**: Repo or snippet is available; project Python floor and tool versions are read from `pyproject.toml` / CI, not assumed beyond defaults in references
- **Postconditions**: Commands use **Poetry** for deps (`poetry add`, `poetry install`, `poetry run …`) unless the user explicitly chose another tool; Ruff and pytest are invoked the way the repo documents (`just`, `poetry run`, etc.); no secret values in examples or log suggestions; if verification was not run, the answer says so

## Execution

### Phase 0: Detect context

- **Entry**: User asks to implement, fix, or review Python
- **Steps**:
  1. If a repo is open, read `pyproject.toml` (and `justfile` if present) for **Poetry** `[tool.poetry]`, Ruff, pytest, Python version
  2. If **AGENTS.md** or `man/07-conventions.md` exist, skim for project-specific rules (public API, danger zones, OpenSpec)
  3. If the user mentions **uv, rye, or pip only** and not Poetry, ask once: *"This skill defaults to **Poetry**; keep Poetry or switch for this task?"* If they want uv-only, use [modern-tooling.md](references/modern-tooling.md) and do not override their choice
- **Exit**: Tooling path is Poetry-first or user-confirmed alternative
- **On fail**: List what file is missing (e.g. no `pyproject.toml`) and work from minimal Poetry layout only as a scaffold, labeled as such

### Phase 1: Classify the task

- **Entry**: Phase 0 complete
- **Steps**:
  1. Pick one primary mode:
     - **Implement**: write or modify Python code
     - **Review**: assess a diff, file, or snippet for correctness, risk, and tests
     - **Tooling**: adjust Poetry, Ruff, pytest, or `just` setup
     - **Explain**: answer questions about Python structure, typing, or project conventions
  2. Keep the task in one mode unless the user clearly asked for both code + review
- **Exit**: One primary mode is chosen
- **On fail**: Ask one short clarifying question that combines scope + mode, for example: `Do you want me to implement the change, review the diff, or adjust the Poetry/Ruff setup?`

### Phase 2: Implement or review

- **Entry**: Phase 0 complete
- **Steps**:
  1. **Implement**
     - Add or remove dependencies with `poetry add` / `poetry remove`; never hand-edit `poetry.lock`
     - Prefer small, reviewable diffs over speculative cleanup
     - For config and API-shaped data, prefer typed models such as Pydantic when the repo already uses them
  2. **Review**
     - Start with behavior, regressions, compatibility, and missing tests before style nits
     - Pay extra attention to auth/config resolution, cache or polling code, transport layers, reporting, and public client APIs
     - Scan for common Python traps from [python-traps-and-tricks.md](references/python-traps-and-tricks.md): mutable defaults, late-bound closures, shallow-copy surprises, list aliasing, broad `except`, float precision, and concurrency misuse
  3. **Tooling**
     - Keep the repo’s chosen stack; configure Ruff, pytest, and Poetry in `pyproject.toml` and `justfile` the way the repo already documents
     - Prefer project commands (`just lint`, `just run-tests`) over ad hoc shell when they exist
  4. **Explain**
     - Use the repo’s own files and conventions before general Python advice
     - When explaining Python behavior, prefer concise examples grounded in the traps and standard-library patterns from [python-traps-and-tricks.md](references/python-traps-and-tricks.md)
     - State assumptions when exact project config is missing
  5. In every mode, apply these rules:
     - `snake_case` / `PascalCase` per [python-library.md](references/python-library.md)
     - no logging of secrets, tokens, or raw JWT
     - for libraries, keep public entry points explicit and backward compatible unless an ADR allows breaking changes
- **Exit**: Code or review notes are consistent with Poetry + Ruff + project conventions
- **On fail**: If Ruff or tests are not runnable in environment, state that and still give the diff or review, with a clear **Verification** gap

### Phase 3: Shape the response

- **Entry**: Code change exists or user asked for commands
- **Steps**:
  1. Use this response shape when the task is non-trivial:
     - `summary`: what changed or what was reviewed
     - `assumptions`: missing config or context that affected the answer
     - `changes`: files, commands, or config touched
     - `risks`: compatibility, security, or test gaps
     - `verification`: what was actually run and what was not
     - `next_step`: only if there is an obvious follow-up
  2. For reviews, lead with findings ordered by severity
  3. For implementation, keep the close-out evidence-first: no “done” without verification
- **Exit**: Response shape matches the task and makes verification explicit
- **On fail**: Fall back to a shorter answer, but still state assumptions and verification limits

### Phase 4: Verify

- **Entry**: Code change exists or user asked for commands
- **Steps**:
  1. Use project recipes: e.g. `just lint`, `just format`, `just run-tests`, or `poetry run ruff check`, `poetry run pytest` as documented
  2. For library repos, prefer targeted tests near the change, then wider suite if reasonable
  3. If only a review was requested, still note which checks would materially reduce risk
- **Exit**: Stated which commands ran, what passed or failed, or that checks were not run
- **On fail**: Report failures; do not claim green CI without evidence

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| No secrets in output | No real keys, tokens, or JWT bodies in code blocks or log examples | Redact; use placeholders |
| Poetry-consistent instructions | Deps use Poetry commands; lock not hand-edited | Fix commands; warn if user insisted on non-Poetry |
| Matches repo Ruff | Edits follow `pyproject` Ruff config | Align or note exception |
| Evidence-first status | Verification says what actually ran | Remove unsupported “done/passing” claims |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Tests mentioned | New behavior tied to a test file or case | Note gap |
| Docs / ADR | Public API change flagged for project process | Suggest `man/` or OpenSpec path |
| Output shape | Review or implementation summary is easy to scan | Reformat around findings / verification |
| Pitfall scan | Reviews consider common Python traps when relevant | Call out the unreviewed risk area |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Suggested `uv add` in a Poetry repo | Pulled in external “modern” defaults | Re-read this skill: **Poetry first** |
| Hand-edited lockfile | Skipped `poetry lock` / `poetry add` | Use Poetry commands only |
| Broad public API | Missed “library” scope | Tighten exports; check AGENTS / ADR |
| Suggested `print(secret)` for debug | Security slip | Use redacted logging pattern |
| Claimed tests passed without running them | Skipped evidence-first closeout | State exactly what was and was not verified |
| Missed a classic Python bug in review | Review stayed at style level and skipped semantic traps | Use [python-traps-and-tricks.md](references/python-traps-and-tricks.md) as a semantic checklist |

### Boundary examples

- **User**: "add requests" in a Poetry repo → `poetry add requests` and run tests; do not add to `requirements.txt` unless the repo is explicitly requirements-only
- **User**: "we use uv for everything now" → follow [modern-tooling.md](references/modern-tooling.md) for that session; do not force Poetry
- **User**: "is this Pydantic model right?" in isolation → answer types/validation; optional Poetry mention only if deps are wrong
- **User**: "review this SDK diff" → focus on behavior, compatibility, and tests first; style comments are secondary
- **User**: "why does this function keep reusing old list data?" → inspect mutable defaults first; point to the safer `None` pattern

### Improvement triggers

- Poetry or Ruff major workflow changes → update [python-library.md](references/python-library.md) and the **description** frontmatter
- User repeatedly asks for uv → consider expanding [modern-tooling.md](references/modern-tooling.md) with a short migration checklist (still not default in SKILL body)

## Additional resources

- Library defaults: [references/python-library.md](references/python-library.md)
- Python traps and standard-library patterns: [references/python-traps-and-tricks.md](references/python-traps-and-tricks.md)
- Optional uv/ty and ToB reference: [references/modern-tooling.md](references/modern-tooling.md)
- External inspiration: [Trail of Bits modern-python](https://github.com/trailofbits/skills/tree/main/plugins/modern-python/skills/modern-python) (not Poetry-default; use for comparison only)
