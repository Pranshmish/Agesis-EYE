# ESP32-CAM Tactical Firmware & Dual-Mode Streamer (Agesis EYE)

High-performance firmware for the **AI-Thinker ESP32-CAM** integrating OV2640 camera capture, dual SG90 pan-tilt servo actuation, and laser targeting with **Dual-Mode Video Streaming** (WiFi MJPEG + USB Serial).

---

## ⚡ 1-Click Direct Flash (Zero Arduino IDE Needed)

A pre-configured compiler & uploader (`arduino-cli`) is included in `firmware/tools/`.

### Method A: One-Click Batch Script
1. Connect your ESP32-CAM via USB programmer module or FTDI adapter.
2. Put board in bootloader mode:
   - **Connect GPIO 0 to GND**
   - **Press the RST button once**
3. Run from terminal or double-click:
   ```cmd
   flash_cam.bat COM14
   ```
   *(Replace `COM14` with your target COM port, or omit to default to COM14)*
4. Once flashed: **Remove GPIO 0 from GND** and press **RST** once.

### Method B: Python Auto-Flasher & IP Discovery
```bash
python firmware/flash_camera.py
```
This automatically finds the connected COM port, compiles, flashes, and launches the serial monitor to read the stream IP.

---

## 🎥 Dual Streaming Modes

### Mode 1: USB Serial Streaming (No WiFi Required!)
- Stream JPEG frames directly through the USB cable.
- In the Web Ground Station (`Controls Card`), select **`ESP-CAM USB`** or enter `usb`.
- The backend connects over USB Serial and extracts frames in real time.

### Mode 2: WiFi MJPEG Stream (Ultra-Low Latency)
- **Home WiFi / Hotspot**: Connects to the credentials defined in `esp32_cam_stream.ino`:
  ```cpp
  const char* ssid     = "Pranshul";
  const char* password = "Pranshul@007";
  ```
  Stream URL: `http://<ESP32-IP>:81/stream`
- **SoftAP Direct Connection (Fallback)**: If WiFi fails to connect, the ESP32 automatically creates a tactical access point:
  - **SSID**: `ESP32-CAM-TURRET`
  - **Password**: `12345678`
  - **Default IP**: `http://192.168.4.1:81/stream` (Select **`ESP-CAM AP`** in UI)

---

## 🔌 Hardware Pinout (AI-Thinker ESP32-CAM)

| Joint / Component | GPIO Pin | Configuration | Notes |
| :--- | :--- | :--- | :--- |
| **Pan Servo (Azimuth)** | **GPIO 12** | LEDC 50Hz PWM (14-Bit) | Base rotation |
| **Tilt Servo (Elevation)**| **GPIO 13** | LEDC 50Hz PWM (14-Bit) | Pitch arm |
| **Laser Emitter** | **GPIO 14** | Digital OUT (Active HIGH) | Targeting laser diode |
| **Flashlight LED** | **GPIO 4** | Digital OUT (Active HIGH) | Onboard high-power illumination |
| **Camera Sensor** | Standard | OV2640 D0-D7, VSYNC, HREF, PCLK | AI-Thinker Pinout |

### 🛡️ 5V 2A Brownout & Slew Protection
- Built-in software slew-rate acceleration limiter prevents SG90 motor current spikes from collapsing the 5V rail.
- Brownout detector disabled via RTC controller registers to ensure rock-solid stability.

