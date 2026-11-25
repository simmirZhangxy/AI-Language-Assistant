FROM python:3.13-slim-bookworm

# libdm_device.so needs libusb_init_context (libusb >= 1.0.27).
# Bookworm only ships 1.0.26.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        pkg-config \
    && curl -fsSL -o /tmp/libusb.tar.bz2 \
        https://github.com/libusb/libusb/releases/download/v1.0.28/libusb-1.0.28.tar.bz2 \
    && tar -xjf /tmp/libusb.tar.bz2 -C /tmp \
    && cd /tmp/libusb-1.0.28 \
    && ./configure --prefix=/usr/local --disable-udev \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig \
    && cd / \
    && rm -rf /tmp/libusb-1.0.28 /tmp/libusb.tar.bz2 \
    && apt-get purge -y build-essential pkg-config curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/usr/local/lib

WORKDIR /app
# Same tree as on the board: run_j4310_demo.py, python/, vendor/, requirements.txt
COPY . .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir vendor/wheels/dmcan_sdk-1.0.4-py3-none-any.whl

# SDK 1.0.4 loads /app/dlls/libdm_device.so (same protocol as the Windows tool).
ENV PYTHONUNBUFFERED=1

CMD ["sleep", "infinity"]
