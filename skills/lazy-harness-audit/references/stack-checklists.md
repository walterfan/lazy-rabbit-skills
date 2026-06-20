# Stack Checklists — Index

Each detected stack has its own checklist under `references/stacks/`. Open the matching file and apply its rows against the project. Do not mix expectations across stacks.

Universal rubric items (`AGENTS.md` presence, secrets policy, freshness ownership, etc.) are scored from `references/universal-rubric.md` directly and do not depend on the stack.

## Per-stack files

| Stack | File | Primary markers |
| --- | --- | --- |
| Java | [`stacks/java.md`](stacks/java.md) | `pom.xml`, `build.gradle*`, `src/main/java` |
| Python | [`stacks/python.md`](stacks/python.md) | `pyproject.toml`, `setup.py`, `requirements*.txt` |
| JavaScript / TypeScript | [`stacks/javascript-typescript.md`](stacks/javascript-typescript.md) | `package.json`, `tsconfig.json` |
| Go | [`stacks/go.md`](stacks/go.md) | `go.mod`, `internal/`, `cmd/` |
| Rust | [`stacks/rust.md`](stacks/rust.md) | `Cargo.toml`, `Cargo.lock` |
| Other / Unknown | [`stacks/other.md`](stacks/other.md) | Anything that does not match the above |

## How to read each checklist

Every per-stack file uses the same headings. Each heading maps to a universal rubric category:

| Section heading | Maps to universal rubric |
| --- | --- |
| Markers | Stack detection (Phase 1) — not scored, used to decide which checklist applies |
| Verification surfaces | §2 Feedback and Verification (items "documented local commands" and "reusable verification entrypoint") |
| Architecture fitness | §3 Architecture Fitness (item "boundaries enforced by deterministic tests appropriate to the stack") |
| Behavior harness | §4 Behavior Correctness (items "integration/E2E/smoke tests" and "approved fixtures") |
| Safety tooling | §5 Safety and Permissions (item "secret scanning, dependency audit, SAST, or supply-chain checks") |
| Priority notes | Auditor discipline — do not re-score, just avoids common interpretation errors |

## Stack ordering

For polyglot projects, audit stacks in this order:

1. The stack with the most source code by file count or LOC (the one agents touch most).
2. The stack with the highest risk surface (handles secrets, money, production data, or persistence migrations).
3. Build-config-only languages (e.g., a `pom.xml` in an otherwise-Python repo) come last and may be folded into "Other" if they have no source code.

If two stacks are roughly equal, audit the one with more complex build tooling first (typically Java > Rust > Go > JS/TS > Python), because complex builds hide more harness gaps in plugins.

## Adding a new stack

When a stack becomes worth its own file:

1. Create `references/stacks/<slug>.md` using the same six headings (Markers, Verification surfaces, Architecture fitness, Behavior harness, Safety tooling, Priority notes).
2. Add a row to the per-stack files table above.
3. If the new stack changes ordering rules, update the "Stack ordering" section.
4. Do not duplicate universal rubric items into the new file — those live in `universal-rubric.md`.
