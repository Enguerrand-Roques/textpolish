"""Film the raw clips for the montage in video/: the app used in TextEdit,
then the menu bar icon with the history submenu. Keys and clicks are logged
with their time so the montage can show them on screen.

    venv/bin/python3 design/record_video.py video/public/raw [menu-only]

Writes demo.mov, menu.mov and events.json. Needs the app running with its
log in design/app.log, plus Accessibility, Automation and Screen Recording.
Don't touch the keyboard or mouse while it runs (~1 min 30).
"""
import json
import os
import subprocess
import sys
import threading
import time

import Quartz
from ApplicationServices import (
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    AXUIElementPerformAction,
    AXValueGetValue,
    kAXValueCGPointType,
    kAXValueCGSizeType,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fluidity import close, key, log_size, osa, panel_visible, shortcut, type_text, wait_ready, wait_until  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
WIN = (200, 140, 900, 520)  # TextEdit window: x, y, w, h (points)
os.makedirs(OUT, exist_ok=True)
MENU_ONLY = "menu-only" in sys.argv[2:]
EVENTS = os.path.join(OUT, "events.json")
events = {"demo": [], "menu": []}
if MENU_ONLY:
    with open(EVENTS) as f:
        events = json.load(f)
    events["menu"] = []
_clip, _t0 = None, 0.0


def mark(label):
    events[_clip].append({"t": round(time.perf_counter() - _t0, 3), "label": label})


def record(name, rect, seconds):
    global _clip, _t0
    x, y, w, h = rect
    path = os.path.join(OUT, f"{name}.mov")
    if os.path.exists(path):
        os.remove(path)
    proc = subprocess.Popen(["screencapture", "-x", "-v", "-C", "-V", str(seconds),
                             "-R", f"{x},{y},{w},{h}", path])
    _clip, _t0 = name, time.perf_counter()
    time.sleep(1.0)
    return proc


def mouse(kind, x, y):
    e = Quartz.CGEventCreateMouseEvent(None, kind, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def glide(x0, y0, x1, y1, seconds=0.6):
    steps = max(2, int(seconds * 60))
    for i in range(1, steps + 1):
        p = i / steps
        p = p * p * (3 - 2 * p)  # ease in-out
        mouse(Quartz.kCGEventMouseMoved, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p)
        time.sleep(seconds / steps)


def ax(el, attr):
    err, v = AXUIElementCopyAttributeValue(el, attr, None)
    return v if err == 0 else None


def frame_of(el):
    p = AXValueGetValue(ax(el, "AXPosition"), kAXValueCGPointType, None)[1]
    s = AXValueGetValue(ax(el, "AXSize"), kAXValueCGSizeType, None)[1]
    return p.x, p.y, s.width, s.height


def status_item():
    pid = int(subprocess.run(["pgrep", "-f", "Python main.py"], capture_output=True, text=True).stdout.split()[0])
    bar = ax(AXUIElementCreateApplication(pid), "AXExtrasMenuBar")
    return ax(bar, "AXChildren")[0]


def menu_items(el):
    for child in ax(el, "AXChildren") or []:
        if ax(child, "AXRole") == "AXMenu":
            return ax(child, "AXChildren") or []
    return []


def by_title(items, title):
    return next(i for i in items if ax(i, "AXTitle") == title)


# ── Set the stage ───────────────────────────────────────────────────────────
def fresh_text():
    """Empty document whose typing size is 24 pt."""
    osa('tell application "TextEdit" to set text of front document to "x"')
    osa('tell application "TextEdit" to set size of text of front document to 24')
    osa('tell application "System Events" to keystroke "a" using command down')
    time.sleep(0.3)


def select_all():
    osa('tell application "System Events" to keystroke "a" using command down')
    time.sleep(0.4)


def film_demo():
    mouse(Quartz.kCGEventMouseMoved, 1460, 940)  # cursor out of the shot
    osa(f'''tell application "TextEdit"
      activate
      if (count of documents) = 0 then make new document
      set bounds of front window to {{{WIN[0]}, {WIN[1]}, {WIN[0] + WIN[2]}, {WIN[1] + WIN[3]}}}
    end tell''')
    time.sleep(1)



    # Warm the model and put one earlier entry in the history, off camera.
    fresh_text()
    type_text("jsuis en retard de 10 min dsl, commencez sans moi")
    select_all()
    since = log_size()
    shortcut()
    wait_ready(since)
    since = log_size()
    key("2", cmd=True)
    wait_ready(since)
    time.sleep(0.5)
    key("return", cmd=True)
    wait_until(lambda: not panel_visible(), 3)
    time.sleep(1)
    fresh_text()

    # ── Clip 1: the app in TextEdit ─────────────────────────────────────────────
    proc = record("demo", WIN, 46)
    mark("type")
    type_text("Salut ! J'ai finit le rapport hier soir, les chiffres sont opérationel.")
    time.sleep(0.8)
    mark("⌘A")
    select_all()
    since = log_size()
    mark("⌥⌘G")
    shortcut()
    r = wait_ready(since)
    mark("ready")
    time.sleep(1.8)
    for _ in range((r or {}).get("changes", 1)):
        mark("↵")
        key("return")
        time.sleep(1.3)
    wait_until(lambda: not panel_visible(), 3)
    mark("pasted")
    time.sleep(1.5)

    select_all()
    since = log_size()
    mark("⌥⌘G")
    shortcut()
    wait_ready(since)
    mark("ready")
    time.sleep(1.8)
    since = log_size()
    mark("⌘2")
    key("2", cmd=True)
    wait_ready(since)
    mark("ready")
    time.sleep(2.6)

    mark("⌘3")
    key("3", cmd=True)
    time.sleep(1.0)
    since = log_size()
    mark("type")
    type_text("en anglais")
    time.sleep(0.4)
    mark("↵")
    key("return")
    wait_ready(since)
    mark("ready")
    time.sleep(2.4)
    mark("⌘↵")
    key("return", cmd=True)
    wait_until(lambda: not panel_visible(), 3)
    mark("pasted")
    time.sleep(2.0)
    proc.wait()


# ── Clip 2: menu bar icon → History ─────────────────────────────────────────
if not MENU_ONLY:
    film_demo()
osa('tell application "TextEdit" to activate')
time.sleep(1)
item = status_item()
ix, iy, iw, ih = frame_of(item)
cx, cy = ix + iw / 2, iy + ih / 2
rect = (int(cx - 820), 0, 1020, 300)
mouse(Quartz.kCGEventMouseMoved, cx - 260, 200)
proc = record("menu", rect, 10)
mark("move")
glide(cx - 260, 200, cx, cy, 0.9)
time.sleep(0.3)
mark("click")
# A synthetic click doesn't open this status item's menu; AXPress does. It
# blocks while the menu is open, so it runs on its own thread.
threading.Thread(target=AXUIElementPerformAction, args=(item, "AXPress"), daemon=True).start()
time.sleep(0.8)
items = menu_items(item)
hx, hy, hw, hh = frame_of(by_title(items, "Historique"))
mark("history")
glide(cx, cy, hx + hw / 2, hy + hh / 2, 0.6)
time.sleep(0.9)
sub = menu_items(by_title(items, "Historique"))
if sub:
    sx, sy, sw, sh = frame_of(sub[0])
    # slide horizontally first so the submenu stays open
    glide(hx + hw / 2, hy + hh / 2, sx + sw / 2, hy + hh / 2, 0.4)
    glide(sx + sw / 2, hy + hh / 2, sx + sw / 2, sy + sh / 2, 0.3)
    mark("entry")
    time.sleep(2.8)
key("escape")
mark("closed")
proc.wait()

events["demo_rect"] = WIN
events["menu_rect"] = rect
with open(EVENTS, "w") as f:
    json.dump(events, f, indent=1, ensure_ascii=False)
print(json.dumps(events, ensure_ascii=False))
