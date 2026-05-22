# qwen3-snap

Inference snap for [Qwen3 0.6B](https://huggingface.co/unsloth/Qwen3-0.6B-GGUF) (Q4_K_M quantization).

## Getting started

```bash
git clone --recurse-submodules https://github.com/canonical/qwen3-snap
cd qwen3-snap
```

## Download model weights

```bash
./download-models.sh
```

## Build

```bash
snapcraft
```

## Install

```bash
sudo snap install qwen3_*.snap --dangerous
sudo snap install qwen3_model-qwen3-q4km_*.comp --dangerous
sudo snap install qwen3_llamacpp_*.comp --dangerous
```

## Usage

```bash
qwen3 --help
sudo snap start qwen3.server
```

API endpoint: `http://127.0.0.1:8080/v1`
WebUI: `http://127.0.0.1:8081`
