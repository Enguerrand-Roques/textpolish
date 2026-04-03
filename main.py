#!/usr/bin/env python3
"""
TextPolish — point d'entrée principal.

Lance un listener de raccourci global (Cmd+Shift+P) et affiche un NSPanel
natif au-dessus de toutes les fenêtres, y compris les apps en plein écran.

Permissions macOS requises :
  • Accessibilité  (pour pynput / GlobalHotKeys)
  • Automatisation (pour osascript / keystroke)
"""

import signal
import sys

from AppKit import NSApplication, NSApp, NSApplicationActivationPolicyAccessory
from pynput import keyboard

from config import SHORTCUT
from ui import setup as setup_panel


def main() -> None:
    # NSApplication doit être initialisé avant tout appel AppKit
    NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    panel = setup_panel()

    def on_shortcut():
        panel.trigger_polish()

    hotkeys = keyboard.GlobalHotKeys({SHORTCUT: on_shortcut})
    hotkeys.daemon = True
    hotkeys.start()

    print(f"TextPolish démarré — raccourci actif : {SHORTCUT}")
    print("Appuie sur Ctrl+C dans ce terminal pour quitter.")

    # Permet Ctrl+C de quitter proprement depuis le terminal
    signal.signal(signal.SIGINT, lambda *_: (hotkeys.stop(), sys.exit(0)))

    NSApp.run()


if __name__ == "__main__":
    main()
