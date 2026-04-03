"""
Global hotkey listener using CGEventTap (Quartz) — contournement du bug
pynput/Python 3.13 où Thread._handle est écrasé par un ThreadHandle.

Supporte le format pynput : "<cmd>+<shift>+p"
"""

import threading
from CoreFoundation import CFRunLoopRun, kCFRunLoopDefaultMode
from Quartz import (
    CGEventTapCreate,
    CGEventMaskBit,
    CFMachPortCreateRunLoopSource,
    CFRunLoopGetCurrent,
    CFRunLoopAddSource,
    CGEventTapEnable,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    kCGSessionEventTap,
    kCGHeadInsertEventTap,
    kCGEventTapOptionListenOnly,
    kCGEventKeyDown,
    kCGKeyboardEventKeycode,
    kCGEventFlagMaskCommand,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskControl,
)

# Keycodes macOS pour les lettres a-z
_KEY_CODES: dict[str, int] = {
    'a': 0,  's': 1,  'd': 2,  'f': 3,  'h': 4,  'g': 5,  'z': 6,  'x': 7,
    'c': 8,  'v': 9,  'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 'y': 16,
    't': 17, 'o': 31, 'u': 32, 'i': 34, 'p': 35, 'l': 37, 'j': 38, 'k': 40,
    'n': 45, 'm': 46,
}

_MODIFIER_MAP: dict[str, int] = {
    'cmd':    kCGEventFlagMaskCommand,
    'shift':  kCGEventFlagMaskShift,
    'alt':    kCGEventFlagMaskAlternate,
    'option': kCGEventFlagMaskAlternate,
    'ctrl':   kCGEventFlagMaskControl,
}

# Masque des modificateurs pertinents (ignore CapsLock, NumLock, etc.)
_MOD_MASK = (
    kCGEventFlagMaskCommand
    | kCGEventFlagMaskShift
    | kCGEventFlagMaskAlternate
    | kCGEventFlagMaskControl
)


def _parse_shortcut(shortcut: str) -> tuple[int, int]:
    """
    Parse un raccourci style pynput (ex: "<cmd>+<shift>+p")
    et retourne (modifier_mask, keycode).
    """
    modifiers = 0
    keycode = None
    for part in shortcut.split('+'):
        part = part.strip().strip('<>').lower()
        if part in _MODIFIER_MAP:
            modifiers |= _MODIFIER_MAP[part]
        elif part in _KEY_CODES:
            keycode = _KEY_CODES[part]
        else:
            raise ValueError(f"Touche non reconnue : {part!r}")
    if keycode is None:
        raise ValueError(f"Aucune touche principale trouvée dans : {shortcut!r}")
    return modifiers, keycode


def install(shortcut: str, callback) -> None:
    """
    Installe un raccourci clavier global.

    Args:
        shortcut: Format pynput, ex. "<cmd>+<shift>+p"
        callback: Fonction appelée (depuis un thread daemon) quand le raccourci est détecté.
    """
    target_mods, target_keycode = _parse_shortcut(shortcut)

    def _event_handler(proxy, event_type, event, refcon):
        if event_type == kCGEventKeyDown:
            flags = CGEventGetFlags(event) & _MOD_MASK
            keycode = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))
            if flags == target_mods and keycode == target_keycode:
                try:
                    callback()
                except Exception as e:
                    print(f"[hotkey] Erreur dans le callback : {e}")
        return event

    def _run():
        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            CGEventMaskBit(kCGEventKeyDown),
            _event_handler,
            None,
        )
        if tap is None:
            print(
                "[hotkey] Impossible de créer l'event tap.\n"
                "→ Vérifie les permissions Accessibilité dans Préférences Système."
            )
            return

        source = CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(loop, source, kCFRunLoopDefaultMode)
        CGEventTapEnable(tap, True)
        CFRunLoopRun()

    t = threading.Thread(target=_run, daemon=True, name="hotkey-listener")
    t.start()
