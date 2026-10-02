# ESP32-CAM Firmware

This folder contains the firmware sketch for the ESP32-CAM video streaming transmitter.

---

## ⚡ Quick Upload (Arduino IDE)

1. Open **`esp32_cam_stream/esp32_cam_stream.ino`** in the Arduino IDE.
2. Update your Wi-Fi SSID and Password in the sketch:
   ```cpp
   const char* ssid = "YOUR_WIFI_HOTSPOT";
   const char* password = "YOUR_PASSWORD";
   ```
3. Under **Tools** menu, select:
   - **Board**: `AI Thinker ESP32-CAM`
   - **CPU Frequency**: `240MHz (WiFi/BT)`
   - **Flash Frequency**: `80MHz`
   - **Flash Mode**: `QIO`
   - **Partition Scheme**: `Huge APP (3MB No OTA/1MB SPIFFS)`
4. Connect GPIO 0 to GND, plug in via USB-UART adapter, and click **Upload**.
5. Once uploaded, disconnect GPIO 0 from GND, press **RESET**, and open the Serial Monitor (115200 baud) to view the stream URL:
   ```
   Camera Ready! Stream available at: http://10.96.117.1:81/stream
   ```
