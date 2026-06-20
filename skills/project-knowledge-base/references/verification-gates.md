# Verification Gates

<!-- Keep in sync with the summary in SKILL.md -->

## Hard Gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Non-empty output | Generated doc has substantive content beyond headings | Retry generation; if still empty, report that project analysis yielded no data |
| Template compliance | All required sections from the template are present | Re-generate missing sections explicitly |
| Valid references | Every `file:path` or code reference points to an existing file | Remove or flag invalid references, warn user |
| No raw placeholders | Output contains no `[TODO]` markers (only `[NEEDS INPUT: reason]` allowed) | Replace TODOs with specific NEEDS INPUT reasons |
| Mermaid syntax valid | Every `` ```mermaid `` block uses valid Mermaid syntax (correct node/edge format, no dangling arrows, matching brackets) | Fix syntax errors in the block; if unfixable, remove the block and add a text description instead — a broken diagram is worse than none |
| Version tracking footer | Doc ends with `<!-- PKB-metadata -->` containing valid `last_updated` (YYYY-MM-DD), `commit` (matches current HEAD short hash), `updated_by`, `review_status` (`pending` or `approved`), `review_score` (0-5), and `reviewed_by` | Append the footer using `git rev-parse --short HEAD` and today's date; AI always sets `review_status: pending`, `review_score: 0`, `reviewed_by:` (empty) |
| Bilingual i18n pipeline (when enabled) | `make gettext` and `make intl-update` are runnable; `locale/zh_CN/LC_MESSAGES/` exists; `conf.py` uses **sphinx_rtd_theme**, **myst_parser**, and required i18n settings; `_templates/layout.html` implements a **language switcher** using `html_context["available_languages"]` | Add/fix theme, templates, i18n config, and Make targets; regenerate catalogs |
| Poetry dependency management (Sphinx mode) | `pyproject.toml` exists; Sphinx/i18n deps declared; **`poetry install` succeeds in `PKB_ROOT`** | Generate/fix `pyproject.toml`; run `poetry install` then `make html` to verify |
| Sphinx scaffold present after init (`--sphinx`) | **`PKB_ROOT/Makefile` and `PKB_ROOT/conf.py` exist** from `/PKB-init --sphinx` (not only after first build) | Add missing files from templates; re-run init logic |

## Soft Gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Diagram presence | Architecture and workflow docs include Mermaid diagrams; architecture docs must cover C4 levels (Context/Container/Component, plus Code when available) | Warn user that visual aids or required C4 levels are missing, suggest regenerating `/PKB-architecture` |
| Consistent naming | Terminology matches the project's conventions (e.g., "service" vs "module") | Highlight inconsistencies for user review |
| Reasonable length | Each doc is 50-500 lines (not trivially short, not overwhelming) | Note if unusually short (may indicate shallow analysis) or long (may need splitting) |
| Ownership markers | Each doc has `<!-- maintained-by: human+ai -->` and human-judgment sections are labeled | Add missing markers; tag sections that need human review with `<!-- human-review-needed -->` |
| Translation completeness (bilingual mode) | New/changed docs have corresponding `.po` entries and no critical untranslated headings | Warn and list files needing translation updates |
| Human review approval | `review_status: approved` in the PKB-metadata footer; `review_score` >= 3; `reviewed_by` is non-empty | Warn that the doc has not been human-reviewed; run `make pkb-review-status` to see the full dashboard. Use `--strict` in CI to block deployment of unreviewed docs |
