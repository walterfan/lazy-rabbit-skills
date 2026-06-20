#!/usr/bin/env bash
#
# setup.sh — Bootstrap installer for lazy-rabbit-skills.
#
# Downloads the lazy-rabbit-skills repository (as a tarball) into
# ~/.lazy-rabbit-skills, then installs all skills into ~/.agents/skills and
# links them into each agent (claude, codex, cursor, opencode).
#
# One-liner (no clone required):
#   curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh | bash
#
# Or download and inspect first (recommended):
#   curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh -o setup.sh
#   less setup.sh
#   bash setup.sh
#
# Environment variables:
#   LRS_REF        Git ref (branch/tag) to download         (default: master)
#   LRS_DIR        Install directory for the repo           (default: ~/.lazy-rabbit-skills)
#   LRS_TARGETS    Comma-separated agent targets            (default: install.sh default)
#   LRS_FORCE      If "1", pass --force to install.sh       (default: unset)
#
# Pass-through args: any extra args are forwarded to install.sh, e.g.
#   curl -fsSL .../setup.sh | bash -s -- --targets claude,codex gitlab-mr-review

set -euo pipefail

# --- config ---
REPO_OWNER="walterfan"
REPO_NAME="lazy-rabbit-skills"
REF="${LRS_REF:-master}"
DEST="${LRS_DIR:-$HOME/.lazy-rabbit-skills}"
TARBALL_URL="https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/refs/heads/${REF}"

# --- colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }
step() { echo -e "${CYAN}==>${NC} $*"; }

cleanup() { [[ -n "${TMP_DIR:-}" && -d "$TMP_DIR" ]] && rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# --- pick a downloader ---
download() {
    local url="$1" out="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$out"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$out" "$url"
    else
        err "Neither curl nor wget is available. Install one and retry."
        exit 1
    fi
}

# --- require tar ---
if ! command -v tar >/dev/null 2>&1; then
    err "tar is required but not found."
    exit 1
fi

echo ""
step "lazy-rabbit-skills setup"
echo "  Source: ${REPO_OWNER}/${REPO_NAME}@${REF}"
echo "  Dest:   $DEST"
echo ""

# --- download tarball ---
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/lrs-setup.XXXXXX")"
TARBALL="$TMP_DIR/repo.tar.gz"

step "Downloading repository tarball..."
download "$TARBALL_URL" "$TARBALL"
info "Downloaded $(du -h "$TARBALL" | cut -f1) tarball"

# --- extract ---
step "Extracting..."
EXTRACT_DIR="$TMP_DIR/extract"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$TARBALL" -C "$EXTRACT_DIR"

# GitHub tarballs extract into a single top-level dir: <repo>-<ref>/
SRC_ROOT="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"
if [[ -z "$SRC_ROOT" || ! -d "$SRC_ROOT/skills" ]]; then
    err "Unexpected tarball layout — could not find skills/ inside the download."
    exit 1
fi
info "Extracted $(find "$SRC_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | xargs) skill folder(s)"

# --- sync into DEST ---
step "Installing repository to $DEST ..."
mkdir -p "$DEST"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude '.git' \
        "$SRC_ROOT"/ "$DEST"/
else
    # Fallback: clear skills/ and copy fresh, plus root scripts/docs
    rm -rf "$DEST/skills"
    cp -R "$SRC_ROOT/skills" "$DEST/skills"
    for f in install.sh uninstall.sh setup.sh README.md LICENSE; do
        [[ -f "$SRC_ROOT/$f" ]] && cp -f "$SRC_ROOT/$f" "$DEST/$f"
    done
fi

chmod +x "$DEST/install.sh" "$DEST/uninstall.sh" "$DEST/setup.sh" 2>/dev/null || true
info "Repository ready at $DEST"

# --- build install.sh arguments ---
declare -a INSTALL_ARGS=()
[[ -n "${LRS_TARGETS:-}" ]] && INSTALL_ARGS+=("--targets" "$LRS_TARGETS")
[[ "${LRS_FORCE:-}" == "1" ]] && INSTALL_ARGS+=("--force")
# forward any extra args passed to setup.sh (e.g. specific skill names)
if [[ $# -gt 0 ]]; then
    INSTALL_ARGS+=("$@")
else
    INSTALL_ARGS+=("--all")
fi

# --- run install.sh ---
step "Installing skills..."
echo ""
bash "$DEST/install.sh" "${INSTALL_ARGS[@]}"

echo ""
step "Setup complete."
echo "  Repo:     $DEST"
echo "  Update:   re-run this setup, or 'curl -fsSL .../setup.sh | bash'"
echo "  Manage:   $DEST/install.sh --help   |   $DEST/uninstall.sh --help"
echo ""
