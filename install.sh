#!/usr/bin/env bash
#
# install.sh — Install lazy-rabbit-skills into ~/.agents/skills and link them
#              into the per-agent skill directories (claude, codex, cursor,
#              opencode) via symlinks.
#
# Layout created:
#   ~/.agents/skills/<name>            -> <repo>/skills/<name>   (canonical)
#   ~/.claude/skills/<name>            -> ~/.agents/skills/<name>
#   ~/.codex/skills/<name>             -> ~/.agents/skills/<name>
#   ~/.cursor/skills/<name>            -> ~/.agents/skills/<name>
#   ~/.config/opencode/skills/<name>  -> ~/.agents/skills/<name>
#
# Usage:
#   ./install.sh [skill ...] [options]
#
# Examples:
#   ./install.sh                              # install ALL skills
#   ./install.sh --all                        # install ALL skills
#   ./install.sh gitlab-mr-review             # install one skill
#   ./install.sh lazy-go-dev lazy-python-dev  # install several skills
#   ./install.sh --targets claude,codex gitlab-mr-review
#   ./install.sh --dry-run --all
#
# Options:
#   --all              Install every skill under skills/ (default when no skill given)
#   --targets LIST     Comma-separated agent targets (default: claude,codex,cursor,opencode)
#   --force            Overwrite existing symlinks without prompting
#   --dry-run          Show what would be done without making changes
#   -h, --help         Show this help

set -euo pipefail

# --- resolve repo root (directory containing this script) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
AGENTS_DIR="$HOME/.agents/skills"

# --- defaults ---
DEFAULT_TARGETS="claude,codex,cursor,opencode"
TARGETS=""
FORCE=false
DRY_RUN=false
INSTALL_ALL=false
declare -a REQUESTED_SKILLS=()

# --- colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }
dry()  { echo -e "${CYAN}[DRY-RUN]${NC} $*"; }

usage() { sed -n '3,38p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# --- map a target name to its skills directory ---
target_dir_for() {
    case "$1" in
        opencode) echo "$HOME/.config/opencode/skills" ;;
        *)        echo "$HOME/.$1/skills" ;;
    esac
}

# --- parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)            INSTALL_ALL=true; shift ;;
        --targets)        TARGETS="$2"; shift 2 ;;
        --targets=*)      TARGETS="${1#*=}"; shift ;;
        --force)          FORCE=true; shift ;;
        --dry-run)        DRY_RUN=true; shift ;;
        -h|--help)        usage 0 ;;
        -*)               err "Unknown option: $1"; usage 1 ;;
        *)                REQUESTED_SKILLS+=("$1"); shift ;;
    esac
done

[[ -z "$TARGETS" ]] && TARGETS="$DEFAULT_TARGETS"

if [[ ! -d "$SKILLS_DIR" ]]; then
    err "skills/ directory not found at $SKILLS_DIR"
    exit 1
fi

# --- determine the list of skills to install ---
declare -a SKILLS=()
if $INSTALL_ALL || [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
    for d in "$SKILLS_DIR"/*/; do
        [[ -d "$d" ]] || continue
        name="$(basename "$d")"
        if [[ -f "$d/SKILL.md" || -f "$d/skill.md" ]]; then
            SKILLS+=("$name")
        fi
    done
else
    for name in "${REQUESTED_SKILLS[@]}"; do
        src="$SKILLS_DIR/$name"
        if [[ ! -d "$src" ]]; then
            err "Skill not found: $name (expected $src)"
            exit 1
        fi
        if [[ ! -f "$src/SKILL.md" && ! -f "$src/skill.md" ]]; then
            err "Not a valid skill (no SKILL.md): $name"
            exit 1
        fi
        SKILLS+=("$name")
    done
fi

if [[ ${#SKILLS[@]} -eq 0 ]]; then
    warn "No skills found to install."
    exit 0
fi

echo ""
echo "Repo:    $SCRIPT_DIR"
echo "Targets: $TARGETS"
echo "Skills:  ${#SKILLS[@]} (${SKILLS[*]})"
$DRY_RUN && echo "Mode:    dry run"
echo ""

# --- link helper: create symlink $1 -> $2, honoring FORCE / DRY_RUN ---
link_into() {
    local link="$1" target="$2"
    local link_parent
    link_parent="$(dirname "$link")"

    if [[ ! -d "$link_parent" ]]; then
        if $DRY_RUN; then dry "Would create directory: $link_parent"
        else mkdir -p "$link_parent"; fi
    fi

    if [[ -L "$link" ]]; then
        local existing; existing="$(readlink "$link")"
        if [[ "$existing" == "$target" ]]; then
            return 0  # already correct
        fi
        if $FORCE; then
            if $DRY_RUN; then dry "Would replace symlink: $link -> $target (was -> $existing)"
            else rm "$link"; ln -s "$target" "$link"; fi
            return 0
        fi
        if $DRY_RUN; then
            dry "Would prompt to replace symlink: $link (was -> $existing) -> $target"
            return 0
        fi
        warn "$link already points to $existing"
        # Non-interactive (e.g. curl | bash): don't hang on a prompt — skip and
        # advise --force. Only prompt when stdin is a real terminal.
        if [[ ! -t 0 ]]; then
            warn "Skipped (non-interactive): $link — re-run with --force to overwrite"
            return 1
        fi
        echo -n "  Replace with $target? [y/N] "
        read -r answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            rm "$link"; ln -s "$target" "$link"
        else
            warn "Skipped: $link"
            return 1
        fi
    elif [[ -e "$link" ]]; then
        err "$link exists and is not a symlink — skipping (remove manually)"
        return 1
    else
        if $DRY_RUN; then dry "Would create symlink: $link -> $target"
        else ln -s "$target" "$link"; fi
    fi
    return 0
}

IFS=',' read -ra TARGET_LIST <<< "$TARGETS"

installed=0
failed=0

for name in "${SKILLS[@]}"; do
    src="$SKILLS_DIR/$name"
    canonical="$AGENTS_DIR/$name"

    echo "• $name"

    # 1) canonical link in ~/.agents/skills -> repo
    if link_into "$canonical" "$src"; then
        $DRY_RUN || info "  ~/.agents/skills/$name -> $src"
    else
        ((failed++)); continue
    fi

    # 2) per-agent links -> canonical
    for target in "${TARGET_LIST[@]}"; do
        target="$(echo "$target" | xargs)"
        [[ -z "$target" ]] && continue
        tdir="$(target_dir_for "$target")"
        if link_into "$tdir/$name" "$canonical"; then
            $DRY_RUN || info "  $tdir/$name -> ~/.agents/skills/$name"
        else
            ((failed++))
        fi
    done
    ((installed++))
done

echo ""
echo "Done: $installed skill(s) processed, $failed link(s) failed/skipped"
