# Makefile for Sphinx documentation

POETRY          ?= poetry
SPHINXOPTS      ?=
SPHINXBUILD     ?= $(POETRY) run sphinx-build
SPHINXAUTOBUILD ?= $(POETRY) run sphinx-autobuild
PYTHON          ?= $(POETRY) run python
SOURCEDIR       = .
BUILDDIR        = _build
SITEDIR         ?= $(BUILDDIR)/site
PKB_SCRIPT_DIR  ?= scripts
PKB_REPO_ROOT   ?= ..
PKB_DOC_DIR     ?= .
PKB_ARGS        ?=
DEFAULT_LANG    ?= en
CONF_MIN_LEVEL  ?= L3

.PHONY: help Makefile clean install html html-en html-zh html-all gettext intl-update translate-zh compile-intl build-landing serve serve-all pkb-check pkb-check-i18n pkb-level1 pkb-review-status changelog-draft strip-confidential

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Custom targets:"
	@echo "  install            Install Poetry dependencies"
	@echo "  html-en            Build English HTML into $(SITEDIR)/en/"
	@echo "  html-zh            Build Chinese HTML into $(SITEDIR)/zh/"
	@echo "  html-all           Build bilingual site into $(SITEDIR)/"
	@echo "  gettext            Generate .pot catalogs"
	@echo "  intl-update        Update zh_CN .po translation files"
	@echo "  translate-zh       Apply dictionary translations to .po files"
	@echo "  compile-intl       Compile zh_CN .mo files"
	@echo "  build-landing      Generate bilingual landing page at $(SITEDIR)/index.html"
	@echo "  serve              Auto-reload dev server (English only)"
	@echo "  serve-all          Serve bilingual site at http://127.0.0.1:8000/"
	@echo "  pkb-check          Zero-token staleness check"
	@echo "  pkb-check-i18n     Check zh_CN translation sync"
	@echo "  pkb-level1         Apply Level 1 mechanical refreshes"
	@echo "  pkb-review-status  Human review dashboard (status, score, confidentiality)"
	@echo "  changelog-draft    Generate changelog draft into _generated/"
	@echo "  strip-confidential Remove pages at >= CONF_MIN_LEVEL (default L3) from $(SITEDIR)"

install:
	$(POETRY) install

clean:
	rm -rf "$(BUILDDIR)"

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

html-en:
	@mkdir -p "$(SITEDIR)"
	SPHINX_LANGUAGE=en $(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(SITEDIR)/en" $(SPHINXOPTS) $(O)

gettext:
	@mkdir -p "$(BUILDDIR)/gettext"
	$(SPHINXBUILD) -b gettext "$(SOURCEDIR)" "$(BUILDDIR)/gettext" $(SPHINXOPTS) $(O)

intl-update: gettext
	@mkdir -p locale/zh_CN/LC_MESSAGES
	$(POETRY) run sphinx-intl update -p "$(BUILDDIR)/gettext" -l zh_CN

translate-zh: intl-update
	$(PYTHON) "$(PKB_SCRIPT_DIR)/translate_po.py" --po-dir locale/zh_CN/LC_MESSAGES

compile-intl: translate-zh
	$(POETRY) run sphinx-intl build -d locale -l zh_CN

html-zh: compile-intl
	@rm -rf "$(SITEDIR)/zh" "$(SITEDIR)/zh_CN"
	@mkdir -p "$(SITEDIR)"
	SPHINX_LANGUAGE=zh_CN $(SPHINXBUILD) -b html -D language=zh_CN "$(SOURCEDIR)" "$(SITEDIR)/zh" $(SPHINXOPTS) $(O)

build-landing:
	$(PYTHON) "$(PKB_SCRIPT_DIR)/render_landing.py" --site-dir "$(SITEDIR)" --default-language "$(DEFAULT_LANG)"

html-all: html-en html-zh build-landing

serve: html
	$(SPHINXAUTOBUILD) "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) \
		--ignore "*.swp" \
		--ignore "*.pdf" \
		--ignore "*.log" \
		--ignore "*.out" \
		--ignore "*.toc" \
		--ignore "*.aux" \
		--ignore "*.idx" \
		--ignore "*.ind" \
		--ignore "*.ilg" \
		--ignore "*.tex" \
		--watch . \
		--open-browser

serve-all: html-all
	python3 -m http.server 8000 --directory "$(SITEDIR)"

pkb-check:
	$(PYTHON) "$(PKB_SCRIPT_DIR)/check_pkb_staleness.py" --repo-root "$(PKB_REPO_ROOT)" --doc-dir "$(PKB_DOC_DIR)" $(PKB_ARGS)

pkb-check-i18n:
	@if [ -d "$(PKB_DOC_DIR)/locale/zh_CN/LC_MESSAGES" ]; then \
		$(PYTHON) "$(PKB_SCRIPT_DIR)/check_translation_sync.py" --repo-root "$(PKB_REPO_ROOT)" --doc-dir "$(PKB_DOC_DIR)" $(PKB_ARGS); \
	else \
		echo "No zh_CN catalogs found under $(PKB_DOC_DIR)/locale/zh_CN/LC_MESSAGES; skipping."; \
	fi

pkb-level1:
	bash "$(PKB_SCRIPT_DIR)/update_doc_level1.sh" "$(PKB_REPO_ROOT)" "$(PKB_DOC_DIR)"

pkb-review-status:
	$(PYTHON) "$(PKB_SCRIPT_DIR)/pkb_review_status.py" --doc-dir "$(PKB_DOC_DIR)"

changelog-draft:
	bash "$(PKB_SCRIPT_DIR)/gen_changelog.sh" --repo-root "$(PKB_REPO_ROOT)" --doc-dir "$(PKB_DOC_DIR)"

strip-confidential: html-all
	$(PYTHON) "$(PKB_SCRIPT_DIR)/strip_confidential.py" --site-dir "$(SITEDIR)" --doc-dir "$(PKB_DOC_DIR)" --min-level "$(CONF_MIN_LEVEL)"
	@echo ""
	@echo "Confidential pages at >= $(CONF_MIN_LEVEL) stripped from $(SITEDIR); site ready to publish."

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
