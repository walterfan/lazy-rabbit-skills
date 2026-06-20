# PKB Help

**Author:** Walter Fan (walterfan@ustc.edu)

## Available Commands

| Command | Purpose |
|---------|---------|
| `/PKB-init [--sphinx] [--minimal] [--bilingual=zh_CN]` | Initialize a PKB skeleton under `man/` (or `doc/`) |
| `/PKB-overview` | Generate project purpose, users, deployment model |
| `/PKB-quick-start` | Generate local setup and first-run guide |
| `/PKB-architecture` | Generate C4 architecture (Context/Container/Component/Code) |
| `/PKB-tech-stack` | Generate languages, frameworks, and dependency inventory |
| `/PKB-repo-map` | Generate directory tree and entry points |
| `/PKB-data-api` | Generate data models, APIs, and event contracts |
| `/PKB-workflow <name>` | Generate a business workflow with code references |
| `/PKB-conventions` | Generate coding style, error handling, and naming rules |
| `/PKB-build-guide` | Generate build, CI, release, and packaging pipeline |
| `/PKB-testing` | Generate test strategy and living test cases |
| `/PKB-runbook` | Generate debugging, troubleshooting, and local ops guide |
| `/PKB-observability` | Generate logging, metrics, tracing, and alerting notes |
| `/PKB-documentation` | Generate PKB authoring, freshness, and publish workflow |
| `/PKB-adr <title>` | Create an Architecture Decision Record |
| `/PKB-change <id>` | Create a change proposal |
| `/PKB-feed-ai [round]` | Generate progressive AI onboarding prompts |
| `/PKB-verify` | Check completeness, freshness, and staleness |
| `/PKB-changelog` | Generate or update project and doc changelogs |
| `/PKB-build [--lang=en\|zh_CN\|all]` | Build Sphinx HTML docs |
| `/PKB-review-status` | Show human review dashboard for all PKB docs |
| `/PKB-help` | Show this help text |

## Standard Page Set

Each page heading includes its sequence number (e.g. `# 00. Project Overview`). Appendices use `# Appendix-NN: Title`. Bilingual `.po` translations must mirror the same numbering.

```text
00-overview.md        # 00. Project Overview
01-quick-start.md     # 01. Quick Start
02-architecture.md    # 02. Architecture
03-tech-stack.md      # 03. Tech Stack
04-repo-map.md        # 04. Repository Map
05-data-and-api.md    # 05. Data and API
06-workflows.md       # 06. Workflows
07-conventions.md     # 07. Conventions
08-build.md           # 08. Build, Release, and Publish
09-testing.md         # 09. Testing Strategy
10-runbook.md         # 10. Runbook
11-observability.md   # 11. Observability
12-document.md        # 12. Documentation Process
ai-guide.md           # 13. How to Use This Documentation for AI
appendix-01-faq.md    # Appendix-01: FAQ
appendix-02-glossary.md  # Appendix-02: Glossary
diagrams-guide.md     # Appendix-03: Diagram Quick Reference
CHANGELOG.md          # Appendix-04: Documentation Changelog
```

## Recommended Freshness Workflow

1. Run `scripts/check_pkb_staleness.py` (zero-token rule-based check)
2. Apply Level 1 mechanical updates via `scripts/update_doc_level1.sh`
3. Review sidecar artifacts under `_generated/`
4. Use LLM only for Level 2 (synthesis) and Level 3 (human-led judgment) updates
5. Batch doc refreshes per PR, sprint, or release -- not per commit

## Quick Start for New Users

1. Run `/PKB-init` (or `/PKB-init --minimal` for small projects)
2. Run `/PKB-overview` then `/PKB-repo-map`
3. Done -- add more pages as the project grows

For Sphinx HTML: `/PKB-init --sphinx`, then `cd man && poetry install && make html`.

For a bilingual build: `cd man && make html-all` (run `make strip-confidential` before publishing the site).
