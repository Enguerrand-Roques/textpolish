# Correction test sets

| File | Size | Role |
|------|-----:|------|
| `correction_fr.json`, `correction_en.json` | 130, 123 | **Development set.** Round 7 measured the app on it, and the safety rules of Round 8 were designed by reading its failures. Its scores can be optimistic. |
| `holdout_fr.json`, `holdout_en.json` | 96, 97 | **Round 8 test set.** Written and committed before the Round 8 safety rules and used once to judge them. Its failures then shaped the Round 9 rules, so from Round 9 on it counts as development data. |
| `holdout2_fr.json`, `holdout2_en.json` | 93, 89 | **Round 9 test set.** Written and committed before the Round 9 rules and used once to judge them; development data from Round 10 on. |
| `holdout3_fr.json`, `holdout3_en.json` | 86, 88 | **Round 10 test set.** Written and committed before LanguageTool was added; never used to tune anything. It is the score to trust. |
| `holdout4_fr.json`, `holdout4_en.json` | 100, 100 | **Round 12 test set (fine-tuning).** Written and committed before any training data, including messages of two or three sentences; never used to tune anything. |
| `pro_fr.json`, `pro_en.json` | 25, 25 | **Pro (Round 11).** Informal messages to rewrite for work, each with the facts that must survive (`keep`). |
| `custom_fr.json`, `custom_en.json` | 15, 15 | **Custom (Round 11).** A message, a request and what it asks (`kind`: translate, shorter, list, one sentence, vous, question, changed), plus the facts to keep. |

Each entry: `text`, `expected` (accepted corrections, or `null` when the text is
correct and must come back unchanged) and `kind` (the kind of mistake). Run with
`design/model_eval.py casual <model> --large` (development), `--holdout`, `--holdout2`, `--holdout3` or `--holdout4`,
add `--en` for English. All sentences are written for the test, not collected
from users.
