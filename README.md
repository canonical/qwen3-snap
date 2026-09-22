# Qwen 3 inference snap
[![qwen3](https://snapcraft.io/qwen3/badge.svg)](https://snapcraft.io/qwen3)

Qwen 3 is a large language model (LLM) developed by Alibaba. It is designed for various natural language processing tasks, including text generation, summarization, and question answering.

Use this snap to quickly install an optimized environment for local inference with Qwen 3.

The snap includes the following hardware-optimized inference engines:

* cpu: Optimized for x64 and ARM (armv8, armv9) CPUs
* nvidia-gpu: CUDA-enabled GPU acceleration
* amd-gpu: ROCm-enabled GPU acceleration for AMD GPUs
* mediatek-npu: Optimized for MediaTek Genio NPUs

The most suitable engine is automatically selected based on the available hardware.

#### Install
```shell
sudo snap install qwen3
```

#### Run
```shell
qwen3
```

> [!TIP]
> Some accelerators require extra [drivers](https://documentation.ubuntu.com/inference-snaps/how-to/setup/drivers/) to be usable with this snap.

## Resources

📚 **[Documentation](https://documentation.ubuntu.com/inference-snaps/)**, learn how to use inference snaps

💬 **[Discussions](https://github.com/canonical/inference-snaps/discussions)**, ask questions and share ideas

🐛 **[Issues](https://github.com/canonical/inference-snaps/issues)**, report bugs and request features

## Build and install from source

Clone the repo:
```shell
git clone https://github.com/canonical/qwen3-snap
cd qwen3-snap
```

Initialize the development environment:
```shell
make init
```

Build and install snap:
```shell
make build
make install
```
