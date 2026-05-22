#!/bin/bash
# Download model weights for local development
set -euo pipefail

DEST="components/model-qwen3-q4km"
mkdir -p "$DEST"

echo "Downloading Qwen3-0.6B-Q4_K_M.gguf..."
curl -L -o "$DEST/Qwen3-0.6B-Q4_K_M.gguf" \
  "https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"

echo "Done."
