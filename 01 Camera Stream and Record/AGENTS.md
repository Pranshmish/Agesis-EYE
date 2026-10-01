# Stage 01: ESP32-CAM Stream and Record Rules

## Strict Workflow Rules
1. **NO ARDUINO IDE**: Do not use, recommend, or require Arduino IDE. All device operations (serial monitoring, IP discovery, firmware flashing via `arduino-cli` / `esptool`, stream reading, and latency testing) MUST be executed purely through Python scripts and CLI utilities.
2. **Serial & IP Discovery**: Use `serial_monitor.py` for automated serial connection and IP detection. Discovered configuration is persisted in `camera_config.json`.
3. **Power Supply**: Power the ESP32-CAM from a dedicated, stable 5V supply (minimum 1A, 2A recommended). USB FTDI power only works reliably at 10MHz xclk with QVGA.

## Camera Firmware Settings (Mandatory)
- `xclk_freq_hz = 10000000` (10 MHz) — 20MHz causes brownout crash loops on USB power
- `frame_size = FRAMESIZE_QVGA` (320×240) — best FPS/bandwidth tradeoff for WiFi
- `jpeg_quality = 15` — lower CPU and power draw, don't go below 12
- `grab_mode = CAMERA_GRAB_LATEST` with PSRAM, `CAMERA_GRAB_WHEN_EMPTY` without
- `fb_count = 2` with PSRAM, `1` without
- Brownout detector: DISABLED (`WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0)`)
- WiFi sleep: DISABLED (`WiFi.setSleep(false)`)
- TX power: `WIFI_POWER_17dBm`

## Python Recorder Rules
- **NEVER use `cv2.VideoCapture(url)`** — GStreamer backend is unreliable for MJPEG over WiFi
- **NEVER use `urllib.request.urlopen().read()`** — returns `None` on disconnect and crashes
- **ALWAYS use `requests.get(stream=True)` + `iter_content()`** for HTTP stream reading
- **ALWAYS use a dedicated VideoWriter thread** — disk I/O must not block stream reading
- **ALWAYS implement auto-reconnect** — ESP32 reboots and WiFi drops are inevitable

## Physical Placement
- Mount camera in its final deployment turret position before capturing dataset video
- Different camera height or angle means a different data distribution

## Recording
- Record raw MJPEG video files using `record_stream.py` across varied lighting, backgrounds, and negative scenes
- Target: 8+ avg FPS sustained over 5+ minutes
