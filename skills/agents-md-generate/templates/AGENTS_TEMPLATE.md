# AGENTS.md - {{PROJECT_NAME}}

<!-- Follows https://agents.md. Keep root files 70-90 lines when possible. -->

{{ONE_SENTENCE_PURPOSE}}

Read this before editing. This file is the operating map, not the
manual; keep deep architecture, domain notes, and runbooks in linked
docs such as `man/`.

## Context Map

- README: {{README_POINTER_OR_REMOVE}}
- Project Knowledge Base: {{PKB_POINTER_OR_REMOVE}}
- Design / change docs: {{DESIGN_DOCS_POINTER_OR_REMOVE}}
- Owner / help: {{OWNER_HINT_OR_REMOVE}}

Repo layout:

{{REPO_MAP_BULLETS}}

## Commands

Use {{TASK_RUNNER_OR_PACKAGE_MANAGER}} so local commands match CI and
the lockfile.

```bash
{{INSTALL_COMMAND}}  # prepare dependencies / local environment
{{BUILD_COMMAND}}    # build the package or deployable artifact
{{TEST_COMMAND}}     # run the suite used for PR confidence
{{LINT_COMMAND}}     # run static checks / formatting gates
```

Focused checks:

```bash
{{FOCUSED_CHECKS_OR_REMOVE}}
```

Mark unverified commands with `# TODO verify`; do not leave stale
commands that agents will try to run.

## Harness Rules

- Never fabricate paths, APIs, commands, tests, or results; inspect the
  repo or run the command first.
- Ask when ambiguity changes the output; otherwise resolve uncertainty
  by reading files and existing patterns.
- Think before coding: state assumptions, tradeoffs, and success
  criteria before non-trivial edits.
- Keep it simple: solve the requested problem without speculative
  features, one-off abstractions, or future-proofing.
- Make surgical changes: every changed line should trace to the request;
  leave unrelated code and formatting alone.
- Verify before reporting done; a plausible diff is not proof.

## Project Rules

- {{PROJECT_RULE_1}}
- {{PROJECT_RULE_2}}
- {{PROJECT_RULE_3}}
- {{PROJECT_RULE_4}}
- {{DO_NOT_RULE_1}}
- {{DO_NOT_RULE_2}}
- {{SECURITY_RULE_1}}
- {{SECURITY_RULE_2}}

## AI Tooling

Primary tools: {{AI_TOOLS_OR_REMOVE}}

- Codex / Cursor: read `AGENTS.md` at the repo root; nested
  `AGENTS.md` files override root rules for package-specific work.
- Claude Code / Gemini CLI: use compatibility symlinks only when
  requested or already present: `CLAUDE.md -> AGENTS.md`,
  `GEMINI.md -> AGENTS.md`.

## Keeping Current

Update this file when commands, layout, guardrails, agent tools, or
linked docs move. If `man/` changes, update links here instead of
copying its content.

When the user corrects a project-specific agent mistake, add or tighten
one concrete rule here, then prune obsolete rules later.

<!-- last_updated: {{DATE}} -->
