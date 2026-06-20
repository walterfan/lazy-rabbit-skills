---
name: lazy-harness-helper
description: >-
  Improve a software project's AI coding-agent harness so the lazy-harness-audit
  score goes up. Use when the user asks to raise a harness score, move a project
  from RED or YELLOW to GREEN, fix top audit findings, add or improve AGENTS.md,
  agent-check scripts, verification matrices, rules, hooks, CI gates, behavior
  fixtures, architecture fitness checks, safety boundaries, or harness
  maintenance practices. Triggers: improve harness, fix harness gaps, raise
  audit score, add AGENTS.md, add agent-check, harness uplift,
  提高 harness 分数, 改进 agent 环境.
license: CC-BY-NC-ND-4.0
metadata:
  version: "0.3.0"
  author: walterfan@ustc.edu
  tags:
    - harness-engineering
    - agentic-coding
    - codex
    - automation
    - score-improvement
  category: dev-tools
  platforms:
    - codex
    - claude-code
    - cursor
  visibility: public
---

# lazy-harness-helper

Improve a project's coding-agent harness with small, concrete changes that should raise its `lazy-harness-audit` score.

## Contract

- **scope_in**: Software projects that need better agent guidance, verification, safety boundaries, behavior tests, architecture checks, hooks, CI, or harness maintenance.
- **scope_out**: Rewriting application architecture, replacing the build system, or adding heavyweight tools without approval. Honesty rules (no fake commands, no invented file references) are covered in the `## Honesty` section.
- **Preconditions**: Target project path is readable. If an audit report or score is provided, use it. If not, run a lightweight baseline scan first.
- **Postconditions**: The project has a focused harness improvement plan and, when the user asked for changes, concrete files/edits that improve one or more audit categories. Score movement is verified or honestly reported as not yet measured.

## Companion skills

This skill pairs with two companions:

1. **`lazy-harness-audit`** — runs the audit that produces the score, breakdown, and findings this skill acts on. The intended loop is:
   1. Run `lazy-harness-audit` to get a baseline score, breakdown, and top findings.
   2. Run this skill (`lazy-harness-helper`) to address the top 2-3 gaps.
   3. Re-run `lazy-harness-audit` to confirm the score moved (or, at minimum, did not regress).

   When the audit is unavailable, fall back to the helper's own planner script.

2. **`agents-md-generate`** *(optional but recommended)* — when the audit gap is "no AGENTS.md" or "stale AGENTS.md", delegate the actual file authoring to this skill instead of using helper's bundled template. It does richer repo-fact discovery, validates each listed command, supports monorepo per-package stubs, and applies dual-audience voice rules. If it is not installed, fall back to `templates/AGENTS.md.template` (less thorough, but works standalone).

## Execution

### Phase 1: Establish the baseline

1. Resolve the target project root. If omitted, default to the current workspace root and state that assumption.
2. If the user provides a `lazy-harness-audit` report, extract every actionable field:
   - current score (with raw sum) and status (GREEN/YELLOW/RED)
   - per-category breakdown
   - **caps that fired** — these are the highest-leverage fixes; each cleared cap can unlock 10+ points at once
   - **Per-Stack Findings** — these tell you which stack-specific tool or command to target
   - Top Findings and Recommended Next Moves

   These drive Phase 2's prioritization directly.
3. If no audit report is provided, run the helper planner. The script is Python 3 stdlib only — no `pip install`. `<skill-dir>` is the directory that contains this `SKILL.md`. The agent reading this file already knows that absolute path — substitute it for `<skill-dir>` below. In shell, you can also derive it from the file path:

```bash
SKILL_DIR="$(dirname "<absolute-path-to-this-SKILL.md>")"
python3 "$SKILL_DIR/scripts/harness_helper.py" "<project-root>" --format markdown
```

For machine-readable output (stack, commands, recommendations as structured data), use `--format json`:

```bash
python3 "$SKILL_DIR/scripts/harness_helper.py" "<project-root>" --format json
```

4. If `lazy-harness-audit` is available, run it before substantial changes to capture a baseline score; run it again in Phase 4.

### Phase 2: Choose the smallest score-lifting path

Read `references/improvement-playbook.md` when choosing actions. If the audit fired one or more **caps**, clear caps first — each cap is a hard ceiling worth more than any incremental sub-item.

Cap-first priority:

| Cap fired | First move |
| --- | --- |
| 70 — no readable project guidance | Add a minimal root `AGENTS.md` |
| 65 — no reusable verification path | Add a reusable target on an existing build surface (see Phase 2 step 2 below) |
| 75 — no CI gate | Wire the same checks the local entrypoint runs into the existing CI |
| 80 — no behavior tests / fixtures | Add one approved fixture for a critical path |
| 80 — secrets/destructive boundaries undocumented | Add explicit safety rules in the agent guide |
| 75 — project does not build locally | Document the working build command or fix the broken one |

When no cap fires (or after all caps are cleared), follow this default order:

1. Add or repair root agent guidance (`AGENTS.md` or equivalent). For new or substantially-rewritten files, prefer the `agents-md-generate` skill — it does repo-fact discovery, validates each listed command, and supports monorepo stubs. If `agents-md-generate` is unavailable, use `templates/AGENTS.md.template` as a fallback.
2. Add a reusable verification entrypoint **on an existing build surface** — `make check`, a top-level package script, a Maven/Gradle `verify`/`check` chain, `./ci/build.sh`, or equivalent. Only create a bespoke `scripts/agent-check.sh` if no existing build surface fits the project's conventions.
3. Document stack-specific verification commands. Use the per-stack tables in `references/improvement-playbook.md` (Feedback and Verification section) as a reference, and confirm each command against the project's actual config — do not invent commands that the project does not already support.
4. Add explicit safety boundaries for secrets, destructive commands, production access, deployments, migrations, and logs.
5. Add or connect lightweight CI/pre-commit checks if the repo already has the platform/tooling.
6. Add behavior fixtures or golden examples for one critical path.
7. Add architecture fitness checks for a real boundary, using the stack's existing tooling (see `references/improvement-playbook.md` Architecture Fitness section for per-stack tool examples).
8. Add harness maintenance cadence and ownership.

Do not chase every point at once. A good first pass usually targets the top 2-3 gaps and keeps the diff small.

### Phase 3: Implement safely

- Read existing docs/config before editing. Preserve project-specific voice and commands.
- Do not overwrite existing `AGENTS.md`, CI, hooks, or scripts. Patch them incrementally — propose a diff or append a section rather than replacing the file.
- Use files from `templates/` only as starting points. Placeholders are written in `ALL_CAPS_TOKENS` (e.g. `CHECK_COMMANDS`, `MISSING_CHECKS`, `PROJECT_NAME`). Every uppercase token must be replaced with a real project fact, removed, or explicitly marked as a known-missing follow-up before writing. (For AGENTS.md specifically, prefer the `agents-md-generate` skill — it has no token placeholders to leak.)
- If a command is unknown, either discover it from project config (`package.json`, `Makefile`, `pyproject.toml`, etc.) or mark it honestly as missing. Do not invent commands.
- Prefer deterministic checks already available in the repo over adding new dependencies.
- Ask before adding dependencies, enabling deployments, changing CI required checks, or touching production/security config.
- For multi-stack repos, add module-level guidance only for the directories touched or clearly identifiable.
- When adding `.pre-commit-config.yaml`, also tell the user to run `pre-commit install` once — otherwise the hook is dead code.
- When adding a reusable verification target to `Makefile`, `pom.xml`, `build.gradle`, `package.json`, or `pyproject.toml`, document the exact command in `AGENTS.md` so agents can find it.
- Only if you must create a new `scripts/agent-check.sh` (no existing build surface fits): mark it executable (`chmod +x`) and link it from the root `AGENTS.md`.

### Phase 4: Verify and report

1. Run cheap syntax/validation checks for files you changed:
   - shell scripts (if any added): `bash -n <file>` (and `shellcheck` if installed)
   - YAML: `python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" <file>`
   - JSON: `python3 -m json.tool <file> > /dev/null`
   - Markdown front matter: `python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])" <file>`
2. Run the new or updated reusable verification entrypoint (`make check`, `mvn verify`, `npm run check`, etc.) if it is safe and not too expensive. If skipped, say why.
3. Re-run `lazy-harness-audit` (preferred) or the helper planner. Compare baseline vs. post-change scores.
4. Report:
   - files changed (list with one-line purpose each)
   - audit categories improved and the score delta (or "not measured, baseline missing")
   - **caps cleared** (e.g., "cap 65 → cleared by adding `make check`")
   - commands run and their exit results
   - remaining score blockers (with which audit cap, if any, still fires)
   - suggested next small improvement

## Common Improvements

Use these when they match the audit gap. For the concrete tool/command name on a given stack, consult `references/improvement-playbook.md`.

| Gap | Practical Improvement |
| --- | --- |
| No feedforward | Author `AGENTS.md` via the `agents-md-generate` skill (preferred); fall back to `templates/AGENTS.md.template` if that skill is unavailable |
| Vague verification | Add a reusable target on an existing build surface (`make check`, package script, `mvn verify`, `gradle check`, `./ci/build.sh`, …); fall back to `scripts/agent-check.sh` only if none fits |
| No safety boundary | Add security/privacy/destructive-command rules in agent guide or tool rules |
| No behavior harness | Add one approved fixture or golden example plus test policy |
| No architecture fitness | Add boundary docs first, then one deterministic import/layer check using the stack's idiomatic tool |
| No CI gate | Add or extend minimal CI to run the same checks the reusable local entrypoint runs |
| Stale harness risk | Add harness owner/cadence and a lightweight freshness checklist |

## Verification

Before finalizing:

- No local article paths, machine-specific references, or per-agent skills install paths were added. To reference the skill's own directory, use a placeholder such as `<skill-dir>` or `<absolute-path-to-this-SKILL.md>` and let the agent substitute the real path at runtime. Naming the per-agent skill install directories under a home folder (the ones used by Claude Code, Cursor, Codex, etc.) trips Skill Market security check SEC-004 — including in negative examples, because the detector matches substrings without context.
- Templates have no unreplaced `ALL_CAPS_TOKENS` placeholders unless clearly marked as examples.
- New shell scripts start with `#!/usr/bin/env bash` and `set -euo pipefail`.
- New executable scripts have executable permissions (`chmod +x`).
- Every new command in `AGENTS.md` or in the reusable verification entrypoint (`make check`, `mvn verify`, `scripts/agent-check.sh`, etc.) was either run successfully or honestly listed as "not yet validated".
- A baseline and post-change `lazy-harness-audit` score is reported, OR the report explicitly states no baseline was captured.
- The final answer states any checks not run and why.

## Honesty

Harness work should reduce ambiguity, not move it into prettier files. Specific failure modes to avoid:

- Writing a verification command into `AGENTS.md` without ever running it.
- Adding a fixture or test stub that does not actually run in the test suite.
- Adding `.pre-commit-config.yaml` without telling the user to install hooks.
- Quoting a tool (ArchUnit, dependency-cruiser, import-linter, gitleaks, …) that the project does not depend on.
- Hardcoding per-agent skill install paths (the per-agent directories under a home folder used by Claude Code, Cursor, Codex, etc.) into harness docs instead of using a portable `<skill-dir>` placeholder.
- Marking a section "done" when only docs changed.

If an improvement cannot be safely automated, produce a precise patch-ready plan instead of pretending it was fixed.
