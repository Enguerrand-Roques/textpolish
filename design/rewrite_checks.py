"""Automatic checks for rewrites (Pro and Custom), where there is no single
right answer. A rewrite fails if it breaks something checkable: the language,
a fact of the message (a name, a day, a time, an amount), the request, or if
it adds a greeting, a signature or a placeholder the user did not write.
They catch what goes wrong, not how good the style is.
"""

from __future__ import annotations

import re
import unicodedata

_GREETING = re.compile(r"^\s*(dear|hi|hello|hey|bonjour|salut|madame|monsieur|cher|chère)\b", re.I)
_SIGN_OFF = re.compile(r"(best regards|kind regards|sincerely|cordialement|bien à vous|respectueusement)", re.I)
_PLACEHOLDER = re.compile(r"\[[^\]]+\]")
_BOILERPLATE = re.compile(r"\*\*|^(objet|subject)\s*:", re.I | re.M)


def _fold(s: str) -> str:
    """Lowercase, no accents, no special spaces: "14 h" and "14h" still differ,
    so facts are written in the test set the way they must survive ("14")."""
    s = s.replace(" ", " ").replace(" ", " ").replace("’", "'").lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# A rewrite may write a number in words ("quinze heures", "two days") or with
# a thousands separator ("1,000"): the fact is kept, so both count as digits.
_UNITS = {
    "zero": 0, "un": 1, "une": 1, "one": 1, "deux": 2, "two": 2, "trois": 3, "three": 3,
    "quatre": 4, "four": 4, "cinq": 5, "five": 5, "six": 6, "sept": 7, "seven": 7,
    "huit": 8, "eight": 8, "neuf": 9, "nine": 9, "dix": 10, "ten": 10, "onze": 11,
    "eleven": 11, "douze": 12, "twelve": 12, "treize": 13, "thirteen": 13, "quatorze": 14,
    "fourteen": 14, "quinze": 15, "fifteen": 15, "seize": 16, "sixteen": 16,
    "dix-sept": 17, "seventeen": 17, "dix-huit": 18, "eighteen": 18, "dix-neuf": 19,
    "nineteen": 19, "vingt": 20, "twenty": 20, "trente": 30, "thirty": 30,
    "quarante": 40, "forty": 40, "cinquante": 50, "fifty": 50,
}
_SCALES = {"cent": 100, "hundred": 100, "mille": 1000, "thousand": 1000}
_NUMBER_WORDS = re.compile(r"\b(" + "|".join(sorted(_UNITS, key=len, reverse=True)) + r")\b(?:\s+("
                           + "|".join(_SCALES) + r"))?")


def _digits(folded: str) -> str:
    """'trois mille euros, 1,000 clients' -> '3000 euros, 1000 clients'."""
    folded = re.sub(r"(?<=\d)[ ,.](?=\d{3}\b)", "", folded)
    return _NUMBER_WORDS.sub(
        lambda m: str(_UNITS[m.group(1)] * (_SCALES[m.group(2)] if m.group(2) else 1)), folded)


def missing_facts(output: str, keep: list[str]) -> list[str]:
    folded = _fold(output)
    numeric = _digits(folded)
    return [fact for fact in keep if _fold(fact) not in folded and _fold(fact) not in numeric]


def rewrite_problems(text: str, output: str, keep: list[str], lang_of) -> list[str]:
    """Problems shared by every rewrite. *lang_of* is the language detector."""
    problems = []
    if _PLACEHOLDER.search(output) and not _PLACEHOLDER.search(text):
        problems.append("placeholder")
    if _BOILERPLATE.search(output):
        problems.append("markdown or subject line")
    if _GREETING.search(output) and not _GREETING.search(text):
        problems.append("invented greeting")
    if _SIGN_OFF.search(output) and not _SIGN_OFF.search(text):
        problems.append("invented sign-off")
    if len(output) > 3 * len(text) + 60:
        problems.append("too long")
    lost = missing_facts(output, keep)
    if lost:
        problems.append("lost " + ", ".join(lost))
    return problems


def pro_problems(text: str, output: str, keep: list[str], lang_of) -> list[str]:
    problems = rewrite_problems(text, output, keep, lang_of)
    if lang_of(text) != lang_of(output):
        problems.append("language changed")
    if _fold(" ".join(output.split())) == _fold(" ".join(text.split())):
        problems.append("unchanged")
    return problems


def _sentences(s: str) -> int:
    return len([p for p in re.split(r"[.!?]+(?:\s|$)", s.strip()) if p.strip()])


def custom_problems(kind: str, text: str, output: str, keep: list[str], lang_of) -> list[str]:
    """*kind* says what the request asks, so the result can be checked."""
    problems = rewrite_problems(text, output, keep, lang_of)
    same = lang_of(text) == lang_of(output)
    checks = {
        "to_en": lang_of(output) == "en",
        "to_fr": lang_of(output) == "fr",
        "shorter": len(output) < 0.8 * len(text) and same,
        # a list: marked items, or one item per line
        "bullets": (len(re.findall(r"^\s*[-•*]\s", output, re.M)) >= 2
                    or len([ln for ln in output.splitlines() if ln.strip()]) >= 3) and same,
        "one_sentence": _sentences(output) == 1 and same,
        # "vous", or an imperative in -ez ("Envoyez-moi"), and no "tu"
        "vous": bool(re.search(r"\bvous\b|\b\w+ez\b", output, re.I))
                and not re.search(r"\b(tu|t'|ton|ta|tes)\b", output, re.I),
        "question": output.rstrip().endswith("?") and same,
        "changed": same and _fold(output) != _fold(text),
    }
    if not checks[kind]:
        problems.append(f"request not met ({kind})")
    return problems
