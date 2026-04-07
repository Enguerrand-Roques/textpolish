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

Install and start Ollama, then pull the two default models:

```bash
ollama serve
ollama pull gemma3:1b   # casual mode
ollama pull gemma3:4b   # pro mode
```

Edit `config.py` if you want to change models or other settings:

- `OLLAMA_MODEL_CASUAL` — model used for casual/SMS mode (default: `gemma3:1b`)
- `OLLAMA_MODEL_PRO` — model used for professional mode (default: `gemma3:4b`)
- `OLLAMA_MODEL` — fallback model for custom mode
- `OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`, `OLLAMA_KEEP_ALIVE`, `SHORTCUT`

Default example:

```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b"
OLLAMA_MODEL_PRO = "gemma3:4b"
OLLAMA_MODEL = OLLAMA_MODEL_CASUAL
OLLAMA_TIMEOUT = 60
OLLAMA_KEEP_ALIVE = 300
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

| Mode | Model | Description |
|------|-------|-------------|
| `pro` | `OLLAMA_MODEL_PRO` (`gemma3:4b`) | Fixes grammar and rewrites for professional contexts (email, LinkedIn) |
| `casual` | `OLLAMA_MODEL_CASUAL` (`gemma3:1b`) | Fixes typos only, keeps the original tone and structure (SMS, WhatsApp) |
| `custom` | `OLLAMA_MODEL` | Applies a free-form instruction entered from the panel UI |

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
- High idle RAM/CPU usage after a request: set `OLLAMA_KEEP_ALIVE = 0` in `config.py` to unload models immediately after each request
- Global shortcut not detected: re-check macOS Accessibility permissions
- Text is not pasted back: make sure the source app still has focus and clipboard permissions are allowed

## Benchmark Models

Compare latency and output quality across multiple local Ollama models:

```bash
python benchmark_models.py --models gemma3:4b llama3.2:3b qwen2.5:3b
```

Test cases are defined in `benchmarks/cases.json` (id, label, mode, input_text).
Results land in `benchmarks/results/` as three files per run:

| File | Contents |
|------|----------|
| `results_<timestamp>.json` | Full results — model, case, input, output, timing, judge scores |
| `summary_<timestamp>.csv` | Per-model stats: timing + avg quality scores when judging |
| `review_<timestamp>.md` | Human-readable side-by-side output comparison with scores |

A timing (and quality) summary is also printed to the terminal at the end of the run.

### LLM-as-judge (optional)

Add `--judge` to score each output with Claude on three dimensions (1–5): spelling/grammar correction, tone appropriateness, and meaning preservation.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python benchmark_models.py --models gemma3:4b llama3.2:3b --judge
```

By default the judge uses `claude-opus-4-6`. Use `--judge-model` to pick a cheaper model:

```bash
python benchmark_models.py --models gemma3:4b --judge --judge-model claude-haiku-4-5
```

Options:
```
--models MODEL [MODEL ...]   Ollama model names to benchmark (required)
--cases PATH                 Cases file (default: benchmarks/cases.json)
--output-dir PATH            Output directory (default: benchmarks/results)
--ollama-url URL             Ollama base URL (default: from config.py or http://localhost:11434)
--timeout SECONDS            Request timeout (default: from config.py or 120)
--judge                      Score outputs with Claude (requires ANTHROPIC_API_KEY)
--judge-model MODEL          Claude model used as judge (default: claude-opus-4-6)
```

## Notes

- `config.py` is intentionally excluded from Git.
- No remote API key is required for the current setup.
- The default local backend is Ollama over HTTP on `OLLAMA_BASE_URL`.
