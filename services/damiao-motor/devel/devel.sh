#!/usr/bin/env bash
# Optional: list USB2FDCAN serial without host pip.
# Motor container: cd devel && docker compose up -d --build
set -euo pipefail

SERVICE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

docker run --rm -it --privileged \
	-v /dev/bus/usb:/dev/bus/usb \
	-v "${SERVICE_ROOT}/vendor/python:/app" -w /app \
	python:3.13-slim-bookworm \
	bash -c "apt-get update -qq && apt-get install -y -qq libusb-1.0-0 \
		&& pip install -q pyusb && python3 dev_sn.py"
