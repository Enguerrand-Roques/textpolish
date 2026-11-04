# TextPolish

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://github.com/Enguerrand-Roques/textpolish/actions/workflows/tests.yml/badge.svg)

**TextPolish** polishes your text using a local AI model — no internet, no subscription, no data sent anywhere.

Select text in any app, press ⌥⌘G, review the fixes, and the text is pasted back. The demo below is the real app, filmed by `design/record_video.py` and edited with Remotion (`video/`). It runs quietly in the macOS menu bar.

<p align="center">
  <img src="docs/demo.gif" width="720" alt="Demo in TextEdit: a 351-character English message with 11 mistakes is corrected with each fix labeled (grammar, agreement, conjugation, spelling, punctuation, capitalization), then rewritten in Pro with ⌘2, then translated into French with a Custom request and pasted back">
</p>

<p align="center"><b><a href="https://enguerrand-roques.github.io/textpolish/textpolish-demo.mp4">▶ Watch the 1-minute video</a></b> — real recordings of the app in English, then the switch to French; only the typing is sped up, and the on-screen stopwatch shows the real model time (made with <a href="video/">Remotion</a>).</p>

The popup reads the selection, then adapts: one card per correction for short texts, a highlighted document for long ones, a single rewrite in Pro / Custom. Everything runs locally.

→ **[Read the UX case study](https://enguerrand-roques.github.io/textpolish/case-study.html)** (design process, iterations, real-use testing) · **[Project website](https://enguerrand-roques.github.io/textpolish/)** · every popup state: [light](docs/screenshots/all-states-light.png) / [dark](docs/screenshots/all-states-dark.png) · [what changed in 2.0](CHANGELOG.md)

> **About this project.** A personal project to learn how to build an AI product end to end, and how to evaluate one honestly. It is not distributed (installing needs Python, Ollama and a 4.3 GB model), so its users are me and the tests. What it shows:
> - **Product and UX:** a popup that adapts to the text, three modes, English and French, ten iterations ([case study](https://enguerrand-roques.github.io/textpolish/case-study.html)).
> - **A model chosen by measurement:** 17 local models benchmarked against expected answers ([report](benchmarks/BENCHMARK_REPORT.md)).
> - **Safety over coverage:** a wrong fix is worse than a missed one, so doubtful fixes wait for a click, and every failure is classified as grave, minor or missed with a rubric written first.
> - **Honest evaluation:** 802 test sentences, and three held-out sets each committed before the change it judges, so the scores can't be tuned to the test.
> - **AI and rules together:** the model, a review layer, then LanguageTool's grammar rules, each measured on its own.

> **Built for macOS.** The popup, the menu-bar icon, the screenshots and every real-app test are macOS (Apple Silicon, tested on an M2 with 16 GB); the unit tests also run on Linux CI. A Windows version exists with a simpler window; it has not been tested since the redesign.

> **Prefer a cloud version?** → [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) uses Google Gemini — no local model required, free API key.

---

## Features

| Feature | Description |
|---------|-------------|
| **Three modes** | Correction (fixes mistakes only, default), Pro (⌘2, professional rewrite), Custom (⌘3, your own request: translate, shorten, warmer…) |
| **English and French** | Corrects and rewrites both languages (tested on an English and a French set). The interface is in English or French: switch from ✏️ → Language, it is remembered |
| **Every fix explained** | Each correction is labeled: spelling, accent, capitalization, punctuation, agreement, conjugation, grammar (including homophones like their/there) or rewrite. Short texts get one card per fix, long ones a highlighted document |
| **Correction history** | Last 10 corrections in the ✏️ menu → History. Click an entry to copy the corrected text |
| **Configurable shortcut** (macOS only) | Change the keyboard shortcut live from the menu bar icon → Preferences… (Cmd+,) — no restart needed. On Windows, edit `SHORTCUT` in `config.py` and restart the app |
| **Native-feeling popup** (macOS) | Opens under the selection with macOS vibrancy, light and dark mode, full keyboard control (↵ ⇥ ⌘↵ ⌘1-3 esc) |
| **Fully private** | Everything runs on your machine. No API key, no telemetry, no data ever leaves your computer |
| **System-level** | Works in any app — VS Code, Notion, Mail, Slack. Panel stays above fullscreen apps |

---

## Installation

<details>
<summary><strong>macOS</strong></summary>

### Requirements
- macOS 13+
- Python 3.10+ (developed and tested on 3.13)
- [Ollama](https://ollama.com) 0.40+ installed and running
- Accessibility permission (granted on first launch)

### Setup

Download the [latest release](https://github.com/Enguerrand-Roques/textpolish/releases/latest) (just the app, 1.5 MB) and run `bash setup.sh` in its folder, or clone the repo:

```bash
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
bash setup.sh
```

`setup.sh` handles everything:
- Creates the Python virtual environment and installs dependencies
- Copies `config.example.py` → `config.py`
- Registers a Launch Agent (it starts when you open the app; auto-start on login is optional, see below)
- Creates **TextPolish.app** on your Desktop

Then pull the AI model (one-time, 4.3 GB):

```bash
ollama pull gemma4:e2b-it-qat   # one model for all three modes (Ollama 0.40+)
```

Optional, recommended: a second, rule-based check after the model (local, ~0.5 GB of RAM, ~15 ms per correction). TextPolish starts it by itself when it is installed:

```bash
brew install languagetool
```

### Start

Double-click **TextPolish.app** on your Desktop.
A pencil icon appears in the menu bar — the app is running.

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
launchctl bootout gui/$(id -u)/com.user.textpolish
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.textpolish.plist
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma4:e2b-it-qat` |
| Timeout errors | Use a smaller model or raise `OLLAMA_TIMEOUT` in `config.py` |
| High RAM after use | Lower `OLLAMA_KEEP_ALIVE` in `config.py` (0 frees the 4.3 GB right away, but every request then waits 3–6 s for the model to load) |
| Shortcut not working | Grant Accessibility in System Settings |
| Text not pasted back | Keep the source app focused |
| App won't start | Check `~/Library/Logs/TextPolish/textpolish.log` for errors |

</details>

---

<details>
<summary><strong>Windows (experimental, untested since the redesign)</strong></summary>

### Requirements
- Windows 10+
- Python 3.11+
- [Ollama](https://ollama.com) installed and running

### Setup

```bat
git clone https://github.com/Enguerrand-Roques/textpolish.git
cd textpolish
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
copy config.example.py config.py
```

Then pull the AI model (one-time, 4.3 GB):

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
| High RAM after use | Lower `OLLAMA_KEEP_ALIVE` in `config.py` (0 frees the 4.3 GB right away, but every request then waits 3–6 s for the model to load) |
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
OLLAMA_MODEL        = "gemma4:e2b-it-qat"   # Custom (your own request)
OLLAMA_TIMEOUT      = 60
OLLAMA_KEEP_ALIVE   = 300
UI_LANGUAGE         = "en"                # "en" or "fr", also from ✏️ → Language
SHORTCUT            = "<cmd>+<alt>+g"     # macOS: Cmd+Option+G, Windows: Ctrl+Alt+G
```

---

## Rewrite Modes

| Mode | Best for |
|------|----------|
| **Correction** (default) | Fixes mistakes, keeps your wording |
| **Pro** (⌘2) | Emails, LinkedIn, formal writing — full rewrite |
| **Custom** (⌘3) | Your own request: translate, shorter, warmer, funnier (“Sur mesure” in the French interface) |

**Speed, measured on an M2 16 GB:**

| | Warm (model in RAM) | Cold (model not loaded) |
|---|---:|---:|
| Short sentence, any mode | 0.5–1.1 s | 3–6 s |
| 338-character report (Correction) | 2.7 s | — |
| ~370-character message, 11–13 mistakes (demo video, EN and FR) | 3–4 s | — |
| ~1,500 characters (Correction) | ~10 s | — |

Time grows with the length of the answer (about 30–35 tokens per second, much less if the Mac is swapping). The 4,000-character input limit stays under the 60 s timeout.

Cold happens on the first request and again after 5 minutes without use (`OLLAMA_KEEP_ALIVE = 300` frees the 4.3 GB of RAM). Right after a reboot, when macOS has not cached the model file yet, the first request took 9–15 s. Raise `OLLAMA_KEEP_ALIVE` if you prefer speed over free RAM.

---

## Project Structure

```
textpolish/
├── main.py              # Entry point — detects OS, loads the right backend
├── clipboard.py         # Copy / paste logic          ─┐
├── llm.py               # Ollama request layer         │
├── languagetool.py      # Optional rule-based 2nd pass │
├── diff.py              # Groups and labels fixes      │
├── i18n.py              # English / French strings     ├─ shared across platforms
├── language.py          # French or English, no model  │
├── history.py           # Correction history           │
├── polish_job.py        # Correction threading         │
├── prompts/             # Prompt templates            ─┘
├── config.example.py
├── setup.sh             # macOS install: venv, config, app bundle
│
├── platforms/
│   ├── macos/           # PyObjC · NSPanel · WKWebView · CGEventTap
│   │   ├── ui.py        # Menu bar item, panel, JS bridge
│   │   ├── panel.html   # The popup: cards, document view, rewrite (HTML/CSS/JS)
│   │   ├── ax_bounds.py # Where the selection is on screen (Accessibility API)
│   │   ├── spelling.py  # macOS dictionary: real word or typo (review rules)
│   │   ├── hotkey.py
│   │   ├── shortcut_parser.py
│   │   └── main.py
│   └── windows/         # PyQt6 · QSystemTrayIcon · pynput (experimental)
│
├── tests/               # pytest, runs on Linux CI (macOS APIs are stubbed)
├── benchmarks/          # Model research: report, harness, every raw output
├── design/              # Dev tools: model eval, real-app timing, previews, recordings
├── video/               # Remotion project that edits the demo video
└── docs/                # GitHub Pages: landing page, UX case study, media
```

---

## How models were chosen

TextPolish uses one local model, `gemma4:e2b-it-qat`, for all three modes. That choice comes from six benchmark rounds and 17 models tested on an Apple M2 16 GB (full list in the [benchmark report](benchmarks/BENCHMARK_REPORT.md#summary--17-models-6-rounds-april--november-2026)).

**Current configuration (Round 6, November 2026):**

| Mode | Model | Warm (median) | Cold (median, range) | Score |
|------|-------|-------------:|------------:|:-----:|
| Correction | `gemma4:e2b-it-qat` | 0.9 s | 5.0 s (3.7–6.3) | On 174 new sentences (written before the last change): 79/86 French, 86/88 English corrected as expected by default with LanguageTool; 1 grave fix (since fixed) and 1 minor. Development sets (628 sentences): 596 right, 3 wrong |
| Pro | `gemma4:e2b-it-qat` | 1.1 s | 3.4 s (3.0–4.0) | 5 / 5 checks (FR and EN) |
| Custom | `gemma4:e2b-it-qat` | 1.1 s | 3.1 s (3.0–3.8) | 3 / 3 checks (FR and EN) |

Warm = median over the test set with the model in RAM. Cold = `ollama stop`, then one request, 3 runs per mode; the model file was still in macOS's file cache, so a first request after a reboot is slower (9–15 s observed).

Key findings that shaped this choice:

- **One model beats two.** With a Correction model and a Pro model, every mode switch reloaded a model (~5 s on 16 GB). With one model, switching modes adds no wait (0.75–0.8 s for a sentence in Pro).
- **Gemma 4 E2B matches the previous Correction model and is better at Pro and Custom.** `gemma3:4b` added "Dear [Recipient Name]" placeholders and once reversed the meaning of a sentence; `ministral-3:3b` answered a message instead of rewriting it.
- **Hybrid-reasoning models need `"think": false`.** Gemma 4, Qwen 3.5 and LFM3 think by default on Ollama; without it a 1 s correction takes tens of seconds. LFM3 still printed its reasoning into the answer and was dropped.
- **MLX is faster but heavier.** Ollama 0.40 runs `gemma4:e2b-nvfp4` on Apple's MLX engine: 0.34 s per correction, but ~7.4 GB in RAM, which pushed this 16 GB Mac into swap. It is the better choice on 24 GB or more.
- **A rule-based checker catches what the model misses.** LanguageTool runs locally after the model and fixes the grammar it knows by rule ("quand au" → "quant au", "have ate" → "have eaten"); only single-suggestion grammar rules are applied, and the French rules that "fix" informal register ("j'ai pas" → "je n'ai pas") are off. On unseen sentences it took English from 84 to 86 of 88 and French from 78 to 79 of 86, for ~15 ms per correction and ~540 MB of RAM.
- **Safe by default.** A missed mistake leaves your text as written; a wrong fix changes what you meant. Fixes that are not a known kind of mistake (a rewording, removed punctuation, an informal word, a real word swapped for one nobody confuses it with, checked with the macOS dictionary) are shown with an orange "Check" and only applied if you click them. Judged on two test sets written before the rules: wrong fixes applied fell from 6 to 1 in 182 sentences.
- **A larger test set lowers the score, as it should.** On 130 French and 123 English everyday messages (`benchmarks/eval/`), Correction gets 95 % and 93 %: accents, agreement and spelling are perfect, the misses are rarer constructions ("si j'aurais su", fewer/less) and 4 wrong fixes that change the meaning — the reason every fix stays a suggestion you accept or ignore.
- **A rule fixes the model's one French miss.** It kept deleting the "?" in "tu fais quoi ce soir ? on peut…". Correction now puts back any "?" or "!" the model removed without replacing it (`diff.keep_sentence_marks`): 12/12 on both sets, while the model alone stays at 11/12 in French.
- **Correction runs at temperature 0.** Gemma 4 defaults to 1, and the same test scored 9, 10 or 11/12 depending on the run. At 0 the same text always gets the same fix; Pro and Custom use 0.4.
- **Tested in both languages.** The interface went bilingual, so the evaluation was repeated on an English set (their/they're, its/it's, then/than, subject-verb agreement…): 12/12 in Correction. It also caught Pro writing "Dear [Recipient Name]" on a two-line message; the Pro prompt now forbids invented greetings and placeholders.
- **Free RAM matters as much as the model.** With the Mac swapping heavily (14 of 15 GB of swap in use), generation fell from ~35 to ~13 tokens per second and the same ~370-character message took 7–11 s instead of 3–4 s.
- **Language detection had a bug** that sent short unaccented French ("J'ai finit le rapport hier soir") to English; fixed in `llm.py`.
- Earlier rounds: `gemma3:1b-it-qat` missed "opérationel" every time, which is how Correction moved to `ministral-3:3b` in Round 5 before this round replaced it.

→ Full methodology, raw scores, and round-by-round analysis: [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md)

---

## Background

This project started as a way to understand how to integrate a language model into a real personal tool — not just a script that calls an API, but something actually usable every day.

Building it surfaced a few things that tutorials don't really cover:

- **Model size vs. latency** — in early rounds a 4B model rewrote better but took 5–8 s, and a 1B model was fast but missed real typos. Gemma 4 E2B (2B effective) ended that trade-off at about 1 s, after disabling its "thinking" and fixing the temperature.
- **Keeping a model in RAM** — loading the model takes 3–6 s (9–15 s after a reboot). `keep_alive` keeps it warm between requests but holds 4.3 GB of RAM; TextPolish frees it after 5 minutes idle. It's a trade-off you have to tune per machine.
- **Local vs. cloud latency** — once loaded, the local model answers a short sentence in about 0.5–1.1 s, close to Gemini Flash-Lite over the network (~0.5 s). Local wins on privacy and offline use, not on raw speed, and only when the model is already in RAM.
- **Integrating an LLM into an OS-level tool** — the LLM part ended up being the simplest piece. The hard parts were the global shortcut, clipboard handling, and making a window appear above fullscreen apps.

Beyond the technical side, this project was also an exercise in building something the way a real open source project is built — using Conventional Commits (`feat:`, `fix:`, `chore:`...), maintaining a proper `LICENSE`, writing a README that someone else can actually follow, and structuring code so it makes sense to a stranger reading it on GitHub. Small habits that make a big difference when a project grows or gets contributors.

The companion project [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) explores the same use case but with a cloud API (Google Gemini), which removes the local model complexity entirely in exchange for an internet dependency.

---

## Related

- [TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud) — same tool, powered by Google Gemini (no local model, free API)
