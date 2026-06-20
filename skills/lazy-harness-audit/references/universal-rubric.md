# Universal Harness Audit Rubric

Score out of 100. Every category applies to every project regardless of stack. Items here describe **what** must exist; the **stack-specific evidence** that satisfies each item lives in `stacks/<stack>.md` (use `stack-checklists.md` as the index).

When a sub-item says "appropriate to the stack" or "where applicable", consult the matching `stacks/<stack>.md` for the tool, command, or file pattern.

Give partial credit only for evidence that is present, discoverable, and likely to be used by a coding agent.

## 1. Feedforward Context — 20 points

- 8 pts: Root agent guide exists and is useful (`AGENTS.md` preferred; `CLAUDE.md`, `.cursor/rules`, `.codex/AGENTS.md`, or equivalent accepted): project purpose, repo map, commands, boundaries, done criteria.
- 4 pts: Module-level guidance exists for major stacks or high-risk directories.
- 3 pts: Project knowledge base or architecture docs are discoverable from the root guide.
- 3 pts: Change/request template captures goal, context, constraints, and definition of done.
- 2 pts: Guidance is concise, current, and points to deeper references instead of becoming a junk drawer.

## 2. Feedback and Verification — 25 points

- 7 pts: Documented local commands for build, test, lint, format, and typecheck where applicable to the stack. (See the matching `stacks/<stack>.md` for which categories are expected per stack.)
- 5 pts: A single reusable verification entrypoint exists on an existing build surface — for example, `make check`, a top-level package script, or a documented build target (`mvn verify`, `gradle check`, `./ci/build.sh`, etc.). The exact command is stack-specific; what matters is that one command chains the project's important checks.
- 5 pts: CI or pre-merge gates run the important checks (same set the local entrypoint runs).
- 3 pts: Hooks or pre-commit checks automate cheap feedback without making daily work painful.
- 3 pts: Test strategy covers the major languages and components actually present in the repo.
- 2 pts: Final-report or stop protocol requires verification results and unrun checks to be stated.

## 3. Architecture Fitness — 15 points

- 4 pts: Architecture boundaries, layering, public surfaces, and danger zones are documented.
- 5 pts: Boundaries are enforced by deterministic tests or tools appropriate to the stack. (See the matching `stacks/<stack>.md` Architecture fitness section for what counts per stack.)
- 3 pts: API contracts, schemas, generated types, or compatibility rules are checked.
- 2 pts: Ownership or approval rules exist for high-risk areas.
- 1 pt: Architecture checks are wired into CI or the reusable verification entrypoint.

## 4. Behavior Correctness — 15 points

- 4 pts: Critical user/business flows have integration, E2E, smoke, or acceptance tests.
- 4 pts: Approved fixtures, golden files, snapshots, or example I/O capture expected behavior.
- 3 pts: The harness discourages agents from modifying tests/fixtures just to make their implementation pass (e.g., explicit AGENTS.md rule, review gate, or hook).
- 2 pts: Manual QA, product acceptance, or reviewer gates are defined for semantic judgments.
- 2 pts: Regression, mutation, or coverage checks reveal shallow tests when appropriate.

## 5. Safety and Permissions — 10 points

- 3 pts: Secrets, tokens, cookies, PII, logs, and local env files have explicit handling rules.
- 2 pts: Destructive Git, delete/overwrite, deployment, database migration, and production access boundaries are documented.
- 2 pts: Secret scanning, dependency audit, SAST, or supply-chain checks exist (tool name varies by stack).
- 2 pts: Sandbox, devcontainer, least-privilege credentials, or read-only tools constrain the agent's blast radius.
- 1 pt: Security/privacy checks are part of CI, hooks, or the reusable verification path.

## 6. Entropy Management — 10 points

- 3 pts: Docs/harness freshness is checked or reviewed on a cadence.
- 2 pts: Dependency health is monitored by scheduled scans, Dependabot/Renovate, or equivalent.
- 2 pts: Harness behavior is observable through cost, failure, flaky-test, or review metrics.
- 2 pts: There is an owner or maintenance process for agent docs, rules, hooks, and skills.
- 1 pt: The project records harness decisions or changes in ADRs, changelogs, or release notes.

## 7. Harnessability and Usability — 5 points

- 2 pts: Local setup is reproducible and fast enough for agents to iterate.
- 1 pt: The repo structure and language/tooling choices make static analysis feasible.
- 1 pt: Workflows are scoped into small, reviewable tasks or reusable skills.
- 1 pt: The harness works for both humans and agents without excessive ceremony.

## Status Mapping

| Score | Status | Meaning |
| --- | --- | --- |
| 80–100 | GREEN | Usable guidance, executable checks, meaningful safety/behavior coverage. |
| 60–79 | YELLOW | Useful harness with material gaps that can cause repeated agent mistakes. |
| 0–59 | RED | Agent environment relies mostly on human memory, luck, or after-the-fact review. |

This is the single source of truth for thresholds. SKILL.md and reports must reference it rather than restating the numbers.

## Score Caps

After summing the seven category subtotals, apply these caps. The final score is `min(sum, lowest applicable cap)`. Note in the report which caps fired and why; skip a cap only with explicit counter-evidence.

| Cap | Trigger |
| ---: | --- |
| 70 | No readable project guidance (`AGENTS.md` or equivalent missing). |
| 65 | No reusable local verification path exists, even when individual commands are documented. |
| 75 | No CI or pre-merge gate. |
| 80 | No behavior-level tests or approved fixtures for user-visible behavior. |
| 80 | Secrets, production access, or destructive command boundaries are undocumented. |
| 75 | Project cannot be built or tested locally from documented commands. |

## Scoring Notes

- Prefer deterministic, cheap feedback over LLM-only review for the same risk.
- Reward systems that close the loop: guidance tells the agent what to do, checks tell it when it drifted, and maintenance keeps both current.
- Penalize "policy wallpaper": long rules with no verification path, owner, or examples.
- Do not require every project to have every tool. Score against the project's risk and stack, but keep the 100-point weights stable.
- When the same evidence could fit two categories (e.g., a CI workflow that runs both architecture checks and secret scans), count it in each category at the appropriate sub-item — do not double-count within a single sub-item.
