"""Type text at the HID level (goes to the key window, e.g. the TextPolish panel)."""
import sys
import time

import Quartz

for ch in sys.argv[1]:
    for down in (True, False):
        e = Quartz.CGEventCreateKeyboardEvent(None, 0, down)
        Quartz.CGEventKeyboardSetUnicodeString(e, len(ch), ch)
        Quartz.CGEventSetFlags(e, 0)  # don't inherit a ⌘ still marked as held
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.015)
