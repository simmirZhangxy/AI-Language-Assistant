# 达妙电机

已在 Ventuno Q 上转起来的配置：USB2FDCAN 双路、J4310、经典 CAN 2.0、1 Mbps、CAN ID `0x01`、Master ID `0x10`。通信库是 SDK 1.0.4（`dlls/libdm_device.so`）。只接一组 CAN H/L，程序在适配器的两路上都发。

```bash
cp env.example .env          # 填 DMCAN_DEVICE_SERIAL
cd devel
docker compose up -d --build
docker compose exec -it damiao-motor python3 run_vel_20.py
```

`Ctrl+C` 下使能并停转。速度在 `.env` 的 `DEMO_TARGET_VEL`（单位 rad/s）。力矩演示是 `run_j4310_demo.py`。

跑之前先在 Windows 上位机里点关闭设备，USB 只能一边占用。
