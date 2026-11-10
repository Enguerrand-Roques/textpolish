"""Merge an MLX LoRA adapter into Google's unquantized QAT weights.

The adapter is trained on the 4-bit MLX build (it fits in 16 GB), but merged
into the bf16 weights the official Q4_0 GGUF comes from, so the result goes
through the same conversion as the model TextPolish uses today.

    finetune/.venv/bin/python finetune/merge_lora.py <base_dir> <adapter_dir> <out_dir>
"""

import json
import os
import shutil
import sys

import torch
from safetensors import safe_open
from safetensors.torch import save_file


def merge(base_dir: str, adapter_dir: str, out_dir: str) -> int:
    with open(os.path.join(adapter_dir, "adapter_config.json")) as f:
        scale = json.load(f)["lora_parameters"]["scale"]
    adapter = safe_open(os.path.join(adapter_dir, "adapters.safetensors"), "pt")
    # "language_model.model.layers.3.mlp.up_proj.lora_a" -> "model.language_model.layers.3.mlp.up_proj.weight"
    pairs = {}
    for key in adapter.keys():
        module, part = key.rsplit(".", 1)
        target = "model." + module.replace("language_model.model.", "language_model.", 1) + ".weight"
        pairs.setdefault(target, {})[part] = adapter.get_tensor(key).float()

    base = safe_open(os.path.join(base_dir, "model.safetensors"), "pt")
    tensors, merged = {}, 0
    for key in base.keys():
        weight = base.get_tensor(key)
        if key in pairs:
            a, b = pairs[key]["lora_a"], pairs[key]["lora_b"]  # (in, r), (r, out)
            delta = scale * (a @ b).T                          # (out, in), as the weight
            weight = (weight.float() + delta).to(weight.dtype)
            merged += 1
        tensors[key] = weight
    missing = set(pairs) - set(tensors)
    if missing:
        raise SystemExit(f"adapter keys not found in the base: {sorted(missing)[:3]}")

    os.makedirs(out_dir, exist_ok=True)
    save_file(tensors, os.path.join(out_dir, "model.safetensors"), metadata={"format": "pt"})
    for name in os.listdir(base_dir):
        if name.endswith((".json", ".jinja")) and name != "model.safetensors.index.json":
            shutil.copy(os.path.join(base_dir, name), out_dir)
    return merged


if __name__ == "__main__":
    print(f"{merge(*sys.argv[1:4])} weights merged")
