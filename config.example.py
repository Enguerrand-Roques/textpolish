# TextPolish configuration
# Copy this file to config.py and fill in your own values.

# Ollama local backend
OLLAMA_BASE_URL = "http://localhost:11434"
# One model for every mode: no reload when switching Correction / Pro / Custom
# (it cost ~5 s with two models on a 16 GB Mac). Round 6 benchmark:
# design/model_eval.py. Faster option on Macs with 24 GB+:
# "gemma4:e2b-nvfp4" runs on Ollama's MLX engine (2-3x faster, ~7.4 GB in RAM).
OLLAMA_MODEL_CASUAL = "gemma4:e2b-it-qat"
OLLAMA_MODEL_PRO = "gemma4:e2b-it-qat"
OLLAMA_MODEL = "gemma4:e2b-it-qat"   # Custom (custom instructions)
OLLAMA_TIMEOUT = 60  # seconds
OLLAMA_KEEP_ALIVE = 300  # keep the model in RAM for 5 min between requests

# Interface language: "en" (default) or "fr". Corrections always follow the
# language of the text itself.
UI_LANGUAGE = "en"

# Global keyboard shortcut (pynput format)
# macOS: Cmd+Option+G  |  Windows: Ctrl+Alt+G  (no known conflicts)
SHORTCUT = "<cmd>+<alt>+g"

# Optional — used by benchmark_models.py --judge (Claude Haiku as quality judge)
# ANTHROPIC_API_KEY = "sk-ant-..."
