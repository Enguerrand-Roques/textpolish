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
- A local Ollama model available on the machine

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

Install and start Ollama, then pull the default model:

```bash
ollama serve
ollama pull gemma3:4b
```

Edit `config.py` if you want to change:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`
- `OLLAMA_KEEP_ALIVE`
- `SHORTCUT`

Default example:

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_TIMEOUT = 60
OLLAMA_KEEP_ALIVE = 0
SHORTCUT = "<cmd>+<shift>+p"
```

## macOS Permissions

TextPolish depends on macOS automation APIs. On first launch, make sure the terminal or Python app you use has:

- Accessibility permission
- Permission to control the keyboard / simulate copy-paste when prompted

Without these permissions, the global shortcut or paste-back step may fail.

## Run

```bash
python3 main.py
```

When TextPolish starts, use the configured shortcut to capture the selected text and open the panel.

## How It Works

1. Select text in any macOS app.
2. Press the configured shortcut.
3. TextPolish copies the current selection.
4. The text is sent to the local Ollama model with the selected prompt mode.
5. The rewritten text is pasted back into the original app.

## Available Modes

- `pro`: cleaner and more professional phrasing
- `casual`: lighter and more natural phrasing
- `custom`: custom prompt entered from the panel UI

## Project Structure

- `main.py`: Cocoa app bootstrap and event loop
- `ui.py`: native `NSPanel` interface and polish actions
- `hotkey.py`: global hotkey listener based on Quartz `CGEventTap`
- `clipboard.py`: selected text capture and paste-back helpers
- `llm.py`: local Ollama request layer
- `prompts/`: prompt templates for each rewrite mode
- `config.py`: local runtime configuration, excluded from Git
- `config.example.py`: example local configuration

## Troubleshooting

- `Cannot connect to Ollama`: start Ollama with `ollama serve`
- `Model not found`: install it with `ollama pull <model>`
- Timeout errors: use a smaller model or increase `OLLAMA_TIMEOUT`
- High idle RAM/CPU usage after a request: set `OLLAMA_KEEP_ALIVE = 0` to unload the model immediately
- Global shortcut not detected: re-check macOS Accessibility permissions
- Text is not pasted back: make sure the source app still has focus and clipboard permissions are allowed

## Notes

- `config.py` is intentionally excluded from Git.
- No remote API key is required for the current setup.
- The default local backend is Ollama over HTTP on `OLLAMA_BASE_URL`.
