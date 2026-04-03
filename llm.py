"""
Anthropic API wrapper — sends text to Claude and returns the polished version.
"""

import os
import logging
import anthropic
from config import ANTHROPIC_API_KEY

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
    Send *text* to Claude and return the corrected version.

    Args:
        text:          The raw text to polish.
        mode:          "pro" | "casual" — selects the matching prompt file.
        custom_prompt: If provided, used as the system prompt instead of a file.

    Returns:
        The polished text string.
    """
    if not text.strip():
        return text

    if custom_prompt:
        system = custom_prompt
    else:
        system = _load_prompt(mode)

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY est vide — définis la variable d'environnement.")

    logging.debug("Appel API Claude | mode=%s | %d caractères", mode, len(text))
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
    except anthropic.AuthenticationError as e:
        logging.error("401 Authentification échouée : %s", e)
        raise
    except anthropic.APIError as e:
        logging.error("Erreur API Anthropic (%s) : %s", type(e).__name__, e)
        raise

    logging.debug("Réponse reçue — %d tokens", message.usage.output_tokens)
    return message.content[0].text.strip()
