#!/usr/bin/env bash
# L3: behavior evaluation runner. Cross-agent capable.
#
# For each YAML case in <cases_dir>, spawn a headless agent session
# with the target skill available, run the prompt, collect the raw output,
# and store it in <output_dir>/<case_basename>.json wrapped in a _skilltest
# envelope key (data contract — kept stable across renames so already-recorded
# run files keep parsing; evaluate_runs.py uses it to pick the right parser).
#
# Usage:
#   behavior_run.sh <skill_dir> <cases_dir> <output_dir> [extra-agent-args...]
#
# Agent selection (env):
#   LAZY_SKILL_CHECK_AGENT   claude | codex | cursor    (default: claude)
#   LAZY_SKILL_CHECK_MODEL   model id for the chosen agent
#
# Per-agent defaults roughly equivalent to --print / headless invocation.
# Override MAX_TURNS / MAX_BUDGET / ALLOWED_TOOLS via env as needed.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  cat >&2 <<EOF
Usage: $0 <skill_dir> <cases_dir> <output_dir> [extra agent args...]

Env:
  LAZY_SKILL_CHECK_AGENT          claude|codex|cursor   (default: claude)
  LAZY_SKILL_CHECK_MODEL          model id
  LAZY_SKILL_CHECK_MAX_TURNS      claude-only; default 10
  LAZY_SKILL_CHECK_MAX_BUDGET     claude-only; default 0.10
  LAZY_SKILL_CHECK_ALLOWED_TOOLS  claude-only; default Read,Edit,Write,Bash,Glob,Grep
EOF
  exit 2
fi

SKILL_DIR="$1"; shift
CASES_DIR="$1"; shift
OUTPUT_DIR="$1"; shift
if [[ $# -gt 0 ]]; then
  EXTRA_ARGS=("$@")
else
  EXTRA_ARGS=()
fi

AGENT="${LAZY_SKILL_CHECK_AGENT:-claude}"

case "$AGENT" in
  claude)
    CLI_NAME="claude"
    DEFAULT_MODEL="claude-sonnet-4-5"
    ;;
  codex)
    CLI_NAME="codex"
    DEFAULT_MODEL="gpt-5-codex"
    ;;
  cursor)
    CLI_NAME="cursor-agent"
    DEFAULT_MODEL="claude-sonnet-4-5"
    ;;
  *)
    echo "ERROR: unknown LAZY_SKILL_CHECK_AGENT=$AGENT (claude|codex|cursor)" >&2
    exit 2
    ;;
esac

if ! command -v "$CLI_NAME" >/dev/null 2>&1; then
  echo "ERROR: $CLI_NAME CLI not found in PATH (agent=$AGENT)" >&2
  exit 2
fi

SKILL_DIR="$(cd "$SKILL_DIR" && pwd)"
CASES_DIR="$(cd "$CASES_DIR" && pwd)"
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

MODEL="${LAZY_SKILL_CHECK_MODEL:-$DEFAULT_MODEL}"
MAX_TURNS="${LAZY_SKILL_CHECK_MAX_TURNS:-10}"
MAX_BUDGET_USD="${LAZY_SKILL_CHECK_MAX_BUDGET:-0.10}"
ALLOWED_TOOLS="${LAZY_SKILL_CHECK_ALLOWED_TOOLS:-Read,Edit,Write,Bash,Glob,Grep}"

echo "[L3 behavior] agent=$AGENT model=$MODEL"
echo "[L3 behavior] skill=$SKILL_DIR"
echo "[L3 behavior] cases=$CASES_DIR"
echo "[L3 behavior] output=$OUTPUT_DIR"
echo

PASS_COUNT=0
FAIL_COUNT=0

shopt -s nullglob
CASE_FILES=("$CASES_DIR"/*.yaml "$CASES_DIR"/*.yml)
if [[ ${#CASE_FILES[@]} -eq 0 ]]; then
  echo "ERROR: no *.yaml or *.yml cases found in $CASES_DIR" >&2
  exit 2
fi

for CASE_FILE in "${CASE_FILES[@]}"; do
  CASE_NAME="$(basename "$CASE_FILE" | sed 's/\.[yY][aA]*[mM][lL]$//')"
  OUT_FILE="$OUTPUT_DIR/$CASE_NAME.json"
  WORK_DIR="$(mktemp -d -t lazyskillcheck-"$CASE_NAME"-XXXXXX)"

  PROMPT="$(python3 -c "
import sys, yaml
case = yaml.safe_load(open(sys.argv[1]))
print(case.get('prompt', ''))
" "$CASE_FILE")"

  if [[ -z "$PROMPT" ]]; then
    echo "SKIP   $CASE_NAME (empty prompt)"
    continue
  fi

  python3 -c "
import os, shutil, sys, yaml, pathlib
case = yaml.safe_load(open(sys.argv[1]))
work = pathlib.Path(sys.argv[2])
cases_dir = pathlib.Path(sys.argv[3])
for item in case.get('setup', []) or []:
    src = (cases_dir / item['from']).resolve()
    dst = (work / item['to']).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
" "$CASE_FILE" "$WORK_DIR" "$CASES_DIR"

  START=$(date +%s)
  set +e
  case "$AGENT" in
    claude)
      ( cd "$WORK_DIR" && \
        claude -p "$PROMPT" \
          --model "$MODEL" \
          --max-turns "$MAX_TURNS" \
          --allowedTools "$ALLOWED_TOOLS" \
          --output-format json \
          ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} \
          < /dev/null \
          > "$OUT_FILE.raw" \
          2> "$OUT_FILE.stderr"
      )
      ;;
    codex)
      # codex exec emits JSONL on stdout with --json
      ( cd "$WORK_DIR" && \
        codex exec --json --skip-git-repo-check \
          --model "$MODEL" \
          ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} \
          "$PROMPT" \
          > "$OUT_FILE.raw" \
          2> "$OUT_FILE.stderr"
      )
      ;;
    cursor)
      # cursor-agent -p prints a single JSON result with --output-format json
      ( cd "$WORK_DIR" && \
        cursor-agent -p --output-format json \
          --model "$MODEL" \
          ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} \
          "$PROMPT" \
          > "$OUT_FILE.raw" \
          2> "$OUT_FILE.stderr"
      )
      ;;
  esac
  RC=$?
  set -e
  END=$(date +%s)

  # Wrap raw payload into the _skilltest envelope (stable JSON key) so
  # evaluate_runs.py knows which agent parser to use. The original raw text is
  # preserved verbatim.
  python3 - "$OUT_FILE" "$OUT_FILE.raw" "$WORK_DIR" "$((END - START))" "$AGENT" "$RC" <<'PY'
import json, pathlib, sys
out_path = pathlib.Path(sys.argv[1])
raw_path = pathlib.Path(sys.argv[2])
work, dur, agent, rc = sys.argv[3], int(sys.argv[4]), sys.argv[5], int(sys.argv[6])

raw_text = raw_path.read_text(encoding="utf-8", errors="replace") if raw_path.exists() else ""

# Try to preserve a structured payload where possible (so human inspection works),
# but always carry the raw text for the parser.
payload_obj = None
try:
    payload_obj = json.loads(raw_text)
except Exception:
    payload_obj = None

envelope = {
    "_skilltest": {
        "agent": agent,
        "workdir": work,
        "duration_seconds": dur,
        "exit_code": rc,
        "payload_text": raw_text,
    }
}
if isinstance(payload_obj, dict):
    # flat-merge convenience fields without clobbering _skilltest
    for k, v in payload_obj.items():
        if k != "_skilltest":
            envelope[k] = v

out_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
PY

  # clean up the intermediate raw stream now that it's embedded
  rm -f "$OUT_FILE.raw"

  if [[ $RC -eq 0 ]]; then
    echo "RUN    $CASE_NAME  ok ($((END - START))s)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "RUN    $CASE_NAME  FAILED rc=$RC ($((END - START))s)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

echo
echo "[L3 behavior] runs complete: $PASS_COUNT ok, $FAIL_COUNT failed"
echo "[L3 behavior] now run: python3 $(dirname "$0")/evaluate_runs.py \\"
echo "              --cases $CASES_DIR --runs $OUTPUT_DIR"
