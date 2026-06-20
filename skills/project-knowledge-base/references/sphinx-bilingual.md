# Bilingual Sphinx Standard (English + Chinese)

When the user requests bilingual or publishable HTML docs, use this **default doc stack** unless the project already pins a different approved setup:

| Layer | Package / setting | Role |
|-------|-------------------|------|
| Engine | **Sphinx** | Builds HTML from sources |
| Markdown | **myst-parser** | Parses `.md` / MyST in Sphinx |
| Theme | **sphinx-rtd-theme** | Read the Docs look; supports sidebar blocks for a switcher |
| i18n | **sphinx-intl** | gettext extraction and `.po` / `.mo` lifecycle for `zh_CN` |

Poetry should declare at least: `sphinx`, `myst-parser`, `sphinx-rtd-theme`, `sphinx-intl`, and `linkify-it-py` (required when the `linkify` MyST extension is enabled). Optional extensions include `sphinxcontrib-mermaid`, `sphinx-copybutton`, `sphinx-design`, etc.

## Language switcher (required for bilingual HTML)

Bilingual builds must not rely on users manually editing URLs. Provide a **visible language switcher** on every HTML page:

1. Set `html_theme = "sphinx_rtd_theme"` in `conf.py`.
2. Populate `html_context["available_languages"]` with entries for `en` and `zh_CN`, but route the published site to `/en/` and `/zh/` (for example via `route` fields consumed by `_templates/layout.html`).
3. Add `_templates/layout.html` that **extends** the RTD theme and overrides a block such as `sidebartitle` (or equivalent) to render a bar or button group: current language highlighted, other language(s) as links. Use CSS classes (`language-switcher`, `lang-label`, `lang-current`, `lang-link`) instead of inline styles.
4. Style the switcher in `_static/custom.css` with a **yellow/amber highlight** so it is clearly visible against the sidebar background:

```css
/* Language switcher — yellow highlight so it's easy to spot */
.language-switcher {
    margin-top: 10px;
    padding: 6px 10px;
    border-top: 1px solid #ccc;
    background-color: #fff8e1;
    border-radius: 4px;
    text-align: center;
}
.language-switcher .lang-label {
    font-size: 0.85em;
    color: #7a6200;
    font-weight: bold;
}
.language-switcher .lang-current {
    font-size: 0.85em;
    font-weight: bold;
    color: #f57f17;
    margin-left: 4px;
}
.language-switcher .lang-link {
    font-size: 0.85em;
    margin-left: 4px;
    color: #e65100;
    font-weight: bold;
    text-decoration: underline;
}
.language-switcher .lang-link:hover {
    color: #bf360c;
}
```

If the project serves a single combined tree with a landing `index.html`, the switcher may link to that landing page plus per-language subtrees — the requirement is **obvious UI to switch language**, not a specific URL shape.

## Required I18N Model

1. English Markdown/MyST files are the single source of truth.
2. Run gettext extraction to produce `.pot` templates.
3. Run `sphinx-intl update` to generate/update `.po` files under `locale/zh_CN/LC_MESSAGES/`.
4. Translators edit `msgstr` in `.po`; Sphinx compiles `.mo` during build.
5. Build both languages and provide a language switch entry point.

## Required Sphinx Configuration

- `extensions` includes `"myst_parser"` (and any other agreed extensions)
- `html_theme = "sphinx_rtd_theme"`
- `language = os.environ.get("SPHINX_LANGUAGE", "en")`
- `locale_dirs = ["locale/"]`
- `gettext_compact = False`
- `gettext_uuid = True`
- `gettext_additional_targets = ["image"]` (when image alt text should be translated)
- `html_context["available_languages"]` must include at least `en` and `zh_CN`, and must be consumed by `_templates/layout.html` for the language switcher
- `myst_fence_as_directive = ["mermaid"]` so ` ```mermaid ` fenced blocks are treated as Sphinx directives (handled by `sphinxcontrib-mermaid`) instead of unknown Pygments lexers
- `exclude_patterns` must include `'_build'`, `'_generated'`, and `'README.md'` to prevent warnings about files not in any toctree

## MyST Title Translation Workaround

MyST-parser's first `# heading` in a document becomes a special title node that Sphinx's i18n transform does **not** translate. All `<h2>` and below headings translate correctly, but the `<h1>` title stays in English.

**Fix**: Add a `doctree-resolved` event hook in `conf.py` that patches the title using the gettext catalog after all other transforms run. The template `conf.py` already includes this hook (`_translate_titles` + `setup(app)`). When regenerating `.po` files after heading changes, always:

1. `make gettext` — regenerate `.pot` catalogs
2. Delete the affected `.po` files and re-run `make intl-update` to get fresh entries with correct metadata
3. Re-apply translations to the new `.po` files (use the bulk translation workflow below if entries are numerous)
4. `make intl-build` — compile `.mo` files
5. Rebuild: `make html-zh`

### Full PO regeneration procedure ("nuclear option")

When `.po` files become out of sync with `.pot` templates (e.g. after heading renumbering, significant content restructuring, or metadata corruption), a clean regeneration with translation preservation is the safest path:

1. **Back up existing translations** — extract all non-empty `msgid`/`msgstr` pairs from each `.po` file into a Python dictionary using `polib`:

```python
import polib
backup = {}
po = polib.pofile('locale/zh_CN/LC_MESSAGES/00-overview.po')
for entry in po.translated_entries():
    backup[entry.msgid] = entry.msgstr
```

2. **Delete `.po` and `.mo` files** — remove the affected files so `sphinx-intl` can regenerate from scratch.

3. **Regenerate `.po` from `.pot`** — `make intl-update` creates fresh `.po` files with correct UUIDs, line references, and metadata.

4. **Restore backed-up translations** — apply the saved dictionary back to the new `.po` files:

```python
po = polib.pofile('locale/zh_CN/LC_MESSAGES/00-overview.po')
for entry in po.untranslated_entries():
    if entry.msgid in backup:
        entry.msgstr = backup[entry.msgid]
po.save()
```

5. **Compile and rebuild** — `make intl-build && make html-zh`

This procedure ensures `.po` metadata (UUIDs, source locations, comment lines) are correct while preserving all existing translation work.

## Visible PKB-metadata Footer

The `<!-- PKB-metadata ... -->` comment block at the end of each `.md` file is invisible in rendered HTML by default. The template `conf.py` includes a `doctree-resolved` event hook (`_inject_pkb_metadata`) that:

1. Reads each source `.md` file at build time
2. Extracts the `<!-- PKB-metadata ... -->` comment via regex
3. Appends a styled table to the page bottom showing: Last Updated, Commit, Updated By, Review Status (with colored badge), Review Score, and Reviewed By

The hook is **bilingual-aware** — labels render in English or Chinese based on `app.config.language`:

| Field | English label | Chinese label |
|-------|--------------|---------------|
| `last_updated` | Last Updated | 最后更新 |
| `commit` | Commit | 提交 |
| `updated_by` | Updated By | 更新者 |
| `review_status` | Review Status | 审核状态 |
| `review_score` | Review Score | 审核评分 |
| `reviewed_by` | Reviewed By | 审核人 |

The `review_status` field gets a colored badge: yellow for `pending`/`待审核`, green for `approved`/`已审核`.

Required CSS classes in `_static/custom.css`:
- `.pkb-metadata-footer` — container with light gray background and rounded border
- `table.pkb-metadata-table` — clean borderless table layout
- `.pkb-status-pending` — yellow badge for pending review
- `.pkb-status-approved` — green badge for approved review

The source `.md` files stay unchanged — the metadata remains a machine-parseable HTML comment while the HTML output renders it visibly. No `.po` translation is needed for the footer since labels are handled in-code.

## Cross-Reference Rules

- **Never link to files outside `PKB_ROOT`** with MyST link syntax (e.g. `[text](../CHANGELOG.md)`). Sphinx cannot resolve targets outside the source tree and will emit `myst.xref_missing` warnings. Use plain backtick text instead (e.g. `` project `CHANGELOG.md` at the repo root ``).
- **Avoid glob toctrees that match `_template/`** directories. A glob like `*/proposal` will pick up `_template/proposal` and conflict with any explicit toctree entry for the same file. Use a single hidden toctree for template files instead.

## Doc build steps (canonical)

Follow this order when building or serving the Sphinx site from **`PKB_ROOT`**:

1. **Install Python and Poetry** — Use **Python 3.10+** and install [Poetry](https://python-poetry.org/docs/#installation) so both are available on `PATH`.
2. **Install dependencies** — From `PKB_ROOT`:  
   `poetry install`  
   This reads `pyproject.toml` / `poetry.lock` and installs Sphinx, MyST, theme, sphinx-intl, and other doc dependencies into the Poetry environment.
3. **Build or serve** — Still from `PKB_ROOT`:  
   - `make html` — generate the doc site (HTML under `_build/` per Makefile layout).  
   - `make serve` — build (if needed) and start the local doc server for preview.

The generated Makefile delegates Sphinx and PKB helper commands to Poetry-managed executables, so after `poetry install` you can run plain `make <target>` from `PKB_ROOT`.

## Recommended Make targets (via Poetry)

Run from **`PKB_ROOT`** (Makefile `SOURCEDIR` is `.`):

- `make html` (build all languages, when bilingual)
- `make html-en` and `make html-zh`
- `make gettext` / `make intl-update`
- `make pkb-check-i18n`

If `PKB_ROOT` is outside the software repo, override the source root explicitly, for example: `make pkb-check-i18n PKB_REPO_ROOT=/path/to/project`.

## Dependency Management (Poetry-first)

- Use Poetry as the default dependency manager for Sphinx docs.
- Maintain doc dependencies in `pyproject.toml`: **Sphinx**, **myst-parser**, **sphinx-rtd-theme**, **sphinx-intl**, and optional extensions.
- **`make install`** in the generated Makefile delegates to Poetry for convenience; the **canonical install step for humans and CI is `poetry install`** in `PKB_ROOT`.
- Keep `requirements.txt` only as an optional fallback for environments that cannot run Poetry.

## Translation Rules

- Never edit `.pot` directly.
- Re-run `gettext` and `intl-update` whenever English source changes.
- Keep one `.po` per source file (`gettext_compact = False`) for easier review/merge.
- If `msgstr` is empty, fallback to English is acceptable but should be flagged for translation follow-up.
- Before publish or CI sign-off, run `make pkb-check-i18n` (or `python3 scripts/check_translation_sync.py --repo-root . --doc-dir .`) to flag missing, stale, fuzzy, or untranslated `zh_CN` entries.

## Bulk Translation Workflow (polib-based)

When a PKB has many untranslated `.po` entries (e.g. after initial generation or a large content update), manual editing of `.po` files is impractical. Use a **polib-based Python script** to apply translations from a dictionary in batch.

### Why polib

Standard `.po` files use multi-line continuation strings that simple regex or `sed` cannot handle reliably. The [`polib`](https://pypi.org/project/polib/) library properly parses all `.po` constructs including multi-line `msgid`/`msgstr`, metadata headers, `#, fuzzy` flags, and translator comments.

### Recommended approach

1. **Assess coverage first** — run a quick stats script to identify which files need translation and how many entries are empty:

```python
import polib, glob
for po_path in sorted(glob.glob('locale/zh_CN/LC_MESSAGES/*.po')):
    po = polib.pofile(po_path)
    pct = po.percent_translated()
    if pct < 100:
        print(f"  {po_path}: {pct:.0f}% ({len(po.untranslated_entries())} empty)")
```

2. **Build translation dictionaries per file** — create a Python script with a dictionary mapping `msgid` text to `msgstr` Chinese translation for each `.po` file. Group dictionaries by filename:

```python
T = {}
T['00-overview'] = {
    "**Call the service HTTP API directly** — get data...":
        "**直接调用服务的 HTTP API** — 从服务获取数据...",
    # ... more entries
}
T['01-quick-start'] = { ... }
```

3. **Apply translations using polib** — iterate untranslated entries and match against the dictionary:

```python
import polib
for name, trans_dict in T.items():
    po = polib.pofile(f'locale/zh_CN/LC_MESSAGES/{name}.po')
    for entry in po.untranslated_entries():
        if entry.msgid in trans_dict:
            entry.msgstr = trans_dict[entry.msgid]
    po.save()
```

4. **Compile and verify** — rebuild `.mo` files and the Chinese HTML:

```bash
make intl-build    # compile .mo from .po
make html-zh       # rebuild Chinese HTML
```

5. **Iterate** — check remaining coverage, add more entries to the dictionary, re-run.

### Practical tips

- **Translate file-by-file, highest-visibility first**: start with `index`, `00-overview`, `01-quick-start`, then work through the remaining pages.
- **Code/URL entries can map to themselves**: entries like `` `github.com/gin-gonic/gin` `` or `v1.11.0` should have `msgstr` equal to `msgid` so they don't show as untranslated.
- **Cross-reference links stay in English syntax**: `[Quick Start](01-quick-start)` translates the label but keeps the MyST link target: `[快速入门](01-quick-start)`.
- **Table cell entries**: Many `.po` files contain short table cell entries (version numbers, package names, single-word labels). These are safe to batch-translate or copy as-is.
- **Multi-line entries**: `polib` handles `msgid` that spans multiple lines transparently — the dictionary key is the joined plain text, not the `.po` wire format.
- **Add `polib` to dev dependencies**: `poetry add --group dev polib` (or add to `pyproject.toml` `[tool.poetry.group.dev.dependencies]`).
- **Save scripts for reuse**: Keep translation scripts (e.g. `scripts/translate_po.py`) in `PKB_ROOT/scripts/` so they can be re-run after English content updates.

### Translation coverage targets

| Stage | Coverage | Action |
|-------|----------|--------|
| Initial generation | 0% | Run `make gettext && make intl-update` to create `.po` files |
| First pass | 40-60% | Translate headings, navigation, short entries, and high-visibility pages |
| Second pass | 80-90% | Translate remaining body paragraphs and technical descriptions |
| Pre-publish | 95%+ | Fill remaining gaps; accept English fallback only for code blocks and URLs |

### Makefile integration

Add a `translate` target to the Makefile for convenience:

```makefile
translate:  ## Apply bulk translations from scripts/translate_po.py
	$(POETRY_RUN) python3 scripts/translate_po.py
	$(MAKE) intl-build
```

## Publishing the built site

After building the bilingual site, strip any confidential pages before publishing to your docs host (for example `https://your-docs-host.example.com`):

```bash
cd "$PKB_ROOT"
make html-all            # build the bilingual site into _build/site/{en,zh}/
make strip-confidential  # remove pages at >= CONF_MIN_LEVEL (default L3)
```

Then copy or upload the contents of `_build/site/` to whatever static hosting you use.

## Examples

### Initialize with Sphinx for publishable docs

**Input:** "I want to build HTML docs from PKB"

**Output:** `/PKB-init --sphinx --poetry` creates **`PKB_ROOT/Makefile`**, **`PKB_ROOT/conf.py`**, `pyproject.toml`, `index.md`, `_static/`, `_templates/`, plus fallback `requirements.txt`. Then:

1. Install Python 3.10+ and Poetry  
2. `cd "$PKB_ROOT" && poetry install`  
3. `make html` (or `make serve` to preview)

### Initialize bilingual docs with sphinx-intl

**Input:** "set up English and Chinese docs with sphinx-intl"

**Output:** `/PKB-init --sphinx --bilingual=zh_CN --poetry` initializes:
- `conf.py` with **myst-parser**, **sphinx-rtd-theme**, and i18n settings (`language`, `locale_dirs`, `gettext_compact=False`, `gettext_uuid=True`)
- `_templates/layout.html` with a **language switcher** backed by `html_context["available_languages"]`
- `locale/zh_CN/LC_MESSAGES/`
- Make targets: `gettext`, `intl-update`, `html-en`, `html-zh`, `html`

Then workflow is:
1. `poetry install` (in `PKB_ROOT`)
2. `make gettext`
3. `make intl-update`
4. edit `.po` files under `locale/zh_CN/LC_MESSAGES/`
5. `make pkb-check-i18n`
6. `make html` (or `make html-zh`; use `make serve` to preview)
