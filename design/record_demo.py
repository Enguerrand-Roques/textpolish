"""Record the demo GIF frames: type a message in TextEdit, then use the real
app like a person (cards, Pro, Perso), while grabbing the screen region.

    venv/bin/python3 design/record_demo.py <frames_dir>

Frames are saved as frames_dir/NNNNN.png plus frames_dir/times.txt; assemble
them into a GIF with any tool (the repo's GIF was built with Pillow).
Needs the app running, plus Accessibility, Automation and Screen Recording.
Don't touch the keyboard or mouse while it runs (~40 s).
"""
import os
import subprocess
import sys
import threading
import time

import Quartz
from Foundation import NSURL

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fluidity import key, log_size, osa, panel_visible, shortcut, type_text, wait_ready, wait_until  # noqa: E402

OUT = sys.argv[1]
WIN = (220, 120, 820, 500)          # TextEdit window: x, y, w, h (points)
REGION = Quartz.CGRectMake(WIN[0] - 10, WIN[1] - 10, WIN[2] + 20, WIN[3] + 20)
FPS = 8
os.makedirs(OUT, exist_ok=True)
stop = threading.Event()


def grab():
    i, times = 0, []
    t0 = time.perf_counter()
    while not stop.is_set():
        t = time.perf_counter()
        img = Quartz.CGWindowListCreateImage(
            REGION, Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageNominalResolution)
        url = NSURL.fileURLWithPath_(os.path.join(OUT, f"{i:05d}.png"))
        dest = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
        Quartz.CGImageDestinationAddImage(dest, img, None)
        Quartz.CGImageDestinationFinalize(dest)
        times.append(t - t0)
        i += 1
        time.sleep(max(0, 1 / FPS - (time.perf_counter() - t)))
    with open(os.path.join(OUT, "times.txt"), "w") as f:
        f.write("\n".join(f"{x:.3f}" for x in times))


def select_all():
    osa('tell application "System Events" to keystroke "a" using command down')
    time.sleep(0.4)


osa(f'''tell application "TextEdit"
  activate
  if (count of documents) = 0 then make new document
  set text of front document to ""
  set bounds of front window to {{{WIN[0]}, {WIN[1]}, {WIN[0] + WIN[2]}, {WIN[1] + WIN[3]}}}
end tell''')
time.sleep(1)
# Large text so it reads in a small GIF: typing over a selected 22 pt
# character keeps that size.
osa('tell application "TextEdit" to set text of front document to "x"')
osa('tell application "TextEdit" to set size of text of front document to 22')
select_all()

rec = threading.Thread(target=grab)
rec.start()
time.sleep(0.8)

# 1. Correction: type a message with mistakes, select it, ⌥⌘G, accept the cards
type_text("Salut ! J'ai finit le rapport hier soir, les chiffres sont opérationel.")
time.sleep(0.8)
select_all()
since = log_size()
shortcut()
r = wait_ready(since)
time.sleep(1.6)
for _ in range((r or {}).get("changes", 1)):
    key("return")
    time.sleep(1.2)
wait_until(lambda: not panel_visible(), 3)
time.sleep(1.5)

# 2. Pro: same (now correct) text, ⌥⌘G, nothing to fix → ⌘2
select_all()
since = log_size()
shortcut()
wait_ready(since)
time.sleep(1.8)
since = log_size()
key("2", cmd=True)
wait_ready(since)
time.sleep(2.5)

# 3. Perso: ⌘3, type an instruction, ↵, then ⌘↵ to replace the text
key("3", cmd=True)
time.sleep(1.0)
since = log_size()
type_text("en anglais")
time.sleep(0.4)
key("return")
wait_ready(since)
time.sleep(2.2)
key("return", cmd=True)
wait_until(lambda: not panel_visible(), 3)
time.sleep(2.0)

stop.set()
rec.join()
print("frames:", len(os.listdir(OUT)) - 1)
