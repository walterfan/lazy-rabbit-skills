---
name: lazy-harness-audit
description: >-
  Audit a software project's AI coding-agent harness and score it on a
  100-point scale (GREEN/YELLOW/RED). Use when the user asks to audit, review,
  benchmark, or score a project's agent harness, Codex/Claude/Cursor
  setup, AGENTS.md, rules, hooks, CI gates, verification matrix, architecture
  fitness checks, behavior tests, safety boundaries, or agent working
  environment. Triggers: audit harness, score harness, harness review,
  AGENTS.md audit, agent setup quality, 审计 harness, 评分 agent 环境.
license: CC-BY-NC-ND-4.0
metadata:
  version: "0.3.0"
  author: walterfan@ustc.edu
  tags:
    - harness-engineering
    - agentic-coding
    - codex
    - audit
    - scorecard
  category: dev-tools
  platforms:
    - codex
    - claude-code
    - cursor
  visibility: public
---

# lazy-harness-audit

Audit whether a project gives coding agents a reliable working environment: clear feedforward guidance, executable feedback, architecture constraints, behavior verification, safety boundaries, and a way to keep the harness fresh.

## Contract

- **scope_in**: Software projects with source code, build/test config, docs, CI, agent instructions, hooks, rules, or equivalent harness assets. Works for monorepos and polyglot projects.
- **scope_out**: Non-software folders, pure document collections, binary-only projects, and requests to implement the harness instead of auditing it.
- **Preconditions**: The target project path is readable. If the user omits a path, default to the current workspace root and state that assumption.
- **Postconditions**: Output a concise harness audit with a 0-100 score, status (`GREEN`, `YELLOW`, or `RED`), evidence, highest-risk gaps, and prioritized improvements.

## Audit Model

Two parallel references drive scoring:

- `references/universal-rubric.md` — the 100-point framework. Every category, sub-item, status threshold, and score cap lives here. This is the single source of truth.
- `references/stack-checklists.md` — index of per-stack checklists. The actual per-stack content lives in `references/stacks/<stack>.md` (one file per stack: `java.md`, `python.md`, `javascript-typescript.md`, `go.md`, `rust.md`, `other.md`). Each per-stack file's headings map back to rubric categories explicitly.

Supporting material:

- `references/harness-model-summary.md` — conceptual framing for findings and recommendations.
- `references/example-report.md` — a self-consistent example of the expected report shape.

Do not depend on external article paths during normal audits; the skill should be portable across machines and repos.

## Execution

### Phase 1: Identify project, stack, and collect evidence

1. **Resolve the project.** If the user did not provide a path, default to the current workspace root and state that assumption in the report. Resolve `<project-name>` as the basename of the project root, unless a clearer name is available (`package.json#name`, `pyproject.toml#project.name`, `Cargo.toml#package.name`, or repo name).
2. **Identify the primary technology stack(s).** Use the primary-marker table in `references/stack-checklists.md` for quick lookup, and the **Markers** section of each `references/stacks/<stack>.md` for the full marker list. For monorepos and polyglot projects, list the stack per major module instead of flattening everything into one label. Use the **Stack ordering** rules in `stack-checklists.md` to decide which stack to audit first — typically the one with the most source code or the highest risk surface, with complex build stacks (Java, Rust) breaking ties.
3. **Scope for monorepos.** By default audit the repo as a whole. If the user names a subpackage, or only one subpackage has agent guides, scope the audit there and mention the choice.
4. **Run the scanner** to collect evidence before interpreting it. The script is Python 3 stdlib only — no `pip install` needed. `<skill-dir>` is the directory that contains this `SKILL.md`. The agent reading this file already knows that absolute path — substitute it for `<skill-dir>` below.

```bash
SKILL_DIR="$(dirname "<absolute-path-to-this-SKILL.md>")"
python3 "$SKILL_DIR/scripts/audit_harness.py" "<project-root>" --format markdown
```

For machine-readable output (post-processing the evidence), use `--format json`:

```bash
python3 "$SKILL_DIR/scripts/audit_harness.py" "<project-root>" --format json
```

The scanner is read-only and skips `.git`, `node_modules`, `vendor`, build outputs, etc.

5. **Apply the per-stack checklist.** For each detected stack, open the matching `references/stacks/<stack>.md` (use `references/stack-checklists.md` as the index) and confirm each row against the scanner output plus direct file reads. Do not mix stack expectations across stacks; cite evidence per stack.
6. **Manual fallback when the scanner cannot run.** Inspect each evidence class directly:
   - agent instructions: `AGENTS.md` (preferred), `CLAUDE.md`, `.cursor/rules`, `.codex/AGENTS.md`, or equivalent
   - docs and knowledge base: `README`, `docs/`, `man/`, architecture notes, ADRs
   - verification: documented commands, reusable build/check entrypoints, package manager scripts
   - CI and hooks: `.github/workflows`, `.gitlab-ci.yml`, pre-commit, hook configs
   - architecture fitness: per-stack tools from `references/stacks/<stack>.md`
   - behavior harness: fixtures, golden tests, E2E/integration/smoke tests, approved examples
   - safety: secret scans, dependency audits, sandbox/devcontainer, permissions rules
   - entropy management: doc freshness checks, scheduled audits, dependency bots, harness maintenance docs

#### Scanner field map

The scanner's `heuristic_summary` fields map to universal rubric categories:

| Scanner field | Rubric category / item |
| --- | --- |
| `feedforward` | §1 — root agent guide presence |
| `knowledge_docs` | §1 — knowledge base discoverability |
| `verification_commands` | §2 — documented local commands |
| `verification_entrypoint` | §2 — reusable verification entrypoint (any documented build surface counts: `make check`, `mvn verify`, `gradle check`, `npm run check`, `./ci/build.sh`, …; bespoke `scripts/agent-check.sh` is just one of many) |
| `ci` | §2 — CI / pre-merge gates |
| `hooks` | §2 — hooks / pre-commit |
| `architecture_fitness` | §3 — boundary-enforcing tests |
| `behavior_fixtures` | §4 — approved fixtures / golden files |
| `tests` | §2 / §4 — test files present |
| `security` | §5 — secret scans, dep audits, SAST |
| `sandbox` | §5 — devcontainer / sandbox / least-privilege |
| `entropy_management` | §6 — freshness, ownership, scheduled audits |

A `present` signal is necessary but not sufficient — confirm by reading the actual files before awarding full points.

### Phase 2: Score with the rubric

Assign points out of 100 using the categories, sub-items, status thresholds, and score caps in `references/universal-rubric.md` — that file is the single source of truth, do not restate its numbers here.

Process:

1. Score each of the seven universal categories. For sub-items that say "appropriate to the stack" or "where applicable", check the matching row in `references/stacks/<stack>.md` for each detected stack and require evidence from at least one stack-appropriate tool.
2. Sum the seven subtotals (the raw sum).
3. Apply the score caps from `universal-rubric.md`. The final score is `min(raw_sum, lowest_applicable_cap)`. Note which caps fired and why; skip a cap only with explicit counter-evidence.
4. Pick the status (GREEN / YELLOW / RED) from the threshold table in `universal-rubric.md`.

### Phase 3: Produce the audit report

Use this report shape:

```markdown
## Harness Audit: <project-name>

Score: <N>/100 (raw sum <S>; caps fired: <list or "none">)
Status: <GREEN|YELLOW|RED>
Primary stack(s): <Java/Python/Go/JS-TS/Rust/... with key marker files>

### Score Breakdown
| Area | Points | Evidence |
| --- | ---: | --- |
| Feedforward context | x/20 | ... |
| Feedback and verification | x/25 | ... |
| Architecture fitness | x/15 | ... |
| Behavior correctness | x/15 | ... |
| Safety and permissions | x/10 | ... |
| Entropy management | x/10 | ... |
| Harnessability and usability | x/5 | ... |

### Per-Stack Findings
Repeat one block per detected stack. Skip this section only if the project has no identifiable stack.

#### <stack name> (markers: <key marker files>)
- Verification surfaces: <observed commands / build entrypoints, or "missing">
- Architecture fitness: <observed stack-specific enforcement, or "missing">
- Behavior harness: <observed fixtures / integration / E2E tests, or "missing">
- Safety tooling: <observed dep audit / SAST / secret scans, or "missing">
- Notes: <stack-specific gaps or strengths>

### Top Findings
1. ...
2. ...
3. ...

### Recommended Next Moves
1. ...
2. ...
3. ...

### Evidence Reviewed
- ...
```

Keep findings concrete. Cite real files and commands. Do not reward aspirational wording unless there is an executable check, owned process, or maintained document behind it.

## Verification

Before finalizing the report:

- The seven universal category maxes sum to exactly 100 (20+25+15+15+10+10+5).
- The raw sum equals the sum of cells in the Score Breakdown table. Re-add the cells before publishing — score arithmetic is the most common mistake.
- The reported score equals `min(raw_sum, lowest_applicable_cap)`. Show the raw sum and list every cap that fired.
- The status matches the threshold table in `universal-rubric.md`.
- Every nonzero category cites at least one concrete file path or command. No invented files.
- Every cited path was either matched by the scanner or directly read during the audit.
- The reported stack matches concrete marker files or source layout. Per-Stack Findings cite stack-appropriate evidence (e.g., `mvn verify` / ArchUnit for Java, `pytest` / `import-linter` for Python, `package.json` scripts / `dependency-cruiser` for JS/TS).
- Every major gap has a practical, specific next action (not "improve docs").
- If scanner evidence and manual inspection disagree, state which one you trusted and why.

## Common Findings

Patterns to watch for, with stack-neutral first-move remediation. For the concrete tool or command name, look up the project's stack in `references/stacks/<stack>.md` (index at `references/stack-checklists.md`).

- **Docs-only harness**: Good `AGENTS.md`, but no reusable verification path. Add the missing check/test steps to the project's existing build surface (`Makefile`, `pom.xml`, `build.gradle`, `pyproject.toml` script entry, `package.json` script, `./ci/build.sh`, etc.) rather than introducing a new bespoke script.
- **Checks-only harness**: Tests and lint exist, but agents lack a map. Recommend a short root `AGENTS.md` with project map, commands, boundaries, and done criteria.
- **Behavior blind spot**: Unit tests exist, but no fixtures, E2E, or approved examples. Recommend one critical golden-path fixture using the stack's idiomatic fixture format.
- **Architecture drift risk**: Layering is documented but not enforced. Recommend the stack's deterministic boundary tool (see the matching `stacks/<stack>.md` Architecture fitness section).
- **Unsafe autonomy**: No stated boundaries for secrets, destructive commands, deployments, or production data. Recommend explicit rules plus pre-tool or pre-commit checks where supported.
- **Stale harness**: Harness files exist but lack ownership, freshness checks, or release cadence. Recommend a lightweight scheduled audit and doc freshness check.
