#!/usr/bin/env bash
# ServerGuard — one-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/AdityaKumar41/serverguard-oss/main/scripts/install.sh | bash

set -euo pipefail

REPO="AdityaKumar41/serverguard-oss"
PACKAGE="serverguard"
MIN_PYTHON="3.11"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
cat << 'EOF'
  ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗
  ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
  ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
  ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
  ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
  ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
  GUARD
  Autonomous server guardian — v0.0.1
EOF
echo -e "${NC}"

# ── Check OS ──────────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Linux*)  OS_TYPE=linux ;;
  Darwin*) OS_TYPE=macos ;;
  *)       error "Unsupported OS: $OS. ServerGuard supports Linux and macOS." ;;
esac
info "Detected OS: $OS_TYPE"

# ── Check Python ──────────────────────────────────────────────────────────────
PYTHON_CMD=""
for cmd in python3.13 python3.12 python3.11 python3; do
  if command -v "$cmd" &>/dev/null; then
    VERSION=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$(echo "$VERSION" | cut -d. -f1)
    MINOR=$(echo "$VERSION" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
      PYTHON_CMD="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  error "Python $MIN_PYTHON+ is required but not found. Install it from https://python.org"
fi

PYTHON_VERSION=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
success "Found Python $PYTHON_VERSION at $(command -v $PYTHON_CMD)"

# ── Check pip ─────────────────────────────────────────────────────────────────
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
  error "pip is not available. Install it: $PYTHON_CMD -m ensurepip --upgrade"
fi

# ── Install via pipx (preferred) or pip ──────────────────────────────────────
if command -v pipx &>/dev/null; then
  info "Installing via pipx (isolated environment)..."
  pipx install "$PACKAGE" && success "ServerGuard installed via pipx"
elif "$PYTHON_CMD" -m pip show pipx &>/dev/null 2>&1; then
  info "Installing pipx then ServerGuard..."
  "$PYTHON_CMD" -m pip install --user pipx
  "$PYTHON_CMD" -m pipx ensurepath
  pipx install "$PACKAGE" && success "ServerGuard installed"
else
  warn "pipx not found. Installing directly with pip (--user)."
  warn "For better isolation, install pipx first: pip install pipx"
  "$PYTHON_CMD" -m pip install --user "$PACKAGE" && success "ServerGuard installed via pip"
fi

# ── Verify installation ───────────────────────────────────────────────────────
if command -v sg &>/dev/null; then
  success "sg is available at $(command -v sg)"
  sg --version
elif command -v sgd &>/dev/null; then
  success "sgd is available at $(command -v sgd)"
else
  warn "Commands not found in PATH. You may need to:"
  warn "  - Add ~/.local/bin to your PATH"
  warn "  - Or restart your shell"
  warn "  - Or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── Security recommendation ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Security Recommendations:${NC}"
echo "  1. Create a dedicated system user:  sudo useradd -r -s /bin/false serverguard"
echo "  2. Set config permissions:          chmod 600 /etc/serverguard/config.toml"
echo "  3. Enable as a service:             sudo systemctl enable --now serverguard"
echo "  4. Verify audit integrity:          serverguard audit verify"
echo ""

# ── Next steps ────────────────────────────────────────────────────────────────
echo -e "${BOLD}Quick Start:${NC}"
echo "  serverguard status --config /etc/serverguard/config.toml"
echo "  serverguard events --config /etc/serverguard/config.toml"
echo "  sgd --config /etc/serverguard/config.toml"
echo ""
echo "  Docs: https://github.com/AdityaKumar41/serverguard-oss/tree/main/docs"
echo ""
success "Installation complete! 🛡️"
