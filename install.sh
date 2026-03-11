#!/bin/sh
set -e

REPO="publu/safe-buddy"
BRANCH="master"
URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}/safe_buddy.py"
BIN_NAME="safe-buddy"

# Determine install directory
if [ -n "$INSTALL_DIR" ]; then
  DIR="$INSTALL_DIR"
elif [ -w /usr/local/bin ]; then
  DIR="/usr/local/bin"
else
  DIR="$HOME/.local/bin"
fi

mkdir -p "$DIR"

echo "Installing ${BIN_NAME} to ${DIR}..."
curl -sL "$URL" -o "${DIR}/${BIN_NAME}"
chmod +x "${DIR}/${BIN_NAME}"

# Verify it's in PATH
if ! command -v "$BIN_NAME" >/dev/null 2>&1; then
  echo ""
  echo "Installed, but ${DIR} is not in your PATH."
  echo "Add it with:"
  echo ""
  echo "  export PATH=\"${DIR}:\$PATH\""
  echo ""
  echo "Or add that line to your shell profile (~/.bashrc, ~/.zshrc, etc.)"
else
  echo "Done! Run: ${BIN_NAME} --help"
fi
