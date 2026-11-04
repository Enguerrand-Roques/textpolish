# Prompt check — a wider Correction prompt (2026-11-04)

`prompts/casual.txt` asks for "spelling mistakes, missing accents, obvious
typos" only, while the app also fixes agreement and verb forms (the model does
some of it anyway, LanguageTool does the rest). Tested: the same prompt with
rule 2 "Fix only clear mistakes: spelling, missing accents, typos, agreement
and verb forms" and rule 5 "keep every word, only fix its spelling, accents or
form (agreement, conjugation)". Both prompts ran the same day, with LanguageTool
(`design/model_eval.py casual gemma4:e2b-it-qat <set> --lt [--en]`).

| Set | Current prompt | Wider prompt |
|-----|----------------|--------------|
| correction (development) FR | 125/130, 1 wrong applied | 127/130, 0 wrong applied |
| correction (development) EN | 117/123, 0 wrong applied | 120/123, 0 wrong applied |
| holdout FR | 91/96, 2 wrong applied | 91/96, 1 wrong applied |
| holdout EN | 90/97, 0 wrong applied | 92/97, 1 wrong applied |
| holdout2 FR | 90/93, 0 wrong applied | 86/93, 0 wrong applied |
| holdout2 EN | 80/89, 0 wrong applied | 83/89, 1 wrong applied |
| holdout3 FR | 81/86, 1 wrong applied | 80/86, 2 wrong applied |
| holdout3 EN | 88/88, 0 wrong applied | 86/88, 1 wrong applied |

**Held-out sets, all six:** current prompt 520/549 with 3 wrong fixes applied;
wider prompt 518/549 with 6. The gain on the development sets (+5) does not
carry over, and wrong fixes applied double. **Not adopted:** a wrong fix is
worse than a missed one, so the narrow prompt stays; agreement and verb forms
are still fixed by the model when they are clear, and by LanguageTool's rules.

Same-day runs differ a little from the published ones (holdout3 with the
current prompt: 169/174 here, 165/174 in Round 10), so only runs from the same
day are compared.

## Raw summary lines

`ab_orig`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 125/130 · cold 7.1s · warm median 0.84s · LanguageTool median 15 ms
accent 12/12 · agreement 18/18 · conjugation 21/23 · correct 29/30 · grammar 23/25 · mixed 9/9 · spelling 13/13
applied by default: 125/130 right · 1 wrong fix applied · 4 missed · 3 fix(es) held for review
```

`ab_orig--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 117/123 · cold 5.9s · warm median 0.91s · LanguageTool median 11 ms
agreement 16/16 · article 5/5 · conjugation 14/15 · correct 29/30 · grammar 26/29 · mixed 8/8 · punctuation 6/7 · spelling 13/13
applied by default: 115/123 right · 0 wrong fix applied · 8 missed · 7 fix(es) held for review
```

`ab_variant`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 127/130 · cold 6.4s · warm median 1.16s · LanguageTool median 16 ms
accent 12/12 · agreement 18/18 · conjugation 22/23 · correct 29/30 · grammar 24/25 · mixed 9/9 · spelling 13/13
applied by default: 127/130 right · 0 wrong fix applied · 3 missed · 3 fix(es) held for review
```

`ab_variant--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 120/123 · cold 5.8s · warm median 1.15s · LanguageTool median 9 ms
agreement 16/16 · article 5/5 · conjugation 15/15 · correct 30/30 · grammar 27/29 · mixed 8/8 · punctuation 6/7 · spelling 13/13
applied by default: 115/123 right · 0 wrong fix applied · 8 missed · 7 fix(es) held for review
```

`ho_orig--holdout--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 90/97 · cold 5.6s · warm median 0.75s · LanguageTool median 8 ms
agreement 9/9 · article 2/2 · conjugation 12/12 · correct 20/20 · grammar 19/22 · informal 9/10 · mixed 6/8 · punctuation 6/6 · spelling 7/8
applied by default: 92/97 right · 0 wrong fix applied · 5 missed · 5 fix(es) held for review
```

`ho_orig--holdout`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 91/96 · cold 6.1s · warm median 0.83s · LanguageTool median 14 ms
accent 10/10 · agreement 14/14 · conjugation 12/13 · correct 20/20 · grammar 16/17 · informal 9/10 · mixed 4/5 · spelling 6/7
applied by default: 92/96 right · 2 wrong fix applied · 2 missed · 3 fix(es) held for review
```

`ho_orig--holdout2--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 80/89 · cold 4.5s · warm median 0.95s · LanguageTool median 11 ms
agreement 9/9 · article 2/2 · conjugation 10/10 · correct 19/20 · grammar 15/20 · informal 8/10 · mixed 4/5 · punctuation 5/5 · spelling 8/8
applied by default: 81/89 right · 0 wrong fix applied · 8 missed · 5 fix(es) held for review
```

`ho_orig--holdout2`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 90/93 · cold 5.7s · warm median 1.06s · LanguageTool median 19 ms
accent 10/10 · agreement 12/12 · conjugation 12/12 · correct 22/22 · grammar 15/15 · informal 8/10 · mixed 4/5 · spelling 7/7
applied by default: 91/93 right · 0 wrong fix applied · 2 missed · 3 fix(es) held for review
```

`ho_orig--holdout3--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 88/88 · cold 6.3s · warm median 1.03s · LanguageTool median 9 ms
agreement 8/8 · article 2/2 · conjugation 10/10 · correct 20/20 · grammar 22/22 · informal 10/10 · mixed 4/4 · punctuation 5/5 · spelling 7/7
applied by default: 86/88 right · 0 wrong fix applied · 2 missed · 2 fix(es) held for review
```

`ho_orig--holdout3`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 81/86 · cold 5.8s · warm median 1.19s · LanguageTool median 19 ms
accent 8/8 · agreement 10/10 · conjugation 12/12 · correct 21/21 · grammar 12/14 · informal 7/10 · mixed 4/4 · spelling 7/7
applied by default: 80/86 right · 1 wrong fix applied · 5 missed · 6 fix(es) held for review
```

`ho_variant--holdout--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 92/97 · cold 5.7s · warm median 0.92s · LanguageTool median 10 ms
agreement 9/9 · article 2/2 · conjugation 12/12 · correct 20/20 · grammar 20/22 · informal 9/10 · mixed 6/8 · punctuation 6/6 · spelling 8/8
applied by default: 92/97 right · 1 wrong fix applied · 4 missed · 5 fix(es) held for review
```

`ho_variant--holdout`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 91/96 · cold 6.6s · warm median 1.12s · LanguageTool median 17 ms
accent 10/10 · agreement 14/14 · conjugation 13/13 · correct 20/20 · grammar 16/17 · informal 8/10 · mixed 4/5 · spelling 6/7
applied by default: 93/96 right · 1 wrong fix applied · 2 missed · 4 fix(es) held for review
```

`ho_variant--holdout2--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 83/89 · cold 5.0s · warm median 0.82s · LanguageTool median 9 ms
agreement 9/9 · article 2/2 · conjugation 10/10 · correct 20/20 · grammar 17/20 · informal 8/10 · mixed 4/5 · punctuation 5/5 · spelling 8/8
applied by default: 83/89 right · 1 wrong fix applied · 5 missed · 4 fix(es) held for review
```

`ho_variant--holdout2`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 86/93 · cold 5.2s · warm median 0.90s · LanguageTool median 16 ms
accent 10/10 · agreement 12/12 · conjugation 12/12 · correct 21/22 · grammar 15/15 · informal 7/10 · mixed 3/5 · spelling 6/7
applied by default: 90/93 right · 0 wrong fix applied · 3 missed · 6 fix(es) held for review
```

`ho_variant--holdout3--en`
```
### casual · en · gemma4:e2b-it-qat · llamacpp
score 86/88 · cold 4.4s · warm median 0.82s · LanguageTool median 8 ms
agreement 8/8 · article 2/2 · conjugation 10/10 · correct 20/20 · grammar 20/22 · informal 10/10 · mixed 4/4 · punctuation 5/5 · spelling 7/7
applied by default: 83/88 right · 1 wrong fix applied · 4 missed · 4 fix(es) held for review
```

`ho_variant--holdout3`
```
### casual · fr · gemma4:e2b-it-qat · llamacpp
score 80/86 · cold 4.8s · warm median 0.92s · LanguageTool median 15 ms
accent 8/8 · agreement 10/10 · conjugation 11/12 · correct 21/21 · grammar 12/14 · informal 7/10 · mixed 4/4 · spelling 7/7
applied by default: 79/86 right · 2 wrong fix applied · 5 missed · 7 fix(es) held for review
```
