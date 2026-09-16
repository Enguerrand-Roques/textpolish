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
