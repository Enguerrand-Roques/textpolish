#!/bin/bash
# design/scenario.sh "text" name [wait] — select text in TextEdit, press ⌥⌘G
# like a human, wait, capture the panel to design/screenshots/real-<name>.png
cd "$(dirname "$0")/.."
osascript -e "tell application \"TextEdit\" to activate" \
  -e "tell application \"TextEdit\" to set text of front document to \"$1\""
sleep 0.8
osascript -e 'tell application "System Events" to keystroke "a" using command down'
sleep 0.3
venv/bin/python3 design/human_shortcut.py
sleep "${3:-8}"
venv/bin/python3 design/capture_panel.py "design/screenshots/real-$2.png"
