"""Compare local models per mode on realistic texts, with expected answers.

    venv/bin/python3 design/model_eval.py casual qwen3.5:2b-nvfp4 ministral-3:3b ...
    venv/bin/python3 design/model_eval.py pro gemma3:4b ...
    venv/bin/python3 design/model_eval.py custom gemma3:4b ...

Correction is scored against expected outputs (exact match after
normalising quotes/spaces), plus "overreach": changing a text that had
no mistake. Pro/Perso are scored with simple checks (language kept or
translated, no Markdown/e-mail boilerplate, sensible length).
Latency: first call (cold load) and median of warm calls.
"""
import os
import re
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import llm  # noqa: E402

GOLD = [  # (input, [acceptable outputs])
    ("RH et opérationel on veut plus operationel", ["RH et opérationnel on veut plus opérationnel"]),
    ("Je pense qu'on pourras livrer mardi si tout ce passe bien", ["Je pense qu'on pourra livrer mardi si tout se passe bien"]),
    ("il reste quelque blocage cote infra", ["il reste quelques blocages côté infra", "il reste quelque blocage côté infra"]),
    ("Les enfant sont partis a l'école ce matin", ["Les enfants sont partis à l'école ce matin"]),
    ("J'ai finit le rapport hier soir", ["J'ai fini le rapport hier soir"]),
    ("Est ce que tu peux m'envoyer le dossier quand tu peux ?", ["Est-ce que tu peux m'envoyer le dossier quand tu peux ?"]),
    ("slt tu fait quoi ce soir ? on peut se retrouver vers 19h", ["slt tu fais quoi ce soir ? on peut se retrouver vers 19h", "Slt tu fais quoi ce soir ? On peut se retrouver vers 19h"]),
    ("Their going to the store tomorow", ["They're going to the store tomorrow"]),
    ("I has finished the report yesterday", ["I have finished the report yesterday", "I finished the report yesterday"]),
    # no mistakes: the model must not touch them
    ("Merci pour ton message, je te rappelle demain matin.", None),
    ("On a fait le meeting ce matin, le deadline est vendredi et le client est ok.", None),
    ("Thanks for the update, I will review the document tomorrow.", None),
]
PRO = [
    "jsuis trop content pour toi frero, tu la merité grave",
    "Hello ! J'ai vu que vous recrutez un stagiaire produit, je suis super motivé, on peut en parler ?",
    "Bonjour, je voulais savoir si on pouvait décaler la réunion de demain parce que j'ai un rdv médical.",
    "hey just wanted to let u know im running late, be there in 10",
    "On a fait le meeting ce matin, le deadline est vendredi et le client est ok.",
]
CUSTOM = [
    ("Salut, je serai un peu en retard demain, on se voit vers 10h.", "Traduis en anglais", "en"),
    ("Bonjour à tous, petit point sur le projet : on a bien avancé sur la partie paiement mais il reste des bugs sur la page de connexion. Je propose qu'on se fasse un point jeudi pour prioriser.", "Rends le texte plus court", "shorter"),
    ("Merci pour ton aide hier, ça m'a vraiment sauvé.", "Rends le ton plus chaleureux et amical", "fr"),
]


def norm(t: str) -> str:
    t = t.replace("’", "'").replace(" ", " ").replace(" ", " ")
    return " ".join(t.split()).strip().rstrip(".").lower()


def run(model, mode, text, instr=None):
    if mode == "casual":
        llm.OLLAMA_MODEL_CASUAL = model
    elif mode == "pro":
        llm.OLLAMA_MODEL_PRO = model
    else:
        llm.OLLAMA_MODEL = model
    t0 = time.time()
    try:
        out = llm.polish_text(text, mode, instr)
    except Exception as e:
        out = f"ERROR: {e}"
    return out, time.time() - t0


def runner(model):
    lines = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout.splitlines()
    if not lines:
        return "?"
    col = lines[0].find("RUNNER")
    for line in lines[1:]:
        if line.startswith(model + " ") and col >= 0:
            return line[col:].split()[0]
    return "?"


def evaluate(mode, model):
    llm._unload_model = lambda m: None
    subprocess.run(["ollama", "stop", model], capture_output=True)
    times, rows = [], []
    if mode == "casual":
        cases = [(t, None, g) for t, g in GOLD]
    elif mode == "pro":
        cases = [(t, None, None) for t in PRO]
    else:
        cases = [(t, i, k) for t, i, k in CUSTOM]
    first = None
    for text, instr, expect in cases:
        out, dt = run(model, mode, text, instr)
        if first is None:
            first = dt
        else:
            times.append(dt)
        rows.append((text, instr, expect, out))
    where = runner(model)
    score, notes = 0, []
    for text, instr, expect, out in rows:
        if out.startswith("ERROR"):
            notes.append(f"ERR {out[:60]}")
            continue
        if mode == "casual":
            ok = norm(out) == norm(text) if expect is None else norm(out) in {norm(e) for e in expect}
            score += ok
            if not ok:
                notes.append(f"{'TOUCHED' if expect is None else 'MISS'}: {text!r} -> {out!r}")
        elif mode == "pro":
            bad = []
            if llm._detect_language(text) != llm._detect_language(out):
                bad.append("lang")
            if re.search(r"\*\*|^objet|^subject", out, re.I | re.M):
                bad.append("boilerplate")
            if len(out) > 3 * len(text) + 60:
                bad.append("too long")
            if norm(out) == norm(text):
                bad.append("unchanged")
            score += not bad
            if bad:
                notes.append(f"{bad}: {out[:90]!r}")
        else:
            kind = expect
            ok = ((kind == "en" and llm._detect_language(out) == "en")
                  or (kind == "shorter" and len(out) < 0.8 * len(text))
                  or (kind == "fr" and llm._detect_language(out) == "fr" and norm(out) != norm(text)))
            score += ok
            if not ok:
                notes.append(f"{instr}: {out[:90]!r}")
    warm = statistics.median(times) if times else float("nan")
    print(f"\n### {mode} · {model} · {where}")
    print(f"score {score}/{len(rows)} · cold {first:.1f}s · warm median {warm:.2f}s")
    for n in notes:
        print("  -", n)
    for text, instr, expect, out in rows:
        print("   ·", repr(out)[:140])


if __name__ == "__main__":
    mode = sys.argv[1]
    for model in sys.argv[2:]:
        evaluate(mode, model)
