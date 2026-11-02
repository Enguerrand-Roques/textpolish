"""Post a key press at the HID level, like a physical keyboard.
    venv/bin/python3 design/press.py return [cmd]"""
import sys
import time

import Quartz

CODES = {"return": 36, "tab": 48, "escape": 53, "1": 18, "2": 19, "3": 20}
code = CODES[sys.argv[1]]
flags = Quartz.kCGEventFlagMaskCommand if "cmd" in sys.argv[2:] else 0
for down in (True, False):
    e = Quartz.CGEventCreateKeyboardEvent(None, code, down)
    Quartz.CGEventSetFlags(e, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.03)
