"""Open at Login: setup.sh installs TextPolish as a LaunchAgent, and launchd
starts it at login when its plist says RunAtLoad. The menu bar checkbox reads
and writes that one key; launchd reads the file again at the next login.
"""

from __future__ import annotations

import os
import plistlib

PLIST = os.path.expanduser("~/Library/LaunchAgents/com.user.textpolish.plist")


def available(path: str = PLIST) -> bool:
    """False when TextPolish runs without setup.sh (no LaunchAgent)."""
    return os.path.exists(path)


def enabled(path: str = PLIST) -> bool:
    try:
        with open(path, "rb") as f:
            return bool(plistlib.load(f).get("RunAtLoad"))
    except (OSError, plistlib.InvalidFileException):
        return False


def set_enabled(on: bool, path: str = PLIST) -> None:
    with open(path, "rb") as f:
        plist = plistlib.load(f)
    plist["RunAtLoad"] = on
    with open(path, "wb") as f:
        plistlib.dump(plist, f)
