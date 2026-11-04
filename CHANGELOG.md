# Changelog

All notable changes to TextPolish. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Larger Pro and Custom test sets (50 messages, 30 requests) with checks
  that the facts of a message survive a rewrite, and no greeting, sign-off or
  placeholder is invented (Round 11 in the benchmark report).

### Changed
- The benchmark report opens with the results at a glance, the method and
  the eleven rounds in one table; each round's details are folded.

## [2.2.0] — 2026-11-04

Install in one command, set up in three clicks.

### Added
- **One-command install** (`install.sh`): a recent Python through uv if
  needed (no Homebrew, no sudo), Ollama, the latest release, LanguageTool
  when Homebrew is there, then it opens the app.
- **Setup window** on first launch (and whenever something is missing):
  Ollama started automatically; the model downloaded with a progress bar,
  speed and time left, resumable; the Accessibility permission with a
  button that opens the right pane, detected as soon as it is on, and the
  shortcut installed without a restart. English and French.

## [2.1.0] — 2026-11-04

Fixes you can trust: doubtful fixes wait for a click, and a grammar checker
catches what the model misses.

### Added
- **Safe by default.** A fix that is not a recognised kind of mistake is
  shown but not applied until you click it (orange dashed underline, "Check"
  on its card): a rewording, removed punctuation, an informal word
  ("aprem", "btw", "u") or one real word swapped for another that is not a
  known confusion (checked with the macOS dictionary). "Accept all" leaves
  them out.
- **LanguageTool as a second pass** (optional, `brew install languagetool`):
  after the model, a local LanguageTool server fixes the grammar it knows by
  rule ("quand au" → "quant au", "have ate" → "have eaten"). Only grammar and
  confused-word rules with a single suggestion are applied; register rules
  ("j'ai pas" → "je n'ai pas") are off. About 15 ms per check, ~540 MB of RAM.
- Larger Correction test sets: 130 French and 123 English messages in
  `benchmarks/eval/`, plus three held-out sets, each written before the change
  it judges (Rounds 7–10 in the benchmark report), and a severity rubric:
  every failure is classified as grave, minor or missed.

### Fixed
- Eight common English words ("or", "to", "in", "on"…) had dropped out of the
  language detector; short English texts could be treated as French.

## [2.0.0] — 2026-11-04

A redesign of the whole experience, a new model chosen by benchmark, and an
English interface.

### Added
- **New popup.** Native macOS window that adapts to the text: one card per fix
  on short texts (accept with ↵, ignore with ⇥), the whole document with
  highlighted fixes on long ones, a single suggestion for rewrites.
- **Every fix says what it is:** spelling, accent, capitalization,
  punctuation, agreement, conjugation, grammar (including their/there,
  a/à) or rewrite. Long texts get a legend that counts them.
- **Three modes:** Correction (⌘1) fixes mistakes without changing how you
  write; Pro (⌘2) rewrites for work; Custom (⌘3) applies your own request
  ("translate into French", "shorter"…).
- **English and French interface**, English by default, switchable from the
  menu bar (Language) and remembered.
- **History** of the last corrections in the menu bar; click one to copy it.
- Correction never removes a "?" or "!" you wrote (the model alone sometimes
  merged two questions).

### Changed
- **One model for all modes: `gemma4:e2b-it-qat`** (4.3 GB), chosen after
  benchmarking 17 models. Correction scores 12/12 on the French and English
  test sets (the model alone: 11/12 in French), Pro 5/5, Custom 3/3.
  Switching modes no longer reloads a model. Requires Ollama 0.40 or later.
- The default shortcut is ⌥⌘G on macOS, Ctrl+Alt+G on Windows (no known
  conflict with common apps); change it in Preferences.
- Correction runs at temperature 0 (same answer every time); Pro and Custom
  at 0.4.
- The model stays loaded 5 minutes after the last request: 0.5–1.1 s per
  sentence while loaded, 3–6 s for the first request after a pause.

### Fixed
- Copy failed when the shortcut's ⌥ was still held (it sent ⌥⌘C).
- English text containing "on" or "as" was answered in French; short French
  without accents ("on a vu un film") was answered in English.
- The popup no longer opens on the wrong screen with two displays, no longer
  shows the previous result for a moment, and a fast double ↵ no longer
  skips a card.
- Several instances could run at once; the user's clipboard is restored after
  pasting; truncated or empty model answers are rejected.

### Removed
- `gemma3:1b` and `gemma3:4b` from the defaults (`ollama rm` them if you
  pulled them for 1.0).

## [1.0.0] — 2026-04-14

First release: menu bar app with a global shortcut (⌘⇧P), Casual, Pro and
custom rewriting with local Ollama models (`gemma3:1b` and `gemma3:4b`),
macOS and Windows.

[2.2.0]: https://github.com/Enguerrand-Roques/textpolish/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/Enguerrand-Roques/textpolish/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/Enguerrand-Roques/textpolish/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Enguerrand-Roques/textpolish/releases/tag/v1.0.0
