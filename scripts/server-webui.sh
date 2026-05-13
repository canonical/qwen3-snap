#!/bin/bash
set -euo pipefail

port="$(modelctl get webui.http.port)"
host="$(modelctl get webui.http.host)"

# Qwen 3 0.6B is a text-only model (no multimodal projector)
capabilities="text, text:markdown"

exec modelctl serve-webui "$SNAP/webui" --port "$port" --host "$host" --capabilities "$capabilities"
