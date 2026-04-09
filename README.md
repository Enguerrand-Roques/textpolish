# TextPolish

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

**TextPolish** polishes your text using a local AI model — no internet, no subscription, no data sent anywhere.

Select text in any app, press a shortcut, pick a rewrite mode, and the corrected text is pasted back instantly. Runs silently in the menubar / system tray.

> **Prefer a cloud version?** → [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) uses Google Gemini — no local model required, free API key.

---

## Installation

<details>
<summary><strong>macOS</strong></summary>

### Requirements
- macOS 13+
- Python 3.13
- [Ollama](https://ollama.com) installed and running
- Accessibility permission (granted on first launch)

### Setup

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
bash setup.sh
```

`setup.sh` handles everything:
- Creates the Python virtual environment and installs dependencies
- Copies `config.example.py` → `config.py`
- Registers the Launch Agent (survives reboots)
- Creates **TextPolish.app** on your Desktop

Then pull the AI models (one-time, ~2 GB total):

```bash
ollama pull gemma3:1b   # casual mode — fast
ollama pull gemma3:4b   # professional mode — higher quality
```

### Start

Double-click **TextPolish.app** on your Desktop.
A ✏️ icon appears in the menubar — the app is running.

### Shortcut

`Cmd + Shift + P`

### Permissions

On first launch, macOS will ask for:
- **Accessibility** — required for the global shortcut and simulated copy/paste
- **Input Monitoring** — may appear alongside Accessibility

Grant both in **System Settings → Privacy & Security**.

### Auto-start on login (optional)

In `~/Library/LaunchAgents/com.user.textpolish.plist`, set `RunAtLoad` to `<true/>`, then reload:

```bash
launchctl bootout gui/$(id -u) com.user.textpolish
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.textpolish.plist
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma3:4b` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not working | Grant Accessibility in System Settings |
| Text not pasted back | Keep the source app focused |
| App won't start | Check `/tmp/textpolish.log` for errors |

</details>

---

<details>
<summary><strong>Windows</strong></summary>

### Requirements
- Windows 10+
- Python 3.11+
- [Ollama](https://ollama.com) installed and running

### Setup

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
copy config.example.py config.py
```

Then pull the AI models (one-time, ~2 GB total):

```bash
ollama pull gemma3:1b
ollama pull gemma3:4b
```

### Start

```bash
python main.py
```

A ✏️ icon appears in the system tray — the app is running.

### Shortcut

`Ctrl + Shift + P`

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma3:4b` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not working | Make sure no other app uses Ctrl+Shift+P |
| Text not pasted back | Keep the source app focused |

</details>

---

## Configuration

Edit `config.py` (excluded from Git — never committed):

```python
OLLAMA_BASE_URL     = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b"   # fast — typo fixes only
OLLAMA_MODEL_PRO    = "gemma3:4b"   # slower — full rewrite
OLLAMA_MODEL        = OLLAMA_MODEL_CASUAL  # used for Custom mode
OLLAMA_TIMEOUT      = 60
OLLAMA_KEEP_ALIVE   = 300
SHORTCUT            = "<cmd>+<shift>+p"   # auto-mapped to Ctrl on Windows
```

---

## Rewrite Modes

| Mode | Speed | Best for |
|------|-------|----------|
| **Professional** | ~5s | Emails, reports, LinkedIn, formal writing |
| **Casual** | ~2s | SMS, WhatsApp, DMs — light touch, keeps your tone |
| **Custom** | ~5s | Any instruction you type freely |

---

## Project Structure

```
textpolish/
├── main.py              # Entry point — detects OS, loads the right backend
├── clipboard.py         # Copy / paste logic  ─┐
├── llm.py               # Ollama request layer  ├─ shared across platforms
├── prompts/             # Prompt templates      ─┘
├── config.example.py
│
└── platforms/
    ├── macos/           # PyObjC · NSPanel · CGEventTap
    │   ├── ui.py
    │   ├── main.py
    │   └── hotkey.py
    └── windows/         # PyQt6 · QSystemTrayIcon · pynput
        ├── ui.py
        ├── main.py
        └── hotkey.py
```

---

## Related

- [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) — same tool, powered by Google Gemini (no local model, free API)
