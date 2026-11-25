#!/usr/bin/env bash
# Populate services/damiao-motor/vendor for aarch64 (clone-and-run on VENTUNO Q).
# Usage from repo root: ./scripts/download-damiao-sdk.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="${ROOT}/services/damiao-motor/vendor"
LIB_DST="${ROOT}/services/damiao-motor/dlls/libdm_device.so"
WHEEL_DST="${VENDOR}/wheels/dmcan_sdk-1.0.4-py3-none-any.whl"
PY_DST="${VENDOR}/python"

need_fetch=0
for f in "$LIB_DST" "$WHEEL_DST" "${PY_DST}/damiao.py" "${PY_DST}/dev_sn.py"; do
  [[ -f "$f" ]] || need_fetch=1
done
if [[ "$need_fetch" -eq 0 ]]; then
  echo "OK: damiao motor vendor bundle already present."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

clone_repo() {
  local url="$1"
  local dest="$2"
  if [[ -d "$dest/.git" ]]; then
    git -C "$dest" pull --ff-only
  else
    git clone --depth 1 "$url" "$dest"
  fi
}

echo "Fetching dm-device-sdk (shallow)..."
clone_repo "https://gitee.com/kit-miao/dm-device-sdk.git" "${TMP}/dm-device-sdk"
echo "Fetching motor-sdk (shallow)..."
clone_repo "https://gitee.com/kit-miao/motor-sdk.git" "${TMP}/motor-sdk"

mkdir -p "$(dirname "$LIB_DST")" "${VENDOR}/wheels" "$PY_DST"

cp "${TMP}/dm-device-sdk/C&C++/lib/v1.1.0/linux/arm64/libdm_device.so" "$LIB_DST"
cp "${TMP}/dm-device-sdk/Python/pack/dmcan_sdk-1.0.4-py3-none-any.whl" "$WHEEL_DST"
# damiao.py 在仓库里有本地修改（先开通道再设波特率）。缺文件时才从上游补。
if [[ ! -f "${PY_DST}/damiao.py" ]]; then
  cp "${TMP}/motor-sdk/Python例程/u2canfd/damiao.py" "${PY_DST}/damiao.py"
fi
cp "${TMP}/motor-sdk/Python例程/u2canfd/dev_sn.py" "${PY_DST}/dev_sn.py"

echo "Installed vendor bundle under ${VENDOR}"
