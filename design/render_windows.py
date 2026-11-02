"""Render the Windows (PyQt6) panel offscreen to a PNG for a visual check.
Run with any Python that has PyQt6:  python design/render_windows.py out.png
macOS fonts stand in for Segoe UI, so spacing is approximate."""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

cfg = types.ModuleType("config")
cfg.OLLAMA_BASE_URL = "http://localhost:11434"
cfg.OLLAMA_MODEL = cfg.OLLAMA_MODEL_CASUAL = "ministral-3:3b"
cfg.OLLAMA_MODEL_PRO = "gemma3:4b"
cfg.OLLAMA_TIMEOUT = 60
cfg.OLLAMA_KEEP_ALIVE = 300
sys.modules["config"] = cfg

from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)
from platforms.windows import ui  # noqa: E402

panel = ui.setup()
panel._selected_text = "RH et opérationel on veut plus operationel"
panel._text_view.setText(panel._selected_text)
panel._set_status("Rewriting text…")
panel._panel.show()
app.processEvents()
panel._panel.grab().save(sys.argv[1])
panel._on_error("Cannot connect to Ollama. Make sure it is running: `ollama serve`")
app.processEvents()
panel._panel.grab().save(sys.argv[1].replace(".png", "-error.png"))
print("saved")
