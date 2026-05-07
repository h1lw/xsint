#!/usr/bin/env bash
set -euo pipefail
APP=xsint
REPO=h1lw/xsint

MUTED='\033[0;2m'
RED='\033[0;31m'
ORANGE='\033[38;5;214m'
GREEN='\033[0;32m'
NC='\033[0m'

usage() {
    cat <<EOF
xsint installer

Usage: install.sh [options]

Options:
    -h, --help              Display this help message
    -v, --version <ref>     Install a specific tag, branch, or commit (default: main)
    -d, --dir <path>        Source install directory (default: ~/.local/share/xsint)
    -b, --bin-dir <path>    Wrapper bin directory (default: ~/.local/bin)
        --no-modify-path    Don't modify shell config files (.zshrc, .bashrc, etc.)

Examples:
    curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash
    curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash -s -- --version v1.0.0
EOF
}

requested_ref="${VERSION:-main}"
no_modify_path=false
install_dir="${XSINT_INSTALL_DIR:-$HOME/.local/share/xsint}"
bin_dir="${XSINT_BIN_DIR:-$HOME/.local/bin}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -v|--version)
            [[ -n "${2:-}" ]] || { echo -e "${RED}Error: --version requires a ref${NC}"; exit 1; }
            requested_ref="$2"; shift 2 ;;
        -d|--dir)
            [[ -n "${2:-}" ]] || { echo -e "${RED}Error: --dir requires a path${NC}"; exit 1; }
            install_dir="$2"; shift 2 ;;
        -b|--bin-dir)
            [[ -n "${2:-}" ]] || { echo -e "${RED}Error: --bin-dir requires a path${NC}"; exit 1; }
            bin_dir="$2"; shift 2 ;;
        --no-modify-path) no_modify_path=true; shift ;;
        *) echo -e "${ORANGE}Warning: unknown option '$1'${NC}" >&2; shift ;;
    esac
done

print_message() {
    local level=$1 msg=$2 color="${NC}"
    case $level in info) color="${NC}" ;; warning) color="${ORANGE}" ;; error) color="${RED}" ;; ok) color="${GREEN}" ;; esac
    echo -e "${color}${msg}${NC}"
}

# In update mode (set by `xsint --update`) the user already has xsint
# working — skip the first-time framing and use "Updating ..." section
# headers instead of "Installing ...".
UPDATE_MODE="${XSINT_UPDATE_MODE:-}"
ACTION_VERB="Installing"
ACTION_VERB_PROG="Installing"
COMPLETION_MSG="Setup complete."
if [[ -n "$UPDATE_MODE" ]]; then
    ACTION_VERB="Updating"
    ACTION_VERB_PROG="Updating"
    COMPLETION_MSG="Update complete."
fi

# ---------- 1. Detect a compatible Python (3.10–3.13) ----------

find_python() {
    local cand
    for cand in python3.13 python3.12 python3.11 python3.10 python3 python; do
        command -v "$cand" >/dev/null 2>&1 || continue
        local minor
        minor=$("$cand" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "")
        local major
        major=$("$cand" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "")
        if [[ "$major" == "3" && "$minor" =~ ^[0-9]+$ && "$minor" -ge 10 && "$minor" -le 13 ]]; then
            echo "$cand"
            return 0
        fi
    done
    return 1
}

print_message info "${MUTED}Looking for Python 3.10–3.13...${NC}"
PYTHON=$(find_python || true)
if [[ -z "$PYTHON" ]]; then
    print_message error "[!] No compatible Python 3.10–3.13 interpreter found."
    print_message info  "    Install Python 3.10+ and retry."
    exit 1
fi
PYVER=$("$PYTHON" --version 2>&1)
print_message ok "${MUTED}Using:${NC} $PYTHON ${MUTED}($PYVER)${NC}"

# ---------- 2. Required tools ----------

for tool in curl tar; do
    command -v "$tool" >/dev/null 2>&1 || { print_message error "[!] '$tool' is required but not installed."; exit 1; }
done

# ---------- 3. Download source tarball ----------

ref_clean="${requested_ref#v}"
# Resolve "main"/"master"/branch/tag to a tarball URL.
case "$requested_ref" in
    main|master|*/*) tarball_url="https://github.com/$REPO/archive/refs/heads/$requested_ref.tar.gz" ;;
    v*|[0-9]*)       tarball_url="https://github.com/$REPO/archive/refs/tags/v${ref_clean}.tar.gz" ;;
    *)               tarball_url="https://github.com/$REPO/archive/$requested_ref.tar.gz" ;;
esac

# Verify URL exists.
http_status=$(curl -sI -o /dev/null -w "%{http_code}" "$tarball_url" || echo "000")
if [[ "$http_status" != "200" && "$http_status" != "302" ]]; then
    # Fall back to tag form for plain version numbers.
    if [[ "$requested_ref" =~ ^[0-9] ]]; then
        tarball_url="https://github.com/$REPO/archive/refs/tags/v${ref_clean}.tar.gz"
        http_status=$(curl -sI -o /dev/null -w "%{http_code}" "$tarball_url" || echo "000")
    fi
fi
if [[ "$http_status" != "200" && "$http_status" != "302" ]]; then
    print_message error "[!] Could not resolve ref '$requested_ref' (HTTP $http_status)."
    print_message info  "    Available releases: https://github.com/$REPO/releases"
    exit 1
fi

tmp_dir="${TMPDIR:-/tmp}/xsint_install_$$"
mkdir -p "$tmp_dir"
trap 'rm -rf "$tmp_dir"' EXIT

if [[ -n "$UPDATE_MODE" ]]; then
    print_message info "\n${MUTED}Fetching latest${NC} $APP ${MUTED}from${NC} $tarball_url"
else
    print_message info "\n${MUTED}Downloading${NC} $APP ${MUTED}from${NC} $tarball_url"
fi
curl -# -fsSL -o "$tmp_dir/src.tar.gz" "$tarball_url"

print_message info "${MUTED}Extracting...${NC}"
tar -xzf "$tmp_dir/src.tar.gz" -C "$tmp_dir"
src_root=$(find "$tmp_dir" -maxdepth 1 -mindepth 1 -type d | head -n1)
[[ -d "$src_root" ]] || { print_message error "[!] Extracted source not found"; exit 1; }

# ---------- 4. Run the Python installer ----------

print_message info "\n${MUTED}${ACTION_VERB_PROG} into${NC} $install_dir"
"$PYTHON" "$src_root/installer.py" \
    --install-dir "$install_dir" \
    --bin-dir "$bin_dir"

# ---------- 5. PATH wiring ----------

add_to_path() {
    local config_file=$1 cmd=$2
    if grep -Fxq "$cmd" "$config_file" 2>/dev/null; then
        print_message info "${MUTED}Already in${NC} $config_file"
    elif [[ -w "$config_file" ]]; then
        printf "\n# xsint\n%s\n" "$cmd" >> "$config_file"
        print_message ok "${MUTED}Added xsint to \$PATH in${NC} $config_file"
    else
        print_message warning "Manually add to $config_file (or similar):"
        print_message info "  $cmd"
    fi
}

if [[ "$no_modify_path" != "true" && ":$PATH:" != *":$bin_dir:"* ]]; then
    XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
    case "$(basename "${SHELL:-}")" in
        fish) configs="$HOME/.config/fish/config.fish" ;;
        zsh)  configs="${ZDOTDIR:-$HOME}/.zshrc ${ZDOTDIR:-$HOME}/.zshenv $XDG_CONFIG_HOME/zsh/.zshrc" ;;
        bash) configs="$HOME/.bashrc $HOME/.bash_profile $HOME/.profile" ;;
        *)    configs="$HOME/.bashrc $HOME/.profile" ;;
    esac

    config=""
    for f in $configs; do
        [[ -f "$f" ]] && { config="$f"; break; }
    done

    if [[ -z "$config" ]]; then
        print_message warning "No shell config found. Add manually:"
        print_message info    "  export PATH=$bin_dir:\$PATH"
    else
        case "$(basename "${SHELL:-}")" in
            fish) add_to_path "$config" "fish_add_path $bin_dir" ;;
            *)    add_to_path "$config" "export PATH=$bin_dir:\$PATH" ;;
        esac
    fi
fi

if [[ -n "${GITHUB_ACTIONS:-}" && "${GITHUB_ACTIONS}" == "true" ]]; then
    echo "$bin_dir" >> "${GITHUB_PATH:-/dev/null}"
    print_message info "${MUTED}Added${NC} $bin_dir ${MUTED}to \$GITHUB_PATH${NC}"
fi

# ---------- 6. Done ----------

echo
print_message ok "$COMPLETION_MSG"
echo -e "  ${MUTED}install dir :${NC} $install_dir"
echo -e "  ${MUTED}bin dir     :${NC} $bin_dir"
if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
    echo -e "  ${MUTED}run         :${NC} xsint <target>"
else
    echo -e "  ${MUTED}run         :${NC} $bin_dir/xsint <target>"
    echo -e "  ${MUTED}or restart your shell to pick up the PATH change${NC}"
fi
echo
echo -e "${MUTED}Optional auth (only if you want those modules):${NC}"
echo -e "  xsint --auth ghunt       ${MUTED}# Google account lookup${NC}"
echo -e "  xsint --auth gitfive     ${MUTED}# GitHub email/profile${NC}"
echo -e "  xsint --auth hibp <key>  ${MUTED}# HaveIBeenPwned${NC}"
echo
echo -e "${MUTED}Docs: https://github.com/$REPO${NC}"
echo
