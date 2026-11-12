#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

DEVEL_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE=(docker compose -f "${DEVEL_DIR}/compose.yaml")

run() {
	"${COMPOSE[@]}" run --rm zephyr bash -lc "$1"
}

cmd_init() {
	echo "==> Building devel image"
	"${COMPOSE[@]}" build
	run '
		set -e
		if [ ! -d .west ]; then
			west init -l . --mf west.yaml
		fi
		west update
		export ZEPHYR_BASE="$(west list zephyr -f "{abspath}")"
		west packages pip --install
		west sdk install --gnu-toolchains arm-zephyr-eabi
		if git -C "$ZEPHYR_BASE" apply --reverse --check patches/0001-udc-rpi-pico-audio-fixes.patch 2>/dev/null; then
			echo "Zephyr UAC patch already applied"
		else
			git -C "$ZEPHYR_BASE" apply patches/0001-udc-rpi-pico-audio-fixes.patch
		fi
		echo "Init done. ZEPHYR_BASE=$ZEPHYR_BASE"
	'
}

cmd_build() {
	"${COMPOSE[@]}" build -q zephyr 2>/dev/null || "${COMPOSE[@]}" build
	run '
		set -e
		test -d .west || { echo "Run ./devel/devel.sh init first"; exit 1; }
		export ZEPHYR_BASE="$(west list zephyr -f "{abspath}")"
		west build -p always -b rpi_pico2/rp2350a/m33 .
		echo "Firmware: build/zephyr/zephyr.uf2"
	'
}

cmd_shell() {
	"${COMPOSE[@]}" run --rm zephyr bash
}

usage() {
	echo "Usage: $0 {init|build|shell}"
	echo "  init   first-time west update, SDK, UAC patch"
	echo "  build  compile zephyr.uf2"
	echo "  shell  interactive shell in devel container"
}

case "${1:-}" in
init)  cmd_init ;;
build) cmd_build ;;
shell) cmd_shell ;;
*)     usage; exit 1 ;;
esac
