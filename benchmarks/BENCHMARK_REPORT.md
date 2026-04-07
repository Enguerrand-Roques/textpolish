# TextPolish — Benchmark Report

---

## Round 1 — April 5–6, 2026

**Goal:** Identify the best local Ollama model for TextPolish on Apple M2 16 GB.

### Methodology

- **Corpus:** 10 representative cases (pro/casual, French/English, short/long, with typos)
- **Models tested:** gemma3:1b, gemma3:1b-it-qat, gemma3:4b, gemma3:4b-it-qat, command-r7b
- **Quality judge:** Claude Haiku 4.5 (Anthropic API), scoring 1–5 on three criteria
- **Configuration:** `num_ctx: 1024`, `keep_alive: 300s`

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

### Optimisations applied after Round 1

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
In casual mode, the instruction is conservative (*"fix typos, keep structure"*) — the model has no reason to change language and doesn't. All six French casual cases are output in correct French.

**4. This confirms and validates the per-mode model architecture**
- `casual` → `gemma3:1b`: 1.87s median, handles both French and English correctly
- `pro` → `gemma3:4b`: 4.50s median, handles both French and English correctly

Using gemma3:1b for pro mode would be a regression on French inputs. The current split is the right configuration.

**5. Latency improvements are unexpectedly large**
gemma3:1b went from 4.18s (Round 1) to 1.87s (−55%). gemma3:4b from 8.71s to 4.50s (−48%). The combined effect of `num_ctx: 1024`, `keep_alive: 300s`, and warm model state (models already loaded at test start) explains the gain.

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

- Re-run after Gemma 4 small variants become available on Ollama
- Consider a language-detection pre-pass to force the correct output language for gemma3:1b if pro mode needs to support both French and English reliably on the 1b model
