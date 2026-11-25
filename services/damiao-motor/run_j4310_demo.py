#!/usr/bin/env python3
"""MIT 力矩模式。力矩看 DEMO_MIT_TAU，默认 0.1 N·m。Ctrl+C 下使能。"""
from __future__ import annotations

import os
import signal
import time

from bus import can_id, channels, open_control
from damiao import Control_Mode, running


def main() -> None:
    mit_tau = float(os.environ.get("DEMO_MIT_TAU", "0.1"))
    loop_period = float(os.environ.get("DEMO_LOOP_PERIOD_S", "0.01"))
    motor_id = can_id()

    signal.signal(signal.SIGINT, lambda s, f: running.clear())

    with open_control(Control_Mode.MIT_MODE) as control:
        motors = [control.getMotor(ch, motor_id) for ch in channels()]
        print(
            f"MIT tau={mit_tau} N·m, CAN 2.0 1 Mbps, channels {channels()} (Ctrl+C)",
            flush=True,
        )
        while running.is_set():
            t0 = time.perf_counter()
            for motor in motors:
                control.control_mit(motor, 0.0, 0.0, 0.0, 0.0, mit_tau)
            time.sleep(max(0.0, loop_period - (time.perf_counter() - t0)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    print("Exited safely.")
