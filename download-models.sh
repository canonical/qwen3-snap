#!/bin/bash


# 8B model
wget -nv https://huggingface.co/unsloth/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf \
    --directory-prefix=components/model-8b-q4-k-m-gguf/

# 4B model    
wget -nv https://huggingface.co/unsloth/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf \
    --directory-prefix=components/model-4b-q4-k-m-gguf/
