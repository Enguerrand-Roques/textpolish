# Changelog

All notable changes to TextPolish. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Larger Correction test sets: 130 French and 123 English messages in
  `benchmarks/eval/`, run with `design/model_eval.py --large`. Result:
  95 % French, 93 % English, correct sentences left alone 29/30 in each
  (Round 7 in the benchmark report).

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

[2.0.0]: https://github.com/Enguerrand-Roques/textpolish/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Enguerrand-Roques/textpolish/releases/tag/v1.0.0
