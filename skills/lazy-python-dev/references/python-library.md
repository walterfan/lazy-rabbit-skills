# Conventions: Python library projects (e.g. a secrets manager SDK)

This reference encodes practices common to internal library-style Python repos that maintain **AGENTS.md**, a **PKB(Project Knowledge Base)** under `man/`, and **Ruff + Poetry + pytest + just**.

## Toolchain defaults

| Area | Typical choice | Notes |
|------|----------------|-------|
| Python | `>3.9, <4.0` (project-specific floor in `pyproject.toml`) | Match `requires-python` to supported runtimes |
| Packaging | **Poetry** (preferred) | Do not hand-edit `poetry.lock`; use `poetry add` / `poetry update` as documented |
| Lint / format | **Ruff** | Project config in root `pyproject.toml` |
| Tasks | **just** | Prefer `just <recipe>` over ad hoc shell |
| Tests | **pytest** (+ coverage, asyncio as needed) | Use mocks for external services; opt-in live markers |
| Config / models | **Pydantic** (or similar) | Prefer validated models over raw dicts for new behavior |

## Command quick reference

| Task | Prefer |
|------|--------|
| Install deps from lock | `poetry install` |
| Add runtime dep | `poetry add <package>` |
| Add dev dep | `poetry add --group dev <package>` or repo-documented equivalent |
| Run lint | `just lint` or `poetry run ruff check .` |
| Run format | `just format` or `poetry run ruff format .` |
| Run tests | `just run-tests` or `poetry run pytest` |
| Run one test file | `poetry run pytest tests/test_x.py -v` |

## Code style

- `snake_case` for modules, functions, and variables; `PascalCase` for classes and Pydantic models.
- Public API surface is explicit and stable; this is a **library**, not app-local glue.
- **Default code paths** stay healthy; optional modes (e.g. alternate transports) must not rot.

## Security

- **Never log secret values**, tokens, or full JWT payloads. Redact; use project logging utilities when present.
- Auth and credentials come from **environment, IAM, or headers** — not hardcoded literals.
- Do not blindly forward **sanitized, optional** outbound headers; treat as policy-sensitive.

## Testing

- **Behavior change ⇒ pytest coverage**; prefer integration tests against mocks over live services.
- Mark expensive or credential-bound tests so they are **opt-in** (e.g. `live_*`).

## Change workflow (when the repo uses OpenSpec)

- Non-trivial work: `openspec/changes/<slug>/` with proposal, design, tasks, and specs; implement against tasks and archive after release.
- **Minimum diff**; avoid public API changes without doc + ADR as required by the project.

## Docs

- PKB pages use **numbered** canonical names (`00`–`12`); preserve `<!-- maintained-by: human+ai -->` and metadata footers where the project uses them.
- **Do not** duplicate the manual in AGENTS — link to `man/`.

## Danger zones (treat as high-risk)

Typical hot spots in secret-manager-style SDKs — touch only with design sign-off: auth and env resolution, cache and polling, alternate transports, usage/reporting pipelines, backward compatibility of the primary public client.

## Related

- Project harness: `AGENTS.md` at repo root
- In-repo: `man/07-conventions.md`, `man/03-tech-stack.md`, `man/09-testing.md`
