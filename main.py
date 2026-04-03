#!/usr/bin/env python3
"""
TextPolish — point d'entrée principal.

Lance un listener de raccourci global (Cmd+Shift+P) et affiche un NSPanel
natif au-dessus de toutes les fenêtres, y compris les apps en plein écran.

Permissions macOS requises :
  • Accessibilité  (pour pynput / GlobalHotKeys)
  • Automatisation (pour osascript / keystroke)
"""

import sys

from AppKit import (
    NSApplication,
    NSApp,
    NSApplicationActivationPolicyAccessory,
    NSDate,
    NSDefaultRunLoopMode,
    NSEventMaskAny,
)

from config import SHORTCUT
from hotkey import install as install_hotkey
from ui import setup as setup_panel


def main() -> None:
    NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    # Indispensable avant de dispatcher des événements manuellement
    NSApp.finishLaunching()

    panel = setup_panel()

    install_hotkey(SHORTCUT, panel.trigger_polish)

    print(f"TextPolish démarré — raccourci actif : {SHORTCUT}")
    print("Appuie sur Ctrl+C dans ce terminal pour quitter.")

    # Boucle Cocoa complète : dispatche les NSEvent (clics, clavier, etc.)
    # Timeout de 0.5 s pour que Python capte KeyboardInterrupt (Ctrl+C).
    try:
        while True:
            event = NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_(
                NSEventMaskAny,
                NSDate.dateWithTimeIntervalSinceNow_(0.5),
                NSDefaultRunLoopMode,
                True,
            )
            if event is not None:
                NSApp.sendEvent_(event)
                NSApp.updateWindows()
    except KeyboardInterrupt:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
