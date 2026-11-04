import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design"))

from rewrite_checks import custom_problems, missing_facts, pro_problems  # noqa: E402


def _lang(text):
    return "fr" if any(w in text.lower().split() for w in ("je", "le", "la", "vous", "on")) else "en"


class TestFacts:
    def test_facts_survive_case_and_accents(self):
        assert missing_facts("La réunion est décalée à MARDI, 14 h", ["mardi", "14"]) == []

    def test_a_changed_day_is_caught(self):
        assert missing_facts("Nous nous verrons vendredi", ["jeudi"]) == ["jeudi"]


class TestPro:
    def test_good_rewrite_passes(self):
        assert pro_problems("dsl je serai en retard, rdv à 10h30",
                            "Je vous prie de m'excuser, je serai en retard ; rendez-vous à 10h30.",
                            ["10", "30"], _lang) == []

    def test_invented_greeting_placeholder_and_lost_fact(self):
        problems = pro_problems("can i take friday off?", "Dear [Manager], may I take Monday off?",
                                ["friday"], _lang)
        assert "invented greeting" in problems and "placeholder" in problems
        assert "lost friday" in problems


class TestCustom:
    def test_list_and_one_sentence_and_vous(self):
        assert custom_problems("bullets", "acheter du pain et du lait", "- pain\n- lait", [], _lang) == []
        assert custom_problems("one_sentence", "On a fini. Le client est content.",
                               "On a fini. Le client est content.", [], _lang) == ["request not met (one_sentence)"]
        assert custom_problems("vous", "Tu peux venir ?", "Vous pouvez venir ?", [], _lang) == []
        assert custom_problems("vous", "Tu peux venir ?", "Tu peux venir, vous ?", [], _lang) != []
