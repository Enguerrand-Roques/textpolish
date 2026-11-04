# Raw benchmark output

Everything `benchmarks/benchmark_models.py` (Rounds 1–4) and `design/model_eval.py`
(Round 6) printed, kept so every number in `../BENCHMARK_REPORT.md` can be
checked against the run it came from.

| File | Written by | Content |
|------|------------|---------|
| `results_<run>.json` | `benchmarks/benchmark_models.py` | every output, latency and judge score |
| `summary_<run>.csv` | `benchmarks/benchmark_models.py` | one row per model |
| `review_<run>.md` | `benchmarks/benchmark_models.py` | outputs side by side, for reading |
| `verdict_<run>.md` | `benchmarks/benchmark_models.py --judge` | the judge's verdict per model |
| `round6_20261102.md` | `design/model_eval.py` | expected-answer test set, French and English |
| `round7_20261104.md` | `design/model_eval.py --large` | the large Correction sets in `../eval/` (130 FR, 123 EN) |
| `round8_20261104.md` | `design/model_eval.py --large/--holdout` | safety rules, judged on the first held-out set |
| `round9_20261104.md` | `design/model_eval.py --large/--holdout/--holdout2` | known confusions, judged on the second held-out set |

Rounds 1–4 read the app's `prompts/*.txt` as they were at the time (they have
changed since), without the app's language detection, with the default
temperature and `keep_alive: 0`. Round 6 sends exactly what the app sends.
