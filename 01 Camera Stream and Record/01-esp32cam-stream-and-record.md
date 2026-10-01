---
name: esp32cam-stream-and-record
description: Battle-tested ESP32-CAM MJPEG streaming and recording workflow for Agesis EYE dataset collection
---

# ESP32-CAM: Stream and Record

## Goal
A stable, sustained MJPEG video stream from ESP32-CAM, recorded to disk as raw video for frame extraction and dataset building.

## Firmware Settings (Proven Stable)

| Parameter | Value | Why |
|---|---|---|
| `xclk_freq_hz` | **10 MHz** | 20MHz causes brownout reboots on USB power |
| `frame_size` | `FRAMESIZE_QVGA` (320×240) | Best FPS/bandwidth for WiFi |
| `jpeg_quality` | **15** | Low CPU/power, smaller frames |
| `fb_count` | 2 (PSRAM) / 1 (DRAM) | Double buffer prevents tearing |
| `grab_mode` | `GRAB_LATEST` (PSRAM) / `WHEN_EMPTY` (DRAM) | Newest frame always |
| `WiFi.setSleep` | `false` | No power-save lag |
| Brownout detector | Disabled | Prevents random reboots |

## Python Recorder Architecture
- `requests.get(stream=True)` + `iter_content(4096)` — robust HTTP chunked decoding
- Dedicated `VideoWriterThread` — disk I/O never blocks reading
- Auto-reconnect on disconnect with 3s backoff
- JPEG boundary scanning: `\xff\xd8...\xff\xd9`

## Browser Viewing
- `http://<ip>:81/` — HTML page with embedded live stream
- `http://<ip>:81/stream` — Raw MJPEG (for Python/curl)
- `http://<ip>:81/jpg` — Single JPEG snapshot

## Recording Sessions Plan
3–5 minutes each with variety: daylight, tube light, dim, backlit, plain wall, cluttered room, near/mid/far target, negative (no target).

## Done When
- 8+ avg FPS sustained over 5+ minutes
- 6–10 sessions recorded under varied conditions
