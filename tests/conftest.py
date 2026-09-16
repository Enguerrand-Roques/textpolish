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

# Injects a synthetic `pynput` module so clipboard.py (and anything that
# imports it) can be imported in CI without a real X11/pynput backend —
# clipboard.py instantiates pynput.keyboard.Controller() at import time,
# which would otherwise try to connect to a display on Linux runners.
_pynput_keyboard = types.ModuleType("pynput.keyboard")


class _FakeKey:
    cmd = "cmd"
    ctrl = "ctrl"


class _FakeController:
    def press(self, key):
        pass

    def release(self, key):
        pass

    def pressed(self, *keys):
        import contextlib

        @contextlib.contextmanager
        def _cm():
            yield

        return _cm()


_pynput_keyboard.Controller = _FakeController
_pynput_keyboard.Key = _FakeKey

_pynput = types.ModuleType("pynput")
_pynput.keyboard = _pynput_keyboard

sys.modules.setdefault("pynput", _pynput)
sys.modules.setdefault("pynput.keyboard", _pynput_keyboard)
