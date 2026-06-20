#!/usr/bin/env bash
# discover_repo.sh — Scan a repo root and print a JSON `repo-facts`
# document used by the `agents-md-generate` skill (Phase A).
#
# Usage:
#   ./discover_repo.sh [repo_path]
#
# Output: JSON to stdout. All fields are best-effort; missing data is
# emitted as null (or [] for lists) so downstream skill logic can
# decide what to do.

set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

# --- helpers ------------------------------------------------------------

has() { [[ -e "$1" ]]; }
json_str() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().rstrip("\n")))'
}
json_list_from_lines() {
  python3 -c '
import json, sys
items = [l for l in sys.stdin.read().splitlines() if l.strip()]
print(json.dumps(items))
'
}
emit_list() {
  # Safely emit a JSON list from the positional args (handles empty
  # arrays under `set -u`). Call as: emit_list "${ARR[@]+"${ARR[@]}"}"
  if (( $# == 0 )); then
    printf '[]'
  else
    printf '%s\n' "$@" | json_list_from_lines
  fi
}

# --- language / package manager ----------------------------------------

LANGUAGE="null"
PKG_MANAGER="null"

if has pyproject.toml; then
  LANGUAGE='"python"'
  if grep -q '^\[tool\.poetry' pyproject.toml 2>/dev/null; then
    PKG_MANAGER='"poetry"'
  elif grep -q '^\[tool\.uv' pyproject.toml 2>/dev/null; then
    PKG_MANAGER='"uv"'
  else
    PKG_MANAGER='"pip"'
  fi
elif has requirements.txt; then
  LANGUAGE='"python"'
  PKG_MANAGER='"pip"'
elif has package.json; then
  LANGUAGE='"javascript"'
  if has pnpm-lock.yaml; then
    PKG_MANAGER='"pnpm"'
  elif has yarn.lock; then
    PKG_MANAGER='"yarn"'
  elif has bun.lockb; then
    PKG_MANAGER='"bun"'
  else
    PKG_MANAGER='"npm"'
  fi
elif has go.mod; then
  LANGUAGE='"go"'
  PKG_MANAGER='"go-mod"'
elif has Cargo.toml; then
  LANGUAGE='"rust"'
  PKG_MANAGER='"cargo"'
elif has pom.xml; then
  LANGUAGE='"java"'
  PKG_MANAGER='"maven"'
elif has build.gradle || has build.gradle.kts; then
  LANGUAGE='"java"'
  PKG_MANAGER='"gradle"'
elif has Gemfile; then
  LANGUAGE='"ruby"'
  PKG_MANAGER='"bundler"'
fi

# --- task runner --------------------------------------------------------

TASK_RUNNER="null"
if has justfile; then
  TASK_RUNNER='"just"'
elif has Taskfile.yml || has Taskfile.yaml; then
  TASK_RUNNER='"task"'
elif has Makefile; then
  TASK_RUNNER='"make"'
elif has package.json; then
  TASK_RUNNER='"npm-scripts"'
fi

# --- test framework (best-effort) ---------------------------------------

TEST_FRAMEWORK="null"
if has pyproject.toml && grep -qE '(\[tool\.pytest|pytest)' pyproject.toml 2>/dev/null; then
  TEST_FRAMEWORK='"pytest"'
elif [[ -d tests ]] || [[ -d test ]]; then
  if [[ "$LANGUAGE" == '"python"' ]]; then
    TEST_FRAMEWORK='"pytest"'
  fi
fi
if [[ "$TEST_FRAMEWORK" == "null" && "$LANGUAGE" == '"javascript"' ]]; then
  if has package.json; then
    if grep -q '"vitest"' package.json 2>/dev/null; then
      TEST_FRAMEWORK='"vitest"'
    elif grep -q '"jest"' package.json 2>/dev/null; then
      TEST_FRAMEWORK='"jest"'
    elif grep -q '"mocha"' package.json 2>/dev/null; then
      TEST_FRAMEWORK='"mocha"'
    fi
  fi
fi
if [[ "$TEST_FRAMEWORK" == "null" ]]; then
  case "$LANGUAGE" in
    '"go"')   TEST_FRAMEWORK='"go-test"' ;;
    '"rust"') TEST_FRAMEWORK='"cargo-test"' ;;
    '"java"') TEST_FRAMEWORK='"junit"' ;;
    '"ruby"') TEST_FRAMEWORK='"rspec"' ;;
  esac
fi

# --- lint / format tools ------------------------------------------------

LINT_TOOLS=()
if has .ruff.toml || has ruff.toml; then LINT_TOOLS+=("ruff"); fi
if has pyproject.toml && grep -q '^\[tool\.ruff' pyproject.toml 2>/dev/null; then
  [[ " ${LINT_TOOLS[*]:-} " == *" ruff "* ]] || LINT_TOOLS+=("ruff")
fi
if has pyproject.toml && grep -q '^\[tool\.mypy' pyproject.toml 2>/dev/null; then
  LINT_TOOLS+=("mypy")
fi
if has .eslintrc.js || has .eslintrc.cjs || has .eslintrc.json || has eslint.config.js || has eslint.config.mjs; then
  LINT_TOOLS+=("eslint")
fi
if has biome.json || has biome.jsonc; then LINT_TOOLS+=("biome"); fi
if has .prettierrc || has .prettierrc.json || has prettier.config.js; then LINT_TOOLS+=("prettier"); fi
if has .golangci.yml || has .golangci.yaml; then LINT_TOOLS+=("golangci-lint"); fi
if has .rubocop.yml; then LINT_TOOLS+=("rubocop"); fi

# --- CI entry point -----------------------------------------------------

CI_PATHS=()
if [[ -d .github/workflows ]]; then CI_PATHS+=(".github/workflows"); fi
if has .gitlab-ci.yml; then CI_PATHS+=(".gitlab-ci.yml"); fi
if has azure-pipelines.yml; then CI_PATHS+=("azure-pipelines.yml"); fi
if has Jenkinsfile; then CI_PATHS+=("Jenkinsfile"); fi
if has .circleci/config.yml; then CI_PATHS+=(".circleci/config.yml"); fi

# --- monorepo signals ---------------------------------------------------

MONOREPO_SIGNALS=()
for f in pnpm-workspace.yaml turbo.json lerna.json nx.json rush.json; do
  if has "$f"; then MONOREPO_SIGNALS+=("$f"); fi
done
if [[ -d packages ]]; then MONOREPO_SIGNALS+=("packages/"); fi
if [[ -d apps ]]; then MONOREPO_SIGNALS+=("apps/"); fi
if [[ -d services ]]; then MONOREPO_SIGNALS+=("services/"); fi
if has package.json && grep -q '"workspaces"' package.json 2>/dev/null; then
  MONOREPO_SIGNALS+=("package.json:workspaces")
fi
if has Cargo.toml && grep -q '^\[workspace\]' Cargo.toml 2>/dev/null; then
  MONOREPO_SIGNALS+=("Cargo.toml:workspace")
fi
if has pyproject.toml && grep -q 'tool\.uv\.workspace' pyproject.toml 2>/dev/null; then
  MONOREPO_SIGNALS+=("pyproject.toml:uv-workspace")
fi

# --- KB / docs ----------------------------------------------------------

KB_PATH="null"
for candidate in man docs handbook doc; do
  if has "$candidate/index.md" || has "$candidate/README.md" || has "$candidate/index.rst"; then
    KB_PATH="\"$candidate\""
    break
  fi
done

# --- OpenSpec / ADR / RFC ----------------------------------------------

CHANGE_SYSTEM="null"
if has openspec; then
  CHANGE_SYSTEM='"openspec"'
elif has adr || has docs/adr; then
  CHANGE_SYSTEM='"adr"'
elif has rfcs || has docs/rfcs; then
  CHANGE_SYSTEM='"rfc"'
fi

# --- existing agent files ----------------------------------------------

EXISTING=()
for f in AGENTS.md CLAUDE.md CURSOR.md .cursorrules .github/copilot-instructions.md .aider.conf.yml .gemini/settings.json; do
  if has "$f"; then EXISTING+=("$f"); fi
done

# --- agent-client dirs --------------------------------------------------

CLIENTS=()
for d in .claude .cursor .codex .opencode .aider .gemini; do
  if has "$d"; then CLIENTS+=("$d"); fi
done

# --- ownership / help hints ---------------------------------------------

OWNER_HINTS=()
for f in CODEOWNERS .github/CODEOWNERS .gitlab/CODEOWNERS docs/CODEOWNERS; do
  if has "$f"; then OWNER_HINTS+=("$f"); fi
done

# --- top-level layout ---------------------------------------------------

TOP_LEVEL=$(ls -1 -A 2>/dev/null | grep -Ev '^(\.git|\.venv|node_modules|\.idea|\.vscode|__pycache__|dist|build|target|\.pytest_cache|\.ruff_cache|htmlcov|\.coverage)$' | json_list_from_lines)

# --- readme first line --------------------------------------------------

README_EXISTS=false
README_LINE1="null"
if has README.md; then
  README_EXISTS=true
  LINE=$(grep -m1 -E '^[A-Za-z]' README.md || true)
  if [[ -n "$LINE" ]]; then
    README_LINE1=$(printf "%s" "$LINE" | json_str)
  fi
fi

# --- emit ---------------------------------------------------------------

EXISTING_JSON=$(emit_list ${EXISTING[@]+"${EXISTING[@]}"})
CLIENTS_JSON=$(emit_list ${CLIENTS[@]+"${CLIENTS[@]}"})
OWNER_HINTS_JSON=$(emit_list ${OWNER_HINTS[@]+"${OWNER_HINTS[@]}"})
LINT_TOOLS_JSON=$(emit_list ${LINT_TOOLS[@]+"${LINT_TOOLS[@]}"})
CI_PATHS_JSON=$(emit_list ${CI_PATHS[@]+"${CI_PATHS[@]}"})
MONOREPO_JSON=$(emit_list ${MONOREPO_SIGNALS[@]+"${MONOREPO_SIGNALS[@]}"})

cat <<EOF
{
  "root": $(printf "%s" "$ROOT" | json_str),
  "language": $LANGUAGE,
  "package_manager": $PKG_MANAGER,
  "task_runner": $TASK_RUNNER,
  "test_framework": $TEST_FRAMEWORK,
  "lint_tools": $LINT_TOOLS_JSON,
  "ci_paths": $CI_PATHS_JSON,
  "monorepo_signals": $MONOREPO_JSON,
  "kb_path": $KB_PATH,
  "change_system": $CHANGE_SYSTEM,
  "existing_agent_files": $EXISTING_JSON,
  "agent_client_dirs": $CLIENTS_JSON,
  "owner_hints": $OWNER_HINTS_JSON,
  "top_level": $TOP_LEVEL,
  "readme_exists": $README_EXISTS,
  "readme_line_1": $README_LINE1
}
EOF
