#!/bin/bash
# Turn bf16 safetensors (Google's QAT weights, with or without a merged
# adapter) into a Q4_0 GGUF and an Ollama model, the same way as the
# gemma4:e2b-it-qat that TextPolish uses today.
#   bash finetune/export.sh <safetensors_dir> <ollama_name>
set -euo pipefail
cd "$(dirname "$0")/out"
SRC="$1"; NAME="$2"
../.venv/bin/python llama.cpp/convert_hf_to_gguf.py "$SRC" --outtype bf16 --outfile "$NAME-bf16.gguf" 2>&1 | grep -E "ERROR|successfully"
llama-quantize "$NAME-bf16.gguf" "$NAME-q4_0.gguf" Q4_0 2>&1 | grep -E "error|total time"
rm "$NAME-bf16.gguf"
sed "s|^FROM .*|FROM ./$NAME-q4_0.gguf|" ../Modelfile > "Modelfile.$NAME"
ollama create "$NAME" -f "Modelfile.$NAME" 2>&1 | tail -1 | tr -d '\033'
