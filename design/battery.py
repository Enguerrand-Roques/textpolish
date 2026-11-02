"""Run realistic user texts through every mode and print what the popup
would show (layout + number of changes + output). Needs Ollama.

    venv/bin/python3 design/battery.py [casual|pro|custom ...]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from diff import choose_layout, group_changes  # noqa: E402
from llm import polish_text  # noqa: E402

TEXTS = {
    "ami_sms":     "tu viens ce soir ou pas ? on se retrouve au bar vers 21h",
    "ami_fautes":  "jsuis trop content pour toi frero, tu la merité grave",
    "propre_info": "Salut, je serai un peu en retard demain, on se voit vers 10h.",
    "mail_boss":   "Bonjour, je voulais savoir si on pouvait décaler la réunion de demain parce que j'ai un rdv médical.",
    "linkedin":    "Hello ! J'ai vu que vous recrutez un stagiaire produit, je suis super motivé, on peut en parler ?",
    "en_typos":    "hey just wanted to let u know im running late, be there in 10",
    "en_clean":    "Thanks for the update, I will review the document tomorrow.",
    "mixte":       "On a fait le meeting ce matin, le deadline est vendredi et le client est ok.",
    "long":        "Bonjour à tous, petit point sur le projet : on a bien avancer sur la partie paiement mais il reste des bug sur la page de connexion. "
                   "Je propose qu'on se fasse un point jeudi pour prioriser, sinon on risque de pas tenir la date de mise en prod.",
}
CUSTOM = ["traduire en anglais", "plus court", "plus drôle", "plus chaleureux"]

modes = sys.argv[1:] or ["casual", "pro", "custom"]
for key, text in TEXTS.items():
    for mode in modes:
        instructions = CUSTOM[:2] if mode == "custom" else [None]
        for instr in instructions:
            t0 = time.time()
            try:
                out = polish_text(text, mode, instr)
            except Exception as e:
                out = f"ERROR: {e}"
            dt = time.time() - t0
            parts = group_changes(text, out) if not out.startswith("ERROR") else []
            n = sum(p["op"] == "change" for p in parts)
            layout = choose_layout(parts, text, mode) if parts else "error"
            tag = mode + (f"[{instr}]" if instr else "")
            print(f"{key:12} {tag:30} {dt:5.1f}s {layout:8} {n:2} chg | {out!r}")
