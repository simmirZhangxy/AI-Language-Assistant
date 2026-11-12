# Damiao motor (DM-J4310 + USB2FDCAN dual)

Runnable stack for **Ubuntu on VENTUNO board** → **DM-USB2FDCAN** (`34b7:6632`) → **DM-J4310-2EC** (48V, CAN-FD **5 Mbps**).

Everything needed to run is under **`vendor/`** (committed). Optional full SDK trees go in repo-root `third_party/` (gitignored).

## Hardware

```
Ubuntu board  →  USB  →  DM-USB2FDCAN (6632)  →  CAN H/L  →  adapter + DM-J4310-2EC
```

## One-time on the board

1. **Motor bus**: set **5M** baud with Damiao PC tool (required).
2. **CAN bus terminator**: 120 Ω at the last motor when multiple nodes exist.
3. **USB permissions**:
   ```bash
   sudo cp udev/99-damiao-usb.rules /etc/udev/rules.d/99-damiao-usb.rules
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
4. **Device serial**:
   ```bash
   cd services/damiao-motor
   python3 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt vendor/wheels/dmcan_sdk-2.1.1-py3-none-any.whl
   export DMCAN_LIBRARY_PATH="$PWD/vendor/lib/linux-aarch64/libdmcan.so"
   python3 vendor/python/dev_sn.py
   ```
5. **Config**: `cp env.example .env` and set `DMCAN_DEVICE_SERIAL=...`.

## Run (native, recommended while debugging)

```bash
cd services/damiao-motor
. .venv/bin/activate
set -a && source .env && set +a
export DMCAN_LIBRARY_PATH="$PWD/vendor/lib/linux-aarch64/libdmcan.so"
python3 run_j4310_demo.py
```

Expected: motor enables (green), light MIT torque (`DEMO_MIT_TAU`, default `0.1`). **Ctrl+C** to stop.

Environment:

| Variable | Default | Meaning |
|----------|---------|---------|
| `DMCAN_DEVICE_SERIAL` | — | From `dev_sn.py` |
| `DMCAN_DEVICE_TYPE` | `dual` | Dual FDCAN adapter (`6632`) |
| `MOTOR_TYPE` | `DM4310_48V` | 48V J4310 |
| `MOTOR_CAN_ID` / `MOTOR_MST_ID` | `0x01` / `0x11` | Must match motor config |

## Run (Docker)

```bash
cd services/damiao-motor
cp env.example .env   # edit serial
docker compose up --build
```

Uses `privileged` + `/dev/bus/usb` so the container can open the adapter.

## If `vendor/` is missing after clone

From repo root:

```bash
./scripts/download-damiao-sdk.sh
```

## License / upstream

- `vendor/python/damiao.py` — from [motor-sdk](https://gitee.com/kit-miao/motor-sdk) Python u2canfd example
- `libdmcan.so` + `dmcan_sdk` wheel — from [dm-device-sdk](https://gitee.com/kit-miao/dm-device-sdk)
