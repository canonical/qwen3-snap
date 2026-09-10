SHELL := /bin/bash

# Always run `hf` via pipx to avoid relying on local `hf` installations.
hf := pipx run --spec "huggingface_hub[cli]" hf

SNAP_NAME ?= qwen3
ENGINE ?= cpu

MEDIATEK_MODEL_BASE_URL := https://mediatek-aiot.s3.ap-southeast-1.amazonaws.com/aiot/download/iot-ai-hub/model-zoo/gai/genio-360-360p-420-520-720
# Snap-safe component-name stems for each MediaTek model size (dots aren't
# allowed in snap/component names, so sizes like "1.7b" become "1-7b").
MEDIATEK_MODEL_SIZES := 0-6b 1-7b 4b 8b
ifneq ($(filter aarch64 arm64,$(shell uname -m)),) # Only include MediaTek model targets on arm64 systems
MEDIATEK_MODEL_TARGETS := $(addsuffix -mediatek,$(addprefix download-model-,$(MEDIATEK_MODEL_SIZES)))
else
MEDIATEK_MODEL_TARGETS :=
endif

.PHONY: all help init build install upload smoke-test install-deps init-submodules download-models download-model-8b download-model-%-mediatek

all: help

#
# Main targets
#

help: ## Show this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Targets:"
	@# List all targets with descriptions (lines starting with '##'):
	@grep -E '^[a-zA-Z0-9_-]+:.*## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-11s %s\n", $$1, $$2}'

init: init-submodules install-deps download-models ## Initialize the build environment (dependencies, model weights, submodules, etc.)

build: ## Build the snap
	./dev/build.sh

install: ## Install the snap
	./dev/install.sh

upload: ## Upload the snap
	./dev/upload.sh

smoke-test: ## Run smoke tests (override with SNAP_NAME=... ENGINE=...)
	sudo ./dev/smoke-test.sh $(SNAP_NAME) $(ENGINE)

#
# Supporting targets
#

install-deps:
	@echo "Installing dependencies..."
	@# Ensure pipx is available for running the hf CLI.
	@command -v pipx >/dev/null 2>&1 || { \
		sudo apt-get update; \
		sudo apt-get install -y pipx; \
	}
	@command -v bsdtar >/dev/null 2>&1 || { \
		sudo apt-get update; \
		sudo apt-get install -y libarchive-tools; \
	}


init-submodules:
	@echo "Initializing submodules..."
	@if git submodule status | grep -q '^-'; then \
		git submodule update --init; \
	fi

download-models: download-model-8b $(MEDIATEK_MODEL_TARGETS)

download-model-8b:
	@echo "Downloading Qwen3-8B-Q4_K_M model weights..."
	$(hf) download unsloth/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf \
		--local-dir components/model-8b-q4-k-m-gguf/

# Downloads a MediaTek NPU-optimized Qwen3 model package. The stem (e.g.
# "1-7b") is the snap-safe component name; MediaTek's own zip/path naming
# uses dots instead of hyphens (e.g. "1.7b"), recovered via $(subst -,.,$*).
download-model-%-mediatek:
	@echo "Downloading MediaTek NPU-optimized Qwen3-$(subst -,.,$*) model weights..."
	rm -rf components/model-$*-mediatek
	mkdir -p components/model-$*-mediatek
	set -o pipefail && curl -L "$(MEDIATEK_MODEL_BASE_URL)/qwen3-$(subst -,.,$*).zip" \
		| bsdtar -xf - -C components/model-$*-mediatek --strip-components=1 \
			'qwen3-$(subst -,.,$*)/2048c/*' 'qwen3-$(subst -,.,$*)/tokenizer/*' 'qwen3-$(subst -,.,$*)/scripts/config-yocto_np8-qwen3-$(subst -,.,$*)*.yaml'
	# Swap MediaTek's baked-in Yocto rootfs path for the $$SNAP_COMPONENT_DIR
	# placeholder that engines/mediatek-npu/server substitutes at runtime.
	sed 's#/usr/share/llm/qwen3-$(subst -,.,$*)#$$SNAP_COMPONENT_DIR#g' \
		components/model-$*-mediatek/scripts/config-yocto_np8-qwen3-$(subst -,.,$*)*.yaml \
		> components/model-$*-mediatek/config.yaml
	rm -rf components/model-$*-mediatek/scripts
