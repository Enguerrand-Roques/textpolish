"""
Ollama local backend — sends text to a local model and returns the polished version.
"""

import os
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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_prompt(name: str) -> str:
    path = os.path.join(_PROMPTS_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def polish_text(text: str, mode: str = "pro", custom_prompt: str | None = None) -> str:
    """
    Send *text* to a local Ollama model and return the corrected version.

    Args:
        text:          The raw text to polish.
        mode:          "pro" | "casual" — selects the matching prompt file.
        custom_prompt: If provided, applied through the custom prompt template.

    Returns:
        The polished text string.
    """
    if not text.strip():
        return text

    prompt_name = "custom" if custom_prompt else mode
    system = _load_prompt(prompt_name)

    if mode == "pro":
        model = OLLAMA_MODEL_PRO
    elif mode == "casual":
        model = OLLAMA_MODEL_CASUAL
    else:
        model = OLLAMA_MODEL

    if custom_prompt:
        prompt_text = (
            f"{system}\n\n"
            "Custom instruction to apply:\n"
            f"{custom_prompt.strip()}\n\n"
            "Text to rewrite:\n"
            f"{text}"
        )
    else:
        prompt_text = f"{system}\n\nText to rewrite:\n{text}"

    payload = {
        "model": model,
        "prompt": prompt_text,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "stream": False,
        "options": {"num_ctx": 1024},
    }

    logging.debug("Calling Ollama | model=%s | mode=%s | %d chars", model, mode, len(text))

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
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

    data = response.json()
    result = data.get("response", "").strip()
    logging.debug("Response received — %d chars", len(result))
    return result
