#!/bin/bash
# TextPolish — one-command setup
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.user.textpolish"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
APP="$HOME/Desktop/TextPolish.app"

echo "Setting up TextPolish..."

PYTHON="${PYTHON:-python3}"  # install.sh passes the Python it found or installed
if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "  ✗ Python 3.10+ is required (found: $("$PYTHON" --version 2>&1))."
    echo "    Install a recent Python, e.g. 'brew install python@3.13'."
    exit 1
fi
if ! command -v ollama >/dev/null 2>&1; then
    echo "  ! Ollama not found — install it from https://ollama.com (setup continues)"
fi
LOG_DIR="$HOME/Library/Logs/TextPolish"
mkdir -p "$LOG_DIR"

# ── 1. Python venv ──────────────────────────────────────────────────────────
if [ ! -d "$REPO_DIR/venv" ]; then
    "$PYTHON" -m venv "$REPO_DIR/venv"
fi
"$REPO_DIR/venv/bin/pip" install -q --upgrade pip
"$REPO_DIR/venv/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
echo "  ✓ Dependencies installed"

# ── 2. Detect the real Python binary (bypass venv symlink for launchd) ──────
REAL_PYTHON=$("$PYTHON" -c "import os, sys; print(os.path.realpath(sys.executable))")

SITE_PACKAGES="$REPO_DIR/venv/lib/$(ls "$REPO_DIR/venv/lib/")/site-packages"

# ── 3. Config ────────────────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/config.py" ]; then
    cp "$REPO_DIR/config.example.py" "$REPO_DIR/config.py"
    echo "  ✓ config.py created — edit it to configure your Ollama settings"
else
    echo "  ✓ config.py already exists"
fi

# ── 4. LaunchAgent plist ─────────────────────────────────────────────────────
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${REAL_PYTHON}</string>
        <string>${REPO_DIR}/main.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>${SITE_PACKAGES}</string>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/textpolish.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/textpolish.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
echo "  ✓ LaunchAgent registered"

# ── 5. TextPolish.app on Desktop ─────────────────────────────────────────────
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/MacOS/TextPolish" << 'SCRIPT'
#!/bin/bash
LABEL="com.user.textpolish"
UID_VAL=$(id -u)
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
if ! launchctl print "gui/${UID_VAL}/${LABEL}" > /dev/null 2>&1; then
    launchctl bootstrap "gui/${UID_VAL}" "$PLIST"
fi
launchctl kickstart "gui/${UID_VAL}/${LABEL}"
SCRIPT
chmod +x "$APP/Contents/MacOS/TextPolish"

cat > "$APP/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>TextPolish</string>
    <key>CFBundleIdentifier</key>
    <string>com.user.textpolish</string>
    <key>CFBundleName</key>
    <string>TextPolish</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
PLIST

if [ -f "$REPO_DIR/AppIcon.icns" ]; then
    cp "$REPO_DIR/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
fi

find "$APP" -exec xattr -c {} \; 2>/dev/null
codesign --force --deep --sign - "$APP" 2>/dev/null || true
echo "  ✓ TextPolish.app created on Desktop"

if [ -n "${TEXTPOLISH_FROM_INSTALLER:-}" ]; then
    exit 0  # install.sh opens the app; its setup window does the rest
fi

echo ""
echo "All done! What's next:"
echo "  1. Make sure Ollama is running:  ollama serve"
echo "  2. Pull the model:               ollama pull enguerrandroquesbdl/textpolish-gemma4"
echo "  3. Double-click TextPolish.app on your Desktop"
echo "  4. Look for the pencil icon in your menu bar — that means it's running"
echo "  5. Select text anywhere, press Cmd+Option+G"
echo ""
echo "Optional: a second, rule-based check after the model (local, ~0.5 GB of RAM):"
echo "  brew install languagetool        # TextPolish starts it by itself when installed"
echo ""
echo "First launch: macOS may ask for Accessibility permission — grant it in System Settings."
