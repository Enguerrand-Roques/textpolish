#!/bin/bash
# LoRA training on the Mac (Round 12). Needs finetune/out/data from make_data.py.
#   bash finetune/train.sh <run_name> <iters> [extra mlx_lm.lora flags]
# Close other apps and stop Ollama first: the run uses about 10 GB of memory.
set -euo pipefail
cd "$(dirname "$0")/.."
RUN="$1"; ITERS="$2"; shift 2
ollama stop gemma4:e2b-it-qat >/dev/null 2>&1 || true
mkdir -p "finetune/out/runs/$RUN"
finetune/.venv/bin/mlx_lm.lora --config finetune/lora.yaml --iters "$ITERS" \
    --adapter-path "finetune/out/runs/$RUN" "$@" 2>&1 | tee "finetune/out/runs/$RUN/log.txt"
