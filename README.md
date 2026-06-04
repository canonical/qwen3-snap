# qwen3 inference snap

Run the [Qwen3 0.6B](https://huggingface.co/unsloth/Qwen3-0.6B-GGUF) large
language model locally with an OpenAI-compatible HTTP API and an optional
Web UI, powered by [llama.cpp](https://github.com/ggerganov/llama.cpp).

The snap ships two engines and selects one automatically based on detected
hardware:

- `cpu` — llama.cpp on CPU (amd64/arm64)
- `nvidia-gpu` — llama.cpp with CUDA backend (NVIDIA GPUs)

## Cloning

This repository uses a git submodule (`dev`). Clone recursively:

```bash
git clone --recurse-submodules https://github.com/canonical/qwen3-snap.git
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

## Building

```bash
./download-models.sh                 # fetch the GGUF weights (git-ignored)
snapcraft pack --destructive-mode
```

## Installing

```bash
sudo snap install ./qwen3_*.snap ./qwen3+*.comp --dangerous
sudo snap connect qwen3:hardware-observe
sudo snap connect qwen3:opengl
sudo snap connect qwen3:network-bind
sudo snap connect qwen3:process-control
```

## Usage

The OpenAI-compatible API listens on port `8080` and the Web UI on `8081`.

```bash
curl http://0.0.0.0:8080/v1/models
curl http://0.0.0.0:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-0.6b-q4-k-m","messages":[{"role":"user","content":"Hello!"}]}'
```

## License

Snap packaging is licensed under Apache-2.0. The Qwen3 model weights are
distributed by Alibaba Cloud under the Apache-2.0 license; see the upstream
model card for details.
