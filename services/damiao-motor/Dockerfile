FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
COPY vendor/wheels/dmcan_sdk-2.1.1-py3-none-any.whl vendor/wheels/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir vendor/wheels/dmcan_sdk-2.1.1-py3-none-any.whl

COPY vendor/lib/linux-aarch64/libdmcan.so vendor/lib/linux-aarch64/
COPY vendor/python/ vendor/python/
COPY run_j4310_demo.py .

ENV DMCAN_LIBRARY_PATH=/app/vendor/lib/linux-aarch64/libdmcan.so \
    PYTHONUNBUFFERED=1

CMD ["python3", "run_j4310_demo.py"]
