# Correction test sets

| File | Size | Role |
|------|-----:|------|
| `correction_fr.json`, `correction_en.json` | 130, 123 | **Development set.** Round 7 measured the app on it, and the safety rules of Round 8 were designed by reading its failures. Its scores can be optimistic. |
| `holdout_fr.json`, `holdout_en.json` | 96, 97 | **Round 8 test set.** Written and committed before the Round 8 safety rules and used once to judge them. Its failures then shaped the Round 9 rules, so from Round 9 on it counts as development data. |
| `holdout2_fr.json`, `holdout2_en.json` | 93, 89 | **Round 9 test set.** Written and committed before the Round 9 rules; never used to tune anything. It is the score to trust. |

Each entry: `text`, `expected` (accepted corrections, or `null` when the text is
correct and must come back unchanged) and `kind` (the kind of mistake). Run with
`design/model_eval.py casual <model> --large` (development), `--holdout` or `--holdout2`,
add `--en` for English. All sentences are written for the test, not collected
from users.
