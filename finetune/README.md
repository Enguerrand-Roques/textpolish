# Fine-tuning Gemma 4 E2B for TextPolish (Round 12)

Goal: fewer missed mistakes in Correction at the same cost (same model size,
~1 s, 4.3 GB), without more wrong fixes and without hurting Pro or Custom.
One model keeps serving all three modes.

## Decision rule (committed before any training data)

Three models are run on the same day:

- **A**: `gemma4:e2b-it-qat`, the model in use;
- **B**: control, Google's unquantized QAT weights through this folder's
  conversion, no training (`export.sh`);
- **C**: the fine-tuned model.

C is adopted only if all of these hold:

1. On the frozen sets (`holdout`, `holdout2`, `holdout3`: 549 sentences) plus
   `holdout4` (200, written before any training data), Correction with
   LanguageTool applies **no more wrong fixes than A**, and gets **at least
   1 point more** sentences right.
2. Pro and Custom (`pro_*`, `custom_*`, Round 11 checks): no more failures
   than A, every failure read.
3. Median warm latency at most 10 % above A; model size about the same.

Training choices (learning rate, epochs) are made on the validation loss and
the development sets only, never on the frozen sets. If C fails the rule, it
is reported as "Round 12, not adopted".

## Pipeline

1. `make_data.py`: training data in the exact format the app sends
   (`llm.build_prompt`), checked against every test set for overlap.
2. `mlx_lm.lora` on `mlx-community/gemma-4-E2B-it-qat-4bit` (fits in 16 GB).
3. `merge_lora.py`: the adapter is merged into
   `google/gemma-4-E2B-it-qat-q4_0-unquantized`, the weights the official Q4_0
   GGUF comes from.
4. `export.sh`: llama.cpp GGUF, Q4_0, `ollama create` with `Modelfile`.

Step 0 (November 10, 2026) checked the chain: B scores like A on the French
development set (125/130, 1 wrong fix applied, 0.86 s median), with a model
file of the same size.

## Result (Round 12, November 10, 2026)

Run `essai3` (LoRA rank 16 on the last 16 layers, learning rate 2e-5 with
warmup and cosine decay, batch 1 with 4-step accumulation, 1 epoch, ~3 h on an
M2 with 16 GB; validation loss 2.11 → 0.033) passed every condition:

| On the frozen sets (749) | A, in use | C, fine-tuned |
|---|---:|---:|
| Right answers | 709 | **723** |
| Wrong fixes applied | 5 | **2** |
| Pro / Custom | 48/50, 30/30 | 48/50, 30/30 |
| Median latency | 0.99 s | 1.00 s |

B (control) scored like A on `holdout4`. Two runs were stopped before it:
all 35 layers with batch 4 needed ~12 GB and swapped (about 20 s per step),
and a learning rate of 1e-4 made the loss spike. Published as
[`enguerrandroquesbdl/textpolish-gemma4`](https://ollama.com/enguerrandroquesbdl/textpolish-gemma4);
details in `benchmarks/BENCHMARK_REPORT.md` (Round 12).

Downloads, the environment and trained weights live in `finetune/out/` and
`finetune/.venv/` (not in git).
