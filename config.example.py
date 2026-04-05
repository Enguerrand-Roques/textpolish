# TextPolish configuration
# Copy this file to config.py and fill in your own values.

# Ollama local backend
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_TIMEOUT = 60  # seconds
OLLAMA_KEEP_ALIVE = 0  # unload the model immediately after each request

# Global keyboard shortcut (pynput format)
SHORTCUT = "<cmd>+<shift>+p"
