# Raw benchmark output

Everything `benchmarks/benchmark_models.py` (Rounds 1–4) and `design/model_eval.py`
(Round 6) printed, kept so every number in `../BENCHMARK_REPORT.md` can be
checked against the run it came from.

| File | Written by | Content |
|------|------------|---------|
| `results_<run>.json` | `benchmarks/benchmark_models.py` | every output, latency and judge score |
| `summary_<run>.csv` | `benchmarks/benchmark_models.py` | one row per model |
| `review_<run>.md` | `benchmarks/benchmark_models.py` | outputs side by side, for reading |
| `verdict_<run>.md` | `benchmark_models.py --judge` | the judge's verdict per model |
| `round6_20261102.md` | `design/model_eval.py` | expected-answer test set, French and English |

Rounds 1–4 used `benchmarks/benchmark_models.py`'s own simplified prompt (no language
rule, default temperature); Round 6 sends exactly what the app sends.
