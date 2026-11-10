"""Pro and Custom examples for the fine-tuning set, written by the model in use.

    venv/bin/python finetune/distill.py [count_per_language] [fr|en]   # appends to finetune/data/rewrites.jsonl

Training only on Correction could change how the model rewrites. So the
current model (config.py) rewrites messages from finetune/data/ in Pro and
Custom, exactly as the app calls it, and only the outputs that pass the
Round 11 checks (design/rewrite_checks.py) are kept as examples.
"""

import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "design"))
import llm  # noqa: E402
import rewrite_checks  # noqa: E402

DATA = os.path.join(ROOT, "finetune", "data")
OUT = os.path.join(DATA, "rewrites.jsonl")
rng = random.Random(7)

# (instruction, what rewrite_checks.custom_problems checks)
INSTRUCTIONS = {
    "fr": [("Traduis en anglais", "to_en"), ("Rends-le plus court", "shorter"),
           ("Fais-en une liste à puces", "bullets"), ("En une seule phrase", "one_sentence"),
           ("Passe au vouvoiement", "vous"), ("Transforme-le en question", "question"),
           ("Rends-le plus chaleureux", "changed"), ("Plus formel", "changed"), ("Plus direct", "changed")],
    "en": [("Translate into French", "to_fr"), ("Make it shorter", "shorter"),
           ("Turn it into a bulleted list", "bullets"), ("Make it one sentence", "one_sentence"),
           ("Turn it into a question", "question"), ("Make it warmer", "changed"),
           ("More formal", "changed"), ("More casual", "changed")],
}
# A list, a shorter text or one sentence only make sense for longer messages.
_NEEDS_LONG = {"shorter", "bullets", "one_sentence"}


def _lines(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def _facts(text):
    """Numbers and times must survive a rewrite."""
    return re.findall(r"\d+(?:[h:.,]\d+)?", text)


def _done():
    if not os.path.exists(OUT):
        return set()
    with open(OUT, encoding="utf-8") as f:
        return {(c["mode"], c["text"], c.get("instruction")) for c in map(json.loads, f)}


def main(count, langs):
    llm._unload_model = lambda m: None
    done, kept, failed = _done(), 0, 0
    with open(OUT, "a", encoding="utf-8") as out:
        for lang in langs:
            casual = _lines(f"clean_{lang}_perso.txt") + _lines(f"informal_{lang}.txt")
            every = casual + _lines(f"clean_{lang}_pro.txt")
            long = [t for t in every if len(t) > 90]
            jobs = [("pro", t, None, None) for t in rng.sample(casual, count)]
            for _ in range(count):
                instruction, kind = rng.choice(INSTRUCTIONS[lang])
                text = rng.choice(long if kind in _NEEDS_LONG else every)
                jobs.append(("custom", text, instruction, kind))
            for mode, text, instruction, kind in jobs:
                if (mode, text, instruction) in done:
                    continue
                try:
                    output = llm.polish_text(text, mode=mode, custom_prompt=instruction)
                except RuntimeError:
                    failed += 1
                    continue
                if mode == "pro":
                    problems = rewrite_checks.pro_problems(text, output, _facts(text), llm.detect_language)
                else:
                    problems = rewrite_checks.custom_problems(kind, text, output, _facts(text),
                                                              llm.detect_language)
                if problems:
                    failed += 1
                    continue
                out.write(json.dumps({"mode": mode, "lang": lang, "text": text, "instruction": instruction,
                                      "output": output}, ensure_ascii=False) + "\n")
                out.flush()
                kept += 1
    print(f"{kept} rewrites kept, {failed} dropped (failed a check or an error)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 250, sys.argv[2:] or ["fr", "en"])
