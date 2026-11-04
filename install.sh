#!/bin/bash
# TextPolish installer, one command:
#   curl -fsSL https://raw.githubusercontent.com/Enguerrand-Roques/textpolish/main/install.sh | bash
#
# Installs what is missing (a recent Python, Ollama), the latest release of
# TextPolish, then opens it. The app's setup window downloads the model with a
# progress bar and asks for the Accessibility permission. Nothing needs sudo.
#
# Options (environment variables):
#   TEXTPOLISH_HOME=<dir>   where the app goes (default: ~/Library/Application Support/TextPolish)
#   TEXTPOLISH_NO_LT=1      skip LanguageTool (installed only if Homebrew is there)
set -euo pipefail

REPO="Enguerrand-Roques/textpolish"
HOME_DIR="${TEXTPOLISH_HOME:-$HOME/Library/Application Support/TextPolish}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
START=$(date +%s)

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
note() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; exit 1; }

bold "Installing TextPolish"
[ "$(uname -s)" = "Darwin" ] || fail "TextPolish is built for macOS."
[ "$(uname -m)" = "arm64" ] || note "Apple Silicon is recommended; on Intel the model is slow."

# ── 1. Python 3.10+ (installed with uv if missing: no Homebrew, no sudo) ─────
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        PYTHON="$(command -v "$candidate")"; break
    fi
done
if [ -z "$PYTHON" ] || [ -n "${TEXTPOLISH_FORCE_UV:-}" ]; then
    if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || fail "Could not install uv (needed for Python)."
    fi
    UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
    "$UV" python install 3.12 >/dev/null 2>&1 || fail "Could not install Python 3.12."
    PYTHON="$("$UV" python find 3.12)"
fi
ok "Python $("$PYTHON" -c 'import platform; print(platform.python_version())')"

# ── 2. Ollama, the engine that runs the model ───────────────────────────────
if [ -d /Applications/Ollama.app ] || [ -d "$HOME/Applications/Ollama.app" ] || command -v ollama >/dev/null 2>&1; then
    ok "Ollama already installed"
else
    echo "  … downloading Ollama (~230 MB)"
    curl -fsSL -o "$TMP/Ollama.zip" https://ollama.com/download/Ollama-darwin.zip || fail "Could not download Ollama."
    APPS=/Applications; [ -w "$APPS" ] || { APPS="$HOME/Applications"; mkdir -p "$APPS"; }
    ditto -x -k "$TMP/Ollama.zip" "$APPS"
    ok "Ollama installed in $APPS"
fi
if ! curl -fs -m 2 http://localhost:11434/api/version >/dev/null; then
    open -g -a Ollama 2>/dev/null || (command -v ollama >/dev/null && (ollama serve >/dev/null 2>&1 &))
fi

# ── 3. TextPolish, latest release ───────────────────────────────────────────
TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | "$PYTHON" -c "import json,sys; print(json.load(sys.stdin)['tag_name'])") \
    || fail "Could not reach GitHub."
curl -fsSL -o "$TMP/textpolish.zip" "https://github.com/$REPO/releases/download/$TAG/textpolish-$TAG.zip" \
    || fail "Could not download TextPolish $TAG."
ditto -x -k "$TMP/textpolish.zip" "$TMP"
mkdir -p "$HOME_DIR"
# Replace the code, keep the user's config.py and the Python environment.
rsync -a --delete --exclude config.py --exclude venv "$TMP/textpolish-$TAG/" "$HOME_DIR/"
ok "TextPolish $TAG in $HOME_DIR"

PYTHON="$PYTHON" TEXTPOLISH_FROM_INSTALLER=1 bash "$HOME_DIR/setup.sh" | sed 's/^/  /'

# ── 4. LanguageTool, the optional grammar checker ───────────────────────────
if [ -n "${TEXTPOLISH_NO_LT:-}" ]; then
    :
elif command -v brew >/dev/null 2>&1; then
    if brew list languagetool >/dev/null 2>&1; then
        ok "LanguageTool already installed"
    else
        echo "  … installing LanguageTool (optional grammar checker)"
        brew install --quiet languagetool >/dev/null 2>&1 && ok "LanguageTool installed" \
            || note "LanguageTool skipped (brew install languagetool failed)"
    fi
else
    note "LanguageTool skipped (needs Homebrew). TextPolish works without it."
fi

# ── 5. Open it: the setup window does the rest ──────────────────────────────
open "$HOME/Desktop/TextPolish.app"
bold "Done in $(( $(date +%s) - START )) s."
echo "  TextPolish is open: its setup window downloads the model (4.3 GB, once)"
echo "  and asks for the Accessibility permission. Then select text and press ⌥⌘G."
