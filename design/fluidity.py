"""Time the real app like a user would feel it, end to end, in TextEdit.

    venv/bin/python3 design/fluidity.py [card perso ...]

Needs the app running with its log in design/app.log
(venv/bin/python main.py > design/app.log 2>&1), plus Accessibility and
Automation for the terminal. Keys are posted at the HID level, like a keyboard.
Don't touch the keyboard or mouse while it runs (~2 min).
"""
import json
import os
import re
import subprocess
import sys
import time

import Quartz

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "app.log")
PY = sys.executable
CODES = {"return": 36, "tab": 48, "escape": 53, "1": 18, "2": 19, "3": 20}


def osa(script):
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True).stdout.strip()


def set_text(text):
    osa(f'''tell application "TextEdit"
  activate
  if (count of documents) = 0 then make new document
  set text of front document to {json.dumps(text, ensure_ascii=False)}
end tell''')
    time.sleep(0.6)


def get_text():
    return osa('tell application "TextEdit" to get text of front document')


def select_all():
    osa('tell application "System Events" to keystroke "a" using command down')
    time.sleep(0.3)


def key(name, cmd=False):
    flags = Quartz.kCGEventFlagMaskCommand if cmd else 0
    for down in (True, False):
        e = Quartz.CGEventCreateKeyboardEvent(None, CODES[name], down)
        Quartz.CGEventSetFlags(e, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
        time.sleep(0.03)


def type_text(s):
    subprocess.run([PY, os.path.join(HERE, "type_text.py"), s], check=True)


def shortcut():
    subprocess.run([PY, os.path.join(HERE, "human_shortcut.py")], check=True)


def panel_visible():
    for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
        if w.get("kCGWindowOwnerName") == "Python" and w.get("kCGWindowLayer", 0) > 0:
            return True
    return False


def log_size():
    return os.path.getsize(LOG)


def wait_ready(since, timeout=30):
    """Wait for the next 'ready in' log line written after byte offset *since*."""
    end = time.time() + timeout
    while time.time() < end:
        with open(LOG, encoding="utf-8", errors="replace") as f:
            f.seek(since)
            m = re.search(r"(\w+) ready in (\d+) ms: (\w+), (\d+) change", f.read())
        if m:
            return {"mode": m[1], "ms": int(m[2]), "layout": m[3], "changes": int(m[4])}
        time.sleep(0.05)
    return None


def copy_ms(since):
    with open(LOG, encoding="utf-8", errors="replace") as f:
        f.seek(since)
        m = re.search(r"Copied \d+ chars in (\d+) ms", f.read())
    return int(m[1]) if m else None


def wait_until(pred, timeout=5):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if pred():
            return (time.perf_counter() - t0) * 1000
        time.sleep(0.02)
    return None


def open_on(text):
    """Select *text* in TextEdit and press the shortcut.
    Returns (log offset, ms until the panel is on screen)."""
    set_text(text)
    select_all()
    since = log_size()
    t0 = time.perf_counter()
    shortcut()
    shown = wait_until(panel_visible)
    return since, (t0, shown and (time.perf_counter() - t0) * 1000)


def close():
    if panel_visible():
        key("escape")
        wait_until(lambda: not panel_visible(), 2)
    time.sleep(0.4)


ROWS = []


def row(name, **kw):
    ROWS.append((name, kw))
    print(name, kw, flush=True)


def scenario_card():
    text = "RH et opérationel on veut plus operationel"
    since, (_, shown) = open_on(text)
    r = wait_ready(since)
    key("return")  # accept the card(s) one by one
    if r and r["changes"] > 1:
        for _ in range(r["changes"] - 1):
            time.sleep(0.35)
            key("return")
    pasted = wait_until(lambda: get_text() != text, 5)
    row("Short text message → cards → ↵", panel_ms=shown, copy_ms=copy_ms(since),
        ready=r, paste_ms=pasted, result=get_text())


def scenario_clean_then_pro():
    text = "Merci pour ton message, je te rappelle demain matin."
    since, (_, shown) = open_on(text)
    r = wait_ready(since)
    since2 = log_size()
    key("2", cmd=True)
    r2 = wait_ready(since2)
    row("Text without mistakes → ⌘2 Pro", panel_ms=shown, ready=r, after_cmd2=r2,
        still_open=panel_visible())
    close()


def scenario_switch_while_busy():
    text = "jsuis trop content pour toi frero tu la merité grave"
    since, (_, shown) = open_on(text)
    time.sleep(0.15)
    key("2", cmd=True)  # switch before the correction finishes
    r = wait_ready(since)
    row("⌘2 during the correction", panel_ms=shown, ready=r)
    close()


def scenario_perso():
    text = "Je serai un peu en retard demain, on se retrouve vers 10h."
    since, (_, shown) = open_on(text)
    wait_ready(since)
    key("3", cmd=True)
    time.sleep(0.4)
    since2 = log_size()
    type_text("en anglais")
    key("return")
    r = wait_ready(since2)
    t = time.perf_counter()
    key("return", cmd=True)  # accept the rewrite
    pasted = wait_until(lambda: get_text() != text, 5)
    row("⌘3 Custom “en anglais” → ⌘↵", panel_ms=shown, ready=r, paste_ms=pasted, result=get_text())


def scenario_document():
    text = ("Bonjour a tous, voici le compte rendu de la reunion de ce matin. "
            "Nous avons valider le budget du trimestre et l'equipe produit va commencer "
            "les test utilisateurs la semaine prochaine. Il reste quelque point a "
            "clarifier avec le service juridique avant la signature du contrat. "
            "Merci a chacun pour votre implication et bonne fin de semaine.")
    since, (_, shown) = open_on(text)
    r = wait_ready(since)
    key("return", cmd=True)  # accept all
    pasted = wait_until(lambda: get_text() != text, 5)
    row("Long report → document → ⌘↵", panel_ms=shown, ready=r, paste_ms=pasted,
        result=get_text())


def scenario_no_selection():
    set_text("")
    since = log_size()
    t0 = time.perf_counter()
    shortcut()
    shown = wait_until(panel_visible)
    time.sleep(0.5)
    row("No selection", panel_ms=shown, ollama_called=wait_ready(since, 1) is not None)
    close()


def scenario_escape():
    text = "Est ce que tu peux m'envoyer le dossier ?"
    since, (_, shown) = open_on(text)
    wait_ready(since)
    t = time.perf_counter()
    key("escape")
    gone = wait_until(lambda: not panel_visible(), 2)
    row("Esc closes without pasting", panel_ms=shown, close_ms=gone, untouched=get_text() == text)


if __name__ == "__main__":
    if not panel_visible() and not os.path.exists(LOG):
        sys.exit("start the app with its log in design/app.log first")
    names = sys.argv[1:]  # optional: run only some scenarios, e.g. "card perso"
    for s in (scenario_card, scenario_clean_then_pro, scenario_switch_while_busy,
              scenario_perso, scenario_document, scenario_no_selection, scenario_escape):
        if names and s.__name__.removeprefix("scenario_") not in names:
            continue
        try:
            s()
        except Exception as e:  # keep going, report the failure
            row(s.__name__, error=repr(e))
        close()
