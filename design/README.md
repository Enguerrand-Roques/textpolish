# design/ — development tools

Scripts used to evaluate models, time the real app and produce the visuals.
None of them is needed to run TextPolish. Run them from the repo root with the
project venv (`venv/bin/python3 design/<script>`).

| Tool | What it does | Needs |
|------|--------------|-------|
| `model_eval.py` | Rounds 6–7 benchmark: expected-answer test sets (French, `--en` for English; `--large` for the 130/123-sentence Correction sets in `benchmarks/eval/`) per mode, cold and warm latency. Prints its results; the saved output is `benchmarks/results/round6_*.md` | Ollama |
| `battery.py` | Runs realistic texts through every mode and prints the layout the popup would pick | Ollama |
| `fluidity.py` | Drives the real app in TextEdit like a user (HID keystrokes) and reads timings from `design/app.log`: 7 scenarios | Running app, Accessibility |
| `type_text.py`, `human_shortcut.py` | HID helpers used by `fluidity.py` and `record_video.py` | Accessibility |
| `record_video.py` | Films the raw clips (app, menu bar history, language switch) edited in `video/` | Running app, Screen Recording |
| `preview.html` + `make_fixtures.py` | Every popup state side by side in a browser, from real model outputs (`fixtures-en.json`, `fixtures-fr.json`) | Ollama for fixtures |
| `shoot.sh` | Screenshots `preview.html` in light and dark into `design/screenshots/` (regenerated, not committed) | Google Chrome |
| `render_windows.py` | Renders the Windows (PyQt6) panel offscreen for a visual check | PyQt6 |
