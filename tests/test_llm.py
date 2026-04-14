"""
Unit tests for llm.py — no Ollama server required (requests.post is mocked).
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

import llm
from llm import _detect_language, _load_prompt, polish_text


# ---------------------------------------------------------------------------
# _detect_language
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    def test_french_accented_chars(self):
        assert _detect_language("Je suis très content de vous voir.") == "fr"

    def test_french_cedilla(self):
        assert _detect_language("Ça marche très bien") == "fr"

    def test_french_stop_words_only(self):
        # No accents but multiple French stop words
        assert _detect_language("le chat de la maison") == "fr"

    def test_english_text(self):
        assert _detect_language("Hello, how are you today?") == "en"

    def test_empty_string(self):
        assert _detect_language("") == "en"

    def test_single_french_stop_word_is_not_enough(self):
        # One stop word match should not trigger French detection
        assert _detect_language("de") == "en"


# ---------------------------------------------------------------------------
# _load_prompt
# ---------------------------------------------------------------------------

class TestLoadPrompt:
    def test_load_pro_contains_professional(self):
        prompt = _load_prompt("pro")
        assert "professional" in prompt.lower()

    def test_load_casual_is_non_empty(self):
        prompt = _load_prompt("casual")
        assert len(prompt) > 20

    def test_load_custom_is_non_empty(self):
        prompt = _load_prompt("custom")
        assert len(prompt) > 20

    def test_missing_prompt_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            _load_prompt("nonexistent_prompt_xyz")


# ---------------------------------------------------------------------------
# polish_text
# ---------------------------------------------------------------------------

class TestPolishText:
    def test_empty_text_skips_ollama(self):
        with patch("llm.requests.post") as mock_post:
            result = polish_text("   ")
            mock_post.assert_not_called()
            assert result == "   "

    def test_connection_error_raises_readable_message(self):
        with patch("llm.requests.post", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect to Ollama"):
                polish_text("Hello", mode="casual")

    def test_timeout_raises_readable_message(self):
        with patch("llm.requests.post", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RuntimeError, match="timed out"):
                polish_text("Hello", mode="casual")

    def test_model_not_found_raises_readable_message(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        http_err = requests.exceptions.HTTPError(response=mock_resp)
        with patch("llm.requests.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = http_err
            with pytest.raises(RuntimeError, match="not found"):
                polish_text("Hello", mode="pro")

    def test_successful_response_returns_text(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Hello, world!"}
        mock_resp.raise_for_status.return_value = None
        with patch("llm.requests.post", return_value=mock_resp):
            assert polish_text("Hello world", mode="casual") == "Hello, world!"

    def test_french_text_injects_language_instruction(self):
        """The prompt sent to Ollama must mention 'French' for French input."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Bonjour"}
        mock_resp.raise_for_status.return_value = None
        with patch("llm.requests.post", return_value=mock_resp) as mock_post:
            polish_text("Bonjour le monde", mode="pro")
            payload = mock_post.call_args.kwargs["json"]
            assert "French" in payload["prompt"]

    def test_english_text_injects_language_instruction(self):
        """The prompt sent to Ollama must mention 'English' for English input."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Hi"}
        mock_resp.raise_for_status.return_value = None
        with patch("llm.requests.post", return_value=mock_resp) as mock_post:
            polish_text("Hello world", mode="pro")
            payload = mock_post.call_args.kwargs["json"]
            assert "English" in payload["prompt"]
