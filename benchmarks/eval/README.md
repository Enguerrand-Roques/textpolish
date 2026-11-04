# Correction test sets

| File | Size | Role |
|------|-----:|------|
| `correction_fr.json`, `correction_en.json` | 130, 123 | **Development set.** Round 7 measured the app on it, and the safety rules of Round 8 were designed by reading its failures. Its scores can be optimistic. |
| `holdout_fr.json`, `holdout_en.json` | 96, 97 | **Frozen test set.** Written and committed before any Round 8 change; never used to tune anything. It is the score to trust. Includes informal messages ("jsp", "aprem", "btw", "u") that must stay as written. |

Each entry: `text`, `expected` (accepted corrections, or `null` when the text is
correct and must come back unchanged) and `kind` (the kind of mistake). Run with
`design/model_eval.py casual <model> --large` (development) or `--holdout`,
add `--en` for English. All sentences are written for the test, not collected
from users.
