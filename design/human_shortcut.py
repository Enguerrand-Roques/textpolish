"""Press ⌥⌘G like a person: modifiers down, G, hold ~250 ms, release.
Posted at the HID level so it goes through the real event routing."""
import time

import Quartz

CMD, ALT, G = 55, 58, 5
FLAGS = Quartz.kCGEventFlagMaskCommand | Quartz.kCGEventFlagMaskAlternate


def post(code, down, flags):
    e = Quartz.CGEventCreateKeyboardEvent(None, code, down)
    Quartz.CGEventSetFlags(e, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


post(CMD, True, Quartz.kCGEventFlagMaskCommand)
post(ALT, True, FLAGS)
time.sleep(0.05)
post(G, True, FLAGS)
time.sleep(0.05)
post(G, False, FLAGS)
time.sleep(0.25)
post(ALT, False, Quartz.kCGEventFlagMaskCommand)
post(CMD, False, 0)
