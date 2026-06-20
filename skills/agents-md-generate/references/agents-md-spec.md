# agents.md — condensed spec reference

Source: <https://agents.md> (stewarded by the Agentic AI Foundation
under the Linux Foundation). This is a working summary for skill
authors — consult the canonical site for authoritative wording.

## What AGENTS.md is

- **A README for agents.** A predictable location at the root of a
  repository where coding agents read project context and
  instructions.
- **Open, vendor-neutral format.** Plain Markdown; no required
  frontmatter, no required schema.
- **Complements README.md.** README stays focused on humans; AGENTS.md
  contains the extra context agents need (build steps, tests,
  conventions, danger zones) that would clutter a README.

## Why a separate file

- Gives agents one predictable place to look, regardless of vendor.
- Keeps READMEs concise and focused on human contributors.
- Provides precise, agent-focused guidance that complements existing
  human docs.

## Compatibility

At time of writing, AGENTS.md is recognized by a growing ecosystem of
coding agents, including (non-exhaustive):

- **OpenAI Codex** — native.
- **Google Jules** — native.
- **Google Gemini CLI** — configure via `.gemini/settings.json`:
  ```json
  { "context": { "fileName": "AGENTS.md" } }
  ```
- **Cursor** — reads AGENTS.md alongside `.cursor/rules/`.
- **Claude Code (Anthropic)** — recognises AGENTS.md; many repos keep
  a `CLAUDE.md` symlink for backward compat.
- **Aider** — configure via `.aider.conf.yml`: `read: AGENTS.md`.
- **Factory, goose, opencode, Zed, Warp, VS Code coding-agent
  integrations, Devin (Cognition), UiPath Autopilot, Junie
  (JetBrains), Amp, RooCode, Kilo Code, Phoenix, Semgrep, GitHub
  Copilot coding-agent, Ona, Windsurf, Augment Code** — all support
  AGENTS.md as onboarding context.

Check <https://agents.md> for the current compatibility list.

## Required / optional content

The spec is intentionally minimal.

- **No required fields.** Any valid Markdown is acceptable.
- **No required sections.** Use whatever headings help your project.

**Recommended compact shape**:

1. One-sentence project purpose.
2. **Context Map**: key directories and links to README, PKB, design
   docs, and owners.
3. **Commands**: install, build, test, lint, and focused checks.
4. **Harness Rules**: compact operating rules that improve agent
   behavior.
5. **Project Rules**: repo-specific conventions, do-not rules, review
   expectations, and security constraints.
6. **AI Tooling**: primary agent clients and compatibility links.
7. **Keeping Current**: when to update AGENTS.md and how to record
   project-specific corrections.

## Monorepo semantics

- **Nested AGENTS.md files are supported.** Place an AGENTS.md inside
  each package; agents read the **nearest file** in the directory tree.
- **Precedence:** the closest AGENTS.md to the file being edited
  wins.
- **Explicit user prompts override any AGENTS.md.** The human is
  always authoritative.
- **Reference example:** the OpenAI codex monorepo reportedly ships
  ~88 AGENTS.md files across packages.

## Behavioral contract for agents

- Agents are expected to **read** AGENTS.md before making changes.
- Agents **will** run commands listed under test/build sections as
  part of task completion — so commands must be correct.
- Agents should respect the **nearest file wins** rule automatically.

## Migration patterns

If the repo already has `CLAUDE.md`, `CURSOR.md`, `.cursorrules`, or
`.github/copilot-instructions.md`:

1. Consolidate content into `AGENTS.md`.
2. Optionally keep backward-compat symlinks:
   ```bash
   mv AGENT.md AGENTS.md
   ln -s AGENTS.md AGENT.md
   # or
   ln -s AGENTS.md CLAUDE.md
   ln -s AGENTS.md GEMINI.md
   ```
3. For Aider and Gemini CLI, point their configs at `AGENTS.md`
   instead of the old file.

## Anti-patterns to avoid

- **Duplicating README.md.** AGENTS.md should complement, not
  restate.
- **Marketing prose.** Agents need actionable facts, not pitches.
- **Time-sensitive text.** Avoid dates and versions inside
  instructions; put the date in a `last_updated` footer instead.
- **Secret-laden examples.** No tokens, internal-only URLs that
  aren't in the public README, or API keys.
- **Opinion-only rules.** Rules should have an action: what to do or
  what to avoid, with reasoning the agent can apply.
- **A single giant AGENTS.md in a monorepo.** Prefer root + nested
  files so the nearest-file-wins rule does its job.

## Maintenance triggers

Update AGENTS.md when:

- Top-level directories or major modules change.
- Commands in the task runner are added, renamed, or removed.
- Documentation layout changes (KB moved, new index).
- A new agent client is wired in (new `.cursor/`, `.claude/`,
  `.codex/`, etc.).
- A convention or danger zone changes.
- A post-session retrospective finds stale commands, missing guardrails,
  or outdated repo-map entries.

## FAQ (condensed)

- **Required fields?** None. Standard Markdown.
- **What if instructions conflict?** Closest AGENTS.md wins; explicit
  user prompts override everything.
- **Will agents auto-run the commands?** Yes, if listed — agents will
  attempt programmatic checks and fix failures.
- **Can I update it later?** Yes; treat it as living documentation.
- **How large can it be?** No hard limit, but target fewer than 100
  lines for root files and fewer than 60 lines for nested package
  files. Long files lose agent attention; prefer linked docs and nested
  files for depth.
