# Harness Improvement Playbook

Use this when deciding how to raise a project's harness audit score.

## Principles

- Improve the agent's workbench, not just the prose around it.
- Pair feedforward with feedback: every important rule should point toward a check, fixture, review gate, or explicit human decision.
- Prefer small, reviewable changes over a giant "AI transformation" commit.
- Use the project's existing tools first. New dependencies require a clear benefit and approval.
- Be honest about missing checks. A documented gap is better than a fake command.

## Fast Score Lifts by Audit Category

### Feedforward Context

Best first actions:

- Create or improve `AGENTS.md`.
- Link to existing README, architecture docs, runbooks, and API docs.
- Add module-level notes only where the repo has clearly distinct stacks or risk areas.
- Add a task/request template with goal, context pointers, constraints, and done criteria.

Minimum useful root guide:

- What the project is.
- Where the important code lives.
- How to install, test, lint, typecheck, build.
- What boundaries and danger zones matter.
- What "done" means for an agent.

### Feedback and Verification

Best first actions (in order):

1. Add a reusable verification target on an **existing build surface**:
   - `Makefile`: `make check`
   - `package.json`: `npm run check` / `pnpm check`
   - Maven: `mvn verify` (with the right plugin bindings)
   - Gradle: `gradle check`
   - CI shim: `./ci/build.sh`
   - Only fall back to a new `scripts/agent-check.sh` when none of the above fits the project's conventions.
2. Make sure that target runs the fastest meaningful checks (test + lint + typecheck where applicable), fail-fast.
3. Document the same command in `AGENTS.md` so agents can find it without grep.
4. Add focused-test examples for the project's actual stack.
5. Add final-report expectations: what changed, what ran, what did not run, remaining risks.

Good verification examples per stack:

| Stack | Common Commands |
| --- | --- |
| Java Maven | `./mvnw test`, `./mvnw verify`, Checkstyle/SpotBugs/PMD if configured |
| Java Gradle | `./gradlew test`, `./gradlew check` |
| Go | `go test ./...`, `go test -race ./...` for concurrency changes, `golangci-lint run` |
| Python | `pytest`, `ruff check .`, `mypy` or `pyright` if configured |
| Rust | `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` |
| Node / TypeScript | `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` |

### Architecture Fitness

Best first actions:

- Document boundaries before enforcing them.
- Add one deterministic rule for the riskiest boundary.
- Keep architecture checks close to existing test/lint tooling.

Tool examples per stack:

- Java: ArchUnit; module boundaries in Maven/Gradle multi-module setups.
- TypeScript / JavaScript: `dependency-cruiser`, `eslint-plugin-boundaries`, ESLint `no-restricted-imports`.
- Python: `import-linter`, custom AST checks.
- Go: `internal/` package boundaries (compiler-enforced), `depguard`/`forbidigo` rules in `golangci-lint`.
- Rust: workspace crate boundaries, `pub(crate)` discipline, Clippy `-D warnings`, `cargo deny`.

### Behavior Correctness

Best first actions:

- Add one approved fixture for a critical path.
- Add a short policy: agents may add tests but must not modify approved fixtures to hide implementation errors.
- Connect fixture usage to an existing test if feasible.
- If test plumbing is not feasible in one pass, add the fixture and an explicit follow-up.

### Safety and Permissions

Best first actions:

- Document no-secrets/no-PII logging rules.
- State that destructive Git, bulk delete, DB migration, deployment, and production access require explicit human approval.
- Add secret scanning or dependency audit only if the repo already uses compatible tooling or the user approves.
- Ensure `.env`, credentials, local DBs, and generated private reports are ignored or documented.

### Entropy Management

Best first actions:

- Add a "Harness Maintenance" section to `AGENTS.md`.
- Name an owner/team or review cadence if known.
- Add a release/PR checklist item to update agent docs when commands, directories, APIs, or workflows change.
- Add scheduled dependency/doc freshness checks when the CI platform is already present.

## Suggested Improvement Sequence

If the audit reported one or more **caps**, clear them first — see the cap-first priority table in `SKILL.md` Phase 2. Caps are score ceilings; each cleared cap unlocks the underlying sub-item points all at once. Only fall back to the sequences below when no cap fires (or after all caps are cleared).

For RED projects:

1. Root `AGENTS.md`.
2. Reusable verification target on an existing build surface (`make check`, `mvn verify`, `gradle check`, `npm run check`, `./ci/build.sh`, or a new `scripts/agent-check.sh` as last resort).
3. Safety boundaries.
4. One behavior fixture.

For YELLOW projects:

1. Fill the weakest scored category from the audit.
2. Add CI/pre-commit coverage for the local verification path.
3. Add architecture or behavior enforcement for the most repeated failure mode.

For GREEN projects:

1. Improve entropy management.
2. Reduce verification cost and flakiness.
3. Add targeted architecture/behavior checks for recent drift.

## Anti-Patterns

- Long `AGENTS.md` with no real commands.
- CI added with commands that fail because dependencies are unknown.
- Hook runs the entire build after every tiny edit.
- New dependency added only to win points.
- Approved fixtures that agents are allowed to rewrite casually.
- Security rules that mention secrets but do not cover logs, env files, production data, or destructive commands.
