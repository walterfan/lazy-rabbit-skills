# Failure Modes

<!-- Keep in sync with the summary in SKILL.md -->

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Skill never triggers | Description missing key trigger phrases | Ensure description lists: PKB, project docs, repo map, architecture doc, ADR, runbook, onboard AI, Sphinx, MyST, sphinx-rtd-theme, sphinx-intl, bilingual / 双语 |
| Generated docs are shallow / generic | Insufficient project analysis — only read config files, not source | Expand Phase A to read key source files (routers, models, main entry points), not just configs |
| LLM usage is expensive and noisy | The whole repo was given to the model for a small doc update | Run rule-based freshness checks first, then give the model only the diff, affected PKB page(s), and relevant source/config snippets |
| Level 1 scripts point to the wrong PKB pages | The script still uses an old numbering scheme | Keep helper scripts aligned with the standard 00-12 page set and test them against current templates |
| Invalid file references in output | Paths assumed from directory structure without verification | Phase C must verify every path reference exists before writing |
| ADR created without PKB | User ran `/PKB-adr` before `/PKB-init` | Check precondition; if **`PKB_ROOT`** missing, prompt user to run `/PKB-init` first |
| Sphinx build fails | MyST syntax errors in generated markdown | Validate MyST syntax in Phase C; common issues: unescaped `{`, missing directive syntax |
| Chinese docs not updated | English sources changed but gettext/intl-update not re-run | Re-run `make gettext` then `make intl-update`, update `.po` translations, rebuild |
| Chinese translations drift silently | No deterministic check compares `.md` and `.po` freshness | Run `scripts/check_translation_sync.py` in CI or before publish, then refresh catalogs and translate unresolved entries |
| Translation files are hard to review | `gettext_compact=True` created monolithic catalog | Set `gettext_compact=False` and regenerate catalogs |
| Existing translations keep getting lost | Unstable message identifiers across refactors | Set `gettext_uuid=True` and regenerate catalogs |
| Dependency setup drifts across machines | pip and Poetry are mixed ad hoc | Standardize on **`poetry install`** in `PKB_ROOT`, then **`make html`**; keep pip/`requirements.txt` as fallback only |
| Nested `man/man` or missing Sphinx files | Treated `PKB_ROOT` wrong or skipped init scaffold | Use a flat doc-project layout inside `PKB_ROOT`; ensure `/PKB-init --sphinx` wrote `Makefile` + `conf.py` |
| Bilingual site has no language switcher | Missing `_templates/layout.html` or `available_languages` | Add RTD theme template override and wire switcher URLs for `en` / `zh` while keeping the locale as `zh_CN` |
| Docs duplicate README content | Skill copied README without adding analytical value | Phase B should synthesize and restructure, not copy — cross-reference README but add architecture analysis, dependency reasoning, etc. |
| Numbering drifts between projects | PKB pages were created ad hoc and later renumbered | Preserve existing numbering, or initialize the standard 00-12 page set and keep gaps/stubs instead of renumbering |
| Wrong doc type generated | AI picked `/PKB-overview` but user wanted `/PKB-architecture` | Ambiguous user intent was not clarified. Phase 0 must disambiguate before proceeding — ask the user when the intent could map to multiple commands |
| Test cases out of date | `09-testing.md` references deleted modules or misses new features | Run `/PKB-testing` every release; diff against previous version to catch drift |
| AI-generated "why" is hollow | ADR context section reads like a summary, not a reasoning chain | AI should prompt the human for forces/constraints instead of guessing; mark context as `<!-- human-review-needed -->` if generated without human input |
| Docs silently stale | No metadata footer, so staleness is invisible | Ensure Phase C always stamps the `<!-- PKB-metadata -->` footer; `/PKB-verify` should flag any doc missing the footer |
| Staleness check misses drift | Commit hash matches but content changed via rebase or amend | Also compare `last_updated` date as a secondary check; warn if >30 days old regardless of commit |
| Docs churn on every commit | No batching policy, so the same pages are regenerated repeatedly | Batch Level 2 refreshes by PR, sprint, or milestone unless immediate publication is required |
| Chinese H1 titles stay in English while H2+ headings translate correctly | MyST-parser's first `# heading` becomes a title node that Sphinx's i18n transform skips | Add a `doctree-resolved` event hook in `conf.py` (see `_translate_titles` in template) that patches the document title via gettext after all transforms run |
| Sphinx warns "document not in any toctree" for `_generated/` files | `_generated/` not in `exclude_patterns` in `conf.py` | Add `'_generated'` and `'README.md'` to `exclude_patterns` in `conf.py` |
| Sphinx warns "document referenced in multiple toctrees" | A glob toctree like `*/proposal` matches `_template/proposal` which is also in a hidden toctree | Remove the glob toctree or use a hidden toctree only for template files; avoid glob patterns that match `_template/` |
| Sphinx warns "myst cross-reference target not found" for `../CHANGELOG.md` | Link syntax `[text](../CHANGELOG.md)` points outside the Sphinx source tree | Use plain backtick text (`` `CHANGELOG.md` ``) instead of MyST link syntax for files outside `PKB_ROOT` |
| Chinese pages show English body text despite correct H1 titles | `.po` files have empty `msgstr` for body paragraphs — only headings were translated | Use the polib-based bulk translation workflow (see `sphinx-bilingual.md`) to fill all empty `msgstr` entries; run `make intl-build && make html-zh` after |
| Regex/sed-based `.po` editing corrupts multi-line entries | `.po` files use continuation lines (`""` prefix) that break naive text substitution | Always use the `polib` Python library to parse and modify `.po` files; never use `sed`, `awk`, or regex for `.po` editing |
| `.po` translations not applied after `make html-zh` | `.mo` files were not recompiled after `.po` edits | Run `make intl-build` (which calls `sphinx-intl build`) to compile `.mo` from `.po` before rebuilding HTML |
| `.po` files become out of sync with `.pot` after heading renumbering | `msgid` in `.po` no longer matches `.pot` entries due to changed headings | Use the "nuclear option" PO regeneration procedure: back up translations, delete `.po`/`.mo`, regenerate from `.pot`, restore translations (see `sphinx-bilingual.md`) |
| Deployed Chinese site shows stale English content | The published site was not rebuilt after translation updates | Always run `make html-all` (and `make strip-confidential`) after any translation update, then re-publish the site |
| PKB-metadata footer not visible in HTML | `conf.py` missing the `_inject_pkb_metadata` hook, or `_static/custom.css` missing `.pkb-metadata-footer` styles | Ensure the template `conf.py` includes both `_translate_titles` and `_inject_pkb_metadata` in `setup(app)`, and `custom.css` includes the `.pkb-metadata-footer`, `.pkb-metadata-table`, `.pkb-status-pending`, `.pkb-status-approved` classes |
| `ModuleNotFoundError: Linkify enabled but not installed` during Sphinx build | `conf.py` enables the `linkify` MyST extension but `linkify-it-py` is not in `pyproject.toml` | Add `linkify-it-py (>=2.0.0)` to `pyproject.toml` dependencies and re-run `poetry install` |
| `WARNING: Unknown Pygments lexer 'mermaid'` during Sphinx build | MyST treats ` ```mermaid ` fenced blocks as code blocks for Pygments instead of Sphinx directives | Add `myst_fence_as_directive = ["mermaid"]` to `conf.py` so `sphinxcontrib-mermaid` handles them |
| `conf.py` uses `SPHINX_LANGUAGE` env var but `sphinx-bilingual.md` says `DOC_LANGUAGE` | Inconsistent env var name between template and reference doc | Standardize on `SPHINX_LANGUAGE` in both `conf.py` template and all reference docs |
