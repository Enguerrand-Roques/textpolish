"""
Shared test fixtures and setup.

Injects a synthetic `config` module so llm.py can be imported in CI
without a real config.py file.
"""

import sys
import types

_config = types.ModuleType("config")
_config.OLLAMA_BASE_URL = "http://localhost:11434"
_config.OLLAMA_MODEL = "gemma3:1b"
_config.OLLAMA_MODEL_PRO = "gemma3:4b"
_config.OLLAMA_MODEL_CASUAL = "gemma3:1b"
_config.OLLAMA_TIMEOUT = 60
_config.OLLAMA_KEEP_ALIVE = 300

sys.modules.setdefault("config", _config)
