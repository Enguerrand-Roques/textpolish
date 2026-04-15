# TextPolish configuration
# Copy this file to config.py and fill in your own values.

# Ollama local backend
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b-it-qat"   # fast model — QAT variant: 9% faster + better quality than gemma3:1b
OLLAMA_MODEL_PRO = "gemma3:4b"      # higher-quality model for professional mode
OLLAMA_MODEL = OLLAMA_MODEL_CASUAL  # fallback default (custom mode)
OLLAMA_TIMEOUT = 60  # seconds
OLLAMA_KEEP_ALIVE = 300  # keep model in RAM for 5 min between requests

# Global keyboard shortcut (pynput format)
# macOS: Cmd+Option+G  |  Windows: Ctrl+Alt+G  (no known conflicts)
SHORTCUT = "<cmd>+<alt>+g"

# Optional — used by benchmark_models.py --judge (Claude Haiku as quality judge)
# ANTHROPIC_API_KEY = "sk-ant-..."
