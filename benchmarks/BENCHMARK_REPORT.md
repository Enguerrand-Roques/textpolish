# TextPolish — Benchmark Report

## Summary — 17 models, 6 rounds (April → November 2026)

Every model below was run on the same machine (MacBook Air M2, 16 GB) through Ollama.
Rounds 1-4 scored outputs with an LLM judge (Claude) on a 10-case corpus; Round 5 was a
targeted bug investigation; Round 6 switched to expected answers (`design/model_eval.py`)
so a score is a count, not an opinion. Raw outputs: `benchmarks/results/`.
17 models were tested; an 18th (`gemma4:e4b-nvfp4`) failed to download.

| Model | Rounds | Best result | Why it was kept or dropped |
|-------|--------|-------------|----------------------------|
| **`gemma4:e2b-it-qat`** | 4, 6, 7 | **Correction 123/130 FR (94.6 %), 114/123 EN (92.7 %) on the large sets; 12/12 on the 12-sentence sets; Pro 5/5; Custom 3/3; ~1 s warm, 3–6 s cold** | **In use for all modes.** Needs `"think": false` and temperature 0 for Correction |
| `gemma4:e2b-nvfp4` (MLX) | 6 | 10/12, 0.34 s | Fastest tested; ~7.4 GB RAM swaps a busy 16 GB Mac. Option for 24 GB+ |
| `gemma4:e4b-it-qat` | 4 | 5.00/5 Pro (judge) | Better than E2B in Pro (5.00 vs 4.73), ~1.6x slower |
| `gemma4:e4b-nvfp4` (MLX) | 6 | — | Download failed; not tested |
| `ministral-3:3b` | 4, 5, 6 | 10/12 clean run (11/12 on a first, busier pass), 0.67 s | Correction model in Round 5; in Pro it wrote whole emails, in Custom (then "Perso") it answered the message |
| `ministral-3:8b` | 4 | 4.87/5 Pro (judge) | 12-15 s per request; added Markdown |
| `gemma3:4b` | 1-6 | 5.00/5 Pro (Round 4) | Pro model until Round 6; 6/12 Correction, "Dear [Recipient Name]" |
| `gemma3:4b-it-qat` | 1, 3 | 4.77/5 (judge) | Slower than `gemma3:4b` in Round 3 (5.79 s vs 4.94 s) |
| `gemma3:1b-it-qat` | 1, 3-5 | 4.53/5, 1.77 s | Correction model from Round 3 to Round 5; never fixed "opérationel" |
| `gemma3:1b` | 1-3 | 4.53/5 | Beaten by its QAT build |
| `qwen3.5:4b` | 4, 5 | 4.73/5 Pro | ~6.5 s; turned "RH et" into "RHO" |
| `qwen3.5:4b-nvfp4` (MLX) | 6 | 10/12, 0.95 s | Rewrote a correct sentence; "Le réunion" in Pro |
| `qwen3.5:2b-mtp-q4_K_M` | 6 | 5/12 | Introduced mistakes |
| `qwen3.5:2b-nvfp4` (MLX) | 6 | 3/12 | Translated French to English |
| `qwen3.5:0.8b` | 4 | 3.33/5 Pro | Distorted meaning in French |
| `lfm3:1.7b` (MLX) | 6 | 2/12, 7.2 s | Printed its reasoning into the answer |
| `command-r7b` | 1 | 3.90/5, 11.8 s | Too slow |
| `qwen3:4b` | 1 | — | Timed out (thinking enabled) |

**What the research changed in the app**, beyond the model choice: prompts in English with a
same-language rule (Round 1), `num_ctx` sized to the input (Round 2), `"think": false` for
hybrid-reasoning models (Round 4), a stricter language detector and Markdown cleanup (Round 6),
and per-mode temperature (Round 6). Later the same day, filming the demo showed that the
"answer in the input language" rule blocked translation requests on long texts; in Custom
the rule now yields to the instruction. Only `gemma4:e2b-it-qat` is installed now; every other
model was removed after testing.

---

## Round 1 — April 5–6, 2026

**Goal:** Identify the best local Ollama model for TextPolish on Apple M2 16 GB.

### Methodology

- **Corpus:** 10 representative cases (pro/casual, French/English, short/long, with typos)
- **Models tested:** gemma3:1b, gemma3:1b-it-qat, gemma3:4b, gemma3:4b-it-qat, command-r7b, qwen3:4b (timed out)
- **Quality judge:** Claude Haiku 4.5 (Anthropic API), scoring 1–5 on three criteria
- **Configuration:** `keep_alive: 0` (model reloaded every call); the harness never sets `num_ctx`, so Ollama's default applies

### Results

| Model | Median latency | Correction | Tone | Preservation | **Overall** | Size |
|-------|---------------:|----------:|-----:|-------------:|------------:|-----:|
| `gemma3:1b-it-qat` | 3.2s | 4.3/5 | 4.1/5 | 4.0/5 | 4.13/5 | 1.0 GB |
| `gemma3:1b` | 4.2s | 4.7/5 | 4.0/5 | 4.1/5 | 4.27/5 | 0.8 GB |
| `gemma3:4b-it-qat` | 6.1s | 4.7/5 | 3.8/5 | 4.0/5 | 4.17/5 | 4.0 GB |
| `gemma3:4b` | 8.7s | 4.9/5 | 3.4/5 | 3.7/5 | 4.00/5 | 3.3 GB |
| `command-r7b` | 11.8s | 4.9/5 | 3.2/5 | 3.6/5 | 3.90/5 | 5.1 GB |
| `qwen3:4b` | — | — | — | — | timeout | 2.5 GB |

### Key findings

**1. All models responded in French on English input** — identified as a prompt engineering issue, not a model limitation. Prompts were in French and small models anchored on the prompt language rather than the input language.

**2. QAT outperforms Q4\_K\_M at equal parameter count** — `gemma3:4b-it-qat` is 30% faster than `gemma3:4b` (6.1s vs 8.7s) with a higher overall score (+0.17).

**3. `num_ctx: 1024` has no quality impact** — the longest case in the corpus is ~544 tokens. `num_ctx: 1024` provides a safety margin while reducing KV cache from ~2 GB to ~16 MB.

### Optimizations applied to the app after Round 1

These changed `llm.py` and `config.py`; the benchmark harness kept `keep_alive: 0` and the default `num_ctx` in every round.

| Parameter | Before | After | Estimated gain |
|-----------|--------|-------|---------------|
| `OLLAMA_MODEL` | `gemma3:4b` | `gemma3:1b` (casual) / `gemma3:4b` (pro) | −5s/request |
| `OLLAMA_KEEP_ALIVE` | `0` | `300s` | −3–5s on cold start |
| `num_ctx` | `131 072` (default) | `1 024` | −2–4s + −2 GB RAM |
| Prompts | French, loose | English, strict language-match rule | language bug fix |

---

## Round 2 — April 7, 2026

**Goal:** Verify the language bug fix and validate the per-mode model architecture (`gemma3:1b` for casual, `gemma3:4b` for pro) after rewriting prompts in English.

### What changed since Round 1

- All three prompt files (`pro.txt`, `casual.txt`, `custom.txt`) rewritten in English
- Rule 1 in every prompt: *"Output in the SAME language as the input"*
- `casual.txt` now explicitly forbids restructuring: *"Keep the original structure exactly — same sentences, same order, same length"*
- Per-mode model selection introduced in `llm.py`

### Results

| Model | Median latency | Correction | Tone | Preservation | **Overall** | vs Round 1 |
|-------|---------------:|----------:|-----:|-------------:|------------:|----------:|
| `gemma3:1b` | **1.87s** | 4.3/5 | 4.5/5 | 4.8/5 | **4.53/5** | +0.26 · −2.3s |
| `gemma3:4b` | 4.50s | 4.4/5 | 5.0/5 | 4.8/5 | **4.74/5** | +0.74 · −4.2s |

Both models improved dramatically on every axis — quality up, latency down.

### Language bug: status

| Case | gemma3:1b | gemma3:4b |
|------|-----------|-----------|
| `en_pro_followup` | ✅ English | ✅ English |
| `en_pro_long` | ✅ English | ✅ English |
| `en_casual_sms` | ✅ English | ✅ English |
| `en_casual_long` | ✅ English | ✅ English |
| `fr_pro_short` | ❌ Translated to English | ✅ French |
| `fr_pro_long` | ❌ Translated to English | ✅ French |
| `fr_pro_linkedin` | ❌ Translated to English | ✅ French |
| `fr_casual_sms` | ✅ French | ✅ French |
| `fr_casual_long` | ✅ French | ✅ French |
| `fr_casual_abbrev` | ✅ French | ✅ French |

**English input → correct language: fully fixed on both models.**

**French pro input → gemma3:1b still translates to English.** The 1b model is too small to reliably follow the language-match rule when the system prompt is in English and the task requires professional rewriting. It defaults to English as its strongest language. gemma3:4b follows the rule correctly on all cases.

### Findings

**1. Language bug fixed for English input on both models**
Round 1 showed every model replying in French on English input. With the new English prompts and explicit language rule, both models now correctly output English for English input — scores of 4.0–5.0/5 on all four English cases.

**2. gemma3:1b: new residual bug on French pro input**
The same fix that solved English input introduced a new failure: gemma3:1b now translates French professional text to English. The model is too small to balance *"write professionally"* and *"stay in the input language"* simultaneously when driven by an English prompt. The judge still scores these outputs 4.67–5.0/5 because the English output is technically excellent — but it is the wrong language for a French user.

**3. gemma3:1b handles French casual mode correctly**
In casual mode, the instruction is conservative (*"fix typos, keep structure"*) — the model has no reason to change language and doesn't. All three French casual cases are output in correct French.

**4. This confirms and validates the per-mode model architecture**
- `casual` → `gemma3:1b`: 1.87s median, handles both French and English correctly
- `pro` → `gemma3:4b`: 4.50s median, handles both French and English correctly

Using gemma3:1b for pro mode would be a regression on French inputs. The current split is the right configuration.

**5. Latency improvements are unexpectedly large**
gemma3:1b went from 4.18s (Round 1) to 1.87s (−55%). gemma3:4b from 8.71s to 4.50s (−48%). The harness sends `keep_alive: 0` and no `num_ctx` in every round, so these settings do not explain the gain; the shorter English prompts are the only known change.

**6. Remaining weakness: heavy abbreviations in casual mode**
`fr_casual_abbrev` ("tkt c bon g geré, jte redis ds 10 min") scores 2/5 on correction for both models — they barely touch it. This is actually correct behavior: casual mode is designed to preserve style, not expand abbreviations. The low correction score reflects the judge's expectation, not a real bug. To be documented as a known scope limitation.

### Current configuration (post Round 2)

| Setting | Value | Rationale |
|---------|-------|-----------|
| `OLLAMA_MODEL_CASUAL` | `gemma3:1b` | 1.87s median, correct on FR+EN casual |
| `OLLAMA_MODEL_PRO` | `gemma3:4b` | 4.50s median, correct on FR+EN pro |
| `OLLAMA_KEEP_ALIVE` | `300s` | Avoid cold-start penalty within a session |
| `num_ctx` | `1024` | Max corpus token count is ~544; 1024 is safe margin |
| Model unload on switch | enabled | Prevents simultaneous model cohabitation (~5 GB peak avoided) |

### Next steps

- ~~Re-run after Gemma 4 small variants become available on Ollama~~ → gemma4 not yet on Ollama as of 2026-04-14; re-run when available
- ~~Consider a language-detection pre-pass~~ → **Done**: `_detect_language()` added to `llm.py`, prepends explicit language instruction to every prompt

---

## Round 3 — April 14, 2026

**Goal:** Validate QAT variants (`gemma3:1b-it-qat`, `gemma3:4b-it-qat`) using the fixed English prompts and language injection introduced after Round 2. Do they outperform standard Q4_K_M at `num_ctx: 1024`?

### Context

Round 1 found QAT to be ~30% faster than Q4_K_M (`gemma3:4b-it-qat` 6.1s vs `gemma3:4b` 8.7s). Round 3 tests whether QAT keeps that advantage with the English prompts.

Note: the benchmark runner calls Ollama directly and does **not** pass through `polish_text()` in `llm.py`. Language injection (`_detect_language`) is therefore **not active** during benchmarking — results reflect raw model capability, not the app pipeline.

### Latency Results

| Model | Median | Mean | P95 | Min | Max |
|-------|-------:|-----:|----:|----:|----:|
| `gemma3:1b-it-qat` | **1.69s** | 1.82s | 2.61s | 1.13s | 2.61s |
| `gemma3:1b` | 1.84s | 1.81s | 2.49s | 1.21s | 2.49s |
| `gemma3:4b-it-qat` | 5.27s | 5.89s | 9.35s | 4.20s | 9.35s |
| `gemma3:4b` | **4.23s** | 4.54s | 7.60s | 3.31s | 7.60s |

### Quality Scores (judge: claude-opus-4-6, run 2026-04-15)

| Model | Median | Correction | Tone | Preservation | **Overall** |
|-------|-------:|----------:|-----:|-------------:|------------:|
| `gemma3:1b-it-qat` | **1.77s** | 4.3/5 | 4.7/5 | 4.6/5 | **4.53/5** |
| `gemma3:1b` | 1.96s | 4.0/5 | 4.9/5 | 4.5/5 | 4.47/5 |
| `gemma3:4b-it-qat` | 5.79s | 4.6/5 | 4.8/5 | 4.9/5 | **4.77/5** |
| `gemma3:4b` | 4.94s | 4.1/5 | 4.9/5 | 5.0/5 | 4.67/5 |

Note: benchmark runs models without the `_detect_language()` injection from `llm.py` — both 1b models translate French pro text to English in raw mode. In the actual app, the language fix is active.

### Key Findings

**1. `gemma3:1b-it-qat` beats `gemma3:1b` on both axes**
Faster (1.77s vs 1.96s, −10%) and better quality (4.53 vs 4.47, +0.06). Clear config switch for casual mode.

**2. `gemma3:4b-it-qat` is higher quality but slower than `gemma3:4b`**
Quality: 4.77 vs 4.67 (+0.10). Latency: 5.79s vs 4.94s (+17%). The quality gain doesn't justify the latency cost for pro mode.

**3. The QAT advantage depends on model size**
For the 1b model, QAT is a strict improvement. For the 4b model, QAT is slower. The Round 1 gap was not reproduced; the harness never changed `num_ctx`, so the cause is unknown.

### Current configuration (updated after Round 3)

| Setting | Value | Rationale |
|---------|-------|-----------|
| `OLLAMA_MODEL_CASUAL` | `gemma3:1b-it-qat` | 1.77s median, faster + better quality than gemma3:1b |
| `OLLAMA_MODEL_PRO` | `gemma3:4b` | 4.94s median, best quality/speed ratio for pro |
| `OLLAMA_KEEP_ALIVE` | `300s` | Avoid cold-start penalty within a session |
| `num_ctx` | `1024` | Max corpus token count is ~544; 1024 is safe margin |
| Language injection | enabled (`llm.py`) | Fixes French pro mode for 1b models in the app pipeline |

### Next steps

- Re-run when `gemma4` variants become available on Ollama

---

## Round 4 — September 2, 2026

**Goal:** Evaluate whether newer model generations released since Round 3 (April 2026) beat the current configuration (`gemma3:1b-it-qat` casual / `gemma3:4b` pro) on Apple M2 16 GB.

### Context

Between Round 3 and Round 4, several relevant model families shipped new generations: Gemma 4 (Google, April 2026), Qwen3.5 (Alibaba, Feb–March 2026, including a dedicated "Small"/edge series), and Ministral 3 (Mistral, Dec 2025). Ollama itself was upgraded from `0.20.2` to `0.33.2` for this round.

**Models tested:** `gemma3:1b-it-qat`, `gemma3:4b` (current config, as baseline), `qwen3.5:4b`, `qwen3.5:0.8b`, `gemma4:e2b-it-qat`, `gemma4:e4b-it-qat`, `ministral-3:8b`, `ministral-3:3b` — 8 models × 10 cases = 80 runs, judged by `claude-opus-4-6` (same corpus and judge as Round 3).

### Pre-run findings (before the comparative benchmark)

**1. Ollama's MLX engine is present but not used for these GGUF models.** Upgrading Ollama pulls in `mlx`/`mlx-c` as bundled dependencies, and a `mlx_metal_v3` runner ships in `libexec/lib/ollama/`. However, a live-traced generation (`gemma3:1b-it-qat`) shows Ollama routing through `llama-server` (llama.cpp) with the classic Metal GPU backend (`msg="using llama-server for model"`), not the MLX runtime. All models pulled here are standard GGUF blobs, which llama.cpp handles directly — the MLX path would require MLX-native model weights, not something these Ollama library tags provide. **No latency gain from the Ollama/MLX transition was observed on this M2 16 GB for the models tested; the standalone MLX backend explored in earlier project notes is not made obsolete by this Ollama upgrade.**

**2. Gemma 4 has "thinking" enabled by default and it is catastrophic for this use case.** A raw call to `gemma4:e2b-it-qat` on a short casual-mode case took **51.6s** and generated **1099 tokens** internally (`eval_count`) before returning a 20-token answer — a 28x latency regression vs. `gemma3:1b-it-qat`. Passing `"think": false` in the `/api/generate` payload eliminates this entirely: the same call dropped to **1.09s** with `eval_count: 25`, correct output preserved. `benchmark_models.py` (`run_case()`) was patched to always send `"think": false` — harmless for models without a thinking mode (confirmed on `gemma3:1b-it-qat`, no behavior change), and this is now required for anyone using Gemma 4 (or another hybrid-reasoning model) through TextPolish. **If Gemma 4 is ever adopted in production, `llm.py` must also send `"think": false` in its request payload** — it did not at the time (added in Round 6).

### Results — Casual mode

| Model | Median latency | **Overall** | vs. current (`gemma3:1b-it-qat`) |
|-------|---------------:|------------:|-----------------------------------|
| `gemma3:1b-it-qat` (current) | **1.34s** | 4.07/5 | — |
| `qwen3.5:0.8b` | 1.96s | 2.93/5 | Slower, notably worse quality (reject) |
| `ministral-3:3b` | 4.07s | 4.53/5 | +0.46 quality, but 3x slower |
| `gemma4:e2b-it-qat` | 4.47s | 4.27/5 | +0.20 quality, 3.3x slower |
| `gemma4:e4b-it-qat` | 5.62s | 4.20/5 | +0.13 quality, 4.2x slower |
| `gemma3:4b` | 6.36s | 4.20/5 | (current pro model, for reference) |
| `qwen3.5:4b` | 6.46s | 4.40/5 | +0.33 quality, 4.8x slower |
| `ministral-3:8b` | 12.58s | 4.53/5 | +0.46 quality, 9.4x slower |

### Results — Pro mode

| Model | Median latency | **Overall** | vs. current (`gemma3:4b`) |
|-------|---------------:|------------:|-----------------------------|
| `gemma3:1b-it-qat` | 1.50s | 4.47/5 | (reference only — translates FR→EN without app-level language injection, see Round 2) |
| `ministral-3:3b` | **5.03s** | 4.67/5 | **−34% latency**, −0.33 quality |
| `gemma4:e2b-it-qat` | 6.16s | 4.73/5 | −19% latency, −0.27 quality |
| `gemma3:4b` (current) | 7.59s | **5.00/5** | — |
| `qwen3.5:4b` | 7.83s | 4.73/5 | +3% latency, −0.27 quality (reject) |
| `gemma4:e4b-it-qat` | 9.87s | 5.00/5 | Same quality, +30% latency (reject) |
| `ministral-3:8b` | 14.84s | 4.87/5 | −0.13 quality, +95% latency (reject) |

### Key findings

**1. No candidate beats the current configuration outright.** For casual mode, every candidate that improves quality does so at 3-9x the latency — a much worse tradeoff than the ~1.3-2s target established since Round 2. For pro mode, no model matches or beats `gemma3:4b`'s perfect 5.00/5 while also being faster; the two that are faster (`ministral-3:3b`, `gemma4:e2b-it-qat`) both give up meaningful quality.

**2. `ministral-3:3b` is the most interesting alternative found, but not a clean swap.** In pro mode it is 34% faster than `gemma3:4b` (5.03s vs 7.59s) at a real but moderate quality cost (4.67 vs 5.00 — still "Excellent" tier per the existing verdict scale). Worth keeping in mind as a "fast pro" option if latency ever becomes the priority over the current quality-first choice, but not adopted this round since the existing methodology (Round 3) treats quality regressions as disqualifying unless the latency gain is dramatic.

**3. `qwen3.5:0.8b` is not viable despite its size.** Smallest model tested (1.0 GB) but weakest by far (2.93/5 casual, 3.33/5 pro) — multiple cases show meaning distortion in French (`fr_pro_long`: "Bienvenue" instead of "Bonjour", nonsensical phrasing). Too small for reliable French correction.

**4. All new candidates handle French pro-mode input correctly without language injection** — unlike `gemma3:1b-it-qat`, which still translates French to English in pro mode when tested without `llm.py`'s `_detect_language()` pass (confirmed again this round, same bug as Round 2). Gemma 4, Qwen3.5, and Ministral 3 all output correct French on `fr_pro_long` at the raw-model level. Not actionable today (no config change proposed), but relevant if French pro-mode robustness becomes a priority independent of speed.

**5. `ministral-3:8b` produced an unwanted formatting artifact** on `fr_pro_long` — it added a bold Markdown subject line (`**Objet : ...**`) not present in the input or requested by the prompt. Judge score didn't penalize it heavily, but it is a real deviation TextPolish's clipboard-paste flow would surface directly to the user.

### Current configuration (unchanged after Round 4)

| Setting | Value | Rationale |
|---------|-------|-----------|
| `OLLAMA_MODEL_CASUAL` | `gemma3:1b-it-qat` | Still the best speed/quality tradeoff — no candidate matches its ~1.3-1.5s latency |
| `OLLAMA_MODEL_PRO` | `gemma3:4b` | Still the only model reaching 5.00/5 overall on the pro corpus |

### Next steps

- Re-run when Phi-5 (status unconfirmed as of Sept 2026) or a further Qwen3.5/Ministral generation ships with a smaller/faster variant.
- If a "fast pro" mode is ever introduced as a user-facing option, `ministral-3:3b` is the pre-vetted candidate (already pulled locally, `think` not applicable — no hybrid reasoning to disable).
- Before any future Gemma 4 adoption: add `"think": False` to the request payload in `llm.py` (not just `benchmark_models.py`) — otherwise casual mode would regress to 50+ seconds. (Done in Round 6.)

---

## Round 5 — September 16, 2026

**Goal:** Investigate a concrete user-reported bug — casual mode left `"opérationel"`/`"operationel"` uncorrected (should be `"opérationnel"`) — and decide whether to change the casual model.

**Not a corpus benchmark run** — this round is a targeted single-case investigation (`"RH et opérationel on veut plus operationel"`), run directly against Ollama outside `benchmark_models.py`, prompted by a real failure the user hit in production use.

### Findings

**1. `gemma3:1b-it-qat` (casual) fails 100% of the time on this typo, not intermittently.** 3/3 runs returned the input unchanged. Unlike the Round 4 `"yo"/"frérot"` bug (non-deterministic — sometimes fine, sometimes not), this is a consistent miss: the model doesn't recognize `"opérationel"` as misspelled at all. A prompt fix (Round 4's added example) doesn't help here — this isn't an instruction-following problem, it's a knowledge/detection gap for this specific word.

**2. It's not just a "too small" problem — `gemma3:4b` fails too when driven by the casual prompt.** Testing the same input with `casual.txt`'s instructions across models: `gemma3:4b` also left both typos uncorrected. `qwen3.5:4b` fixed the typo but corrupted `"RH et"` → `"RHO"`. `ministral-3:3b` fixed both occurrences perfectly with zero side effects. This looks like a Gemma3-family-specific weakness on this word, not a general small-model limitation.

**3. Re-tested fairly with the real `pro.txt` prompt (not `casual.txt`) before touching the pro model.** Under its actual prompt, `gemma3:4b` correctly fixes both occurrences (`"opérationnel"`, `"opérationnelle"`) — the earlier casual-prompt test was not representative of real pro-mode behavior. `ministral-3:3b` under `pro.txt`, however, fabricated an entire formal email (`"**Objet:**"`, `"Bonjour,"`, `"Cordialement,"`, invented signature placeholder) from a two-clause fragment — a severe over-generation failure, worse than the original bug. **`ministral-3:3b` is not suitable for pro mode.**

### Decision

| Setting | Before | After | Rationale |
|---------|--------|-------|-----------|
| `OLLAMA_MODEL_CASUAL` | `gemma3:1b-it-qat` | `ministral-3:3b` | Fixes a reproducible real-world typo class gemma3:1b/4b both miss; ~+2.7s median latency accepted as the tradeoff (1.3s → ~4.1s per Round 4 timing) |
| `OLLAMA_MODEL_PRO` | `gemma3:4b` | unchanged | Already handles this case correctly under its real prompt; `ministral-3:3b` fabricates content in pro mode — a regression, not an improvement |

### Next steps

- Re-run the full 10-case corpus (`benchmarks/benchmark_models.py --models ministral-3:3b gemma3:1b-it-qat --judge`) now that casual has changed, to get updated aggregate scores rather than relying on a single-case spot check.
- Watch for further over-generation from `ministral-3:3b` in casual mode on longer/more ambiguous inputs — this round only tested a short fragment.

---

## Round 6 — November 2, 2026

**Goal:** Pick the best local model per mode after Ollama 0.40 (MLX engine for some architectures) and new small models, with a test set that has expected answers instead of a judge.

**Method** (`design/model_eval.py`): Correction is scored against expected outputs on 12 realistic sentences (9 with mistakes, 3 already correct that must stay untouched), exact match after normalizing quotes and spaces. Pro and Custom use checks: language kept or translated as asked, no Markdown or email boilerplate, sensible length, plus reading every output by hand. Latency: first call (cold) and median of warm calls, Ollama 0.40.13, M2 16 GB. All requests send `"think": false`.

### Correction

| Model | Engine | Score | Warm median | Notes |
|-------|--------|------:|------------:|-------|
| `gemma4:e2b-nvfp4` | MLX | 10/12 | **0.34 s** | 7.4 GB in RAM |
| `ministral-3:3b` (previous) | llama.cpp | 10/12 | 0.67 s | expanded "infra" to "infrastructure" |
| `gemma4:e2b-it-qat` | llama.cpp | 10/12 | 0.88 s | 4.3 GB |
| `qwen3.5:4b-nvfp4` | MLX | 10/12 | 0.95 s | rewrote a correct sentence |
| `gemma3:4b` | llama.cpp | 6/12 | 1.43 s | missed "opérationel" again |
| `qwen3.5:2b-mtp-q4_K_M` | llama.cpp | 5/12 | 0.78 s | introduced mistakes |
| `qwen3.5:2b-nvfp4` | MLX | 3/12 | 0.52 s | translated, introduced mistakes |
| `lfm3:1.7b` | MLX | 2/12 | 7.2 s | printed its reasoning into the answer |

### Pro and Custom (then "Perso")

| Model | Pro | Pro warm | Custom | Custom warm | Notes |
|-------|----:|---------:|------:|-----------:|-------|
| `gemma4:e2b-nvfp4` | 5/5 | 0.88 s | 3/3 | 0.56 s | keeps "tu" with a friend |
| `gemma4:e2b-it-qat` | 5/5 | 1.06 s | 3/3 | 1.10 s | |
| `gemma3:4b` (previous Pro) | 5/5 | 1.65 s | 2/3 | 1.83 s | "Dear [Recipient Name]"; missed "make it shorter"; on a rerun reversed who thanked whom |
| `qwen3.5:4b-nvfp4` | 5/5 | 2.04 s | 3/3 | 1.75 s | grammar slips ("Le réunion") |
| `ministral-3:3b` | 3/5 | 1.98 s | 3/3* | 1.15 s | *answered a message instead of rewriting it |

### Findings

1. **One model for all modes removes the mode-switch reload.** With `ministral-3:3b` + `gemma3:4b`, switching mode reloaded a model (~5-6 s; Ollama could not keep both in RAM on this busy 16 GB Mac). With a single Gemma 4 model, measured switches were 0.5-1 s.
2. **MLX helps a lot but costs RAM.** `gemma4:e2b-nvfp4` was the fastest everywhere, but loading it took free memory from 52 % to 24 % and added swap on a Mac already using 20 GB of swap.
3. **Language detection bug.** Short unaccented French ("J'ai finit le rapport hier soir") was detected as English and the model was told to answer in English; Gemma 4 obeyed and translated. Fixed with a larger stop-word list and apostrophe splitting.
4. **Temperature matters more than expected for Correction.** Gemma 4 defaults to temperature 1; three identical runs scored 9, 10 and 11/12. `llm.py` now sends 0 for Correction (same answer every run) and 0.4 for Pro/Custom (more consistent tone, still varied). Final run: **11/12** twice in a row; the remaining miss drops the "?" in "slt tu fait quoi ce soir ? on peut…". "si tout ça se passe bien" was added as an accepted answer (correct and same meaning).

### Cold vs warm latency (chosen model, app pipeline)

Measured with `polish_text()` after `ollama stop` (cold) and on the next three calls (warm), 3 runs per mode, short sentences:

| Mode | Cold median | Cold range | Warm median |
|------|------------:|-----------:|------------:|
| Correction | 4.96 s | 3.68–6.28 s | 0.56 s |
| Pro | 3.43 s | 2.97–3.99 s | 0.51 s |
| Custom | 3.08 s | 3.00–3.79 s | 0.56 s |

The model file stayed in macOS's file cache between runs. Cold loads with an empty cache (first request after a reboot, or after heavy memory use) were 9.4 s and 15.4 s in this round. With `OLLAMA_KEEP_ALIVE = 300` a cold load happens again after 5 minutes idle. The warm numbers in the tables above are higher (0.9–1.1 s) because the test set has longer sentences.

The Custom mode was called "Perso" during this round; it is now **Custom** in English and **Sur mesure** in French.

### English test set

The project and its interface are English-first, so the same evaluation was repeated on an
English set (`design/model_eval.py --en`: their/they're, its/it's, your/you're, then/than, to/too,
subject-verb agreement, spelling, plus 3 correct sentences that must stay untouched).

| Mode | French set | English set | Warm median (EN) |
|------|-----------:|------------:|-----------------:|
| Correction | 11/12 | **12/12** (two identical runs) | 0.84 s |
| Pro | 5/5 | 5/5 (the first run also scored 5/5 but invented "Dear [Recipient Name or Hiring Manager]"; prompt fixed, and the eval now flags placeholders) | 0.94 s |
| Custom / Sur mesure | 3/3 | 3/3 | 0.93 s |

### Question-mark guard

The one French miss was always the same: in "slt tu fait quoi ce soir ? on peut se retrouver
vers 19h" the model fixed "fait" but deleted the "?", merging two questions. A correction should
never remove the user's question, so `diff.keep_sentence_marks` (Correction only) puts back a
"?" or "!" that the model removed without replacing it. A mark turned into ".", moved, or a "??" reduced to "?" is left
alone. Result on what the app pastes: **12/12 French, 12/12 English**. The model alone is still
11/12 French; the guard is a rule in the app, not a better model.

### Decision

| Setting | Before | After |
|---------|--------|-------|
| Correction | `ministral-3:3b` | `gemma4:e2b-it-qat` |
| Pro | `gemma3:4b` | `gemma4:e2b-it-qat` |
| Custom (then "Perso") | `ministral-3:3b` | `gemma4:e2b-it-qat` |
| `OLLAMA_KEEP_ALIVE` | 300 s | 300 s (kept; cold vs warm measured above) |
| Temperature | model default (1) | 0 Correction, 0.4 Pro/Custom |

`gemma4:e2b-nvfp4` (MLX) is documented in `config.example.py` as the faster option for Macs with 24 GB or more. Only `gemma4:e2b-it-qat` is kept installed; the other test models, including the `ministral-3:3b` fallback, were removed (Ollama models now take 4.3 GB). Raw outputs: `benchmarks/results/round6_20261102.md`.

## Round 7 — November 4, 2026: a larger test set

12 sentences per language is a weak signal: one sentence is 8 points. Round 7
keeps the same script and scoring (`design/model_eval.py --large`) on two
larger sets, `benchmarks/eval/correction_fr.json` (130 sentences) and
`correction_en.json` (123): everyday messages written for the test, grouped by
kind of mistake, with 30 correct sentences per language that must come back
unchanged. Where two corrections are both right ("parti"/"partie"), both are
accepted. Configuration: the app as shipped (`gemma4:e2b-it-qat`, temperature
0, sentence-mark guard).

| Kind | French | English |
|------|-------:|--------:|
| Accent | 12/12 | — |
| Agreement | 18/18 | 16/16 |
| Conjugation / verb forms | 21/23 | 14/15 |
| Grammar (homophones…) | 21/25 | 23/29 |
| Spelling | 13/13 | 13/13 |
| Punctuation, apostrophes | — | 6/7 |
| Articles | — | 5/5 |
| Several mistakes in one message | 9/9 | 8/8 |
| Correct sentences left alone | 29/30 | 29/30 |
| **Total** | **123/130 (94.6 %)** | **114/123 (92.7 %)** |
| Warm median per sentence | 0.83 s | 0.77 s |

Every miss was read; all 16 are real model errors, none is a wrong expected
answer (raw output: `benchmarks/results/round7_20261104.md`).

### Findings

1. **The 12/12 did not hold at scale, as expected: 93–95 %.** Accents,
   agreement, spelling and multi-mistake messages are perfect in both
   languages; the misses concentrate on rarer constructions.
2. **French misses (7):** subjunctive "que tu vien" and "si j'aurais su" left
   as is; three homophones not caught ("peut de trains", "c'est clés",
   "quand à moi"); "c'est bien passée" kept instead of "s'est"; and one
   overreach, "Jsuis dispo demain aprem" rewritten as "Je suis dispo demain
   après", which changes the meaning.
3. **English misses (9):** too/to, whose/who's, principal/principle,
   fewer/less and "since 2020" not fixed; three wrong fixes that change the
   meaning ("Where going to be late" → "Where are you going…", "borrow me
   your pen" → "borrow my pen", "file's" → "file"); one overreach (the comma
   in "Great job on the launch, everyone!" removed).
4. **Wrong fixes matter more than missed ones.** A missed mistake leaves the
   text as the user wrote it; a wrong fix changes what they meant. Four of the
   16 misses are of that kind, which is why every fix stays a suggestion the
   user accepts or ignores.

The sets are written by me, not collected from real users; the next step is
real messages.
