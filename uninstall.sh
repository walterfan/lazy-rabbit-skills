#!/usr/bin/env bash
#
# uninstall.sh — Remove lazy-rabbit-skills symlinks from the per-agent skill
#                directories and from ~/.agents/skills.
#
# Removes:
#   ~/.claude/skills/<name>            (symlink)
#   ~/.codex/skills/<name>             (symlink)
#   ~/.cursor/skills/<name>            (symlink)
#   ~/.config/opencode/skills/<name>  (symlink)
#   ~/.agents/skills/<name>            (canonical symlink to this repo)
#
# Only symlinks are removed; real files/directories are never deleted.
# A canonical link is only removed if it points into THIS repo's skills/.
#
# Usage:
#   ./uninstall.sh [skill ...] [options]
#
# Examples:
#   ./uninstall.sh                              # uninstall ALL repo skills
#   ./uninstall.sh --all                        # uninstall ALL repo skills
#   ./uninstall.sh gitlab-mr-review             # uninstall one skill
#   ./uninstall.sh lazy-go-dev lazy-python-dev  # uninstall several
#   ./uninstall.sh --targets claude,codex gitlab-mr-review
#   ./uninstall.sh --dry-run --all
#
# Options:
#   --all              Uninstall every skill under skills/ (default when none given)
#   --targets LIST     Comma-separated agent targets (default: claude,codex,cursor,opencode)
#   --keep-agents      Do NOT remove the canonical ~/.agents/skills/<name> link
#   --dry-run          Show what would be done without making changes
#   -h, --help         Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
AGENTS_DIR="$HOME/.agents/skills"

DEFAULT_TARGETS="claude,codex,cursor,opencode"
TARGETS=""
DRY_RUN=false
UNINSTALL_ALL=false
KEEP_AGENTS=false
declare -a REQUESTED_SKILLS=()

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }
dry()  { echo -e "${CYAN}[DRY-RUN]${NC} $*"; }

usage() { sed -n '3,38p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

target_dir_for() {
    case "$1" in
        opencode) echo "$HOME/.config/opencode/skills" ;;
        *)        echo "$HOME/.$1/skills" ;;
    esac
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)            UNINSTALL_ALL=true; shift ;;
        --targets)        TARGETS="$2"; shift 2 ;;
        --targets=*)      TARGETS="${1#*=}"; shift ;;
        --keep-agents)    KEEP_AGENTS=true; shift ;;
        --dry-run)        DRY_RUN=true; shift ;;
        -h|--help)        usage 0 ;;
        -*)               err "Unknown option: $1"; usage 1 ;;
        *)                REQUESTED_SKILLS+=("$1"); shift ;;
    esac
done

[[ -z "$TARGETS" ]] && TARGETS="$DEFAULT_TARGETS"

# --- determine which skills to uninstall ---
declare -a SKILLS=()
if $UNINSTALL_ALL || [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
    if [[ -d "$SKILLS_DIR" ]]; then
        for d in "$SKILLS_DIR"/*/; do
            [[ -d "$d" ]] || continue
            SKILLS+=("$(basename "$d")")
        done
    fi
else
    SKILLS=("${REQUESTED_SKILLS[@]}")
fi

if [[ ${#SKILLS[@]} -eq 0 ]]; then
    warn "No skills specified to uninstall."
    exit 0
fi

echo ""
echo "Repo:    $SCRIPT_DIR"
echo "Targets: $TARGETS"
echo "Skills:  ${#SKILLS[@]} (${SKILLS[*]})"
$KEEP_AGENTS && echo "Keeping: ~/.agents/skills/* links"
$DRY_RUN && echo "Mode:    dry run"
echo ""

# --- remove a symlink at $1; if $2 is given, only remove when it points to $2 ---
remove_link() {
    local link="$1" must_point_to="${2:-}"
    if [[ -L "$link" ]]; then
        if [[ -n "$must_point_to" ]]; then
            local existing; existing="$(readlink "$link")"
            if [[ "$existing" != "$must_point_to" ]]; then
                warn "$link points to $existing (not this repo) — leaving it"
                return 1
            fi
        fi
        if $DRY_RUN; then dry "Would remove symlink: $link"
        else rm "$link"; info "Removed: $link"; fi
        return 0
    elif [[ -e "$link" ]]; then
        warn "$link is not a symlink — leaving it (remove manually if needed)"
        return 1
    else
        return 2  # nothing there
    fi
}

IFS=',' read -ra TARGET_LIST <<< "$TARGETS"

removed=0

for name in "${SKILLS[@]}"; do
    echo "• $name"
    canonical="$AGENTS_DIR/$name"

    # 1) per-agent links — only remove links that point at OUR canonical link
    for target in "${TARGET_LIST[@]}"; do
        target="$(echo "$target" | xargs)"
        [[ -z "$target" ]] && continue
        tdir="$(target_dir_for "$target")"
        if remove_link "$tdir/$name" "$canonical"; then ((removed++)); fi
    done

    # 2) canonical link in ~/.agents/skills (only if it points into this repo)
    if ! $KEEP_AGENTS; then
        if remove_link "$canonical" "$SKILLS_DIR/$name"; then ((removed++)); fi
    fi
done

echo ""
echo "Done: $removed symlink(s) removed"
