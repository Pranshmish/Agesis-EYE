#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiUdp.h>
#include "esp_http_server.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// 1. WiFi Configuration (Update credentials)
// ==========================================
const char* ssid     = "Pranshul";
const char* password = "Pranshul@007";

// Fallback Access Point credentials:
const char* ap_ssid  = "ESP32-CAM-TURRET";
const char* ap_pass  = "12345678";

// ==========================================
// 2. SG90 Servo & Hardware Pin Definitions
// ==========================================
// Pan Servo: Base azimuth (controls 360 / 180 deg)
#define PAN_SERVO_PIN      12
// Tilt Servo: Elevation axis
#define TILT_SERVO_PIN     13
// Laser Emitter Diode / Transistor Trigger Pin
#define LASER_PIN          14
// Built-in Flash LED on GPIO 4
#define FLASH_LED_PIN       4

// LEDC PWM Configuration for SG90 (50Hz = 20ms period)
#define PAN_LEDC_CH         2
#define TILT_LEDC_CH        3
#define SERVO_PWM_FREQ     50
#define SERVO_RES_BITS     14   // 14-bit: 0 to 16383 counts per 20ms

// SG90 Pulse Width Constants (microseconds)
#define SERVO_MIN_US      544   // 0 degrees
#define SERVO_MID_US     1500   // 90 degrees (Neutral)
#define SERVO_MAX_US     2400   // 180 degrees

// Set to true if Pan servo is a 360° Continuous Rotation SG90
#define SERVO_360_PAN_MODE false

// ==========================================
// 3. 5V 2A Power & Slew-Rate Safety System
// ==========================================
// Shared 5V 2A adapter protection:
// Abrupt full-speed SG90 servo acceleration can pull up to 800mA stall current per servo,
// dipping the 5V rail and causing ESP32 brownout/WiFi crashes.
// The slew-rate engine limits maximum angular velocity to ~120 deg/sec.
float targetPanAngle   = 90.0;
float targetTiltAngle  = 90.0;
float currentPanAngle  = 90.0;
float currentTiltAngle = 90.0;
bool  laserState       = false;

const float MAX_SLEW_STEP_DEG = 2.4;  // Max deg change per 20ms tick (~120 deg/sec)
unsigned long lastServoUpdateMs = 0;

// ==========================================
// 4. UDP High-Speed Command Receiver (Port 8888)
// ==========================================
WiFiUDP udp;
#define UDP_CMD_PORT 8888
char udpPacketBuffer[128];

// ==========================================
// 5. Camera Pin Definitions (AI-THINKER Model)
// ==========================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// HTTP Server instance
httpd_handle_t stream_httpd = NULL;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;

// Helper: Convert angle (0-180) to 14-bit PWM duty cycle
uint32_t angleToDuty(float angle) {
    angle = constrain(angle, 0.0f, 180.0f);
    float us = SERVO_MIN_US + (angle / 180.0f) * (SERVO_MAX_US - SERVO_MIN_US);
    // Period is 20000 us, max count is 16383 ((1<<14) - 1)
    return (uint32_t)((us / 20000.0f) * 16383.0f);
}

// Low-level servo driver update
void applyServoDuty() {
    uint32_t panDuty = angleToDuty(currentPanAngle);
    uint32_t tiltDuty = angleToDuty(currentTiltAngle);
    ledcWrite(PAN_LEDC_CH, panDuty);
    ledcWrite(TILT_LEDC_CH, tiltDuty);
    digitalWrite(LASER_PIN, laserState ? HIGH : LOW);
}

// Parse Command String (Supports "P:95.5,T:88.0,L:1" and "P95 T88 L1")
void parseCommand(const char* cmd) {
    float p = targetPanAngle;
    float t = targetTiltAngle;
    int l = laserState ? 1 : 0;

    const char* ptrP = strchr(cmd, 'P');
    if (ptrP) {
        if (*(ptrP + 1) == ':') ptrP++;
        p = atof(ptrP + 1);
    }
    const char* ptrT = strchr(cmd, 'T');
    if (ptrT) {
        if (*(ptrT + 1) == ':') ptrT++;
        t = atof(ptrT + 1);
    }
    const char* ptrL = strchr(cmd, 'L');
    if (ptrL) {
        if (*(ptrL + 1) == ':') ptrL++;
        l = atoi(ptrL + 1);
    }

    targetPanAngle = constrain(p, 0.0f, 180.0f);
    targetTiltAngle = constrain(t, 15.0f, 165.0f);
    laserState = (l != 0);
}

// ----------------------------------------------------
// HTTP Handlers
// ----------------------------------------------------
static const char INDEX_HTML[] = R"rawliteral(
<!DOCTYPE html><html><head><title>Agesis EYE Turret Node</title>
<style>body{background:#0e060c;color:#f5f6fa;font-family:sans-serif;text-align:center;margin:0;padding:20px}
img{max-width:100%;border:2px solid #ff0f3d;border-radius:6px;margin:10px}
h2{color:#ff0f3d}p{color:#888;font-size:13px}
.badge{background:#1e0817;border:1px solid #ff0f3d;padding:6px 12px;border-radius:4px;display:inline-block;margin:5px}
</style></head>
<body><h2>AGESIS EYE - TACTICAL ESP32 TURRET</h2>
<img src="/stream" />
<div class="badge">Stream: QVGA 320x240 @ Port 81</div>
<div class="badge">UDP Receiver: Port 8888 (Active)</div>
<div class="badge">Servos: SG90 Pan (IO12) | Tilt (IO13) | Laser (IO14)</div>
<p>5V 2A Slew-Rate Protected | Brownout Safe</p>
</body></html>)rawliteral";

static esp_err_t index_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, INDEX_HTML, strlen(INDEX_HTML));
}

static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[128];

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if (res != ESP_OK) return res;

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "Cache-Control", "no-cache, no-store, must-revalidate");

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        size_t hlen = snprintf(part_buf, sizeof(part_buf),
            "\r\n--" PART_BOUNDARY "\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);

        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        }

        esp_camera_fb_return(fb);
        fb = NULL;

        if (res != ESP_OK) break;
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    return res;
}

// REST Servo Control Endpoint: /servo?pan=90&tilt=90&laser=1
static esp_err_t servo_handler(httpd_req_t *req) {
    char* buf = NULL;
    size_t buf_len = httpd_req_get_url_query_len(req) + 1;
    if (buf_len > 1) {
        buf = (char*)malloc(buf_len);
        if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
            char param[32];
            if (httpd_query_key_value(buf, "pan", param, sizeof(param)) == ESP_OK) {
                targetPanAngle = constrain(atof(param), 0.0f, 180.0f);
            }
            if (httpd_query_key_value(buf, "tilt", param, sizeof(param)) == ESP_OK) {
                targetTiltAngle = constrain(atof(param), 15.0f, 165.0f);
            }
            if (httpd_query_key_value(buf, "laser", param, sizeof(param)) == ESP_OK) {
                laserState = (atoi(param) != 0);
            }
        }
        free(buf);
    }
    char resp[128];
    snprintf(resp, sizeof(resp), "{\"status\":\"ok\",\"pan\":%.1f,\"tilt\":%.1f,\"laser\":%d}",
             currentPanAngle, currentTiltAngle, laserState ? 1 : 0);
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, resp, strlen(resp));
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 81;
    config.ctrl_port = 32768;
    config.stack_size = 8192;
    config.max_open_sockets = 5;
    config.send_wait_timeout = 5;
    config.recv_wait_timeout = 5;
    config.lru_purge_enable = true;

    httpd_uri_t stream_uri = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL };
    httpd_uri_t snap_uri   = { .uri = "/jpg",    .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL };
    httpd_uri_t index_uri  = { .uri = "/",       .method = HTTP_GET, .handler = index_handler,   .user_ctx = NULL };
    httpd_uri_t servo_uri  = { .uri = "/servo",   .method = HTTP_GET, .handler = servo_handler,   .user_ctx = NULL };

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &index_uri);
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        httpd_register_uri_handler(stream_httpd, &snap_uri);
        httpd_register_uri_handler(stream_httpd, &servo_uri);
        Serial.println("[+] HTTP Web & Servo Server started on port 81");
    } else {
        Serial.println("[ERROR] HTTP server failed to start!");
    }
}

void setup() {
    // 1. Critical Power Stabilization: Disable brownout trigger for 5V 2A shared supply
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    Serial.setDebugOutput(false);
    Serial.println("\n==========================================");
    Serial.println("  AGESIS EYE - ESP32 TACTICAL TURRET NODE");
    Serial.println("==========================================");

    // 2. Configure Laser Emitter and Flash LED
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW); // Flash off
    pinMode(LASER_PIN, OUTPUT);
    digitalWrite(LASER_PIN, LOW);     // Laser disarmed

    // 3. Configure SG90 Servos with ESP32 Native LEDC PWM Driver
    ledcSetup(PAN_LEDC_CH, SERVO_PWM_FREQ, SERVO_RES_BITS);
    ledcAttachPin(PAN_SERVO_PIN, PAN_LEDC_CH);

    ledcSetup(TILT_LEDC_CH, SERVO_PWM_FREQ, SERVO_RES_BITS);
    ledcAttachPin(TILT_SERVO_PIN, TILT_LEDC_CH);

    // Initial neutral center position (90, 90)
    applyServoDuty();
    Serial.println("[+] SG90 Servo PWM Attached: IO12 (Pan) | IO13 (Tilt)");

    // 4. Camera Hardware Setup
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 10000000; // 10MHz rock-solid clock
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_QVGA; // 320x240 for ultra-high FPS
    config.jpeg_quality = 14;
    config.fb_count     = psramFound() ? 2 : 1;
    config.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
    config.grab_mode    = CAMERA_GRAB_LATEST;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[ERROR] Camera init failed: 0x%x\n", err);
        delay(2000);
        ESP.restart();
    }
    Serial.println("[+] Camera Sensor Initialized (QVGA 320x240)");

    // Camera sensor optimizations
    sensor_t * s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_brightness(s, 1);
        s->set_contrast(s, 1);
        s->set_saturation(s, 0);
        s->set_gainceiling(s, (gainceiling_t)4);
    }

    // 5. Connect to WiFi
    Serial.printf("[*] Connecting to WiFi: %s\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED && timeout < 25) {
        delay(400);
        Serial.print(".");
        timeout++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        WiFi.setSleep(false);
        WiFi.setTxPower(WIFI_POWER_17dBm);
        Serial.println("\n[+] WiFi Connected!");
        Serial.print("[+] IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[-] WiFi connection failed. Starting SoftAP fallback...");
        WiFi.mode(WIFI_AP);
        WiFi.softAP(ap_ssid, ap_pass);
        Serial.print("[+] SoftAP IP: ");
        Serial.println(WiFi.softAPIP());
    }

    // 6. Start High-Speed UDP Listener
    udp.begin(UDP_CMD_PORT);
    Serial.printf("[+] Ultra-Fast UDP Command Receiver Listening on Port %d\n", UDP_CMD_PORT);

    // 7. Start HTTP MJPEG Streaming & Control Server
    startCameraServer();
    Serial.println("[+] AGESIS EYE READY FOR FULL AUTONOMOUS TRACKING\n");
}

void loop() {
    unsigned long now = millis();

    // ====================================================
    // A. High-Speed Sub-Millisecond UDP Command Processing
    // ====================================================
    int packetSize = udp.parsePacket();
    if (packetSize > 0) {
        int len = udp.read(udpPacketBuffer, sizeof(udpPacketBuffer) - 1);
        if (len > 0) {
            udpPacketBuffer[len] = '\0';
            parseCommand(udpPacketBuffer);
        }
    }

    // ====================================================
    // B. Direct UART Serial Command Listener (Fallback)
    // ====================================================
    if (Serial.available()) {
        String s = Serial.readStringUntil('\n');
        s.trim();
        if (s.length() > 0) {
            parseCommand(s.c_str());
        }
    }

    // ====================================================
    // C. 5V 2A Slew-Rate Smooth Motion Engine (50 Hz Tick)
    // ====================================================
    // Interpolates angle smoothly to eliminate current spikes and prevent brownouts
    if (now - lastServoUpdateMs >= 20) {
        lastServoUpdateMs = now;

        // Pan axis smooth slew
        float dPan = targetPanAngle - currentPanAngle;
        if (abs(dPan) > MAX_SLEW_STEP_DEG) {
            currentPanAngle += (dPan > 0) ? MAX_SLEW_STEP_DEG : -MAX_SLEW_STEP_DEG;
        } else {
            currentPanAngle = targetPanAngle;
        }

        // Tilt axis smooth slew
        float dTilt = targetTiltAngle - currentTiltAngle;
        if (abs(dTilt) > MAX_SLEW_STEP_DEG) {
            currentTiltAngle += (dTilt > 0) ? MAX_SLEW_STEP_DEG : -MAX_SLEW_STEP_DEG;
        } else {
            currentTiltAngle = targetTiltAngle;
        }

        // Apply calibrated PWM to SG90 servos
        applyServoDuty();
    }

    // ====================================================
    // D. WiFi Watchdog
    // ====================================================
    if (WiFi.status() != WL_CONNECTED && WiFi.getMode() == WIFI_MODE_STA) {
        vTaskDelay(pdMS_TO_TICKS(500));
        WiFi.reconnect();
    }

    // Yield CPU to FreeRTOS
    vTaskDelay(pdMS_TO_TICKS(2));
}
