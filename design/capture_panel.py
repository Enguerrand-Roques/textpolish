"""Capture the visible TextPolish panel (with a margin) to the given path."""
import subprocess
import sys

import Quartz

for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
    if w.get("kCGWindowOwnerName") == "Python" and w.get("kCGWindowLayer", 0) > 0:
        b = w["kCGWindowBounds"]
        x, y, wd, h = int(b["X"]), int(b["Y"]), int(b["Width"]), int(b["Height"])
        m = 40
        subprocess.run(["screencapture", "-x", "-R", f"{x-m},{y-m},{wd+2*m},{h+2*m}", sys.argv[1]], check=True)
        print("captured", (x, y, wd, h))
        break
else:
    print("panel not visible")
