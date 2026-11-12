#!/usr/bin/env bash
# Download Kokoro ONNX weights for the custom kokoro_tts brick.
# Run from the repository root: ./scripts/download-kokoro-models.sh
set -euo pipefail

RELEASE="model-files-v1.0"
BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/${RELEASE}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${ROOT}/Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/bricks/kokoro_tts/container/models"

mkdir -p "${MODEL_DIR}"

download() {
  local name="$1"
  local dest="${MODEL_DIR}/${name}"
  if [[ -f "${dest}" ]]; then
    echo "OK (already present): ${dest}"
    return 0
  fi
  echo "Downloading ${name} ..."
  if command -v wget >/dev/null 2>&1; then
    wget -O "${dest}" "${BASE}/${name}"
  elif command -v curl >/dev/null 2>&1; then
    curl -fL -o "${dest}" "${BASE}/${name}"
  else
    echo "Need wget or curl to download models." >&2
    exit 1
  fi
  echo "Saved: ${dest}"
}

download "kokoro-v1.0.fp16.onnx"
download "voices-v1.0.bin"

echo "Done. Kokoro models are in: ${MODEL_DIR}"
