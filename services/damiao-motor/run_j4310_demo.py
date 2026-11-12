#!/usr/bin/env python3
"""Minimal MIT demo for DM-J4310-2EC (48V) over DM-USB2FDCAN dual (34b7:6632).

Reads configuration from the environment (see .env.example). Vendor layout:
  vendor/lib/linux-aarch64/libdmcan.so
  vendor/wheels/dmcan_sdk-2.1.1-py3-none-any.whl
  vendor/python/damiao.py
"""
from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
LIB = VENDOR / "lib" / "linux-aarch64" / "libdmcan.so"

os.environ.setdefault("DMCAN_LIBRARY_PATH", str(LIB))
sys.path.insert(0, str(VENDOR / "python"))

from dmcan import dmcan_device_type  # type: ignore  # after wheel install / PYTHONPATH

from damiao import (  # noqa: E402
    Control_Mode,
    DM_Motor_Type,
    DmActData,
    Motor_Control,
    running,
)


def _env_serial() -> str:
    serial = os.environ.get("DMCAN_DEVICE_SERIAL", "").strip()
    if not serial:
        print(
            "Set DMCAN_DEVICE_SERIAL (run: python3 vendor/python/dev_sn.py)",
            file=sys.stderr,
        )
        sys.exit(1)
    return serial


def _env_device_type():
    kind = os.environ.get("DMCAN_DEVICE_TYPE", "dual").strip().lower()
    if kind in ("dual", "d", "6632", "usb2canfd_dual"):
        return dmcan_device_type.USB2CANFD_DUAL
    return dmcan_device_type.USB2CANFD


def _motor_type() -> DM_Motor_Type:
    name = os.environ.get("MOTOR_TYPE", "DM4310_48V").strip()
    try:
        return DM_Motor_Type[name]
    except KeyError:
        print(f"Unknown MOTOR_TYPE={name!r}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    can_id = int(os.environ.get("MOTOR_CAN_ID", "0x01"), 0)
    mst_id = int(os.environ.get("MOTOR_MST_ID", "0x11"), 0)
    mit_tau = float(os.environ.get("DEMO_MIT_TAU", "0.1"))
    loop_period = float(os.environ.get("DEMO_LOOP_PERIOD_S", "0.01"))

    if not LIB.is_file():
        print(f"Missing {LIB} — run ../../../scripts/download-damiao-sdk.sh", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, lambda s, f: running.clear())

    init = [
        DmActData(
            motorType=_motor_type(),
            mode=Control_Mode.MIT_MODE,
            can_id=can_id,
            mst_id=mst_id,
        )
    ]

    # Arbitration 1 Mbps, CAN FD data 5 Mbps (motor bus must be set to 5M via official tool).
    with Motor_Control(
        1_000_000,
        5_000_000,
        _env_serial(),
        init,
        device_type=_env_device_type(),
    ) as control:
        print(
            f"MIT demo: can_id=0x{can_id:02x} tau={mit_tau} (Ctrl+C to stop)",
            flush=True,
        )
        while running.is_set():
            t0 = time.perf_counter()
            control.control_mit(control.getMotor(can_id), 0.0, 0.0, 0.0, 0.0, mit_tau)
            elapsed = time.perf_counter() - t0
            time.sleep(max(0.0, loop_period - elapsed))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    print("Exited safely.")
