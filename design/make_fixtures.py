"""Build design/fixtures.json from real model outputs, so the design
preview shows what the app would actually display. Needs Ollama running.

    venv/bin/python3 design/make_fixtures.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diff import group_changes, choose_layout  # noqa: E402
from llm import polish_text  # noqa: E402

SAMPLES = [
    ("typo", "casual", "RH et opérationel on veut plus operationel"),
    ("sms", "casual", "slt tu fait quoi ce soir ? on peut se retrouver genre vers 19h pour manger un truc ?"),
    ("clean", "casual", "Merci pour ton message, je te rappelle demain matin."),
    ("long", "casual", "Bonjour a tous, je voulais vous faire un petit point sur le projet. On a bien avancer cette semaine "
              "sur la partie synchronisation mais il reste quelque blocage cote infra. Je pense qu'on pourras livrer "
              "mardi si tout ce passe bien, sinon on decalera de quelques jours. N'hesitez pas si vous avez des questions."),
    ("pro", "pro", "Salut, j'ai vu ton profil et je pense qu'on pourrait faire des trucs cool ensemble, t'as 5min pour qu'on se parle?"),
]

out = {}
for key, mode, text in SAMPLES:
    result = polish_text(text, mode)
    parts = group_changes(text, result)
    out[key] = {"mode": mode, "input": text, "output": result,
                "parts": parts, "layout": choose_layout(parts, text, mode)}
    print(f"{key:6} {mode:7} -> {out[key]['layout']:8} {result!r}")

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
