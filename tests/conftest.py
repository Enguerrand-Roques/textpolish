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
# Distinct names per mode so tests can check which model each mode picks
# (the real config uses one model, enguerrandroquesbdl/textpolish-gemma4, for all three).
_config.OLLAMA_MODEL = "test-model-custom"
_config.OLLAMA_MODEL_PRO = "test-model-pro"
_config.OLLAMA_MODEL_CASUAL = "test-model-casual"
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


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _no_background_unload(monkeypatch):
    """Switching modes unloads the previous model in a background thread;
    keep that thread from starting (and from calling a real Ollama) in tests."""
    import llm
    monkeypatch.setattr(llm, "_unload_model", lambda model: None)
    monkeypatch.setattr(llm, "_active_model", None)
