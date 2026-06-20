---
name: agents-md-generate
description: >-
  Use when asked to create, refresh, improve, or migrate AGENTS.md, the
  vendor-neutral coding-agent onboarding file read by Codex, Cursor,
  Claude Code, Gemini CLI, Aider, and similar tools. Handles existing
  AGENTS.md / CLAUDE.md / CURSOR.md / .cursorrules files, PKB-backed
  repos, monorepos, and optional compatibility symlinks.
version: 0.2.0
author: walterfan@ustc.edu
tags:
  - agents-md
  - ai-onboarding
  - harness
  - documentation
  - coding-agents
category: dev-tools
use_cases:
  - "Generate a concise AGENTS.md for a repo"
  - "Improve an existing AGENTS.md or CLAUDE.md"
  - "Migrate CLAUDE.md / CURSOR.md / .cursorrules into AGENTS.md"
  - "Link AGENTS.md to a Project Knowledge Base under man/ or docs/"
  - "Raise a project's AI coding-agent harness level"
platforms:
  - codex
  - claude-code
  - cursor
  - gemini-cli
  - aider
visibility: public
---

# agents-md-generate

Create or improve a concise, high-signal `AGENTS.md` for coding agents.
The file should make agents more correct, more surgical, and easier to
verify without duplicating the repo's README or Project Knowledge Base.

Use progressive disclosure:

- `AGENTS.md` is the operating map: commands, boundaries, harness rules,
  and links.
- `README.md` remains the human overview.
- `man/`, `docs/`, ADRs, RFCs, and design specs remain the deep source
  of architecture, domain knowledge, and runbooks.

## Core Outcome

The delivered repo has:

- `AGENTS.md` at the target root, or an improved existing one.
- A compact harness section adapted from strong public AGENTS.md
  examples, including: no fabrication, ask on material ambiguity,
  think before coding, simplicity first, surgical changes, and verified
  execution.
- Repo-specific commands and guardrails grounded in files that exist.
- Links to `man/` or other PKB docs when present, with no copied
  architecture/tutorial content.
- Optional compatibility symlinks only when the user wants them:
  `CLAUDE.md -> AGENTS.md` and/or `GEMINI.md -> AGENTS.md`.

## Ask First

Before generating or migrating, ask one concise preference question when
the answer is not already supplied:

> Which AI coding tools should this optimize for: Codex, Claude Code,
> Cursor, Gemini CLI, Aider, or another tool? Should I create
> `CLAUDE.md` / `GEMINI.md` symlinks to `AGENTS.md`?

If the repo already contains `.claude/`, `.cursor/`, `.codex/`,
`.gemini/`, or `.aider`, mention that as the inferred default, but still
ask before creating symlinks or replacing existing files.

## Workflow

### 1. Discover

Run the helper from the skill root:

```bash
bash scripts/discover_repo.sh <repo-path>
```

Then read only what is needed:

- Existing agent files: `AGENTS.md`, `CLAUDE.md`, `CURSOR.md`,
  `.cursorrules`, `.github/copilot-instructions.md`.
- `README.md` for the one-sentence purpose.
- Task runners and CI files for real install/build/test/lint commands.
- `man/index.md`, `man/README.md`, `docs/index.md`, or equivalent PKB
  index for links only.
- Package boundaries when monorepo signals exist.

Do not invent missing commands, owners, paths, or docs. Use
`# TODO verify` only when a useful command is likely but not proven.

### 2. Decide Shape

Pick the smallest useful shape:

| Repo shape | Output |
|---|---|
| Small script or tiny library | Root `AGENTS.md`, 30-60 lines |
| Typical app or package | Root `AGENTS.md`, 60-90 lines |
| PKB-backed repo with `man/` | Link-heavy root `AGENTS.md`, no duplicated PKB content |
| Monorepo | Short root `AGENTS.md`; nested files only for packages with distinct commands or boundaries |

Prefer one root file unless nested rules truly prevent mistakes. Long
instructions belong in `man/`, `docs/`, or nested `AGENTS.md`.

### 3. Draft

Use `templates/AGENTS_TEMPLATE.md` for root files and
`templates/AGENTS_SUBPACKAGE_TEMPLATE.md` for nested files.

Required sections:

- **Context Map**: project purpose, key directories, and links to README,
  PKB, design docs, or owners. If `man/` exists, link it and state that
  deep architecture and runbooks stay there.
- **Commands**: install/build/test/lint/focused checks. Prefer existing
  task runners over raw commands.
- **Harness Rules**: compact operating rules that improve agent behavior:
  honesty, ambiguity handling, planning, simplicity, surgical changes,
  and verification.
- **Project Rules**: only repo-specific conventions, danger zones,
  review expectations, and security constraints.
- **AI Tooling**: primary tools chosen by the user or inferred from repo
  config; mention symlinks only if requested or already present.
- **Keeping Current**: update triggers and a one-line learning loop after
  user corrections.

Style:

- Write imperatives with a short reason.
- Keep bullets concrete; every rule should prevent a known failure mode.
- Link out for rationale; do not copy PKB, README, ADR, or runbook text.
- Delete placeholder groups that do not apply.
- Target under 90 lines; hard cap 100 for root and 60 for nested files.

### 4. Merge Existing Agent Files

If `AGENTS.md` already exists, improve it instead of replacing it:

- Keep project-specific commands, danger zones, ownership, and hard-won
  lessons.
- Remove duplicated README/PKB/tutorial content and replace it with
  links.
- Re-check every command against current repo files.
- Tighten vague rules into concrete imperatives with reasons.
- Preserve user-specific tool preferences when still valid.

If only `CLAUDE.md`, `CURSOR.md`, `.cursorrules`, or Copilot
instructions exist:

- Migrate reusable repo rules into `AGENTS.md`.
- For `.cursorrules`, translate the rules; do not symlink it to
  Markdown.
- Leave existing non-symlink files untouched unless the user explicitly
  asks to replace them.

### 5. Optional Compatibility Links

Only create symlinks after user approval and only when the target path is
clear:

```bash
ln -s AGENTS.md CLAUDE.md
ln -s AGENTS.md GEMINI.md
```

If `CLAUDE.md` or `GEMINI.md` already exists and is not a symlink, ask
before changing it. Never delete or overwrite an existing agent file
silently.

For Cursor, prefer `AGENTS.md` plus existing `.cursor/rules/` when
present. For Gemini CLI or Aider config files, point configs at
`AGENTS.md` only if the user asks for config edits.

## Verification

Block delivery until these pass:

- `AGENTS.md` exists at the target path.
- No unresolved `{{PLACEHOLDER}}` remains.
- Root file is 100 lines or fewer; nested files are 60 lines or fewer.
- Commands are real or marked `# TODO verify`.
- Links to `README.md`, `man/`, `docs/`, ADRs, and design docs resolve.
- No secrets, tokens, or private URLs are introduced.
- Existing user changes outside the target files are untouched.
- If symlinks were created, `readlink CLAUDE.md` or `readlink GEMINI.md`
  returns `AGENTS.md`.

Warn, but still deliver:

- No reliable test command was found.
- No PKB index exists for a complex repo.
- A monorepo would benefit from nested files, but the user declined.

## Delivery Summary

Return a short summary:

- Files written or improved.
- Line count.
- AI tools optimized for.
- Symlinks created or intentionally skipped.
- Commands verified and any `# TODO verify` markers.
- Existing files merged or left untouched.

## Reference Principles

This skill absorbs the useful parts of strong public AGENTS.md examples
without copying their full shape:

- Working, verified code matters more than plausible diffs.
- Agents must not fabricate files, APIs, commands, or results.
- Ambiguity that changes the output requires a question.
- Simplicity and surgical changes beat speculative extensibility.
- `AGENTS.md` should improve through real corrections, then be pruned so
  it stays short enough to read.

## Resources

- Root template: `templates/AGENTS_TEMPLATE.md`
- Nested template: `templates/AGENTS_SUBPACKAGE_TEMPLATE.md`
- Discovery helper: `scripts/discover_repo.sh`
- Spec summary: `references/agents-md-spec.md`
- Voice rules: `references/voice-rules.md`
- Examples: `references/examples.md`

<!-- last_updated: 2026-06-05 -->
<!-- maintained-by: walter.fan -->
