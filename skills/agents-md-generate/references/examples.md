# AGENTS.md - worked examples

The `agents-md-generate` skill should produce compact maps, not full
manuals. Root files target fewer than 100 lines; nested package files
target fewer than 60 lines.

These examples show how to fill repo-specific context. The current
template also includes compact **Harness Rules** and **AI Tooling**
sections; keep those short and use links for depth.

---

## Example 1 - Minimal CLI (~30 lines)

Signals: no KB, no monorepo, one runtime script, one small test suite.

````markdown
# AGENTS.md - jwt-helper

<!-- Follows https://agents.md. Keep this file short: target <100 lines. -->

A single-file Python CLI that signs and verifies JWTs against a secrets
manager's public keys.

## Context Map

- `jwt_helper.py` - CLI entry point and signing logic.
- `tests/` - pytest coverage for encode/decode paths.
- `README.md` - user-facing install and usage examples.

## Commands

```bash
pip install -e .          # install editable package for local runs
pytest tests/             # run the full test suite
python -m jwt_helper --help  # verify the CLI loads
ruff check .              # lint before opening a PR
```

## Project Rules

- Format with `ruff format` - keeps diffs reviewable.
- Keep one test per public command - CLI regressions are easy to miss.
- Do not print secrets or tokens - verbose output may land in logs.
- Do not add network calls to tests - local runs must stay deterministic.

## Keeping Current

Update this file when commands, paths, or guardrails change. After a
substantial session, ask Codex for a retrospective and apply any
AGENTS.md updates it recommends.

<!-- last_updated: 2026-05-14 -->
````

---

## Example 2 - Typical Library (~80 lines)

Signals: `pyproject.toml`, `justfile`, `tests/`, `docs/`, no monorepo.

````markdown
# AGENTS.md - retrycat

<!-- Follows https://agents.md. Keep this file short: target <100 lines. -->

Retry utilities for Python HTTP clients, with async and sync APIs.

## Context Map

- `src/retrycat/__init__.py` - public re-export surface; breaking
  changes need release notes.
- `src/retrycat/async_retry.py` - async retry logic; cancellation bugs
  hide here.
- `src/retrycat/sync_retry.py` - sync/threaded retry logic.
- `tests/` - pytest + hypothesis coverage.
- `docs/index.md` - architecture and usage details.
- `README.md` - user-facing install and examples.

## Commands

Use `just` so local commands match CI.

```bash
just setup      # install Poetry deps and pre-commit hooks
just build      # build sdist and wheel under dist/
just test       # run full pytest suite, including slow cases
just lint       # run ruff and mypy checks used by CI
```

Focused checks:

```bash
just test-fast
pytest tests/test_async_retry.py -k cancellation
```

## Project Rules

- Keep `src/retrycat/` fully typed - `mypy --strict` gates merges.
- Treat `__init__.py` as public API - downstream services import from it.
- Add regression tests for retry timing changes - jitter hides edge cases.
- Prefer hypothesis for backoff behavior - generated cases catch math bugs.
- Do not add runtime dependencies - vendoring depends on a tiny tree.
- Do not edit generated docs output - update docs sources instead.
- Do not log request payloads - they may contain tokens or PII.

PR expectations:

- Run `just lint` and `just test` before requesting review.
- Mention public API changes in the PR body and changelog.

## Keeping Current

Update this file when repo layout, commands, guardrails, or docs move.
After a substantial coding session, ask Codex for a retrospective and
apply any AGENTS.md updates it recommends.

<!-- last_updated: 2026-05-14 -->
````

---

## Example 3 - PKB-backed repo (~90 lines)

Signals: `man/` or `docs/` with numbered chapters, ADRs/OpenSpec, and
multiple important modules. Even here, AGENTS.md stays as the index.

Required shape:

- `Context Map` lists only the high-value paths and points to the KB index.
- `Commands` lists install, build, test, lint, and focused checks.
- `Project Rules` summarizes the few local rules agents must see
  before editing, then links to the deeper KB chapter.
- `Keeping Current` maps doc changes to the KB and includes the
  Codex retrospective reminder.

Example PKB pointers:

- `man/index.md` - canonical architecture and workflow index.
- `man/02-architecture.md` - service boundaries and dependencies.
- `man/04-repo-map.md` - deeper module map.
- `man/changes/` - design specs, plans, and implementation notes.

Do not inline the full KB table in AGENTS.md. Link to the KB index and
only call out the chapters needed before the first edit.

---

## Example 4 - Monorepo root + nested stubs

Signals: `packages/`, `apps/`, `pnpm-workspace.yaml`, Turborepo, Nx,
Lerna, or Yarn Workspaces.

### Root (`/AGENTS.md`, ~70 lines)

````markdown
# AGENTS.md - acme-platform

<!-- Follows https://agents.md. Nested AGENTS.md files override this. -->

Acme Platform monorepo: services, shared libraries, and web apps.

## Context Map

- `apps/web/` - customer web UI; see `apps/web/AGENTS.md`.
- `services/api/` - public REST API; see `services/api/AGENTS.md`.
- `services/worker/` - async jobs; see `services/worker/AGENTS.md`.
- `packages/ui/` - shared React components.
- `packages/sdk/` - typed API client used by services and web.
- `docs/` - architecture, ADRs, and release workflow.

## Commands

Use `pnpm` and Turborepo; the lockfile is `pnpm-lock.yaml`.

```bash
pnpm install              # install workspace dependencies
pnpm turbo run build      # build all affected packages
pnpm turbo run test       # run workspace tests
pnpm turbo run lint       # run lint/typecheck gates
```

Focused checks:

```bash
pnpm turbo run test --filter <pkg>
pnpm turbo run dev --filter <pkg>
```

## Project Rules

- Keep package-specific rules in nested AGENTS.md files - nearest file wins.
- Preserve shared package APIs - changes ripple across services.
- Use Conventional Commits - release automation reads commit types.
- Do not mix package managers - npm/yarn rewrite the dependency graph.
- Do not edit generated SDK code - update schemas and regenerate.
- Do not log auth headers, cookies, or tokens - production logs persist.

PR expectations:

- Run the filtered checks for touched packages plus root lint.
- Mention cross-package impact in the PR body.

## Keeping Current

Update this file when workspaces, commands, or global guardrails change.
After a substantial coding session, ask Codex for a retrospective and
apply any AGENTS.md updates it recommends.

<!-- last_updated: 2026-05-14 -->
````

### Nested (`/services/api/AGENTS.md`, ~35 lines)

````markdown
# AGENTS.md - services/api

Root guide: [`../../AGENTS.md`](../../AGENTS.md)

Public REST API for Acme Platform. Fastify + Zod.

## Context Map

- `src/routes/` - OpenAPI-published route handlers.
- `src/auth/` - token validation and session boundaries.
- `src/db/migrations/` - append-only database changes.
- `test/` - API integration tests.

## Commands

```bash
pnpm --filter api test   # run API tests
pnpm --filter api build  # typecheck and build API package
```

## Guardrails

- Public surface: `src/routes/` - update OpenAPI snapshots with changes.
- Do not edit existing migrations - deployed environments cannot replay them.
- Do not log auth headers - tokens can leak into centralized logs.

<!-- last_updated: 2026-05-14 -->
````

---

## Decision table

| Repo signals | Shape |
| --- | --- |
| Single file, no docs tree, no task runner | Example 1 |
| One package, tests, maybe docs | Example 2 |
| PKB / numbered docs / ADRs | Example 3, but still under 100 lines |
| Workspaces or multiple packages | Example 4 root + nested stubs |

When in doubt, generate Example 2 and let supporting docs carry depth.
