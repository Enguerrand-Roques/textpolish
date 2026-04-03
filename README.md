# TextPolish

TextPolish is a macOS desktop helper that captures the selected text, sends it to Anthropic for polishing, and pastes the improved version back into the active app.

## Features

- Global shortcut to trigger polishing
- Native macOS panel
- Multiple prompt modes via `prompts/`
- Clipboard-based copy/paste workflow

## Requirements

- macOS
- Python 3.13 recommended
- Accessibility permission for global shortcuts
- Automation permission for copy/paste scripting when needed
- An Anthropic API key

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

Then edit `config.py` and set:

- `ANTHROPIC_API_KEY`
- `SHORTCUT` if you want a different hotkey

## Run

```bash
python3 main.py
```

## Project Structure

- `main.py`: app entry point
- `ui.py`: native panel UI
- `clipboard.py`: selection and clipboard helpers
- `llm.py`: Anthropic API integration
- `prompts/`: prompt templates

## Notes

- `config.py` is intentionally excluded from Git.
- Do not commit real API keys.
