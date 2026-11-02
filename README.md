# TextPolish

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://github.com/Enguerrand-Roques/textpolish/actions/workflows/tests.yml/badge.svg)

**TextPolish** polishes your text using a local AI model — no internet, no subscription, no data sent anywhere.

Select text in any app, press ⌥⌘G, review the fixes, and the text is pasted back. The demo above is the real app, recorded by `design/record_demo.py`. Runs silently in the menubar / system tray.

<p align="center">
  <img src="docs/demo.gif" width="560" alt="Demo in TextEdit: a message with two mistakes is corrected card by card, then rewritten in Pro with ⌘2, then translated with a Sur mesure request and pasted back">
</p>

<p align="center"><b><a href="docs/textpolish-demo.mp4">▶ Watch the 40-second video</a></b> — real recordings of the app, not sped up (made with <a href="video/">Remotion</a>).</p>

The popup reads the selection, then adapts: one card per correction for short texts, a highlighted document for long ones, a single rewrite in Pro / Sur mesure. Everything runs locally.

→ UX case study (design process, iterations, real-use testing): [`docs/case-study.html`](docs/case-study.html) · all popup states: [light](docs/screenshots/all-states-light.png) / [dark](docs/screenshots/all-states-dark.png)

> **Prefer a cloud version?** → [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) uses Google Gemini — no local model required, free API key.

---

## Features

| Feature | Description |
|---------|-------------|
| **Three rewrite modes** | Professional (full rewrite), Casual (light touch, keeps tone), Custom (any instruction) |
| **Streaming output** | Corrected text appears word by word in the panel as the model generates — no waiting for the full response |
| **Correction history** | Last 10 corrections available in the ✏️ menu → History. Click any entry to copy the corrected text |
| **Configurable shortcut** (macOS only) | Change the keyboard shortcut live from ✏️ → Preferences… (Cmd+,) — no restart needed. On Windows, edit `SHORTCUT` in `config.py` and restart the app |
| **Panel UI** (macOS) | Native WKWebView panel with Pip, a small pixel-art mascot that reacts to the selected mode |
| **Fully private** | Everything runs on your machine. No API key, no telemetry, no data ever leaves your computer |
| **System-level** | Works in any app — VS Code, Notion, Mail, Slack. Panel stays above fullscreen apps |

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
ollama pull gemma4:e2b-it-qat   # one model for all three modes (Ollama 0.40+)
```

### Start

Double-click **TextPolish.app** on your Desktop.
A ✏️ icon appears in the menubar — the app is running.

### Shortcut

`Cmd + Option + G`

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
| `Model not found` | Run `ollama pull gemma4:e2b-it-qat` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not working | Grant Accessibility in System Settings |
| Text not pasted back | Keep the source app focused |
| App won't start | Check `~/Library/Logs/TextPolish/textpolish.log` for errors |

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
ollama pull gemma4:e2b-it-qat
```

### Start

```bash
python main.py
```

A ✏️ icon appears in the system tray — the app is running.

### Shortcut

`Ctrl + Alt + G`

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma4:e2b-it-qat` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Set `OLLAMA_KEEP_ALIVE = 0` in `config.py` |
| Shortcut not working | Make sure no other app uses Ctrl+Alt+G |
| Text not pasted back | Keep the source app focused |

</details>

---

## Configuration

Edit `config.py` (excluded from Git — never committed):

```python
OLLAMA_BASE_URL     = "http://localhost:11434"
OLLAMA_MODEL_CASUAL = "gemma4:e2b-it-qat"   # Correction
OLLAMA_MODEL_PRO    = "gemma4:e2b-it-qat"   # Pro
OLLAMA_MODEL        = "gemma4:e2b-it-qat"   # Sur mesure (custom instructions)
OLLAMA_TIMEOUT      = 60
OLLAMA_KEEP_ALIVE   = 300
SHORTCUT            = "<cmd>+<alt>+g"     # macOS: Cmd+Option+G, Windows: Ctrl+Alt+G
```

---

## Rewrite Modes

| Mode | Best for |
|------|----------|
| **Correction** (default) | Fixes mistakes, keeps your wording |
| **Pro** (⌘2) | Emails, LinkedIn, formal writing — full rewrite |
| **Sur mesure** (⌘3) | Your own request: translate, shorter, warmer, funnier |

**Speed, measured on an M2 16 GB:**

| | Warm (model in RAM) | Cold (model not loaded) |
|---|---:|---:|
| Short sentence, any mode | 0.5–1.1 s | 3–6 s |
| 338-character report (Correction) | 2.7 s | — |

Cold happens on the first request and again after 5 minutes without use (`OLLAMA_KEEP_ALIVE = 300` frees the 4.3 GB of RAM). Right after a reboot, when macOS has not cached the model file yet, the first request took 9–15 s. Raise `OLLAMA_KEEP_ALIVE` if you prefer speed over free RAM.

---

## Project Structure

```
textpolish/
├── main.py              # Entry point — detects OS, loads the right backend
├── clipboard.py         # Copy / paste logic     ─┐
├── llm.py               # Ollama request layer     │
├── history.py           # Correction history        ├─ shared across platforms
├── polish_job.py        # Correction threading      │
├── prompts/             # Prompt templates         ─┘
├── config.example.py
│
└── platforms/
    ├── macos/                 # PyObjC · NSPanel · WKWebView · CGEventTap
    │   ├── ui.py
    │   ├── panel.html         # WKWebView UI (Pip mascot, HTML/CSS/JS)
    │   ├── main.py
    │   ├── hotkey.py
    │   └── shortcut_parser.py # Pure shortcut parsing, no PyObjC dependency
    └── windows/         # PyQt6 · QSystemTrayIcon · pynput
        ├── ui.py
        ├── main.py
        └── hotkey.py
```

---

## How models were chosen

TextPolish uses one local model, `gemma4:e2b-it-qat`, for all three modes. That choice comes from six benchmark rounds and 17 models tested on an Apple M2 16 GB (full list in the [benchmark report](benchmarks/BENCHMARK_REPORT.md#summary--17-models-6-rounds-april--november-2026)).

**Current configuration (Round 6, November 2026):**

| Mode | Model | Warm (median) | Cold (median, range) | Score |
|------|-------|-------------:|------------:|:-----:|
| Correction | `gemma4:e2b-it-qat` | 0.9 s | 5.0 s (3.7–6.3) | 11 / 12 expected fixes, no rewrite of correct texts |
| Pro | `gemma4:e2b-it-qat` | 1.1 s | 3.4 s (3.0–4.0) | 5 / 5 checks |
| Sur mesure | `gemma4:e2b-it-qat` | 1.1 s | 3.1 s (3.0–3.8) | 3 / 3 checks |

Warm = median over the test set with the model in RAM. Cold = `ollama stop`, then one request, 3 runs per mode; the model file was still in macOS's file cache, so a first request after a reboot is slower (9–15 s observed).

Key findings that shaped this choice:

- **One model beats two.** With a Correction model and a Pro model, every mode switch reloaded a model (~5 s on 16 GB). One model makes switching instant.
- **Gemma 4 E2B matches the previous Correction model and is better at Pro and Sur mesure.** `gemma3:4b` added "Dear [Recipient Name]" placeholders and once reversed the meaning of a sentence; `ministral-3:3b` answered a message instead of rewriting it.
- **Hybrid-reasoning models need `"think": false`.** Gemma 4, Qwen 3.5 and LFM3 think by default on Ollama; without it a 1 s correction takes tens of seconds. LFM3 still printed its reasoning into the answer and was dropped.
- **MLX is faster but heavier.** Ollama 0.40 runs `gemma4:e2b-nvfp4` on Apple's MLX engine: 0.34 s per correction, but ~7.4 GB in RAM, which pushed this 16 GB Mac into swap. It is the better choice on 24 GB or more.
- **Correction runs at temperature 0.** Gemma 4 defaults to 1, and the same test scored 9, 10 or 11/12 depending on the run. At 0 the same text always gets the same fix; Pro and Sur mesure use 0.4.
- **Language detection had a bug** that sent short unaccented French ("J'ai finit le rapport hier soir") to English; fixed in `llm.py`.
- Earlier rounds: QAT builds and `num_ctx: 1024` cut latency and RAM; `gemma3:1b` missed "opérationel" every time, which is how Correction moved to `ministral-3:3b` in Round 5 before this round replaced it.

→ Full methodology, raw scores, and round-by-round analysis: [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md)

---

## Background

This project started as a way to understand how to integrate a language model into a real personal tool — not just a script that calls an API, but something actually usable every day.

Building it surfaced a few things that tutorials don't really cover:

- **Model size vs. latency** — a 4B model rewrites better but takes 5–8s; a 1B model is nearly instant but misses nuance. The right choice depends on the use case, not just benchmarks.
- **Keeping a model in RAM** — loading a model from disk on every request adds 2–3s of overhead. `keep_alive` keeps it warm between requests, but costs RAM permanently. It's a trade-off you have to tune per machine.
- **Local vs. cloud latency** — a local model on an M-series chip is often faster than a cloud API for short texts, once the model is loaded. Network round-trips add up.
- **Integrating an LLM into an OS-level tool** — the LLM part ended up being the simplest piece. The hard parts were the global shortcut, clipboard handling, and making a window appear above fullscreen apps.

Beyond the technical side, this project was also an exercise in building something the way a real open source project is built — using Conventional Commits (`feat:`, `fix:`, `chore:`...), maintaining a proper `LICENSE`, writing a README that someone else can actually follow, and structuring code so it makes sense to a stranger reading it on GitHub. Small habits that make a big difference when a project grows or gets contributors.

The companion project [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) explores the same use case but with a cloud API (Google Gemini), which removes the local model complexity entirely in exchange for an internet dependency.

---

## Related

- [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) — same tool, powered by Google Gemini (no local model, free API)
