# TextPolish configuration
# Copy this file to config.py and fill in your own values.

# Ollama local backend
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b"   # fast model for casual/SMS mode
OLLAMA_MODEL_PRO = "gemma3:4b"      # higher-quality model for professional mode
OLLAMA_MODEL = OLLAMA_MODEL_CASUAL  # fallback default (custom mode)
OLLAMA_TIMEOUT = 60  # seconds
OLLAMA_KEEP_ALIVE = 300  # keep model in RAM for 5 min between requests

# Global keyboard shortcut (pynput format)
SHORTCUT = "<cmd>+<shift>+p"
