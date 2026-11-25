"""USB2FDCAN 双路 + J4310 的已验证总线配置。

上位机（DM调试工具）里这台电机是经典 CAN 2.0、1 Mbps，
CAN ID 0x01，Master ID 0x10。适配器固件配合 SDK 1.0.4
（dlls/libdm_device.so）。只接了一组 H/L，程序在两路上都发。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
LIB = ROOT / "dlls" / "libdm_device.so"

sys.path.insert(0, str(VENDOR / "python"))

from dmcan import dmcan_device_type  # type: ignore  # noqa: E402

from damiao import Control_Mode, DM_Motor_Type, DmActData, Motor_Control  # noqa: E402

BAUD = 1_000_000


def _require_lib() -> None:
    if not LIB.is_file():
        print(f"Missing {LIB} — run scripts/download-damiao-sdk.sh", file=sys.stderr)
        sys.exit(1)


def serial() -> str:
    value = os.environ.get("DMCAN_DEVICE_SERIAL", "").strip()
    if not value:
        print("Set DMCAN_DEVICE_SERIAL in .env", file=sys.stderr)
        sys.exit(1)
    return value


def device_type():
    kind = os.environ.get("DMCAN_DEVICE_TYPE", "dual").strip().lower()
    if kind in ("dual", "d", "6632", "usb2canfd_dual"):
        return dmcan_device_type.USB2CANFD_DUAL
    return dmcan_device_type.USB2CANFD


def channels() -> tuple[int, ...]:
    kind = os.environ.get("DMCAN_DEVICE_TYPE", "dual").strip().lower()
    if kind in ("dual", "d", "6632", "usb2canfd_dual"):
        return (0, 1)
    return (0,)


def motor_type() -> DM_Motor_Type:
    name = os.environ.get("MOTOR_TYPE", "DM4310_48V").strip()
    try:
        return DM_Motor_Type[name]
    except KeyError:
        print(f"Unknown MOTOR_TYPE={name!r}", file=sys.stderr)
        sys.exit(1)


def can_id() -> int:
    return int(os.environ.get("MOTOR_CAN_ID", "0x01"), 0)


def mst_id() -> int:
    return int(os.environ.get("MOTOR_MST_ID", "0x10"), 0)


def actuators(mode: Control_Mode) -> list[DmActData]:
    return [
        DmActData(
            motorType=motor_type(),
            mode=mode,
            can_id=can_id(),
            mst_id=mst_id(),
            channel=ch,
        )
        for ch in channels()
    ]


def open_control(mode: Control_Mode) -> Motor_Control:
    _require_lib()
    return Motor_Control(
        BAUD,
        BAUD,
        serial(),
        actuators(mode),
        device_type=device_type(),
        canfd=False,
        brs=False,
    )
