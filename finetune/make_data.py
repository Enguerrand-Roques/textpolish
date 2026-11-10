"""Build the fine-tuning set from finetune/data/ (Round 12).

    venv/bin/python finetune/make_data.py            # writes finetune/out/data/{train,valid}.jsonl

Correction examples come from three sources:
- correct messages (clean_*.txt) with 1 to 3 mistakes injected by the rules
  below; the target is the original message, so it is always right; about a
  third stay as written and must come back unchanged;
- harder mistakes written as pairs (hard_*.jsonl), including correct sentences
  a naive corrector would "fix";
- informal chat (informal_*.txt) that must come back unchanged.
Pro and Custom examples (rewrites.jsonl, from distill.py) keep those modes as
they are. Every prompt is built with llm.build_prompt, as in the app.

Nothing may come from the test sets: an example whose text shares too many
word trigrams with any sentence of benchmarks/eval/ is dropped.
"""

import glob
import json
import os
import random
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import languagetool  # noqa: E402
import llm  # noqa: E402

DATA = os.path.join(ROOT, "finetune", "data")
OUT = os.path.join(ROOT, "finetune", "out", "data")
KEEP_AS_IS = 0.3      # share of clean messages left without mistakes
OVERLAP_MAX = 0.5     # max trigram overlap with a test sentence
VALID_SHARE = 0.1
rng = random.Random(12)


# ── Mistakes, by language ──────────────────────────────────────────────────

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _swap_word(pairs: dict[str, str]):
    """A rule that replaces one whole word (lowercase) by its confusion."""
    def rule(s: str) -> str | None:
        hits = [m for m in re.finditer(r"[\w'’-]+", s) if m.group().lower() in pairs]
        if not hits:
            return None
        m = rng.choice(hits)
        new = pairs[m.group().lower()]
        if m.group()[0].isupper():
            new = new[0].upper() + new[1:]
        return s[:m.start()] + new + s[m.end():]
    return rule


def _regex(pattern: str, repl):
    def rule(s: str) -> str | None:
        hits = list(re.finditer(pattern, s))
        if not hits:
            return None
        m = rng.choice(hits)
        return s[:m.start()] + (repl(m) if callable(repl) else m.expand(repl)) + s[m.end():]
    return rule


def _typo(s: str) -> str | None:
    words = [m for m in re.finditer(r"\b[a-zà-ÿ]{6,}\b", s)]  # lowercase: no names
    if not words:
        return None
    m = rng.choice(words)
    w, i = m.group(), rng.randrange(1, len(m.group()) - 2)
    kind = rng.choice(("double", "swap", "drop"))
    if kind == "double":
        w = w[:i] + w[i] + w[i:]
    elif kind == "swap":
        w = w[:i] + w[i + 1] + w[i] + w[i + 2:]
    else:
        w = w[:i] + w[i + 1:]
    return s[:m.start()] + w + s[m.end():]


def _accent_one(s: str) -> str | None:
    words = [m for m in re.finditer(r"\w*[éèêàùçîôâëï]\w*", s)]
    if not words:
        return None
    m = rng.choice(words)
    return s[:m.start()] + _strip_accents(m.group()) + s[m.end():]


def _accent_all(s: str) -> str | None:
    out = _strip_accents(s)
    return out if out != s else None


_FR_SPELLING = {
    "intéressant": "interressant", "développement": "dévelopement", "connexion": "connection",
    "appeler": "apeller", "rappeler": "rapeller", "parmi": "parmis", "malgré": "malgrés",
    "vraiment": "vraiement", "beaucoup": "beacoup", "aujourd'hui": "aujourdhui",
    "langage": "language", "professionnel": "professionel",
    "opérationnel": "opérationel", "rendez-vous": "rendez vous", "personnellement": "personnelement",
    "occasion": "occassion", "adresse": "addresse", "apercevoir": "appercevoir",
    "dilemme": "dilemne", "bizarre": "bizzare", "évidemment": "évidement",
    "différent": "différend", "envoyer": "envoyé", "acheter": "achetter", "courrier": "courier",
    "salle": "sale", "calendrier": "calandrier", "abonnement": "abonnemment",
}

FR_RULES = [
    (_accent_one, 4), (_accent_all, 1), (_typo, 2),
    (_swap_word({"à": "a", "où": "ou", "ces": "ses", "ses": "ces", "sont": "son", "son": "sont",
                 "est": "et", "et": "est", "ça": "sa", "se": "ce", "ce": "se", "peut": "peu",
                 "peu": "peut", "ont": "on", "on": "ont", "dès": "des", "là": "la", "mais": "mes",
                 "quant": "quand", "leur": "leurs", "prêt": "près", "c'est": "s'est",
                 "s'est": "c'est", "quel": "quelle", "tous": "tout"}), 5),
    (_swap_word(_FR_SPELLING), 2),
    # past participle after avoir/être -> infinitive, and the reverse after a modal or preposition
    (_regex(r"\b(ai|as|a|avons|avez|ont|suis|es|est|sommes|êtes|sont)\s+(\w{2,})é\b",
            lambda m: f"{m.group(1)} {m.group(2)}er"), 3),
    (_regex(r"\b(vais|vas|va|allons|allez|vont|peux|peut|pouvons|pouvez|peuvent|dois|doit|"
            r"devons|devez|doivent|veux|veut|voulez|faut|pour|de|d'|sans|à)\s+(\w{2,})er\b",
            lambda m: f"{m.group(1)} {m.group(2)}é"), 3),
    (_regex(r"\b(\w{2,})ez\b(?= (?:le|la|les|moi|nous|un|une))",
            lambda m: f"{m.group(1)}er"), 1),
    # plural or feminine agreement dropped
    (_regex(r"\b(les|des|mes|tes|ses|nos|vos|leurs|ces|plusieurs|quelques)\s+(\w{3,})s\b",
            lambda m: f"{m.group(1)} {m.group(2)}"), 3),
    (_regex(r"\b(sont|étaient|seront|sommes|êtes|été)\s+(\w{3,}é)(?:e|s|es)\b",
            lambda m: f"{m.group(1)} {m.group(2)}"), 2),
    (_regex(r"\b(elle|Elle) (est|était|s'est) (\w{3,}é)e\b",
            lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)}"), 1),
    # wrong person
    (_regex(r"\b([Jj]e) (crois|dois|fais|vois|sais|veux|peux|prends|mets|reçois|dis|lis|écris)\b",
            lambda m: f"{m.group(1)} {m.group(2)[:-1]}t"), 2),
    (_regex(r"\btu (veux|peux)\b", lambda m: f"tu {m.group(1)[:-1]}t"), 1),
    (_regex(r"\b(je|tu) (envoie|envoies|oublie)\b", lambda m: f"{m.group(1)} {m.group(2).rstrip('es')}"), 1),
    (_regex(r"\b(ils|elles) (\w+)ront\b", lambda m: f"{m.group(1)} {m.group(2)}rons"), 1),
]

_EN_SPELLING = {
    "receive": "recieve", "definitely": "definately", "separate": "seperate", "tomorrow": "tommorow",
    "until": "untill", "business": "buisness", "necessary": "neccessary", "government": "goverment",
    "weird": "wierd", "calendar": "calender", "occurred": "occured", "accommodate": "accomodate",
    "embarrass": "embarass", "beginning": "begining", "believe": "beleive", "address": "adress",
    "really": "realy", "which": "wich", "because": "becuase", "different": "diffrent",
    "environment": "enviroment", "probably": "probaly", "schedule": "schedual", "argument": "arguement",
    "existence": "existance", "publicly": "publically", "truly": "truely", "familiar": "familar",
    "restaurant": "restaraunt", "experience": "experiance", "independent": "independant",
}
_EN_PARTICIPLES = {"gone": "went", "eaten": "ate", "written": "wrote", "taken": "took", "driven": "drove",
                   "broken": "broke", "chosen": "chose", "seen": "saw", "done": "did", "given": "gave",
                   "forgotten": "forgot", "spoken": "spoke", "begun": "began", "known": "knew"}

_EN_BARE = {"works": "work", "lives": "live", "needs": "need", "wants": "want", "thinks": "think",
            "says": "say", "goes": "go", "knows": "know", "likes": "like", "has": "have"}

EN_RULES = [
    (_typo, 2),
    (_swap_word(_EN_SPELLING), 3),
    (_swap_word({"don't": "dont", "can't": "cant", "won't": "wont", "didn't": "didnt", "doesn't": "doesnt",
                 "isn't": "isnt", "i'm": "im", "let's": "lets", "it's": "its", "that's": "thats",
                 "i've": "ive", "we're": "were", "you're": "your", "they're": "their"}), 4),
    (_swap_word({"their": "there", "there": "their", "your": "you're", "its": "it's", "than": "then",
                 "then": "than", "too": "to", "lose": "loose", "accept": "except", "affect": "effect",
                 "whether": "weather", "whose": "who's", "fewer": "less", "advice": "advise",
                 "principal": "principle", "passed": "past"}), 5),
    (_regex(r"\b(\w+)'s\b(?= [a-z])", lambda m: f"{m.group(1)}s"), 1),
    (_regex(r"\b(could|should|would|must) have\b", lambda m: f"{m.group(1)} of"), 1),
    (_regex(r"\b(have|has|had|'ve) (" + "|".join(_EN_PARTICIPLES) + r")\b",
            lambda m: f"{m.group(1)} {_EN_PARTICIPLES[m.group(2)]}"), 3),
    (_regex(r"\b(I|we|they|you) saw\b", lambda m: f"{m.group(1)} seen"), 1),
    (_regex(r"\b(he|she|it) doesn't\b", lambda m: f"{m.group(1)} don't"), 1),
    (_regex(r"\b(he|she|it|I) was\b", lambda m: f"{m.group(1)} were"), 1),
    (_regex(r"\b(we|they|you) were\b", lambda m: f"{m.group(1)} was"), 1),
    (_regex(r"\b(he|she|it) (works|lives|needs|wants|thinks|says|goes|knows|likes|has)\b",
            lambda m: f"{m.group(1)} {_EN_BARE[m.group(2)]}"), 1),
    (_regex(r"\ban (?=[aeiou])", "a "), 1),
    (_regex(r"\ba (?=[bcdfgjklmnpqrstvwxyz])", "an "), 1),
]


def inject(s: str, lang: str) -> str | None:
    """1 to 3 mistakes, each from a different rule; None if none applies."""
    rules = FR_RULES if lang == "fr" else EN_RULES
    out, unused = s, list(rules)
    for _ in range(rng.choice((1, 1, 1, 2, 2, 3))):
        while unused:
            rule = rng.choices([r for r, _ in unused], [w for _, w in unused])[0]
            unused = [(r, w) for r, w in unused if r is not rule]
            new = rule(out)
            if new and new != out:
                out = new
                break
    return out if out != s else None


# ── Test-set overlap ───────────────────────────────────────────────────────

def _norm(s: str) -> list[str]:
    return re.findall(r"\w+", _strip_accents(s.lower()))


def _trigrams(s: str) -> set:
    w = _norm(s)
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)} or {tuple(w)}


def test_index() -> tuple[set, dict]:
    sentences = set()
    for path in glob.glob(os.path.join(ROOT, "benchmarks", "eval", "*.json")):
        with open(path, encoding="utf-8") as f:
            for case in json.load(f):
                sentences.add(case["text"])
                sentences.update(e for e in (case.get("expected") or []) if isinstance(e, str))
    exact = {" ".join(_norm(s)) for s in sentences}
    index: dict = {}
    for s in sentences:
        grams = _trigrams(s)
        for g in grams:
            index.setdefault(g, []).append(grams)
    return exact, index


def overlaps(text: str, exact: set, index: dict) -> bool:
    if " ".join(_norm(text)) in exact:
        return True
    grams = _trigrams(text)
    for g in grams:
        for other in index.get(g, ()):
            if len(grams & other) / len(grams | other) > OVERLAP_MAX:
                return True
    return False


# ── Assembly ───────────────────────────────────────────────────────────────

def _lines(name: str) -> list[str]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def correction_examples() -> list[dict]:
    rows = []
    for lang in ("fr", "en"):
        for line in _lines(f"clean_{lang}_perso.txt") + _lines(f"clean_{lang}_pro.txt"):
            wrong = None if rng.random() < KEEP_AS_IS else inject(line, lang)
            rows.append({"src": "clean" if wrong else "clean_kept", "lang": lang,
                         "text": wrong or line, "target": line})
        for line in _lines(f"informal_{lang}.txt"):
            rows.append({"src": "informal", "lang": lang, "text": line, "target": line})
        for line in _lines(f"hard_{lang}.jsonl"):
            case = json.loads(line)
            rows.append({"src": "hard_" + case["kind"], "lang": lang,
                         "text": case["text"], "target": case["expected"]})
    return rows


def rewrite_examples() -> list[dict]:
    rows = []
    for line in _lines("rewrites.jsonl"):
        case = json.loads(line)
        rows.append({"src": case["mode"], "lang": case["lang"], "text": case["text"],
                     "instruction": case.get("instruction"), "target": case["output"]})
    return rows


def target_flagged(row: dict) -> bool:
    """LanguageTool finds a safe fix in a correction target. Read by hand, not
    dropped: on the first build, 27 of 29 flags were LanguageTool's mistakes
    ("viens en cueillir" -> "viennent")."""
    return bool(languagetool.safe_fixes(row["target"], row["lang"]))


def main():
    rows = correction_examples()
    exact, index = test_index()
    kept, dropped, flagged = [], 0, []
    use_lt = languagetool.installed() and languagetool.start()
    for row in rows:
        if overlaps(row["text"], exact, index) or overlaps(row["target"], exact, index):
            dropped += 1
        else:
            kept.append(row)
            if use_lt and target_flagged(row):
                flagged.append(row)
    rewrites = [r for r in rewrite_examples()
                if not overlaps(r["text"], exact, index)]
    examples = kept + rewrites
    rng.shuffle(examples)

    os.makedirs(OUT, exist_ok=True)
    n_valid = int(len(examples) * VALID_SHARE)
    for name, part in (("valid", examples[:n_valid]), ("train", examples[n_valid:])):
        with open(os.path.join(OUT, f"{name}.jsonl"), "w", encoding="utf-8") as f:
            for r in part:
                mode = "custom" if r["src"] == "custom" else "pro" if r["src"] == "pro" else "casual"
                prompt = llm.build_prompt(r["text"], mode, r.get("instruction"))
                f.write(json.dumps({"messages": [{"role": "user", "content": prompt},
                                                 {"role": "assistant", "content": r["target"]}]},
                                   ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "flagged.jsonl"), "w", encoding="utf-8") as f:
        for r in flagged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"{len(examples)} examples ({len(examples) - n_valid} train, {n_valid} valid); "
          f"{dropped} dropped for overlap with the test sets; {len(flagged)} targets flagged by LanguageTool (see flagged.jsonl)")
    print("by source:", dict(Counter(r["src"].split("_")[0] if r["src"].startswith("hard") else r["src"]
                                     for r in examples)))
    print("by language:", dict(Counter(r["lang"] for r in examples)))
    unchanged = sum(r["text"] == r["target"] for r in kept)
    print(f"Correction: {len(kept)} examples, {unchanged} must come back unchanged")


if __name__ == "__main__":
    main()
