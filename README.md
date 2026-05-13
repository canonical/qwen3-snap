# Qwen 3 0.6B snap

This snap installs a hardware-optimized engine for inference with
[Qwen 3 0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), Alibaba's
compact instruction-tuned text model, in the Q4_K_M GGUF quantization
re-hosted by Unsloth.

## Resources

📚 **[Documentation](https://documentation.ubuntu.com/inference-snaps/)**, learn how to use inference snaps

💬 **[Discussions](https://github.com/canonical/inference-snaps/discussions)**, ask questions and share ideas

🐛 **[Issues](https://github.com/canonical/inference-snaps/issues)**, report bugs and request features

## Build and install from source

Clone this repo with its submodules:
```shell
git clone --recurse-submodules https://github.com/canonical/qwen3-snap
```

Prepare the required model file by running `download-models.sh` (it
fetches the GGUF and verifies its SHA256).

Build the snap and its components:
```shell
snapcraft pack -v
```

Install the result (snap + components):
```shell
sudo snap install ./qwen3_*.snap ./qwen3+*.comp --dangerous
```

Connect interfaces and select an engine:
```shell
sudo snap connect qwen3:hardware-observe
sudo snap connect qwen3:opengl
sudo snap connect qwen3:network-bind
sudo qwen3 use-engine --auto --assume-yes --verbose
```

The OpenAI-compatible HTTP API listens on `http://127.0.0.1:8652/v1`
and the WebUI on `http://127.0.0.1:8653`.

Refer to the `./dev` submodule for additional development tools.
