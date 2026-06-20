#!/usr/bin/env bash
# =============================================================================
# PKB Init Script — initialize a PKB skeleton from templates
#
# Usage:
#   ./init_pkb.sh --pkb-root ./doc
#   ./init_pkb.sh --pkb-root ./man --sphinx
#   ./init_pkb.sh --pkb-root ./man --minimal
#   ./init_pkb.sh --pkb-root ../my-project-pkb/man --sphinx --force
#   ./init_pkb.sh --pkb-root ./man --sphinx --project-name "My App" --author "Jane Doe"
#
# Author: Walter Fan (walterfan@ustc.edu)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PKB_ROOT=""
ENABLE_SPHINX=0
ENABLE_POETRY=1
ENABLE_MINIMAL=0
ENABLE_BILINGUAL=0
BILINGUAL_LOCALE=""
FORCE=0
PROJECT_NAME=""
AUTHOR_NAME="Walter Fan"
AUTHOR_EMAIL="walterfan@ustc.edu"
COPYRIGHT_HOLDER=""
COPYRIGHT_YEAR="$(date +%Y)"

usage() {
  cat <<'EOF'
Usage:
  init_pkb.sh --pkb-root <path> [options]

Options:
  --pkb-root <path>       Target PKB root directory to initialize (required)
  --skill-root <path>     Path to the skill root (default: parent of script dir)
  --minimal               Create only essential pages (00-overview, 01-quick-start, 04-repo-map)
  --sphinx                Also copy Sphinx build scaffold files
  --poetry                Explicit Poetry scaffold flag (default when --sphinx)
  --bilingual=<locale>    Enable bilingual scaffold (for example: zh_CN)
  --project-name <name>   Project name for conf.py and index (default: derived from parent dir)
  --author <name>         Author name (default: Walter Fan)
  --force                 Overwrite existing files
  -h, --help              Show this help
EOF
}

copy_file() {
  local source="$1"
  local target="$2"

  mkdir -p "$(dirname "$target")"
  if [[ -f "$target" && "$FORCE" -ne 1 ]]; then
    echo "skip  $target"
    return
  fi
  cp "$source" "$target"
  echo "write $target"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pkb-root)
      PKB_ROOT="${2:-}"
      shift 2
      ;;
    --skill-root)
      SKILL_ROOT="${2:-}"
      shift 2
      ;;
    --minimal)
      ENABLE_MINIMAL=1
      shift
      ;;
    --sphinx)
      ENABLE_SPHINX=1
      shift
      ;;
    --poetry)
      ENABLE_POETRY=1
      shift
      ;;
    --bilingual=*)
      ENABLE_BILINGUAL=1
      BILINGUAL_LOCALE="${1#*=}"
      shift
      ;;
    --project-name)
      PROJECT_NAME="${2:-}"
      shift 2
      ;;
    --author)
      AUTHOR_NAME="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$PKB_ROOT" ]]; then
  echo "--pkb-root is required" >&2
  usage
  exit 1
fi

SKILL_ROOT="$(cd "$SKILL_ROOT" && pwd)"
TEMPLATES_DOCS="$SKILL_ROOT/templates/docs"
TEMPLATES_SPHINX="$SKILL_ROOT/templates/sphinx"
TEMPLATES_ADR="$SKILL_ROOT/templates/adr"
TEMPLATES_CHANGES="$SKILL_ROOT/templates/changes/_template"
HELPER_SCRIPTS="$SKILL_ROOT/scripts"

PKB_ROOT="$(mkdir -p "$PKB_ROOT" && cd "$PKB_ROOT" && pwd)"

if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME="$(basename "$(dirname "$PKB_ROOT")")"
fi

if [[ -z "$COPYRIGHT_HOLDER" ]]; then
  COPYRIGHT_HOLDER="$AUTHOR_NAME"
fi

echo "=== PKB Init ==="
echo "PKB root      : $PKB_ROOT"
echo "Skill root    : $SKILL_ROOT"
echo "Project name  : $PROJECT_NAME"
echo "Author        : $AUTHOR_NAME"
echo "Minimal       : $ENABLE_MINIMAL"
echo "Use Sphinx    : $ENABLE_SPHINX"
echo "Use Poetry    : $ENABLE_POETRY"
echo "Bilingual     : $ENABLE_BILINGUAL"
echo "Locale        : ${BILINGUAL_LOCALE:-n/a}"
echo "Force         : $FORCE"
echo ""

# --- Create directory structure ---
mkdir -p "$PKB_ROOT/adr" "$PKB_ROOT/changes/_template" "$PKB_ROOT/scripts"

# --- Copy doc templates ---
if [[ "$ENABLE_MINIMAL" -eq 1 ]]; then
  for file in \
    00-overview.md \
    01-quick-start.md \
    04-repo-map.md; do
    copy_file "$TEMPLATES_DOCS/$file" "$PKB_ROOT/$file"
  done
else
  for file in \
    00-overview.md \
    01-quick-start.md \
    02-architecture.md \
    03-tech-stack.md \
    04-repo-map.md \
    05-data-and-api.md \
    06-workflows.md \
    07-conventions.md \
    08-build.md \
    09-testing.md \
    10-runbook.md \
    11-observability.md \
    12-document.md \
    appendix-01-faq.md \
    appendix-02-glossary.md \
    diagrams-guide.md; do
    copy_file "$TEMPLATES_DOCS/$file" "$PKB_ROOT/$file"
  done
fi

# --- Copy index, ai-guide, adr, and change templates ---
copy_file "$TEMPLATES_SPHINX/index.md" "$PKB_ROOT/index.md"
copy_file "$TEMPLATES_SPHINX/ai-guide.md" "$PKB_ROOT/ai-guide.md"
copy_file "$TEMPLATES_SPHINX/adr/index.md" "$PKB_ROOT/adr/index.md"
copy_file "$TEMPLATES_SPHINX/changes/index.md" "$PKB_ROOT/changes/index.md"
copy_file "$TEMPLATES_ADR/template.md" "$PKB_ROOT/adr/template.md"
copy_file "$TEMPLATES_CHANGES/proposal.md" "$PKB_ROOT/changes/_template/proposal.md"
copy_file "$TEMPLATES_CHANGES/design.md" "$PKB_ROOT/changes/_template/design.md"
copy_file "$TEMPLATES_CHANGES/tasks.md" "$PKB_ROOT/changes/_template/tasks.md"

# --- Copy helper scripts ---
if [[ "$ENABLE_MINIMAL" -eq 1 ]]; then
  for file in \
    generated_output.py \
    generated_output.sh \
    gen_repo_map.sh \
    gen_index.py; do
    if [[ -f "$HELPER_SCRIPTS/$file" ]]; then
      copy_file "$HELPER_SCRIPTS/$file" "$PKB_ROOT/scripts/$file"
      chmod +x "$PKB_ROOT/scripts/$file"
    fi
  done
else
  for file in \
    generated_output.py \
    generated_output.sh \
    check_pkb_staleness.py \
    check_translation_sync.py \
    update_doc_level1.sh \
    gen_repo_map.sh \
    gen_tech_stack.py \
    gen_index.py \
    extract_api_signatures.py \
    gen_changelog.sh \
    gen_dep_graph.py \
    pkb_review_status.py \
    strip_confidential.py \
    render_landing.py \
    translate_po.py \
    validate_template_links.py; do
    if [[ -f "$HELPER_SCRIPTS/$file" ]]; then
      copy_file "$HELPER_SCRIPTS/$file" "$PKB_ROOT/scripts/$file"
      chmod +x "$PKB_ROOT/scripts/$file"
    fi
  done
fi

# --- Sphinx scaffold ---
if [[ "$ENABLE_SPHINX" -eq 1 ]]; then
  mkdir -p "$PKB_ROOT/_static" "$PKB_ROOT/_templates"
  copy_file "$TEMPLATES_SPHINX/Makefile" "$PKB_ROOT/Makefile"
  copy_file "$TEMPLATES_SPHINX/make.bat" "$PKB_ROOT/make.bat"
  copy_file "$TEMPLATES_SPHINX/conf.py" "$PKB_ROOT/conf.py"
  if [[ "$ENABLE_POETRY" -eq 1 ]]; then
    copy_file "$TEMPLATES_SPHINX/pyproject.toml" "$PKB_ROOT/pyproject.toml"
  fi
  copy_file "$TEMPLATES_SPHINX/requirements.txt" "$PKB_ROOT/requirements.txt"
  copy_file "$TEMPLATES_SPHINX/_static/custom.css" "$PKB_ROOT/_static/custom.css"
  if [[ "$ENABLE_BILINGUAL" -eq 1 ]]; then
    mkdir -p "$PKB_ROOT/locale/$BILINGUAL_LOCALE/LC_MESSAGES"
    copy_file "$TEMPLATES_SPHINX/_templates/layout.html" "$PKB_ROOT/_templates/layout.html"
  fi

  # Replace conf.py sentinels with actual values
  if [[ -f "$PKB_ROOT/conf.py" ]]; then
    sed -i.bak \
      -e "s|__PROJECT_NAME__|${PROJECT_NAME}|g" \
      -e "s|__AUTHOR__|${AUTHOR_NAME}|g" \
      -e "s|__COPYRIGHT__|${COPYRIGHT_YEAR}, ${COPYRIGHT_HOLDER}|g" \
      "$PKB_ROOT/conf.py"
    rm -f "$PKB_ROOT/conf.py.bak"
    echo "patch conf.py (project=$PROJECT_NAME, author=$AUTHOR_NAME)"
  fi
fi

# --- Generate index ---
if [[ -f "$HELPER_SCRIPTS/gen_index.py" && ( ! -f "$PKB_ROOT/index.md" || "$FORCE" -eq 1 ) ]]; then
  python3 "$HELPER_SCRIPTS/gen_index.py" --doc-dir "$PKB_ROOT" --stdout > "$PKB_ROOT/index.md"
fi

echo ""
echo "PKB skeleton initialized."
echo "Suggested next steps:"
echo "  1. Review $PKB_ROOT/00-overview.md"
echo "  2. Regenerate navigation with: python3 \"$PKB_ROOT/scripts/gen_index.py\" --doc-dir \"$PKB_ROOT\""
echo "  3. Refresh repo map with: bash \"$PKB_ROOT/scripts/gen_repo_map.sh\" --repo-root . --doc-dir \"$PKB_ROOT\""
if [[ "$ENABLE_MINIMAL" -eq 0 ]]; then
  echo "  4. Check zh_CN sync with: python3 \"$PKB_ROOT/scripts/check_translation_sync.py\" --repo-root . --doc-dir \"$PKB_ROOT\""
fi
if [[ "$ENABLE_SPHINX" -eq 1 ]]; then
  echo "  5. From $PKB_ROOT, run: poetry install"
  if [[ "$ENABLE_BILINGUAL" -eq 1 ]]; then
    echo "  6. Build bilingual docs with: make html-all"
    echo "  7. Strip confidential pages before publishing with: make strip-confidential"
  else
    echo "  6. Then build docs with: make html"
  fi
fi
