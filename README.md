# TextPolish

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://github.com/Enguerrand-Roques/textpolish/actions/workflows/tests.yml/badge.svg)

**Fix the text you select, in any Mac app, with an AI that runs on your Mac.** Select, press **⌥⌘G**, accept the fixes, and the text is pasted back. Nothing leaves your Mac.

> **What this project is, honestly.** A personal project I built to learn how an AI product is made end to end: the app and its interface, choosing a model, training it, and measuring whether it really works. It works and I use it myself, but it has not been used by other people yet, and its test sentences were written for the tests rather than collected from real messages. The numbers below come from those tests; how they were measured, and what they don't cover, is in the [benchmark report](benchmarks/BENCHMARK_REPORT.md).

<p align="center">
  <img src="docs/demo.gif" width="720" alt="Demo in TextEdit: an English message with 11 mistakes is corrected with each fix labeled, rewritten in Pro with ⌘2, then translated into French with a Custom request and pasted back">
</p>

<p align="center"><b><a href="https://enguerrand-roques.github.io/textpolish/textpolish-demo.mp4">▶ Watch the 1-minute video</a></b></p>

| **97 %** | **~1 s** | **0** | **0 bytes** |
|:---:|:---:|:---:|:---:|
| of new sentences corrected right | per sentence | doubtful fixes applied without your click | of your text sent anywhere |

## Install

macOS 13+, Apple Silicon recommended. Paste in Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Enguerrand-Roques/textpolish/main/install.sh | bash
```

It installs what is missing and opens TextPolish. A setup window then downloads the model (3.3 GB, once) and asks for the Accessibility permission. No administrator password; [read the script](install.sh) first if you like.

## What it does

- **Correction** (default): fixes spelling, accents, grammar and agreement, and labels each fix. A fix it isn't sure about is shown in orange and waits for your click.
- **Pro** (⌘2): rewrites the message for work. **Custom** (⌘3): your own request, like "translate into French" or "make it shorter".
- English and French, in the text and in the interface. Open at Login, history and shortcut from the ✏️ menu.

## How the model was made

17 local models were benchmarked on the same sentences; the best one, Gemma 4 E2B, was then **fine-tuned on a MacBook Air** to do exactly this job. Wrong fixes fell from 5 to 2 on 749 test sentences, at the same speed and 1 GB lighter.

→ **[The model: benchmark, fine-tuning, before and after](https://enguerrand-roques.github.io/textpolish/model.html)**

## What this project taught me

**Technically**
- **The model is the easy part of an AI product.** Calling it took a day; the global shortcut, the clipboard, the Accessibility permission, a window above fullscreen apps and shortcuts on a French keyboard took weeks.
- **Running AI locally is a memory problem.** On a 16 GB Mac, RAM decides more than speed: quantization, keeping the model loaded or not, and turning off "thinking" mattered more than the model's size.
- **Measuring an AI is a skill of its own.** Scores against expected answers, not impressions; a test set frozen before each change; failures sorted by how much they hurt. A perfect 12/12 on twelve sentences became 95 % on 253.
- **When to prompt and when to train.** A longer prompt made things worse; fine-tuning the model on 5,000 examples, on a laptop, made it better, once I had a control model and a rule written before the training.
- **AI and rules each fail differently**, and both need testing: the grammar checker added after the model fixes real mistakes and invents a few of its own.

**Beyond the code**
- **Product:** removing a decision from the user helped more than adding a feature, and trust came from what the app *doesn't* do on its own.
- **Deciding:** writing each choice with its cost made trade-offs explicit, and changing one thing at a time made results explainable.
- **Honesty with numbers:** knowing exactly what a figure measures, and keeping the failures in the report.
- **Shipping:** an install in one command, versions, a changelog and documentation turned a script on my Mac into something another person can use.
- **Writing for a reader in a hurry:** this README went from 3,100 words to a page.

## Learn more

- **[UX case study](https://enguerrand-roques.github.io/textpolish/case-study.html)**: eleven iterations of the window, ten decisions and what each cost.
- **[Benchmark report](benchmarks/BENCHMARK_REPORT.md)**: twelve rounds, every raw result. **[Fine-tuning](finetune/README.md)**: data, scripts, the rule written before training.
- **[Developer guide](DEVELOPMENT.md)**: troubleshooting, install by hand, settings, speed, code layout.
- **[Changelog](CHANGELOG.md)** · **[TextPolish Cloud](https://github.com/Enguerrand-Roques/textpolish-cloud)**, the same tool with Google Gemini.

*MIT license.*
