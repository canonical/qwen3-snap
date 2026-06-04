# Qwen 3 snap
[![qwen3](https://snapcraft.io/qwen3/badge.svg)](https://snapcraft.io/qwen3)

This snap installs a hardware-optimized engine for inference with
[Qwen 3](https://qwen.ai/blog?id=qwen3).

## Resources

📚 **[Documentation](https://documentation.ubuntu.com/inference-snaps/)**, learn how to use inference snaps

💬 **[Discussions](https://github.com/canonical/inference-snaps/discussions)**, ask questions and share ideas

🐛 **[Issues](https://github.com/canonical/inference-snaps/issues)**, report bugs and request features

## Build and install from source

Clone this repo with its submodules:
```shell
git clone --recurse-submodules https://github.com/canonical/qwen3-snap
```

Prepare the required models by running `download-models.sh`.

Build the snap and its component:
```shell
snapcraft pack -v
```

Refer to the `./dev` directory for additional development tools.
