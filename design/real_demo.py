"""Drive the real app for a screenshot: put text in TextEdit, select it,
press the shortcut, wait, capture the TextPolish panel.

    venv/bin/python3 design/real_demo.py "texte à corriger" out.png [wait_s] [keys]
keys: optional comma list of extra keys to press after the result appears
      (e.g. "return" to accept a card, "cmd+2" to switch to Pro).
Needs Accessibility + Automation + Screen Recording for the terminal app.
"""
import json
import subprocess
import sys
import time

import Quartz

text, out = sys.argv[1], sys.argv[2]
wait = float(sys.argv[3]) if len(sys.argv) > 3 else 8
keys = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []

def osa(script):
    subprocess.run(["osascript", "-e", script], check=True)

osa(f'''tell application "TextEdit"
  activate
  if (count of documents) = 0 then make new document
  set text of front document to {json.dumps(text, ensure_ascii=False)}
end tell''')
time.sleep(0.8)
osa('tell application "System Events" to keystroke "a" using command down')
time.sleep(0.3)
osa('tell application "System Events" to key code 5 using {command down, option down}')
time.sleep(wait)

CODES = {"return": 36, "tab": 48, "escape": 53}
for k in keys:
    if k.startswith("cmd+"):
        rest = k[4:]
        if rest in CODES:
            osa(f'tell application "System Events" to key code {CODES[rest]} using command down')
        else:
            osa(f'tell application "System Events" to keystroke "{rest}" using command down')
    else:
        osa(f'tell application "System Events" to key code {CODES[k]}')
    time.sleep(wait if k.startswith("cmd+") else 0.8)

def panel_bounds():
    for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
        if w.get("kCGWindowOwnerName") == "Python" and w.get("kCGWindowLayer", 0) > 0:
            b = w["kCGWindowBounds"]
            return int(b["X"]), int(b["Y"]), int(b["Width"]), int(b["Height"])
    return None

b = panel_bounds()
if b is None:
    print("panel not visible")
    sys.exit(1)
x, y, w, h = b
m = 40
subprocess.run(["screencapture", "-x", "-R", f"{x-m},{y-m},{w+2*m},{h+2*m}", out], check=True)
print("captured", b)
