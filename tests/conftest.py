"""
Shared test fixtures and setup.

Injects a synthetic `config` module so llm.py can be imported in CI
without a real config.py file.
"""

import os
import sys
import types

# Add project root to sys.path so `import llm` works in CI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_config = types.ModuleType("config")
_config.OLLAMA_BASE_URL = "http://localhost:11434"
_config.OLLAMA_MODEL = "gemma3:1b"
_config.OLLAMA_MODEL_PRO = "gemma3:4b"
_config.OLLAMA_MODEL_CASUAL = "gemma3:1b"
_config.OLLAMA_TIMEOUT = 60
_config.OLLAMA_KEEP_ALIVE = 300

sys.modules.setdefault("config", _config)
