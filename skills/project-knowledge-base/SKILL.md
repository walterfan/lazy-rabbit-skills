---
name: project-knowledge-base
description: >-
  Creates and maintains a Project Knowledge Base (PKB): AI-readable Markdown/MyST
  docs, C4 architecture narratives, ADRs, runbooks, and Sphinx-published HTML.
  For publishable or bilingual docs, defaults to Sphinx + myst-parser +
  sphinx-rtd-theme + sphinx-intl (English source, zh_CN gettext catalogs) with a
  visible language switcher in the HTML theme. Make sure to use this skill
  whenever the user mentions PKB, project knowledge base, project docs, repo map,
  architecture doc, C4, ADR, runbook, change proposal, onboard AI, Sphinx, MyST,
  Read the Docs theme, sphinx-intl, bilingual docs, 双语文档, 中英文, 中文文档,
  语言切换, gettext, locale, or any /PKB-* command — even when they do not ask
  for structured documentation explicitly. Also trigger on "document this project",
  "create project docs", "generate architecture overview", "set up docs",
  external PKB, sibling docs repo, or "<project-name>-pkb".
version: 0.7.8
author: walterfan@ustc.edu
tags:
  - documentation
  - knowledge-base
  - architecture
  - c4-model
  - sphinx
  - i18n
  - onboarding
  - adr
category: dev-tools
platforms:
  - claude-code
  - codex
  - cursor
use_cases:
  - "Initialize a structured Project Knowledge Base for a software project"
  - "Initialize PKB outside the repo at <project-name>-pkb/man"
  - "Generate project overview, repo map, or architecture docs"
  - "Create ADRs or change proposals"
  - "Feed project knowledge to AI assistants progressively"
  - "Build HTML docs with Sphinx + MyST + sphinx-rtd-theme"
  - "Build bilingual English + Chinese docs with sphinx-intl and a language switcher"
  - "Keep PKB pages fresh with rule-based staleness checks and tiered updates"
repository: https://github.com/walterfan/lazy-rabbit-skills/tree/main/skills/project-knowledge-base
visibility: public
---
# project-knowledge-base
Create a structured Project Knowledge Base (PKB) — AI-readable documentation that enables AI to locate code, understand architecture, execute workflows, and verify changes like a human engineer.
**Author:** Walter Fan (walterfan@ustc.edu)
## 30-Second Start (for first-time users)
1. Say **"set up project docs"** (or run `/PKB-init`) -- the skill creates a `man/` folder with doc stubs and an index.
2. Run `/PKB-overview` then `/PKB-repo-map` to fill the two most useful pages.
3. Done -- you have a working knowledge base. Add more pages as needed.
For a **small project**, use `/PKB-init --minimal` to get just the 3 essential pages (`00-overview`, `01-quick-start`, `04-repo-map`).
For **Sphinx HTML output**, add `--sphinx` to step 1, then run `cd man && poetry install && make html`.
See the full [Command Summary](#command-summary) and [Quick Start](#quick-start) below for advanced options.
## PKB root path (`PKB_ROOT`)
All generated markdown, Sphinx sources, and build tooling live under a single directory **`PKB_ROOT`**. Paths below are relative to `PKB_ROOT` unless stated otherwise.
### How `PKB_ROOT` is chosen
1. **`project-name`**: Derive from the software project folder basename (e.g. repo directory name), or from `package.json` `name` / `go.mod` module path last segment when clearer. Normalize to a filesystem-safe slug if needed.
2. **Inside the project (default)**:
   - Prefer `<project-root>/doc/` only when that folder already exists and is used for non-PKB docs; otherwise use **`<project-root>/man/`**.
   - Set **`PKB_ROOT = <project-root>/man`** (or `PKB_ROOT = <project-root>/doc` when the doc-folder rule applies). The **on-disk layout inside `PKB_ROOT` is a flat standalone Sphinx doc project** (flat tree: `index.md`, `conf.py`, and `adr/` at the same level — see [Generated file structure](#generated-file-structure)).
3. **Outside the project**: When the user asks to keep PKB **outside** the repo (sibling workspace, shared docs monorepo, etc.), set  
   **`PKB_ROOT = <parent-directory>/<project-name>-pkb/man`**  
   where `<parent-directory>` defaults to the parent of `<project-root>` unless the user specifies another parent.  
   Example: project `/work/foo-app` → external PKB at `/work/foo-app-pkb/man/`.
4. **Persistence**: After `/PKB-init`, record the chosen `PKB_ROOT` in the session or project notes so follow-on `/PKB-*` commands write to the same place. If ambiguous, ask: inside (`…/man`) vs outside (`…/<project-name>-pkb/man`).
### Analysis vs output
- **Phase A** always analyzes **`<project-root>`** (source code, configs).
- **Phase B/C** write outputs to **`PKB_ROOT`** (which may be outside `<project-root>`).
## Standard PKB page set & numbering
Keep PKB numbering stable so links, translation catalogs, freshness scripts, and AI reading order remain predictable.
1. **If a PKB already exists**: preserve the current file names, numeric prefixes, and `index.md` toctree order. Do **not** renumber published pages unless the user explicitly asks for a migration.
2. **For a new PKB**: default to this standard page set:
| File | H1 heading | Purpose |
|------|------------|---------|
| `00-overview.md` | `# 00. Project Overview` | Product scope, users, deployment model, top-level summary |
| `01-quick-start.md` | `# 01. Quick Start` | First-run setup, local prerequisites, shortest path to productivity |
| `02-architecture.md` | `# 02. Architecture` | C4 architecture (Context, Container, Component, Code) |
| `03-tech-stack.md` | `# 03. Tech Stack` | Languages, frameworks, runtimes, key dependencies |
| `04-repo-map.md` | `# 04. Repository Map` | Directory tree, entry points, important modules |
| `05-data-and-api.md` | `# 05. Data and API` | Data models, schemas, APIs, events, contracts |
| `06-workflows.md` | `# 06. Workflows` | Business workflows and runtime request/response flows |
| `07-conventions.md` | `# 07. Conventions` | Coding conventions, error handling, naming, operational norms |
| `08-build.md` | `# 08. Build, Release, and Publish` | Build, CI, release, packaging, and docs publishing pipeline |
| `09-testing.md` | `# 09. Testing Strategy` | Test strategy, coverage, regression notes, living test cases |
| `10-runbook.md` | `# 10. Runbook` | Debugging, troubleshooting, local ops, common fixes |
| `11-observability.md` | `# 11. Observability` | Logging, metrics, tracing, dashboards, alerting notes |
| `12-document.md` | `# 12. Documentation Process` | How the PKB itself is generated, updated, translated, and published |
| `ai-guide.md` | `# 13. How to Use This Documentation for AI` | AI onboarding and progressive reading guidance |
| `CHANGELOG.md` | `# Appendix-04: Documentation Changelog` | **Documentation** changelog — tracks PKB page additions, translation updates, tooling changes. A separate `<project-root>/CHANGELOG.md` tracks code/feature changes. |
| `appendix-01-faq.md` | `# Appendix-01: FAQ` | Frequently asked questions |
| `appendix-02-glossary.md` | `# Appendix-02: Glossary` | Key terms and definitions |
| `diagrams-guide.md` | `# Appendix-03: Diagram Quick Reference` | Diagram tutorial and Mermaid examples |
| `adr/`, `changes/` | — | Architecture Decision Records and change proposals |
3. **Heading numbering convention**: Every PKB page must include its sequence number in the H1 heading. Main pages use the format `# NN. Title` (e.g. `# 00. Project Overview`, `# 09. Testing Strategy`). Appendices use `# Appendix-NN: Title` (e.g. `# Appendix-01: FAQ`). For bilingual builds, the Chinese `.po` translations must mirror the same numbering prefix (e.g. `msgstr "00. 项目概述"`, `msgstr "附录-01: 常见问题"`).
4. **Minimum viable PKB**: For small projects or libraries, start with `00-overview.md`, `01-quick-start.md`, and `04-repo-map.md`; leave other pages as stubs until the project grows enough to justify them.
5. **If a page is thin**: keep the number and create a short stub with verified facts or `[NEEDS INPUT: reason]` rather than collapsing or renumbering the whole set.
6. **If dedicated templates are missing** for pages like `01-quick-start.md`, `03-tech-stack.md`, `08-build.md`, `11-observability.md`, or `12-document.md`, derive the structure from the standard page contract and nearby PKB examples instead of skipping the page.
7. **If migrating from an older compact 00-07 layout**: prefer additive migration and stable mapping (`04-repo-map.md`, `06-workflows.md`, `09-testing.md`, `10-runbook.md`) rather than renumbering pages repeatedly across projects.
## Contract
- **scope_in**: Any software project with recognizable structure (`src/`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml`, `requirements.txt`, `build.gradle`, `CMakeLists.txt`, etc.). Supports generating overviews, quick-start guides, tech-stack docs, repo maps, architecture docs, workflow docs, data/API docs, conventions, build guides, testing docs, runbooks, observability docs, documentation-process docs, ADRs, change proposals, and AI onboarding prompts.
- **scope_out**: Non-software directories (e.g., pure media assets, empty folders). Binary-only projects without source code. Projects the user has not granted read access to. Generating code — this skill produces documentation only.
- **Preconditions**:
  - Target directory exists and contains at least one project marker file
  - `PKB_ROOT` is known (default `man/` or `doc/` under project, or `<project-name>-pkb/man` when external)
  - For Sphinx builds: **Python 3.10+** and **Poetry** installed; dependencies installed with **`poetry install`** run **from `PKB_ROOT`**
  - For bilingual Sphinx mode: `sphinx-intl` is managed by Poetry dependencies and `locale/zh_CN/LC_MESSAGES/` is initialized under `PKB_ROOT`
  - For `/PKB-change` and `/PKB-adr`: PKB has been initialized via `/PKB-init` under `PKB_ROOT`
- **Postconditions**:
  - Generated docs are valid Markdown (or MyST if Sphinx mode)
  - All code references use real file paths verified in the project
  - Each doc follows a corresponding template structure from `templates/docs/` when available, or the standard numbered page contract when a dedicated template does not yet exist
  - Architecture output follows a C4-first structure (Context -> Container -> Component -> Code)
  - In bilingual mode, English source is the single source of truth and Chinese is delivered through gettext catalogs (`.pot` -> `.po` -> `.mo`) using **sphinx-intl**
  - In bilingual HTML builds, every page exposes a **language switcher** (links or buttons between English and Chinese builds), driven by `html_context["available_languages"]` and a Jinja override such as `_templates/layout.html`. The switcher must use CSS classes (`language-switcher`, `lang-label`, `lang-current`, `lang-link`) styled with a **yellow/amber highlight** in `_static/custom.css` for high visibility
  - No placeholder text like `[TODO]` remains in final output (unless data is genuinely unavailable, in which case mark with `[NEEDS INPUT: reason]`)
  - Each generated doc includes an `<!-- maintained-by: human+ai -->` marker indicating shared ownership
  - Sections requiring human judgment (ADR context/decisions, business goals, acceptance criteria) are clearly distinguished from AI-maintainable sections (file paths, dependency lists, API signatures)
  - Each generated doc ends with a `<!-- PKB-metadata -->` footer containing `last_updated`, `commit`, and `updated_by` fields
  - Existing numbering and `index.md` navigation order stay stable across updates unless the user explicitly approves a renumbering or migration
## C4-First Architecture Standard
Use the C4 model (Context, Container, Component, Code) as the default architecture lens for `/PKB-architecture`. Always organize from Context down to Code, include Mermaid diagrams where feasible, and keep the Code level selective.
For the full C4 levels, UML mapping table, and generation rules, see [references/c4-standard.md](references/c4-standard.md).
## Bilingual Sphinx Standard (English + Chinese)
Default stack: **Sphinx** + **myst-parser** + **sphinx-rtd-theme** + **sphinx-intl**. English is the single source of truth; Chinese is delivered through gettext catalogs. Bilingual HTML builds require a visible language switcher on every page. Build with Poetry: `poetry install` then `make html` from `PKB_ROOT`.
For the full configuration guide (conf.py settings, language switcher setup, make targets, translation workflow, and Poetry dependency management), see [references/sphinx-bilingual.md](references/sphinx-bilingual.md).
## Maintenance Philosophy
Documentation is a living artifact co-maintained by humans and AI:
- **Human** authors intent, decisions, and domain context that only people close to the product understand — the "why" behind architecture, trade-offs accepted, and business constraints.
- **AI** keeps mechanical facts current — file paths, dependency versions, directory maps, API signatures — and flags sections that have drifted from the code.
Neither alone produces good docs. Humans without AI let docs rot; AI without humans produces accurate but shallow text. Every PKB document should carry an `<!-- maintained-by: human+ai -->` marker to reinforce this shared ownership.
### Cost-aware update strategy
| Strategy | Guidance |
|---------|----------|
| 1. Rule first, LLM second | Use `scripts/check_pkb_staleness.py` or an equivalent deterministic checker first. Spend zero tokens until rules show likely stale pages or the user explicitly asks for regeneration. |
| 2. Minimal context to the LLM | Never dump the whole repository into the model. Provide only the relevant diff, the affected PKB pages, and the source/config snippets needed for that update. |
| 3. Tiered updates | Classify the work as Level 1, Level 2, or Level 3 before deciding whether to use scripts, a targeted LLM pass, or human-authored content. |
| 4. Batch instead of thrash | Prefer refreshing PKB pages per PR, sprint, milestone, or release checkpoint rather than after every commit, unless the docs themselves are the shipped deliverable. |
### Three-level update strategy
- **Level 1 — Automatic (zero token)**: file paths, command renames, repo-map tree refreshes, dependency version extraction, index regeneration, changelog drafting, and other mechanical substitutions. If `scripts/update_doc_level1.sh` exists, run it before any LLM pass.
- **Level 2 — LLM-assisted (low token)**: added or deleted modules, API contract changes, build/config updates, or workflow changes that need synthesis. Feed the model only the diff, affected PKB page(s), and the relevant source/config snippets.
- **Level 3 — Human-led (LLM only polishes)**: ADRs, architectural rationale, product direction, new feature intent, or business trade-offs. The human supplies the "why"; AI formats, cross-links, and tightens wording without inventing rationale.
### Script-first automation toolkit
Prefer deterministic scripts before using the LLM. Use the script outputs as bounded input when a later Level 2 update still needs synthesis.
| Script | Role | Typical level |
|--------|------|---------------|
| `scripts/init_pkb.sh` | Initialize PKB skeleton from templates | Level 1 |
| `scripts/gen_repo_map.sh` | Regenerate repo-map directory tree | Level 1 |
| `scripts/gen_tech_stack.py` | Extract versions from `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, `pyproject.toml`, `requirements*.txt`, etc. | Level 1 |
| `scripts/gen_index.py` | Regenerate `index.md` from the PKB page set | Level 1 |
| `scripts/check_pkb_staleness.py` | Zero-token doc freshness report (`info` / `warning` / `critical`) | Level 1 |
| `scripts/check_translation_sync.py` | Check whether `zh_CN` gettext catalogs are in sync with English Markdown sources | Level 1 |
| `scripts/update_doc_level1.sh` | Orchestrate safe mechanical updates before any LLM pass | Level 1 |
| `scripts/extract_api_signatures.py` | Extract Tauri command and REST signatures deterministically | Level 1 or Level 2 input |
| `scripts/gen_changelog.sh` | Generate a draft changelog from `git log` | Level 1 |
| `scripts/gen_dep_graph.py` | Generate a dependency Mermaid graph from static analysis | Level 1 or Level 2 input |
| `scripts/pkb_review_status.py` | Read-only summary of document review status, scores, reviewers, and confidentiality | Level 1 |
| `scripts/strip_confidential.py` | Remove pages with `confidentiality: L3` or above from `_build/site/` before publishing the HTML site | Level 1 |
### Script artifact contract
Every deterministic PKB script should follow the same safety rules:
1. **Mechanical extraction does not replace understanding**: whenever a result needs interpretation, the generated artifact must leave explicit markers such as `[NEEDS INPUT: explain why this matters]` instead of inventing narrative.
2. **Source annotation is mandatory**: every generated artifact file must start with an `Auto-generated by ...` header and include provenance for the source files, repo root, or command range used to produce it.
3. **Do not overwrite human-maintained docs**: except for `scripts/init_pkb.sh` (which requires explicit overwrite confirmation via `--force`), scripts must write to independent sidecar artifacts under `PKB_ROOT/_generated/` or another explicit output file.
4. **LLM intervention must stay precise**: after scripts finish, the next LLM step should consume only the affected PKB page(s), the relevant source diff/snippets, and the generated artifact files — never the whole repo.
### Release-Cadence Updates
Treat docs like code: update them every release, not "when we get around to it."
1. **During PR or pre-release** — run `/PKB-verify` or a rule-based checker like `scripts/check_pkb_staleness.py` to detect stale sections before spending tokens on doc generation.
2. **During the sprint, milestone, or release window** — batch Level 1 and Level 2 updates for the affected docs (`/PKB-overview`, `/PKB-repo-map`, `/PKB-architecture`, etc.) instead of regenerating pages after every small commit. Prefer deterministic helpers like `gen_repo_map.sh`, `gen_tech_stack.py`, `gen_index.py`, `extract_api_signatures.py`, and `gen_dep_graph.py` before escalating to the LLM. These scripts should emit sidecar artifacts into `_generated/`, not rewrite narrative pages directly.
   For bilingual projects, also run `scripts/check_translation_sync.py` so `zh_CN` drift is caught before publish.
3. **For high-judgment changes** — record architectural or product decisions via `/PKB-adr`. The human writes Context and Decision; AI fills in Alternatives research and Consequences analysis.
4. **After English source changes land** — refresh gettext catalogs and rebuild the Sphinx site so published docs match the updated PKB.
Add `/PKB-verify` to your CI pipeline or release checklist so staleness is caught automatically, not by accident.
## Quick Start
1. Determine the goal:
   - **New project docs?** → `/PKB-init` (add `--external-pkb` if PKB should live at `<project-name>-pkb/man` outside the repo)
   - **Generate a specific doc?** → `/PKB-overview`, `/PKB-quick-start`, `/PKB-tech-stack`, `/PKB-repo-map`, `/PKB-architecture`, `/PKB-observability`, `/PKB-documentation`, etc.
   - **Record a decision?** → `/PKB-adr "Decision title"`
   - **Propose a change?** → `/PKB-change change-id`
   - **Feed knowledge to AI?** → `/PKB-feed-ai 1`
   - **Verify completeness or freshness?** → `/PKB-verify` (rule-based first, targeted refresh second)
2. Run the command — it analyzes the project and generates structured markdown
3. Run `scripts/update_doc_level1.sh` to apply all Level 1 mechanical refreshes automatically, or run individual helper scripts as needed (see the [Script-first automation toolkit](#script-first-automation-toolkit) table)
4. Review the generated sidecar artifacts under `PKB_ROOT/_generated/`; keep `[NEEDS INPUT: ...]` markers until a human or a targeted LLM pass resolves them
5. For bilingual PKBs, run `make pkb-check-i18n` after `poetry install` (or `python3 scripts/check_translation_sync.py --repo-root . --doc-dir .`) before publish
6. Apply only the minimal needed updates to the real PKB pages
7. **Sphinx HTML** (after `/PKB-init --sphinx`): install Python + Poetry → `cd PKB_ROOT && poetry install` → `make html` or `make serve` (see [references/sphinx-bilingual.md](references/sphinx-bilingual.md))
For changes to the skill itself, run `cd skills/project-knowledge-base && poetry install && make verify-all`.
## Local Development
Use this workflow when maintaining the skill itself:
1. Install local tooling: `cd skills/project-knowledge-base && poetry install`
2. Run the full verification suite before and after meaningful changes: `make verify-all`
3. For one-off script checks, prefer the Poetry-managed environment via `make validate-scripts`, `make validate-templates`, and `make validate-consistency`
4. When changing Python doc dependencies, update `pyproject.toml`, keep `templates/sphinx/pyproject.toml` aligned for generated PKBs, refresh `poetry.lock`, and keep `templates/sphinx/requirements.txt` as a fallback snapshot
5. When changing scaffolded files or commands, re-run `scripts/validate_skill_consistency.py` indirectly via `make verify-all` so `SKILL.md`, `references/commands.md`, `templates/`, and `scripts/init_pkb.sh` stay in sync
## Command Summary
<!-- Keep in sync with references/commands.md -->
| Command | Purpose | Output |
|---------|---------|--------|
| `/PKB-init [project-root] [--sphinx] [--minimal] [--bilingual=zh_CN] [--poetry] [--project-name <name>] [--author <name>] [--external-pkb [parent-dir]]` | Initialize PKB under `PKB_ROOT`; `--minimal` creates only core pages (00, 01, 04); prefer `scripts/init_pkb.sh` for deterministic skeleton creation, then layer in generated content | `PKB_ROOT/` with flat doc-project tree |
| `/PKB-overview` | Project purpose, users, deployment | `PKB_ROOT/00-overview.md` |
| `/PKB-quick-start` | Local prerequisites, setup, shortest path to first success | `PKB_ROOT/01-quick-start.md` |
| `/PKB-architecture` | C4 architecture (Context, Container, Component, Code) with UML alignment | `PKB_ROOT/02-architecture.md` |
| `/PKB-tech-stack` | Languages, frameworks, runtimes, and key dependencies; prefer `scripts/gen_tech_stack.py` to extract versions first | `PKB_ROOT/03-tech-stack.md` |
| `/PKB-repo-map` | Directory tree, entry points; prefer `scripts/gen_repo_map.sh` for the tree block | `PKB_ROOT/04-repo-map.md` |
| `/PKB-data-api` | DB schema, APIs, events; use `scripts/extract_api_signatures.py` when signatures can be extracted deterministically | `PKB_ROOT/05-data-and-api.md` |
| `/PKB-workflow <name>` | Business workflow with code refs | `PKB_ROOT/06-workflows.md` |
| `/PKB-conventions` | Code style, error handling | `PKB_ROOT/07-conventions.md` |
| `/PKB-build-guide` | Build, CI, packaging, release, and docs publishing pipeline; `scripts/gen_changelog.sh` can help draft release changes | `PKB_ROOT/08-build.md` |
| `/PKB-testing` | Test strategy, coverage, living test cases | `PKB_ROOT/09-testing.md` |
| `/PKB-runbook` | Setup, debugging, troubleshooting | `PKB_ROOT/10-runbook.md` |
| `/PKB-observability` | Logging, metrics, tracing, dashboards, and alerts | `PKB_ROOT/11-observability.md` |
| `/PKB-documentation` | PKB authoring, freshness, translation, and publish workflow; `scripts/gen_index.py` and `scripts/check_pkb_staleness.py` are part of the preferred deterministic path | `PKB_ROOT/12-document.md` |
| `/PKB-adr <title>` | Architecture Decision Record (focus on "why") | `PKB_ROOT/adr/0001-*.md` |
| `/PKB-change <id>` | Change proposal | `PKB_ROOT/changes/<id>/` |
| `/PKB-changelog` | Generate or update changelogs: doc changelog in `PKB_ROOT/CHANGELOG.md` and project changelog in `<project-root>/CHANGELOG.md`; prefer `scripts/gen_changelog.sh` for the mechanical draft | `PKB_ROOT/CHANGELOG.md`, `<project-root>/CHANGELOG.md` |
| `/PKB-feed-ai [round]` | AI onboarding prompts | Prompt text |
| `/PKB-verify` | Completeness + staleness check, using rule-based freshness checks before any LLM-heavy refresh; prefer `scripts/check_pkb_staleness.py` | Verification report |
| `/PKB-build [format] [--lang=en\|zh_CN\|all]` | Build Sphinx docs (single or bilingual); run from **`PKB_ROOT`** | HTML / PDF |
| `/PKB-help` | Display available PKB commands, numbered page set, and freshness workflow; see [references/help-text.md](references/help-text.md) | Help text |
## Generated file structure
Layout is a flat standalone Sphinx doc project: **English sources and Sphinx config live at the root of `PKB_ROOT`** (not nested under an extra `man/` inside `PKB_ROOT`). The directory name **`man` appears only as the last segment** when `PKB_ROOT` is `…/<project-name>-pkb/man` or `…/repo/man`.
```
PKB_ROOT/                    # e.g. …/myapp/man/ OR …/myapp-pkb/man/
├── index.md                 # Sphinx root + toctree
├── 00-overview.md
├── 01-quick-start.md
├── 02-architecture.md
├── 03-tech-stack.md
├── 04-repo-map.md
├── 05-data-and-api.md
├── 06-workflows.md
├── 07-conventions.md
├── 08-build.md
├── 09-testing.md
├── 10-runbook.md
├── 11-observability.md
├── 12-document.md
├── appendix-01-faq.md
├── appendix-02-glossary.md
├── diagrams-guide.md
├── ai-guide.md
├── CHANGELOG.md             # curated project changelog
├── conf.py                  # Sphinx — created on /PKB-init --sphinx
├── Makefile                 # build targets — created on init
├── pyproject.toml           # Poetry (recommended)
├── requirements.txt         # pip fallback
├── _static/                 # custom.css, optional lang-switcher.js
├── _templates/              # layout.html (language switcher), optional landing.html
├── locale/zh_CN/LC_MESSAGES/  # sphinx-intl catalogs (bilingual mode)
├── _generated/              # deterministic sidecar artifacts; safe to overwrite
├── scripts/                 # copied deterministic PKB helper scripts
├── adr/                     # index.md, template.md, 0001-*.md
├── changes/                 # index.md, <change-id>/{proposal,design,tasks}.md
└── _build/                  # gitignored; site/{en,zh}, gettext/
```
### Sphinx tooling created at init
When `/PKB-init --sphinx` runs, **create build tooling immediately** — do not defer `Makefile` or `conf.py` to a later `/PKB-build` or manual step.
- **Always on `--sphinx`**: `Makefile` (Unix targets: `install`, `gettext`, `intl-update`, `html`, `html-en`, `html-zh`, `serve`, `clean`, `strip-confidential`, etc.), `conf.py` with `myst_parser`, `sphinx_rtd_theme`, and `myst_fence_as_directive = ["mermaid"]` (so ` ```mermaid ` blocks are treated as Sphinx directives), `pyproject.toml` (must include `linkify-it-py` when the `linkify` MyST extension is enabled), `requirements.txt` fallback, `index.md` skeleton, `_static/`, `_templates/` stubs as needed. The `conf.py` `exclude_patterns` must include `'_build'`, `'_generated'`, and `'README.md'` to prevent Sphinx warnings about files not in any toctree.
- **Always on init**: copy deterministic PKB helper scripts into `PKB_ROOT/scripts/` so generated PKBs can run `python3 scripts/check_translation_sync.py ...`, `bash scripts/update_doc_level1.sh ...`, or `make pkb-check-i18n` locally.
- **Always on Level 1 refresh**: write candidate outputs and reports into `PKB_ROOT/_generated/` with an `Auto-generated by ...` header; leave the published PKB pages untouched until a human or a targeted LLM merge step applies the relevant facts.
- **Poetry-first scaffold**: `--poetry` is accepted for explicitness, but `/PKB-init --sphinx` should already create `pyproject.toml`; `Makefile` should delegate `install` to `poetry install`, and the canonical flow is **`poetry install`** then **`make html`** / **`serve`**.
- **With `--bilingual=zh_CN`**: extend the same init pass with `locale/zh_CN/LC_MESSAGES/`, i18n settings in `conf.py`, `layout.html` switcher, and bilingual Makefile targets.
### Version Tracking Footer
Every generated PKB document must end with a version tracking footer so staleness, review status, and confidentiality can be detected automatically:
```markdown
---
<!-- PKB-metadata
last_updated: 2026-03-30
commit: a1b2c3d
updated_by: human+ai
review_status: pending
review_score: 0
reviewed_by:
confidentiality: L1
-->
```
- **`last_updated`**: The date (YYYY-MM-DD) when this doc was last generated or meaningfully edited.
- **`commit`**: The short commit hash (`git rev-parse --short HEAD`) at the time of update. This is the key staleness indicator — if HEAD has moved significantly, the doc may be outdated.
- **`updated_by`**: Who performed the update (`human`, `ai`, or `human+ai`).
- **`review_status`**: `pending` or `approved`. A doc is either waiting for human review (`pending`) or explicitly approved by a human (`approved`). **Only a human may set `approved`; AI always sets `pending`.**
- **`review_score`**: Integer 0-5 — quality assessment. `0` = unreviewed, `1` = poor, `2` = needs work, `3` = acceptable, `4` = good (verified), `5` = excellent (production-ready). AI sets this to `0` on generation; the human sets their own score when approving.
- **`reviewed_by`**: Empty when `pending`; the reviewer's name or ID (e.g. `walter.fan`) when `approved`.
- **`confidentiality`**: Sensitivity classification, one of `L1`–`L5`. Defaults to `L1` (Public). See [Confidentiality & Publish Policy](#confidentiality--publish-policy) for the full level table and what is stripped from HTML output.
This footer is written automatically by Phase C. When reading an existing doc in Phase B, parse this footer to determine staleness before deciding whether to regenerate.
Run `make pkb-review-status` (or `python3 scripts/pkb_review_status.py --doc-dir .`) to see a dashboard of all docs with their review states and confidentiality levels.

### Confidentiality & Publish Policy
Some PKB pages contain internal-only or sensitive context (security details, customer data, unreleased product strategy) that must **not** be published as HTML. Each page declares its sensitivity in the `confidentiality` field of the `<!-- PKB-metadata -->` footer.

| Level | 中文 | English | Default audience | Published to HTML? |
|-------|------|---------|------------------|--------------------|
| `L1` | 公开 | Public / Unclassified | Anyone | **Yes** (default) |
| `L2` | 内部 | Internal | Internal team members | **Yes** |
| `L3` | 机密 | Confidential | Need-to-know team members | **No — stripped** |
| `L4` | 秘密 | Secret | Named owners only | **No — stripped** |
| `L5` | 绝密 | Top Secret | Restricted security review | **No — stripped** |

Rules:
1. **Default is `L1`**. Templates ship with `confidentiality: L1`. AI-generated pages must keep `L1` unless the human explicitly raises the level.
2. **AI never lowers the level**. If a human marks a page `L3+`, AI updates must preserve that value during refresh.
3. **HTML build still includes every level** so humans can preview locally; the strip step runs **after `make html-all` and before publishing the site**.
4. **Pre-publish strip**: `scripts/strip_confidential.py` walks the source `*.md` files, identifies any with `confidentiality: L3` or above, and removes the corresponding files from `_build/site/{en,zh}/` (HTML, source `.txt`, search-index references) before the site is published. The default minimum strip threshold is `L3`; override with `--min-level L4` for less aggressive stripping or `--min-level L2` to publish only `L1` pages.
5. **Publish flow gate**: run `make strip-confidential` (which depends on `html-all`) before publishing the built site. The strip step is mandatory; publishing the raw `make html-all` output without `strip-confidential` is **not** the recommended path.
6. **Audit before publish**: `make pkb-review-status` shows confidentiality per page so reviewers can confirm which pages will be stripped. The Sphinx HTML metadata footer also displays the confidentiality level with a colored badge.
7. **Stripped pages remain in source**: only the *built* HTML is removed. The source `.md` is still tracked in git for human readers.
## Execution
### Staleness Detection
Before any LLM-heavy command runs, do a **token-free freshness pass first**. Staleness detection should happen automatically at the start of every invocation:
1. **Prefer a deterministic checker first**: if the skill bundle or project provides `scripts/check_pkb_staleness.py` (or an equivalent project-local checker), run it before asking the LLM to analyze doc drift.
2. **If the requested change is Level 1**, run `scripts/update_doc_level1.sh` (or the repo's equivalent) before any LLM pass so mechanical updates cost zero tokens and land in sidecar artifacts instead of published docs.
3. **Prefer the smallest deterministic helper** before a broader orchestrator:
   - `scripts/init_pkb.sh` for PKB skeleton creation
   - `scripts/gen_repo_map.sh` for repo tree refresh
   - `scripts/gen_tech_stack.py` for dependency/version inventory
   - `scripts/gen_index.py` for `index.md`
   - `scripts/check_translation_sync.py` for bilingual `zh_CN` catalog drift
   - `scripts/extract_api_signatures.py` for Tauri command / REST signature extraction
   - `scripts/gen_changelog.sh` for release-note drafts
   - `scripts/gen_dep_graph.py` for dependency Mermaid diagrams
4. **Read the `<!-- PKB-metadata -->` footer** from existing `PKB_ROOT/*.md` files (and `PKB_ROOT/adr/*.md` when relevant).
5. **Get the current HEAD**: run `git rev-parse --short HEAD`.
6. **Compare**:
   - If the doc's `commit` differs from HEAD, run `git log --oneline <doc-commit>..HEAD -- <relevant-paths>` to count how many commits have touched files relevant to that doc.
   - If **10+ relevant commits** have landed since the doc was last updated, warn: _"⚠ `PKB_ROOT/02-architecture.md` was last updated at commit `a1b2c3d` (2026-01-15). There have been 23 commits to `src/` since then. Consider running `/PKB-architecture` to refresh it."_
   - If the `last_updated` date is **more than 30 days ago**, warn regardless of commit count: _"⚠ `PKB_ROOT/00-overview.md` hasn't been updated in 45 days. Consider refreshing it."_
7. If the user ran a specific command (e.g., `/PKB-architecture`), only check that doc. If they ran `/PKB-verify`, check all docs.
8. Present staleness warnings **before** generating new content, classify them as Level 1 / Level 2 / Level 3 where possible, and encourage batching related page refreshes when the docs do not need immediate publication.
### Phase 0: Command Routing
- **Entry**: User has expressed an intent (natural language or explicit `/PKB-*` command)
- **Steps**:
  1. Match user intent to the Command Summary table above
  2. If ambiguous (e.g., "document this project" could mean `/PKB-init` or `/PKB-overview`), ask the user: "Do you want to initialize the full PKB structure, or generate a specific doc like an overview?"
  3. Determine the execution path:
     - **Full discovery commands** (`/PKB-init`, `/PKB-overview`, `/PKB-quick-start`, `/PKB-architecture`, `/PKB-tech-stack`, `/PKB-repo-map`, `/PKB-data-api`, `/PKB-workflow`, `/PKB-conventions`, `/PKB-build-guide`, `/PKB-testing`, `/PKB-runbook`, `/PKB-observability`, `/PKB-documentation`, `/PKB-verify`) → proceed to Phase A
     - **Fast-path commands** (`/PKB-adr`, `/PKB-change`) → skip Phase A, verify **`PKB_ROOT`** exists, proceed directly to Phase B. If missing, prompt user to run `/PKB-init` first.
       - For `/PKB-adr` specifically: the ADR's value is in the **"why"**, not the "what". Prompt the user for the reasoning, constraints, and forces that led to the decision. AI can research alternatives and consequences, but the human must supply the context and motivation.
     - **Output-only commands** (`/PKB-feed-ai`, `/PKB-build`, `/PKB-help`) → skip Phase A, read existing **`PKB_ROOT`** docs, produce output directly
- **Exit**: Target command identified, execution path chosen
- **On fail**: If intent cannot be mapped to any command, list the available commands and ask user to clarify
### Phase 0.5: Update Classification & Context Budget
- **Entry**: Phase 0 has identified the target command or the user asked for a refresh of existing PKB pages
- **Steps**:
  1. Classify the requested work as **Level 1**, **Level 2**, or **Level 3**
  2. For **Level 1**, run deterministic scripts or direct mechanical replacements and stop if they satisfy the request
  3. For **Level 2**, collect only the minimal working set: relevant git diff, affected PKB page(s), source/config snippets, and any existing headings or metadata that must be preserved
  4. For **Level 3**, ask the human for rationale, constraints, and intended trade-offs before drafting
  5. Prefer one batched update pass for a PR, sprint, or milestone over repeated per-commit rewrites unless the user explicitly wants immediate updates
- **Exit**: Either the zero-token update is complete or a bounded context package is ready for Phases A/B
- **On fail**: If the level is unclear, default to the safer path: ask for human intent rather than letting the LLM guess
### Phase A: Project Discovery
- **Entry**: Phase 0 routed here (full discovery commands only)
- **Steps**:
  1. Verify project markers exist (`package.json`, `go.mod`, `pom.xml`, `Cargo.toml`, `requirements.txt`, `build.gradle`, `CMakeLists.txt`, `src/`, etc.)
  2. Read key config files to identify language, framework, and build system
  3. Run `tree -L 3 -d` (or equivalent) to map directory structure
  4. Identify entry points: main files, routers, DI containers, CLI entrypoints
  5. Read up to 5-10 key source files per target page (entry points, routers, models, configs) — prioritize files with the most imports or cross-references, and do **not** dump the whole repo into the LLM context
- **Exit**: Language, framework, build system, and directory layout are known
- **On fail**: If no project markers found, stop and tell the user: "This directory doesn't appear to be a software project. Ensure you're in the project root."
### Phase B: Template Selection & Generation
- **Entry**: Phase A complete (or Phase 0 fast-path for ADR/change commands)
- **Steps**:
  1. Load the corresponding template from `templates/docs/`, `templates/adr/`, or `templates/changes/`; if a dedicated template does not yet exist for a standard numbered page, derive the structure from the standard page contract and nearby PKB examples
  2. If the target file already exists, read it first — preserve user-added content, update generated sections, and note what changed
  3. Analyze only the relevant source files, configs, existing docs, and diff snippets needed for this update
  4. Fill each template section with project-specific content. For architecture docs, enforce C4 order: Context -> Container -> Component -> Code, and use the C4/UML mapping table when selecting diagram styles.
  5. For code references, verify file paths exist before including them — broken references confuse both human readers and AI consumers
  6. Generate Mermaid diagrams where architecture or workflows benefit from visualization
  7. If bilingual mode is enabled: ensure the full stack exists under **`PKB_ROOT`** — **myst-parser**, **sphinx-rtd-theme**, **sphinx-intl** in Poetry; `conf.py` with `html_theme` and `myst_parser`; `locale/`, Make targets for gettext/intl-update/html-en/html-zh; **`_templates/layout.html`** language switcher wired to `available_languages`; optional `_templates/landing.html` for a bilingual entry page
  8. If Sphinx mode is enabled: **`Makefile` and `conf.py` must already exist** (created by `/PKB-init --sphinx`). Ensure `pyproject.toml` exists as the default Python dependency manifest, keep `requirements.txt` only as fallback, and instruct users to run **`poetry install`** then **`make html`** / **`serve`**. Do not leave Sphinx projects without a Makefile/`conf.py` until the first build.
- **Exit**: Draft document with all required sections filled
- **On fail**: If a section cannot be filled due to missing information, mark it `[NEEDS INPUT: what's missing]` and continue with remaining sections. Do not skip sections silently.
### Phase C: Refinement & Output
- **Entry**: Phase B complete
- **Steps**:
  1. Verify all file path references are valid (glob or stat check)
  2. Remove redundancy across sections
  3. Ensure consistent terminology (match the project's own naming)
  4. If Sphinx mode: convert to MyST syntax, verify `conf.py` compatibility
  5. Stamp the version tracking footer: run `git rev-parse --short HEAD` to get the current commit hash, set `last_updated` to today's date, set `updated_by` to `human+ai` (or `ai` if no human edits were involved). If the doc already has a `<!-- PKB-metadata -->` footer, replace it; otherwise append it.
  6. Set review fields in the footer according to these rules:
     - **Standard AI update (Level 2/3)**: set `review_status: pending`, `review_score: 0`, `reviewed_by:` (empty). The human must re-approve after any substantive change.
     - **Trivial Level 1 mechanical fix** (path rename, version bump): keep existing `review_status`, `review_score`, and `reviewed_by` unchanged; set `updated_by: ai+trivial`.
     - **Never** set `review_status: approved` — only a human may do that.
  7. Write the file under **`PKB_ROOT`**
- **Exit**: Final document written with version tracking footer, postconditions met
- **On fail**: If file write fails (permissions, path issues), report the error and suggest the user check directory permissions. If invalid references are found, list them and ask the user to confirm or correct.
### Test Case Maintenance
Test documentation is not a snapshot — it must evolve with the code:
1. **When a new feature is added**: `/PKB-testing` should append test cases covering the new behavior (happy path, edge cases, error scenarios). AI drafts the cases; a human validates they match the actual acceptance criteria.
2. **When a bug is fixed**: Add a regression test case to `PKB_ROOT/09-testing.md` documenting the bug scenario, so the same class of issue is caught in future.
3. **When architecture changes**: Review existing test cases for invalidated assumptions (e.g., a service split means integration test boundaries changed). AI flags potentially affected cases; a human confirms.
4. **Per release**: Run `/PKB-testing` to regenerate the test strategy section and diff against the previous version — highlight new modules without test coverage.
The goal is that `PKB_ROOT/09-testing.md` serves as a living quality assurance checklist, not a one-time artifact.
### Resilience
- **Rollback**: If Phase C finds postcondition violations (e.g., broken references), return to Phase B with specific feedback on what to fix
- **Degradation**: If `tree` command is unavailable, fall back to `ls -R` or glob patterns to build directory map
- **Scope guard**: If the user asks to document something outside scope_in (e.g., generate code, document a non-software directory), explain why and suggest an alternative
## Verification
Every generated document must pass hard gates (non-empty output, template compliance, valid file references, no raw `[TODO]` placeholders, valid Mermaid syntax, PKB-metadata footer, and Sphinx/i18n scaffold when enabled) and soft gates (diagram presence, consistent naming, reasonable length, ownership markers, translation completeness, and human review approval).
For the full gate tables, see [references/verification-gates.md](references/verification-gates.md).
## Examples
### Initialize a project knowledge base
**Input:** "set up project docs for this repo"
**Output:** `/PKB-init` creates **`PKB_ROOT`** (default `…/man/`) with the flat doc-project tree, lists what was created, suggests starting with `/PKB-overview`.
### Initialize PKB outside the project folder
**Input:** "put the knowledge base next to the repo, not inside it"
**Output:** `/PKB-init --external-pkb` creates **`PKB_ROOT = <parent>/<project-name>-pkb/man`** with the same layout as above; analysis still uses the original project root.
### Generate repo map for a Go project
**Input:** "create a repo map"
**Output:** `/PKB-repo-map` analyzes directory tree, identifies entry points (`cmd/main.go`, `internal/router/router.go`), documents naming conventions and layering patterns, saves to `PKB_ROOT/04-repo-map.md`.
### Record an architecture decision
**Input:** "we decided to use PostgreSQL over MongoDB"
**Output:** `/PKB-adr "Use PostgreSQL over MongoDB"` creates `PKB_ROOT/adr/0001-use-postgresql-over-mongodb.md` with Context, Decision, Alternatives (with pros/cons), and Consequences.
### Feed project knowledge to AI progressively
**Input:** "onboard AI into this project"
**Output:**
- Round 1: AI reads overview + repo map, summarizes, lists gaps
- Round 2: Deep dive into 2-3 key workflows
- Round 3: Module-by-module acceptance
### Keep PKB fresh without wasting tokens
**Input:** "check which project docs are stale and update only what matters"
**Output:** Run `scripts/check_pkb_staleness.py` (or equivalent) first, classify suggested updates into Level 1 / 2 / 3, apply zero-token fixes like repo-map or dependency refreshes where possible, and only then send the LLM the diff, affected PKB pages, and relevant source snippets for targeted updates.
### Prefer scripts before the model
**Input:** "initialize the PKB, regenerate the repo map, refresh the index, extract API signatures, and draft a changelog"
**Output:** Use `scripts/init_pkb.sh`, `scripts/gen_repo_map.sh`, `scripts/gen_index.py`, `scripts/extract_api_signatures.py`, and `scripts/gen_changelog.sh` first. Only if those script outputs still need narrative synthesis should the LLM update `00-overview.md`, `05-data-and-api.md`, `08-build.md`, or `12-document.md`.
For Sphinx and bilingual doc examples, see [references/sphinx-bilingual.md](references/sphinx-bilingual.md#examples).
## Feedback
### Failure Modes
Common failure modes include: skill not triggering (missing trigger phrases), shallow docs (insufficient source analysis), expensive LLM usage (no rule-based freshness check first), stale numbering in scripts, broken file references, Sphinx/MyST build errors (missing `linkify-it-py`, Mermaid lexer warnings), translation drift, and docs churning on every commit.
For the full symptom/root-cause/fix table, see [references/failure-modes.md](references/failure-modes.md).
### Boundary Examples
- **Minimal project**: Single-file script with no config → should still produce an overview and repo map (just shorter), skip architecture/workflow sections with `[NEEDS INPUT]`
- **Monorepo**: Multiple projects in subdirectories → ask user which sub-project to document, or generate a top-level overview linking to per-project docs
- **No source code yet**: Skeleton project with only config files → produce overview and conventions docs, mark other sections as pending
- **Non-software directory**: Media assets, raw data → refuse politely, explain scope limitation
- **Partial update**: User says "update the architecture section about the new auth module" → read existing `PKB_ROOT/02-architecture.md`, preserve all other sections, update only the relevant parts, note what changed at the top of the commit/output
### Improvement Triggers
- Users frequently rewrite generated architecture sections → review template structure and analysis depth in Phase B
- File path references are often wrong → strengthen verification in Phase C, consider using glob patterns instead of assumptions
- Users ask for formats not supported (e.g., AsciiDoc, reStructuredText) → consider adding format options
- Generated docs become stale quickly → suggest adding `/PKB-verify` to CI or pre-commit hooks
- Users complain about token cost → strengthen the Level 1 / Level 2 split and reduce LLM context further
- Teams keep renumbering pages after adding new sections → adopt and preserve the standard 00-12 page set earlier
## Additional Resources
- Detailed per-command instructions: [references/commands.md](references/commands.md)
- Static help text for `/PKB-help`: [references/help-text.md](references/help-text.md)
- C4 architecture standard: [references/c4-standard.md](references/c4-standard.md)
- Verification gates: [references/verification-gates.md](references/verification-gates.md)
- Failure modes: [references/failure-modes.md](references/failure-modes.md)
- Sphinx & bilingual configuration: [references/sphinx-bilingual.md](references/sphinx-bilingual.md)
- PKB initializer: [scripts/init_pkb.sh](scripts/init_pkb.sh)
- Repo-map generator: [scripts/gen_repo_map.sh](scripts/gen_repo_map.sh)
- Tech-stack extractor: [scripts/gen_tech_stack.py](scripts/gen_tech_stack.py)
- Index generator: [scripts/gen_index.py](scripts/gen_index.py)
- Rule-based freshness checker: [scripts/check_pkb_staleness.py](scripts/check_pkb_staleness.py)
- Translation sync checker: [scripts/check_translation_sync.py](scripts/check_translation_sync.py)
- API signature extractor: [scripts/extract_api_signatures.py](scripts/extract_api_signatures.py)
- Changelog draft generator: [scripts/gen_changelog.sh](scripts/gen_changelog.sh)
- Dependency graph generator: [scripts/gen_dep_graph.py](scripts/gen_dep_graph.py)
- Review status dashboard: [scripts/pkb_review_status.py](scripts/pkb_review_status.py)
- Confidentiality strip (pre-publish gate): [scripts/strip_confidential.py](scripts/strip_confidential.py)
- Template link validator: [scripts/validate_template_links.py](scripts/validate_template_links.py)
- Skill self-consistency checker: [scripts/validate_skill_consistency.py](scripts/validate_skill_consistency.py)
- Zero-token mechanical refresh helper: [scripts/update_doc_level1.sh](scripts/update_doc_level1.sh)
- Local Poetry config for skill development: [pyproject.toml](pyproject.toml)
- AI onboarding prompt collection: [prompts.md](prompts.md)
- Diagram examples (Mermaid): [references/diagram-examples.md](references/diagram-examples.md)
