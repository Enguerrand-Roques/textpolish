# TextPolish — Handoff notes (September 2026)

Status snapshot for resuming work later. Written at the point where work paused on
`textpolish` to switch to `textpolish-cloud`.

## Current configuration

| Mode | Model | Why |
|------|-------|-----|
| Casual | `ministral-3:3b` | `gemma3:1b-it-qat` consistently missed real typos (e.g. `"opérationel"` → `"opérationnel"`), 100% reproducible, not intermittent. Ministral fixes them reliably. ~+2.7s latency accepted as the tradeoff. |
| Professional | `gemma3:4b` | Still the best under its real prompt — correctly fixes the same typo case. `ministral-3:3b` was tested for pro too but fabricates entire fake emails from short fragments; not safe for that mode. |

Full history and raw numbers: `benchmarks/BENCHMARK_REPORT.md` (Rounds 1–5).

## What changed this session

1. **Round 4 benchmark** — re-tested newer model generations (Gemma 4, Qwen3.5, Ministral 3) released since Round 3 against the then-current config. None beat it outright on the 10-case corpus. Found and fixed a real Gemma 4 footgun along the way: it has "thinking" on by default on Ollama, turning a ~2s call into 50+ seconds unless `"think": false` is sent explicitly.
2. **Code cleanup (4 axes)** — factored the duplicated history/threading logic out of the macOS and Windows UIs into shared modules (`history.py`, `polish_job.py`); extracted shortcut parsing into `platforms/macos/shortcut_parser.py` so it's testable without PyObjC; added test coverage that didn't exist before (`clipboard.py`, history, polish job, shortcut parsing — 19 → 66 tests); synced `README.md` with the actual WKWebView panel architecture; added a native alert when the macOS Accessibility permission is missing (was previously a silent `print`).
3. **Grammarly-style popup** — added a diff view (`diff.py`) with Accept/Revise actions to the macOS panel, positioned near the text selection via the Accessibility API (`platforms/macos/ax_bounds.py`) instead of always centering. Then iterated twice based on live testing:
   - v2: popup starts compact (380×258) instead of full-size, correction now **auto-triggers** in casual mode as soon as the panel opens (no more "pick a mode then click Repolir"), with a chevron to expand into the full view (mascot, history, custom-instruction row) on demand.
   - v3: mode chips (Pro/Casual/Perso) are now visible even in the compact view and instantly re-trigger a correction on click — only "Perso" forces an expand, since it needs the instruction field.
4. **Round 5 (single-case investigation)** — the casual-mode typo bug above; led to the Ministral 3B switch documented in the table.

## Known gotcha hit twice this session

The app doesn't hot-reload. If you edit `ui.py`/`panel.html`/prompts and the running
`main.py` process was started *before* the edit, you're testing stale code — looks
like a bug but isn't. Check with:
```
ps aux | grep "[m]ain.py"
ps -p <pid> -o lstart=          # compare to file mtimes
```

## Open items / not done yet

- **Round 4 corpus not re-run with `ministral-3:3b` as casual.** The switch is based on one targeted real-world case (the "opérationel" bug), not aggregate scores. Worth running `python benchmark_models.py --models ministral-3:3b gemma3:1b-it-qat --judge` for a fuller picture, and watching for over-generation from Ministral on longer/more ambiguous casual inputs (it hallucinated a full fake email in pro mode on a short fragment — same risk class could show up in casual on the wrong input).
- **Anthropic API key exposed in clear text** in local `config.py` (line 13, gitignored, never committed — confirmed clean history). Recommended to rotate on console.anthropic.com regardless, since it's readable on disk.
- **~20 GB of benchmark models** pulled during Round 4 (`qwen3.5:4b/0.8b`, `gemma4:e2b/e4b-it-qat`, `ministral-3:8b/3b`) still on disk. Not urgent (561 GB free at last check) but `ollama rm` candidates if space matters.
- **Real-time "as you type" popup (Grammarly's actual continuous mode)** was deliberately *not* pursued — explicitly deferred after research showed real macOS-level blockers: `AXValueGetValue` unsupported in PyObjC (needs a manual wrapper), a long-standing Apple bug where caret position can't be read without an active text selection, and inconsistent Accessibility support in Electron apps. The shortcut-triggered flow (what exists now) matches how real "no-browser-extension" Grammarly alternatives for Mac are actually built, per research done this session — not a corner-cut, a considered choice.
- **Local GPU fine-tuning** — user has an NVIDIA GPU at home, raised as a possible way to get a more reliable correction model than picking among pretrained options. Not investigated yet — needs GPU model/VRAM specs before any feasibility call. Current recommendation stands: exhaust pretrained-model swaps (like the Ministral switch) before considering training something custom, given how much the Ministral swap alone fixed for zero cost.
- **`textpolish-cloud` improvements** — the reason this doc exists. Known gaps there (unchanged since audit, see that repo's own state): no error handling or timeout in `llm.py` (raw Gemini SDK exceptions reach the UI), still on the old native NSPanel UI (never got the WKWebView/diff-popup work this doc describes), no landing page. Proposed order when resumed: robustness (timeout + typed errors) before UI port, since the UI port is the bigger lift and error handling is cheap and unblocks safer testing.

## Where things are documented

- Model choice rationale + all benchmark data: `benchmarks/BENCHMARK_REPORT.md`
- User-facing feature list and architecture: `README.md`
- This file: session handoff only — update or delete once stale, it's not meant to be permanent project documentation.

## Reliability pass (October 2026, uncommitted until reviewed)

Fixes from the full project audit:
- `clipboard.py`: clipboard is emptied before the simulated copy, polled until filled (no more fixed 0.35 s sleep), so "nothing selected" yields an empty text instead of stale clipboard content; the user's clipboard (all macOS types) is restored right after the copy and again after the paste.
- `llm.py`: input capped at `MAX_INPUT_CHARS` (4000), `num_ctx` sized from the prompt (min 1024), truncated (`done_reason == "length"`), empty, mid-stream error and invalid-JSON responses now raise readable errors. `logging.basicConfig` moved out of `llm.py` into the platform `main.py` files (INFO, no more text excerpt in logs).
- `polish_job.py`: a superseded job's result no longer overwrites the current one.
- Install: casual model is `ministral-3:3b` everywhere (README, `setup.sh`, `release.yml`); `anthropic` moved to `requirements-dev.txt`; Quartz/ApplicationServices listed explicitly; `setup.sh` checks Python >= 3.10 and Ollama, logs to `~/Library/Logs/TextPolish/`.
- `benchmark_models.py` reads `ANTHROPIC_API_KEY` from the environment only. The key in local `config.py` is still there: rotate it and delete the line.
- UI errors are no longer cut at 80 characters.
Not done: same clipboard fix in `textpolish-cloud` (its `clipboard.py` was identical), CI lint/coverage, benchmark alignment with `llm.py`.

## UX redesign (November 2026)

- macOS popup rebuilt Apple-style: native vibrancy behind a transparent WKWebView, no title-bar chrome, content-height panel, popover dismissal. Adaptive layouts chosen by `diff.choose_layout`: per-correction cards (short text), highlighted document (long text), single rewrite with compare (Pro/Perso), "no mistakes" auto-close. Keyboard: ↵ accept, ⇥ ignore, ⌘↵ all, ⌘1-3 modes (physical keys, AZERTY-safe), esc.
- `diff.py`: `group_changes` / `classify_change` / `apply_choices` / `choose_layout`; typographic-only differences (' vs ’, nbsp) are not corrections.
- Bugs found by driving the real app (design/scenario.sh): copy sent ⌥⌘C while the shortcut's ⌥ was held (now waits for release); several instances could run (now single-instance lock); Windows crashed at import (QAction from QtWidgets).
- `design/`: preview harness with fixtures from real model outputs, headless-Chrome screenshots, real-app drivers, offscreen Qt render. Driving the real app needs Accessibility, Automation and Screen Recording for VS Code.
- Portfolio: `docs/case-study.html` (also published as a private artifact), screenshots in `docs/screenshots/`. Demo GIF: `docs/demo.gif`, recorded from the real app by `design/record_demo.py` (warm the model through the app first, or the first correction shows a cold load).
- Not ported to `textpolish-cloud` yet (diff.py, clipboard.py and the panel are identical candidates). Windows only got a style refresh, untested on Windows.

## Model switch and UX fixes (November 2026, second pass)

- Ollama upgraded to 0.40.13. Round 6 (`design/model_eval.py`, expected-answer test set): one model, `gemma4:e2b-it-qat`, now serves Correction, Pro and Perso. Same correction score as Ministral, better Pro/Perso, and no ~5 s reload when switching modes. `gemma4:e2b-nvfp4` (MLX, 0.34 s) is faster but needs ~7.4 GB RAM; documented for bigger Macs. All other models removed, `ministral-3:3b` included; only `gemma4:e2b-it-qat` is installed (4.0 GB). Raw outputs archived in `benchmarks/results/round6_20261102.md`; the report opens with a 17-model summary.
- `llm.py` sends temperature 0 for Correction, 0.4 for Pro/Perso (Gemma 4's default of 1 made Correction score 9-11/12 between identical runs; now 11/12 every run).
- `llm.py` sends `"think": false`; strips Markdown the model adds; language detection handles short unaccented French.
- Popup: "no mistakes" no longer auto-closes (offers Pro/Perso), switching mode during a request works, one-line explanation per mode, Perso presets.
- Testing gotcha: synthetic HID keystrokes can inherit a ⌘ flag from a previous synthetic ⌘-shortcut; `design/type_text.py` now forces flags to 0.

## Final model cleanup and fluidity pass (November 2, 2026)

- Only `gemma4:e2b-it-qat` installed. The benchmark report opens with a 17-model summary; Round 6 raw outputs are in `benchmarks/results/round6_20261102.md`.
- Per-mode temperature in `llm.py` (0 Correction, 0.4 Pro/Perso): Correction went from 9-11/12 between runs to 11/12 every run.
- `design/fluidity.py` plays 7 user scenarios in TextEdit against the running app and reads timings from `design/app.log` (`ui.py` now logs copy time and "<mode> ready in N ms", lengths only). 14/14 over two passes: panel ~0.7 s after the shortcut, sentence ~1 s, ⌘2 switch ~0.8 s, 338-char report 2.7 s.
- Bug found by it: ⌘↵ with the cursor in the Perso field re-ran the instruction instead of pasting. Fixed in `panel.html`.
- Not changed: "no selection" takes ~1.2 s because the copy waits up to 1 s for slow apps (`_COPY_TIMEOUT`).

