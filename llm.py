"""
Ollama local backend — sends text to a local model and returns the polished version.
"""

import os
import re
import json
import logging
import requests
from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_MODEL_PRO,
    OLLAMA_MODEL_CASUAL,
    OLLAMA_TIMEOUT,
    OLLAMA_KEEP_ALIVE,
)

# Texts longer than this are rejected: the model context is sized from the
# input (see _num_ctx_for), and very long inputs would be slow and risk
# silent truncation of the instructions.
MAX_INPUT_CHARS = 4000

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# Track the last model used so we can unload it when switching models.
# Two models loaded simultaneously on 16 GB causes heavy swap usage.
_active_model: str | None = None


def _unload_model(model: str) -> None:
    """Ask Ollama to evict *model* from RAM (best-effort, non-blocking)."""
    try:
        requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "keep_alive": 0},
            timeout=5,
        )
        logging.debug("Unloaded model from RAM: %s", model)
    except Exception:
        pass


def _load_prompt(name: str) -> str:
    path = os.path.join(_PROMPTS_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


_FRENCH_CHARS = set("éèêëàâùûüîïôœæç")
_FRENCH_STOP_WORDS = {
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "en", "au", "aux",
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "que", "qui", "ne", "pas", "sur", "par", "pour", "avec", "dans", "chez",
    "ce", "ça", "ca", "est", "ai", "as", "suis", "es", "sont", "mais", "ou", "donc",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses", "moi", "toi",
    "très", "tres", "bien", "plus", "tout", "rien", "hier", "demain", "soir",
    "merci", "bonjour", "salut", "slt", "oui", "non", "quoi", "peux", "veux",
}
# Split on apostrophes too, so "j'ai" counts as "j" + "ai".
_WORD_RE = re.compile(r"[\w]+", re.UNICODE)


def _detect_language(text: str) -> str:
    """Return 'fr' if the text is likely French, 'en' otherwise.

    Uses two signals in order of priority:
    1. French-specific accented characters (é, è, ç, œ…) — very reliable.
    2. French stop words — catches unaccented French text.
    """
    if any(c in _FRENCH_CHARS for c in text.lower()):
        return "fr"
    words = set(_WORD_RE.findall(text.lower()))
    if len(words & _FRENCH_STOP_WORDS) >= 2:
        return "fr"
    return "en"


def _num_ctx_for(prompt_text: str) -> int:
    """Context window sized to the prompt: ~3 chars/token worst case, room for
    an output about as long as the input, floor of 1024 to keep the KV cache small."""
    est_tokens = len(prompt_text) // 3 + 1
    return max(1024, ((est_tokens * 2 + 255) // 256) * 256)


def polish_text(
    text: str,
    mode: str = "pro",
    custom_prompt: str | None = None,
    on_token=None,
) -> str:
    """
    Send *text* to a local Ollama model and return the corrected version.

    Args:
        text:          The raw text to polish.
        mode:          "pro" | "casual" — selects the matching prompt file.
        custom_prompt: If provided, applied through the custom prompt template.
        on_token:      Optional callback(token: str) called for each streamed
                       token. When provided, streaming mode is used and tokens
                       are delivered as they arrive. The full result is still
                       returned at the end.

    Returns:
        The polished text string.
    """
    global _active_model

    if not text.strip():
        return text

    if len(text) > MAX_INPUT_CHARS:
        raise RuntimeError(
            f"Text too long ({len(text)} characters, max {MAX_INPUT_CHARS}). "
            "Select a shorter passage."
        )

    prompt_name = "custom" if custom_prompt else mode
    system = _load_prompt(prompt_name)

    if mode == "pro":
        model = OLLAMA_MODEL_PRO
    elif mode == "casual":
        model = OLLAMA_MODEL_CASUAL
    else:
        model = OLLAMA_MODEL

    # If switching to a different model, unload the previous one first
    # to avoid both models occupying RAM simultaneously.
    if _active_model and _active_model != model:
        _unload_model(_active_model)
    _active_model = model

    # Small models (gemma3:1b) ignore the "same language" rule in the system
    # prompt when the task is cognitively demanding (e.g. pro rewriting).
    # We detect the input language and prepend an explicit override so the
    # model cannot miss it — this was validated in benchmark Round 2.
    lang = _detect_language(text)
    lang_names = {"fr": "French", "en": "English"}
    lang_instruction = (
        f"IMPORTANT: The input text is in {lang_names[lang]}. "
        f"You MUST output in {lang_names[lang]} only.\n\n"
    )

    if custom_prompt:
        prompt_text = (
            f"{lang_instruction}{system}\n\n"
            "Custom instruction to apply:\n"
            f"{custom_prompt.strip()}\n\n"
            "Text to rewrite:\n"
            f"{text}"
        )
    else:
        prompt_text = f"{lang_instruction}{system}\n\nText to rewrite:\n{text}"

    is_streaming = on_token is not None
    payload = {
        "model": model,
        "prompt": prompt_text,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "stream": is_streaming,
        # Hybrid-reasoning models (Gemma 4, Qwen 3.5, LFM3) think by default,
        # which turns a 1 s correction into tens of seconds.
        "think": False,
        "options": {"num_ctx": _num_ctx_for(prompt_text)},
    }

    logging.debug("Calling Ollama | model=%s | mode=%s | %d chars | stream=%s",
                  model, mode, len(text), is_streaming)

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
            stream=is_streaming,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure it is running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {OLLAMA_TIMEOUT}s. "
            "Try a smaller model or increase OLLAMA_TIMEOUT in config.py."
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise RuntimeError(
                f"Model '{model}' not found. "
                f"Install it with: `ollama pull {model}`"
            )
        raise RuntimeError(f"Ollama returned an error: {e}")

    if is_streaming:
        parts: list[str] = []
        truncated = False
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            try:
                chunk = json.loads(raw_line)
            except json.JSONDecodeError:
                raise RuntimeError("Ollama sent an unreadable response. Try again.")
            if chunk.get("error"):
                raise RuntimeError(f"Ollama error: {chunk['error']}")
            token = chunk.get("response", "")
            if token:
                on_token(token)
                parts.append(token)
            if chunk.get("done"):
                truncated = chunk.get("done_reason") == "length"
                break
        result = "".join(parts).strip()
    else:
        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"Ollama error: {data['error']}")
        result = data.get("response", "").strip()
        truncated = data.get("done_reason") == "length"

    # Small models sometimes wrap the words they changed in Markdown bold.
    if "**" not in text:
        result = result.replace("**", "")
    if "__" not in text:
        result = result.replace("__", "")

    if truncated:
        raise RuntimeError(
            "The model ran out of context and the result is incomplete. "
            "Select a shorter passage."
        )
    if not result:
        raise RuntimeError("The model returned an empty response. Try again.")

    logging.debug("Response received — %d chars", len(result))
    return result
