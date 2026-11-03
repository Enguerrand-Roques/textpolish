"""Build design/fixtures-en.json and fixtures-fr.json from real model outputs, so the design
preview shows what the app would actually display. Needs Ollama running.

    venv/bin/python3 design/make_fixtures.py [en|fr]   (default en → fixtures-en.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diff import group_changes, choose_layout  # noqa: E402
from llm import polish_text  # noqa: E402

SAMPLES_EN = [
    ("typo", "casual", "Their going to the store tomorow"),
    ("sms", "casual", "hey r u free tonite, we could grab dinner around 7 if your up for it"),
    ("clean", "casual", "Thanks for your message, I'll call you back tomorrow morning."),
    ("long", "casual", "Hi everyone, here is a quick update on the project. Last night we finish the new version late, "
              "the tests was passing and the client were happy with what he seen. However their are still a few bug "
              "on the login page and its mostly on mobile that it break. Can someone take care of it tomorow morning? "
              "I dont think we can finish everything before friday."),
    ("pro", "pro", "hey, saw ur profile and i think we could do cool stuff together, got 5 min to chat?"),
]
SAMPLES = [
    ("typo", "casual", "RH et opérationel on veut plus operationel"),
    ("sms", "casual", "slt tu fait quoi ce soir ? on peut se retrouver genre vers 19h pour manger un truc ?"),
    ("clean", "casual", "Merci pour ton message, je te rappelle demain matin."),
    ("long", "casual", "Bonjour a tous, je voulais vous faire un petit point sur le projet. On a bien avancer cette semaine "
              "sur la partie synchronisation mais il reste quelque blocage cote infra. Je pense qu'on pourras livrer "
              "mardi si tout ce passe bien, sinon on decalera de quelques jours. N'hesitez pas si vous avez des questions."),
    ("pro", "pro", "Salut, j'ai vu ton profil et je pense qu'on pourrait faire des trucs cool ensemble, t'as 5min pour qu'on se parle?"),
]

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
out = {}
for key, mode, text in (SAMPLES_EN if LANG == "en" else SAMPLES):
    result = polish_text(text, mode)
    parts = group_changes(text, result)
    out[key] = {"mode": mode, "input": text, "output": result,
                "parts": parts, "layout": choose_layout(parts, text, mode)}
    print(f"{key:6} {mode:7} -> {out[key]['layout']:8} {result!r}")

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fixtures-{LANG}.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
