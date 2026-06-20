# Example Harness Audit Report

A self-consistent worked example showing the expected report shape, level of detail, cap application, and tone for a finished audit. Use it as a copy-from template, not as a scoring precedent — every project's evidence is different.

The example below describes a fictional Python + TypeScript service called `payments-gateway`. Do not transplant its scores or findings to a real project.

---

## Harness Audit: payments-gateway

Score: 55/100 (raw sum 55; caps fired: none — score is already below all applicable cap thresholds)
Status: RED
Primary stack(s): Python (`pyproject.toml`, `pytest.ini`) + TypeScript (`package.json`, `tsconfig.json`)

### Score Breakdown
| Area | Points | Evidence |
| --- | ---: | --- |
| Feedforward context | 14/20 | Root `AGENTS.md` covers project map, commands, and done criteria. No module-level guidance under `services/`. Change template absent. |
| Feedback and verification | 11/25 | `pytest`, `ruff`, `mypy`, `pnpm test`, `pnpm lint` documented in `README.md`. No single reusable verification entrypoint chains them. CI workflow file present but only runs unit tests on Linux. |
| Architecture fitness | 6/15 | `docs/architecture.md` describes layering. No deterministic enforcement (no `import-linter`, no `dependency-cruiser`, no boundary tests). |
| Behavior correctness | 9/15 | E2E suite in `tests/e2e/` covers checkout and refund. Golden fixtures in `tests/fixtures/`. No mutation or regression coverage check. |
| Safety and permissions | 7/10 | `AGENTS.md` calls out secrets, prod DB, and destructive Git rules. `gitleaks` runs in CI. No devcontainer or sandbox. |
| Entropy management | 4/10 | Dependabot enabled. No documented owner for `AGENTS.md`. No freshness check. |
| Harnessability and usability | 4/5 | `make dev` boots the stack in <60s. Repo layout is conventional and statically analyzable. |

Raw sum: 14 + 11 + 6 + 9 + 7 + 4 + 4 = 55. No caps apply because the raw sum is already below the lowest applicable cap (65). Final score: 55/100. Status: RED.

### Per-Stack Findings

#### Python (markers: `pyproject.toml`, `pytest.ini`, `tests/`)
- Verification surfaces: `pytest`, `ruff check`, `mypy` documented individually; no single command chains them.
- Architecture fitness: missing. `docs/architecture.md` forbids `services/payments` importing `services/billing` but nothing enforces it.
- Behavior harness: present. `tests/fixtures/` and `tests/e2e/` exist with golden checkout/refund flows.
- Safety tooling: `gitleaks` in CI; no `pip-audit` or `bandit`.
- Notes: `pre-commit` config exists but not installed in CI.

#### TypeScript (markers: `package.json`, `tsconfig.json`, `pnpm-lock.yaml`)
- Verification surfaces: `pnpm test`, `pnpm lint` exist as package scripts; no `typecheck` script wired (`tsc --noEmit` not present).
- Architecture fitness: missing. No `dependency-cruiser` or `eslint-plugin-boundaries` config.
- Behavior harness: partial. Playwright present in `tests/e2e/`; no component or visual regression tests.
- Safety tooling: `pnpm audit` not invoked in CI.
- Notes: build runs on Linux only; macOS/Windows agents have no CI signal.

### Top Findings

1. **No reusable verification path.** Agents must remember and chain `pytest && ruff check && mypy && pnpm test && pnpm lint`. This is the biggest barrier to consistent agent verification.
2. **Architecture rules are documented but not enforced.** `docs/architecture.md` forbids `services/payments` from importing `services/billing`, but nothing fails when it does. High drift risk under agent edits.
3. **Module-level `AGENTS.md` files missing.** Agents touching `services/checkout/` get no local guidance about its async patterns or the legacy adapter layer.

### Recommended Next Moves

1. Add a `make check` target to the existing `Makefile` that runs `ruff check`, `mypy`, `pytest -x`, `pnpm typecheck`, `pnpm lint`, `pnpm test --run` in order with fail-fast. Document it in `AGENTS.md` as the single command agents must run before stopping. Estimated 1 hour.
2. Add an `import-linter` config that enforces the `services/payments` ↔ `services/billing` boundary and one other documented rule. Wire it into `make check` and CI. Estimated 2 hours.
3. Add `services/checkout/AGENTS.md` (≤30 lines) describing async patterns, the legacy adapter, and "do not modify" zones. Estimated 30 minutes.

### Evidence Reviewed

- `AGENTS.md` (read in full)
- `README.md` (commands section)
- `docs/architecture.md`
- `.github/workflows/ci.yml`
- `tests/e2e/` (listed)
- `tests/fixtures/` (listed)
- `Makefile`
- `pyproject.toml`, `package.json` (scripts and tool configs)
- Scanner output: `feedforward=present`, `agent_check_entrypoint=missing`, `architecture_fitness=missing`, `ci=present`, `tests=present`, `behavior_fixtures=present`, `security=present`, `sandbox=missing`.

---

## Common arithmetic mistake

The Verification step exists because score arithmetic is the most frequent reporting error. Two failure modes recur:

1. **Subtotals written before they are summed.** Authors guess at a "looks right" total (often 65 or 70) instead of adding the cells.
2. **Caps confused with scores.** Authors write a cap value as the score even when the raw sum is already below it. Caps only matter when the raw sum exceeds them.

Always: sum the seven cells, then check whether any caps apply, then pick the status. Show the raw sum in the header so a reader can audit the arithmetic in one glance.
