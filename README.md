# TextPolish

TextPolish is a macOS desktop helper that grabs the currently selected text, sends it to a local Ollama model for rewriting, and pastes the polished version back into the active app.

## Features

- Global macOS shortcut to trigger polishing
- Native `NSPanel` UI that stays visible above fullscreen apps
- Local LLM backend via Ollama
- Prompt modes in `prompts/` (`pro` and `casual`)
- Clipboard-based capture and paste workflow

## Requirements

- macOS
- Python 3.13 recommended
- Ollama installed locally
- Accessibility permission for the global hotkey and copy/paste automation

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

Then install and start your local model:

```bash
ollama serve
ollama pull gemma3:4b
```

Edit `config.py` if you want to change:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`
- `SHORTCUT`

## Run

```bash
python3 main.py
```

When TextPolish starts, use the configured shortcut to capture the selected text and open the panel.

## Project Structure

- `main.py`: Cocoa app bootstrap and event loop
- `ui.py`: native `NSPanel` interface and polish actions
- `hotkey.py`: global hotkey listener based on Quartz `CGEventTap`
- `clipboard.py`: selected text capture and paste-back helpers
- `llm.py`: local Ollama request layer
- `prompts/`: prompt templates for each rewrite mode
- `config.py`: local runtime configuration, excluded from Git
- `config.example.py`: example local configuration

## Notes

- `config.py` is intentionally excluded from Git.
- No remote API key is required for the current setup.
- If Ollama is not running, the app will fail until `ollama serve` is available on `OLLAMA_BASE_URL`.
