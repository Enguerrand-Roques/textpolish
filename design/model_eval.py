"""Compare local models per mode on realistic texts, with expected answers.

    venv/bin/python3 design/model_eval.py casual gemma4:e2b-it-qat gemma4:e2b-nvfp4 ...
    venv/bin/python3 design/model_eval.py pro gemma4:e2b-it-qat ...
    venv/bin/python3 design/model_eval.py custom gemma4:e2b-it-qat ...
    add --en to use the English test set
    add --large for the development Correction sets (benchmarks/eval/correction_{fr,en}.json)
    or --holdout / --holdout2 / --holdout3 / --holdout4 for the frozen test sets (holdout*_{fr,en}.json); they print a breakdown by
    kind of mistake and what the app applies by default (fixes marked for review are not)
    add --lt to run LanguageTool after the model, as the app does when it is installed

Correction is scored against expected outputs (exact match after
normalizing quotes/spaces), plus "overreach": changing a text that had
no mistake. Pro and Custom are scored with simple checks (language kept or
translated, no Markdown/email boilerplate, sensible length).
Latency: first call (cold load) and median of warm calls.
"""
import json
import os
import re
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import diff  # noqa: E402
import languagetool  # noqa: E402
import rewrite_checks  # noqa: E402
from platforms.macos.spelling import is_word  # noqa: E402

import llm  # noqa: E402

GOLD = [  # (input, [acceptable outputs])
    ("RH et opérationel on veut plus operationel", ["RH et opérationnel on veut plus opérationnel"]),
    ("Je pense qu'on pourras livrer mardi si tout ce passe bien", ["Je pense qu'on pourra livrer mardi si tout se passe bien",
                                                                   "Je pense qu'on pourra livrer mardi si tout ça se passe bien"]),
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
GOLD_EN = [
    ("Their going to the store tomorow", ["They're going to the store tomorrow"]),
    ("I has finished the report yesterday", ["I have finished the report yesterday", "I finished the report yesterday"]),
    ("Its a great idea, lets do it.", ["It's a great idea, let's do it."]),
    ("She dont know where they is.", ["She doesn't know where they are."]),
    ("We was planning to meet at the cafe, but it were closed.", ["We were planning to meet at the cafe, but it was closed."]),
    ("Can you send me you're notes before the meeting?", ["Can you send me your notes before the meeting?"]),
    ("The results was better then expected.", ["The results were better than expected."]),
    ("I recieve to many emails every day", ["I receive too many emails every day"]),
    ("He go to the gym every morning befor work.", ["He goes to the gym every morning before work."]),
    # no mistakes
    ("Thanks for the update, I will review the document tomorrow.", None),
    ("Let's meet on Friday at 10 to go over the plan.", None),
    ("The new version is live and the client is happy with it.", None),
]
PRO_EN = [
    "hey can u send me the file asap, need it for the meeting",
    "sorry im late, traffic was crazy, be there in 10",
    "thx for the help yesterday, ur a lifesaver",
    "we had the meeting, deadline is friday and the client is ok with it",
    "hi, saw ur hiring a product intern, super motivated, can we talk?",
]
CUSTOM_EN = [
    ("I'll be a bit late tomorrow, see you around 10.", "Translate into French", "fr_any"),
    ("Hi everyone, quick update on the project: we made good progress on payments but there are still bugs on the login page. I suggest we meet on Thursday to prioritize.", "Make the text shorter", "shorter"),
    ("Thanks for your help yesterday, it really saved me.", "Make the tone warmer and friendlier", "en_changed"),
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


def _checker_for(text):
    """Same dictionary rule as the app: the text's own language."""
    lang = llm.detect_language(text)
    diff.set_word_checker(lambda w: is_word(w, lang))


def _change_set(original, corrected):
    return {(p["before"].strip(), p["after"].strip())
            for p in diff.group_changes(original, corrected) if p["op"] == "change"}


def default_report(rows):
    """Score what the app applies by default (fixes marked for review are
    left out) and sort the failures: a wrong fix applied changes what the
    user wrote (grave); a missed fix leaves the text as written."""
    ok = wrong = missed = held = 0
    lines = []
    for text, _, expect, out in rows:
        if out.startswith("ERROR"):
            continue
        _checker_for(text)
        parts = diff.group_changes(text, out, TRUSTED.get(text, ()))
        held += sum(1 for p in parts if p["op"] == "change" and p["review"])
        applied = diff.apply_choices(parts, diff.default_accepted(parts))
        good = {norm(text)} if expect is None else {norm(e) for e in expect}
        if norm(applied) in good:
            ok += 1
            continue
        allowed = set().union(*(_change_set(text, e) for e in expect)) if expect else set()
        bad = _change_set(text, applied) - allowed
        if bad:
            wrong += 1
            lines.append(f"  - WRONG FIX APPLIED: {text!r} -> {applied!r}")
        else:
            missed += 1
            lines.append(f"  - missed: {text!r} -> {applied!r}")
    head = (f"applied by default: {ok}/{len(rows)} right · {wrong} wrong fix applied · "
            f"{missed} missed · {held} fix(es) held for review")
    return "\n".join([head] + lines)


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


LANG = "en" if "--en" in sys.argv else "fr"
if LANG == "en":
    GOLD, PRO, CUSTOM = GOLD_EN, PRO_EN, CUSTOM_EN
KINDS = {}  # text -> kind of mistake, for the large sets
USE_LT = "--lt" in sys.argv  # second pass with LanguageTool, as in the app
TRUSTED = {}  # text -> ranges LanguageTool rewrote (applied by default)
_SET = ("holdout4" if "--holdout4" in sys.argv else "holdout3" if "--holdout3" in sys.argv
        else "holdout2" if "--holdout2" in sys.argv else "holdout" if "--holdout" in sys.argv
        else "correction" if "--large" in sys.argv else None)
if _SET:
    _path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "benchmarks", "eval", f"{_SET}_{LANG}.json")
    with open(_path, encoding="utf-8") as _f:
        _large = json.load(_f)
    GOLD = [(c["text"], c["expected"]) for c in _large]
    KINDS = {c["text"]: c["kind"] for c in _large}
KEEP = {}  # text -> facts a rewrite must keep (names, days, times, amounts)
if "--large" in sys.argv:
    _eval = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmarks", "eval")
    with open(os.path.join(_eval, f"pro_{LANG}.json"), encoding="utf-8") as _f:
        _pro = json.load(_f)
    with open(os.path.join(_eval, f"custom_{LANG}.json"), encoding="utf-8") as _f:
        _custom = json.load(_f)
    PRO = [c["text"] for c in _pro]
    CUSTOM = [(c["text"], c["instruction"], c["kind"]) for c in _custom]
    KEEP = {c["text"]: c["keep"] for c in _pro + _custom}
# Kinds used by the small Round 6 sets, in the names of rewrite_checks
_OLD_KINDS = {"en": "to_en", "fr_any": "to_fr", "en_changed": "changed", "fr": "changed"}


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
    lt_times = []
    TRUSTED.clear()
    if USE_LT and mode == "casual":
        languagetool.start()
        for lang_, text_ in (("fr", "Bonjour à tous."), ("en", "Hello everyone.")):
            languagetool.check(text_, lang_)  # build both pipelines first
    for text, instr, expect in cases:
        out, dt = run(model, mode, text, instr)
        if USE_LT and mode == "casual" and not out.startswith("ERROR"):
            t0 = time.time()
            out, TRUSTED[text] = languagetool.improve(out, llm.detect_language(text))
            lt_times.append(time.time() - t0)
            dt += lt_times[-1]
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
            bad = rewrite_checks.pro_problems(text, out, KEEP.get(text, []), llm.detect_language)
            score += not bad
            if bad:
                notes.append(f"{bad}: {text!r} -> {out[:110]!r}")
        else:
            kind = _OLD_KINDS.get(expect, expect)
            bad = rewrite_checks.custom_problems(kind, text, out, KEEP.get(text, []), llm.detect_language)
            score += not bad
            if bad:
                notes.append(f"{instr} {bad}: {out[:110]!r}")
    warm = statistics.median(times) if times else float("nan")
    print(f"\n### {mode} · {LANG} · {model} · {where}")
    lt = f" · LanguageTool median {statistics.median(lt_times) * 1000:.0f} ms" if lt_times else ""
    print(f"score {score}/{len(rows)} · cold {first:.1f}s · warm median {warm:.2f}s{lt}")
    if KINDS and mode == "casual":
        by_kind = {}
        for text, instr, expect, out in rows:
            ok = not out.startswith("ERROR") and (
                norm(out) == norm(text) if expect is None else norm(out) in {norm(e) for e in expect})
            hit, total = by_kind.get(KINDS[text], (0, 0))
            by_kind[KINDS[text]] = (hit + ok, total + 1)
        print(" · ".join(f"{k} {h}/{n}" for k, (h, n) in sorted(by_kind.items())))
        print(default_report(rows))
    for n in notes:
        print("  -", n)
    for text, instr, expect, out in rows:
        print("   ·", repr(out)[:140])


if __name__ == "__main__":
    mode = sys.argv[1]
    for model in [a for a in sys.argv[2:] if not a.startswith("--")]:
        evaluate(mode, model)
