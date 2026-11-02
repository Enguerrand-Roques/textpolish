"""Film the raw clips for the montage in video/: the app used in TextEdit,
then the menu bar icon with the history submenu. Keys and clicks are logged
with their time so the montage can show them on screen.

    venv/bin/python3 design/record_video.py video/public/raw [menu-only|lang-only]

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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import t  # noqa: E402
from fluidity import close, key, log_size, osa, panel_visible, shortcut, type_text, wait_ready, wait_until  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
WIN = (150, 100, 980, 760)  # TextEdit window: x, y, w, h (points)
# Long enough to open the document view and show several kinds of mistakes
# (grammar, agreement, conjugation, spelling, punctuation, capitalization).
TEXT = ("Hi everyone, here is a quick update on the project. Last night we finish the new version late, "
        "the tests was passing and the client were happy with what he seen. However their are still a few bug "
        "on the login page and its mostly on mobile that it break. Can someone take care of it tomorow morning? "
        "I dont think we can finish everything before friday.")
REQUEST = "translate into French"
# Shown after switching the interface to French (menu → Language → Français).
TEXT_FR = ("Bonjour a tous, voici un petit point sur le projet. Hier soir on a finit la nouvelle "
           "version tard, les testes sont passer et le client a était content de ce qu'il a vu. "
           "Par contre il reste quelque bug sur la page de connexion et ces surtout sur mobile que "
           "sa bloque. Est ce que quelqu'un peux s'en occupé demain matin, je pense qu'on a encore "
           "besoin de deux jour pour tout finir.")
os.makedirs(OUT, exist_ok=True)
MENU_ONLY = "menu-only" in sys.argv[2:]
LANG_ONLY = "lang-only" in sys.argv[2:]
EVENTS = os.path.join(OUT, "events.json")
events = {"demo": [], "menu": [], "lang": []}
if MENU_ONLY or LANG_ONLY:
    with open(EVENTS) as f:
        events = json.load(f)
    events["lang"] = []
    if MENU_ONLY:
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


def save_events():
    events["demo_rect"] = WIN
    with open(EVENTS, "w") as f:
        json.dump(events, f, indent=1, ensure_ascii=False)


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
    osa('tell application "TextEdit" to set size of text of front document to 22')
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
    type_text("sorry im 10 min late, start without me")
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
    proc = record("demo", WIN, 55)
    mark("type")
    type_text(TEXT)
    time.sleep(0.8)
    mark("⌘A")
    select_all()
    since = log_size()
    mark("⌥⌘G")
    shortcut()
    wait_ready(since)
    mark("ready")
    time.sleep(5.0)  # time to read the highlighted fixes and the legend
    mark("⌘↵")
    key("return", cmd=True)
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
    type_text(REQUEST)
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
    save_events()


def film_language():
    """Clip 3: menu → Language → Français, then the popup in French."""
    osa('tell application "TextEdit" to activate')
    osa(f'tell application "TextEdit" to set text of front document to {json.dumps(TEXT_FR, ensure_ascii=False)}')
    for _ in range(5):  # TextEdit sometimes applies the size late
        osa('tell application "TextEdit" to set size of text of front document to 22')
        time.sleep(0.4)
        if osa('tell application "TextEdit" to get size of character 1 of front document') == "22":
            break
    item = status_item()
    ix, iy, iw, ih = frame_of(item)
    cx, cy = ix + iw / 2, iy + ih / 2
    # up to the screen's right edge: the Language submenu opens to the right
    screen_w = int(Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()).size.width)
    rect = (WIN[0], 0, screen_w - WIN[0], 760)
    mouse(Quartz.kCGEventMouseMoved, cx - 300, 300)
    proc = record("lang", rect, 30)
    mark("move")
    glide(cx - 300, 300, cx, cy, 0.8)
    mark("click")
    threading.Thread(target=AXUIElementPerformAction, args=(item, "AXPress"), daemon=True).start()
    time.sleep(0.8)
    items = menu_items(item)
    lang_item = by_title(items, t("menu_language"))
    lx, ly = press_item_hover(lang_item, cx, cy)
    mark("language")
    choices = menu_items(lang_item)
    french = next(c for c in choices if ax(c, "AXTitle") == "Français")
    fx, fy, fw, fh = frame_of(french)
    glide(lx, ly, fx + fw / 2, ly, 0.3)
    glide(fx + fw / 2, ly, fx + fw / 2, fy + fh / 2, 0.3)
    time.sleep(0.6)
    mark("français")
    AXUIElementPerformAction(french, "AXPress")
    time.sleep(1.0)
    mouse(Quartz.kCGEventMouseMoved, 1460, 940)
    select_all()
    since = log_size()
    mark("⌥⌘G")
    shortcut()
    wait_ready(since, 60)
    mark("ready")
    time.sleep(4.5)
    key("escape")
    mark("closed")
    proc.wait()
    events["lang_rect"] = rect
    save_events()


def press_item_hover(item, x0, y0):
    """Glide onto a menu item so its submenu opens; returns where the cursor is."""
    x, y, w, h = frame_of(item)
    glide(x0, y0, x + w / 2, y + h / 2, 0.6)
    time.sleep(0.9)
    return x + w / 2, y + h / 2


def switch_language(code):
    """Off camera: set the language back through the same menu."""
    item = status_item()
    threading.Thread(target=AXUIElementPerformAction, args=(item, "AXPress"), daemon=True).start()
    time.sleep(0.8)
    lang_item = next(i for i in menu_items(item) if ax(i, "AXTitle") in ("Language", "Langue"))
    AXUIElementPerformAction(lang_item, "AXPress")
    time.sleep(0.5)
    choice = next(c for c in menu_items(lang_item) if ax(c, "AXRepresentedObject") == code
                  or ax(c, "AXTitle") == {"en": "English", "fr": "Français"}[code])
    AXUIElementPerformAction(choice, "AXPress")
    time.sleep(0.5)


if LANG_ONLY:
    film_language()
    switch_language("en")
    print(json.dumps(events["lang"], ensure_ascii=False))
    sys.exit(0)

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
hx, hy, hw, hh = frame_of(by_title(items, t("menu_history")))
mark("history")
glide(cx, cy, hx + hw / 2, hy + hh / 2, 0.6)
time.sleep(0.9)
sub = menu_items(by_title(items, t("menu_history")))
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

events["menu_rect"] = rect
save_events()
if not MENU_ONLY:
    film_language()
    switch_language("en")
print(json.dumps(events, ensure_ascii=False))
