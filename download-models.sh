#!/bin/bash -eu
# Developer convenience: download model weights into the model component
# directory. These files are git-ignored and fetched at build time.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/components/model-0-6b-q4-k-m-gguf"
MODEL_URL="https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
MODEL_FILE="$MODEL_DIR/Qwen3-0.6B-Q4_K_M.gguf"

mkdir -p "$MODEL_DIR"
echo "Downloading Qwen3-0.6B-Q4_K_M.gguf ..."
curl -L --fail --output "$MODEL_FILE" "$MODEL_URL"
echo "Saved to $MODEL_FILE"
