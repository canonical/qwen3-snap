#!/bin/bash
set -euo pipefail

# Qwen3 0.6B Q4_K_M (single-file GGUF, ~378 MiB)
wget -nv https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf \
    --directory-prefix=components/model-0-6b-q4-k-m-gguf/

# Provenance check (SHA256 verified at scaffold time)
expected_sha="ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a"
actual_sha=$(sha256sum components/model-0-6b-q4-k-m-gguf/Qwen3-0.6B-Q4_K_M.gguf | awk '{print $1}')
if [ "$expected_sha" != "$actual_sha" ]; then
    echo "ERROR: SHA256 mismatch for Qwen3-0.6B-Q4_K_M.gguf"
    echo "  expected: $expected_sha"
    echo "  actual:   $actual_sha"
    exit 1
fi
echo "Model SHA256 verified: $actual_sha"
