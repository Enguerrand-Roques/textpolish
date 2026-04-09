# TextPolish

**TextPolish** is a macOS menubar utility that polishes your text using a local AI model. Select any text in any app, press a shortcut, choose a rewrite mode — the corrected text is pasted back instantly. No cloud, no data sent anywhere.

---

## How It Works

1. Select text in any macOS app
2. Press `Cmd+Shift+P`
3. Pick a mode — **Professional**, **Casual**, or **Custom**
4. The rewritten text is automatically pasted back

TextPolish runs silently in the menubar. No Dock icon, no Terminal window.

---

## Requirements

- macOS 13+
- Python 3.13
- [Ollama](https://ollama.com) installed and running locally
- macOS **Accessibility** permission (for the global shortcut and clipboard automation)

---

## Installation

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

Pull the two default Ollama models:

```bash
ollama pull gemma3:1b   # casual mode
ollama pull gemma3:4b   # professional mode
```

---

## Configuration

Edit `config.py` (excluded from Git):

```python
OLLAMA_BASE_URL     = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b"   # fast, typo fixes only
OLLAMA_MODEL_PRO    = "gemma3:4b"   # slower, full rewrite
OLLAMA_MODEL        = OLLAMA_MODEL_CASUAL  # fallback for custom mode
OLLAMA_TIMEOUT      = 60
OLLAMA_KEEP_ALIVE   = 300
SHORTCUT            = "<cmd>+<shift>+p"
```

---

## Launch as a Native macOS App

TextPolish ships with a native launcher so you never need to open a terminal.

### One-time setup

Register the Launch Agent (runs once per machine, survives reboots):

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.textpolish.plist
```

> The `com.user.textpolish.plist` file is included in the repo — copy it to `~/Library/LaunchAgents/` first.

### Daily use

Double-click **TextPolish.app** on your Desktop to start. A ✏️ icon appears in the menubar.  
Click the icon → **Quit TextPolish** to stop.

### Auto-start on login (optional)

Set `RunAtLoad` to `true` in the plist, then reload:

```bash
launchctl bootout gui/$(id -u) com.user.textpolish
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.textpolish.plist
```

---

## macOS Permissions

On first launch, macOS will ask for:

- **Accessibility** — required for the global shortcut (`CGEventTap`) and simulated copy/paste
- **Input Monitoring** — may be requested alongside Accessibility

Grant both in **System Settings → Privacy & Security**.

---

## Rewrite Modes

| Mode | Model | Description |
|------|-------|-------------|
| Professional | `gemma3:4b` | Full rewrite for emails, LinkedIn, formal writing |
| Casual | `gemma3:1b` | Light typo fix, preserves your tone (SMS, WhatsApp) |
| Custom | configurable | Free-form instruction entered in the panel |

---

## Project Structure

```
textpolish/
├── main.py          # Cocoa app bootstrap and event loop
├── ui.py            # NSPanel UI + menubar status item
├── hotkey.py        # Global shortcut via CGEventTap
├── clipboard.py     # Selected text capture and paste-back
├── llm.py           # Ollama request layer
├── prompts/         # Prompt templates (pro, casual, custom)
├── config.py        # Local config — excluded from Git
├── config.example.py
└── benchmarks/      # Model comparison tools
```

---

## Benchmarking Models

Compare latency and quality across Ollama models:

```bash
python benchmark_models.py --models gemma3:4b llama3.2:3b qwen2.5:3b
```

Add `--judge` to score outputs with Claude (requires `ANTHROPIC_API_KEY`):

```bash
python benchmark_models.py --models gemma3:4b --judge --judge-model claude-haiku-4-5
```

Results land in `benchmarks/results/` as JSON, CSV, and a readable Markdown comparison.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` |
| `Model not found` | Run `ollama pull <model>` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` |
| High idle RAM after a request | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not detected | Check Accessibility in System Settings |
| Text not pasted back | Keep the source app focused; check clipboard permissions |

---

## Related

- [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) — same tool, powered by Google Gemini (no local model required)
