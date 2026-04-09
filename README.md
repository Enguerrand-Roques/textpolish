# TextPolish

**TextPolish** polishes your text using a local AI model — no internet, no subscription, no data sent anywhere.

Select any text in any app, press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows), pick a rewrite mode, and the corrected text is pasted back instantly. TextPolish runs silently in the menubar / system tray.

> **Prefer a cloud version?** → [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) uses Google Gemini — no local model required, free API key.

---

## Requirements

| | macOS | Windows |
|---|---|---|
| OS | macOS 13+ | Windows 10+ |
| Python | 3.13 | 3.11+ |
| AI engine | [Ollama](https://ollama.com) | [Ollama](https://ollama.com) |
| Permission | Accessibility | — |

---

## Installation

### macOS

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
bash setup.sh
```

`setup.sh` does everything automatically:
- Creates the Python virtual environment and installs dependencies
- Copies `config.example.py` → `config.py`
- Registers the macOS Launch Agent
- Creates **TextPolish.app** on your Desktop

Then pull the AI models (one-time):

```bash
ollama pull gemma3:1b   # casual mode — fast
ollama pull gemma3:4b   # professional mode — higher quality
```

**Start the app:** double-click **TextPolish.app** on your Desktop. A ✏️ icon appears in the menubar.

---

### Windows

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
copy config.example.py config.py
```

Then pull the AI models (one-time):

```bash
ollama pull gemma3:1b
ollama pull gemma3:4b
```

**Start the app:**

```bash
python main.py
```

A ✏️ icon appears in the system tray.

---

## Configuration

Edit `config.py` (excluded from Git):

```python
# macOS / Windows
OLLAMA_BASE_URL     = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma3:1b"   # fast — typo fixes
OLLAMA_MODEL_PRO    = "gemma3:4b"   # slower — full rewrite
OLLAMA_MODEL        = OLLAMA_MODEL_CASUAL  # used for Custom mode
OLLAMA_TIMEOUT      = 60
OLLAMA_KEEP_ALIVE   = 300
SHORTCUT            = "<cmd>+<shift>+p"   # becomes Ctrl+Shift+P on Windows automatically
```

---

## How to use

1. Select text in **any app** (browser, Word, Slack, Notes…)
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows)
3. A small panel appears — pick a mode:

| Mode | Speed | Best for |
|------|-------|----------|
| **Professional** | ~5s | Emails, reports, LinkedIn, formal writing |
| **Casual** | ~2s | SMS, WhatsApp, DMs — light touch, keeps your tone |
| **Custom** | ~5s | Any free-form instruction you type |

4. The rewritten text is pasted back automatically

---

## macOS Permissions

On first launch, macOS will ask for:

- **Accessibility** — required for the global shortcut and simulated copy/paste
- **Input Monitoring** — may appear alongside Accessibility

Grant both in **System Settings → Privacy & Security**.

---

## Auto-start on login (macOS)

In `~/Library/LaunchAgents/com.user.textpolish.plist`, set `RunAtLoad` to `<true/>`, then reload:

```bash
launchctl bootout gui/$(id -u) com.user.textpolish
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.textpolish.plist
```

---

## Project Structure

```
textpolish/
├── main.py              # Entry point — detects OS and starts the right backend
├── clipboard.py         # Copy / paste logic — shared across platforms
├── llm.py               # Ollama request layer — shared across platforms
├── prompts/             # Prompt templates (pro, casual, custom)
├── config.py            # Your local config — excluded from Git
├── config.example.py    # Config template to copy
│
├── platforms/
│   ├── macos/           # macOS-specific code (PyObjC, NSPanel, CGEventTap)
│   │   ├── ui.py        #   Native floating panel + menubar icon
│   │   ├── main.py      #   Cocoa event loop
│   │   └── hotkey.py    #   Global shortcut via CGEventTap
│   └── windows/         # Windows-specific code (PyQt6, QSystemTrayIcon)
│       ├── ui.py        #   Qt floating window + system tray icon
│       ├── main.py      #   Qt event loop
│       └── hotkey.py    #   Global shortcut via pynput
│
├── requirements.txt         # macOS dependencies
└── requirements-windows.txt # Windows dependencies
```

`main.py` is the only entry point. It reads `sys.platform` and loads the right implementation from `platforms/`. Everything in the root is shared between both platforms.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma3:4b` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not working (macOS) | Grant Accessibility in System Settings |
| Text not pasted back | Keep the source app focused; check clipboard permissions |
| App won't start (macOS) | Check `/tmp/textpolish.log` for errors |

---

## Related

- [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) — same tool, powered by Google Gemini (no local model needed, free API)
