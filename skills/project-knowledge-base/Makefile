MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SCRIPT_DIR := $(MAKEFILE_DIR)scripts
POETRY := poetry
PYTHON := $(POETRY) run python

REPO_ROOT ?= .
DOC_DIR ?= doc
ARGS ?=

.PHONY: help install pkb-check pkb-check-i18n pkb-level1 validate-templates validate-scripts validate-consistency test verify-all

help:
	@echo "PKB helper targets"
	@echo "  make install                                           # run poetry install for local PKB skill tooling"
	@echo "  make pkb-check REPO_ROOT=/path/to/repo DOC_DIR=/path/to/doc"
	@echo "  make pkb-check-i18n REPO_ROOT=/path/to/repo DOC_DIR=/path/to/doc"
	@echo "  make pkb-level1 REPO_ROOT=/path/to/repo DOC_DIR=/path/to/doc   # writes sidecar artifacts under DOC_DIR/_generated"
	@echo "  make validate-templates                                  # validates template cross-links against templates/sphinx/index.md"
	@echo "  make validate-scripts                                    # syntax-check all .py and .sh scripts"
	@echo "  make validate-consistency                                # cross-check SKILL.md against file system"
	@echo "  make verify-all                                          # run all validation checks"

install:
	$(POETRY) install

pkb-check:
	$(PYTHON) "$(SCRIPT_DIR)/check_pkb_staleness.py" --repo-root "$(REPO_ROOT)" --doc-dir "$(DOC_DIR)" $(ARGS)

pkb-check-i18n:
	$(PYTHON) "$(SCRIPT_DIR)/check_translation_sync.py" --repo-root "$(REPO_ROOT)" --doc-dir "$(DOC_DIR)" $(ARGS)

pkb-level1:
	bash "$(SCRIPT_DIR)/update_doc_level1.sh" "$(REPO_ROOT)" "$(DOC_DIR)"

validate-templates:
	$(PYTHON) "$(SCRIPT_DIR)/validate_template_links.py" $(ARGS)

validate-scripts:
	@echo "=== Checking Python syntax ==="
	@for f in "$(SCRIPT_DIR)"/*.py; do $(PYTHON) -m py_compile "$$f" && echo "  ok $$f"; done
	@echo "=== Checking Bash syntax ==="
	@for f in "$(SCRIPT_DIR)"/*.sh; do bash -n "$$f" && echo "  ok $$f"; done
	@echo "All script syntax checks passed."

validate-consistency:
	$(PYTHON) "$(SCRIPT_DIR)/validate_skill_consistency.py"

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

verify-all: validate-scripts validate-templates validate-consistency test
	@echo ""
	@echo "All verification checks passed."
