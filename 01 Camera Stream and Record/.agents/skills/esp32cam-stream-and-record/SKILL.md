---
name: esp32cam-stream-and-record
description: Battle-tested ESP32-CAM MJPEG streaming and recording workflow for Agesis EYE dataset collection. Covers firmware config, Python recorder, power/WiFi stability, and browser viewing.
---

# ESP32-CAM: Stream and Record

## Goal
A stable, sustained MJPEG video stream from ESP32-CAM, recorded to disk as raw video for frame extraction and dataset building.

## Firmware Settings (Proven Stable)

These settings were tested and tuned to eliminate brownout reboots and maximize sustained FPS on USB power:

| Parameter | Value | Why |
|---|---|---|
| `xclk_freq_hz` | **10 MHz** | 20MHz causes brownout reboots on USB power |
| `frame_size` | `FRAMESIZE_QVGA` (320×240) | Best FPS/bandwidth tradeoff for WiFi streaming |
| `jpeg_quality` | **15** | Lower CPU/power draw, smaller frames. Don't go below 12. |
| `fb_count` | 2 (with PSRAM) | Double buffer prevents tearing |
| `grab_mode` | `CAMERA_GRAB_LATEST` (PSRAM), `WHEN_EMPTY` (DRAM) | Always show newest frame |
| `WiFi.setSleep` | `false` | Prevents WiFi power-save lag |
| `WiFi.setTxPower` | `WIFI_POWER_17dBm` | Stable without drawing too much current |
| Brownout detector | **Disabled** | `WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0)` — prevents random reboots |
| `max_open_sockets` | 4 | Allows browser + Python + snapshot simultaneously |
| `send_wait_timeout` | 5s | Tolerates WiFi jitter without hanging |

### DO NOT
- Use `xclk_freq_hz = 20000000` on USB power (causes crash loops)
- Use `jpeg_quality < 12` (massive frames choke WiFi)
- Use `cv2.VideoCapture(url)` (GStreamer backend is unreliable for MJPEG over WiFi)
- Use `max_open_sockets > 5` (exhausts ESP32 heap)
- Use `CAMERA_GRAB_LATEST` without PSRAM (causes FB-OVF)

## Python Recorder (`record_stream.py`)

### Architecture
- **StreamReader thread**: `requests.get(stream=True)` + `iter_content(4096)` for robust HTTP chunked decoding
- **VideoWriterThread**: Dedicated thread for disk I/O, never blocks stream reading
- **Auto-reconnect**: If ESP32 reboots or WiFi drops, reader reconnects with 3s backoff
- **JPEG extraction**: Raw `\xff\xd8...\xff\xd9` boundary scanning from HTTP chunks

### DO NOT
- Use `urllib.request.urlopen().read()` — returns `None` on disconnect and crashes the reader thread
- Use `cv2.VideoCapture(url)` — GStreamer MJPEG parsing is fragile and adds 2-3s latency
- Do `VideoWriter.write()` in the main thread — disk I/O blocks and drops frames
- Set queue `maxsize < 200` — WiFi bursts can deliver 20+ frames at once

### Usage
```bash
python record_stream.py --tag daylight              # Manual stop with 'q'
python record_stream.py --tag negative --duration 60 # Auto-stop after 60s
python record_stream.py --ip 192.168.1.100           # Override IP
```

## Browser Viewing

The firmware serves a web page at `http://<esp-ip>:81/` with an embedded live stream.

| URL | Function |
|---|---|
| `http://<ip>:81/` | HTML page with embedded live stream |
| `http://<ip>:81/stream` | Raw MJPEG stream (for Python/curl) |
| `http://<ip>:81/jpg` | Single JPEG snapshot |

**Important**: Close browser tabs before running `record_stream.py` — each viewer uses a socket and ESP32 only has 4.

## Power Supply Rules
1. **USB FTDI power is marginal**. Works for QVGA at 10MHz xclk but may brownout at higher resolutions.
2. For VGA (640×480) or higher, use a **dedicated 5V/2A supply** with short, thick wires.
3. If you see repeated `PORT 81` messages in serial monitor, the ESP32 is **crash-looping** — this is always a power issue.

## WiFi Rules
1. Use **2.4 GHz** (not 5 GHz).
2. Keep ESP32 within **5 meters** of the router/hotspot.
3. Avoid channels with interference — check with WiFi analyzer app.
4. The firmware has a **WiFi watchdog** in `loop()` — auto-reconnects and restarts if WiFi drops.
5. Mobile hotspot (phone tethering) has high jitter (9ms–1500ms ping). Best to use a proper router.

## Recording Sessions Plan
Record several sessions, 3–5 minutes each, with variety:
- **Lighting**: daylight, tube light, dim, backlit from a window
- **Backgrounds**: plain wall, cluttered room, dark furniture
- **Target**: different distances (near, mid, far), sizes, partly hidden, swinging, held in hand
- **Negative**: NO target, but black objects, shadows, wires, chairs, bags (prevents false positives)

## Tools
- `flash_camera.py` — Compile and flash firmware via `arduino-cli`
- `serial_monitor.py` — Read ESP32 serial output and auto-discover IP
- `measure_latency.py` — Benchmark stream FPS and latency

## Done When
- Stream runs for **5+ minutes** at **8+ avg FPS** with no crash
- At least 6–10 sessions recorded under varied conditions
- Browser can view stream at `http://<ip>:81/` while Python is NOT recording
