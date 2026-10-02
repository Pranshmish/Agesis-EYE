#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// 1. WiFi Configuration (Update credentials)
// ==========================================
const char* ssid     = "Pranshul";
const char* password = "Pranshul@007";

// If WiFi fails, fallback to Access Point mode:
const char* ap_ssid  = "ESP32-CAM-TURRET";
const char* ap_pass  = "12345678"; // 8 chars min

// ==========================================
// 2. Camera Pin Definitions (AI-THINKER Model)
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

// Built-in Flash LED on GPIO 4
#define FLASH_LED_PIN      4

// HTTP Server instance
httpd_handle_t stream_httpd = NULL;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;

// Simple HTML page for browser viewing
static const char INDEX_HTML[] = R"rawliteral(
<!DOCTYPE html><html><head><title>ESP32-CAM Stream</title>
<style>body{background:#111;color:#eee;font-family:sans-serif;text-align:center;margin:0;padding:20px}
img{max-width:100%;border:2px solid #444;border-radius:8px;margin:10px}
h2{color:#0f0}p{color:#888;font-size:14px}</style></head>
<body><h2>ESP32-CAM Live Stream</h2>
<img src="/stream" />
<p>Resolution: QVGA 320x240 | Port 81</p>
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
    httpd_resp_set_hdr(req, "Connection", "close");
    esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[128];

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if (res != ESP_OK) {
        return res;
    }

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "Cache-Control", "no-cache, no-store, must-revalidate");

    Serial.println("[STREAM] Client connected");

    int frame_cnt = 0;
    int64_t last_report = esp_timer_get_time();
    int send_errors = 0;

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("[STREAM] fb_get failed!");
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;  // Don't break on transient fb failures
        }

        size_t hlen = snprintf(part_buf, sizeof(part_buf),
            "\r\n--" PART_BOUNDARY "\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);

        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        }

        esp_camera_fb_return(fb);
        fb = NULL;

        if (res != ESP_OK) {
            send_errors++;
            Serial.printf("[STREAM] Send error #%d, client likely disconnected\n", send_errors);
            break;  // Client gone, exit cleanly
        }

        frame_cnt++;
        int64_t now = esp_timer_get_time();
        if (now - last_report >= 5000000) {  // Report every 5 seconds to reduce serial overhead
            Serial.printf("[STREAM] %d FPS | RSSI: %d dBm | heap: %u\n",
                frame_cnt / 5, WiFi.RSSI(), ESP.getFreeHeap());
            frame_cnt = 0;
            last_report = now;
        }

        // Yield to WiFi/TCP stack - critical for stable streaming
        vTaskDelay(pdMS_TO_TICKS(1));
    }

    Serial.println("[STREAM] Client disconnected, handler exiting cleanly");
    return res;
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 81;
    config.ctrl_port = 32768;
    config.stack_size = 8192;
    config.max_open_sockets = 4;        // Room for browser + Python + snapshot
    config.send_wait_timeout = 5;       // 5s timeout before giving up on stuck client
    config.recv_wait_timeout = 5;
    config.lru_purge_enable = true;     // Auto-purge stale connections

    httpd_uri_t stream_uri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = stream_handler,
        .user_ctx  = NULL
    };

    httpd_uri_t snap_uri = {
        .uri       = "/jpg",
        .method    = HTTP_GET,
        .handler   = capture_handler,
        .user_ctx  = NULL
    };

    httpd_uri_t index_uri = {
        .uri       = "/",
        .method    = HTTP_GET,
        .handler   = index_handler,
        .user_ctx  = NULL
    };

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &index_uri);
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        httpd_register_uri_handler(stream_httpd, &snap_uri);
        Serial.println("[+] HTTP server started on port 81");
    } else {
        Serial.println("[ERROR] HTTP server failed to start!");
    }
}

void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout detector

    Serial.begin(115200);
    Serial.setDebugOutput(true);
    Serial.println("\n--- ESP32-CAM Turret Streamer Starting ---");
    Serial.printf("[+] Free heap: %u bytes\n", ESP.getFreeHeap());

    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW); // Keep bright flash LED off

    // Camera hardware configuration
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
    config.xclk_freq_hz = 10000000;    // 10 MHz - much more stable than 20MHz on USB power
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode    = CAMERA_GRAB_LATEST;

    // Check for PSRAM
    if (psramFound()) {
        Serial.println("[+] PSRAM detected! Using QVGA double buffered.");
        config.frame_size   = FRAMESIZE_QVGA;
        config.jpeg_quality = 15;           // Slightly lower quality = less power draw + smaller frames
        config.fb_count     = 2;
        config.fb_location  = CAMERA_FB_IN_PSRAM;
        config.grab_mode    = CAMERA_GRAB_LATEST;
    } else {
        Serial.println("[-] No PSRAM detected! Using QVGA in DRAM.");
        config.frame_size   = FRAMESIZE_QVGA;
        config.jpeg_quality = 15;
        config.fb_count     = 1;
        config.fb_location  = CAMERA_FB_IN_DRAM;
        config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
    }

    // Initialize Camera
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[ERROR] Camera init failed with error 0x%x\n", err);
        delay(3000);
        ESP.restart();
        return;
    }
    Serial.println("[+] Camera initialized successfully");

    // Camera sensor tuning for consistent exposure & high framerate
    sensor_t * s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_brightness(s, 1);
        s->set_contrast(s, 1);
        s->set_saturation(s, 0);
        s->set_whitebal(s, 1);
        s->set_awb_gain(s, 1);
        s->set_wb_mode(s, 0);
        s->set_exposure_ctrl(s, 1);
        s->set_aec2(s, 0);
        s->set_ae_level(s, 0);
        s->set_gain_ctrl(s, 1);
        s->set_gainceiling(s, (gainceiling_t)4);
    }

    // Connect to WiFi
    Serial.printf("[*] Connecting to WiFi: %s\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED && timeout < 30) {
        delay(500);
        Serial.print(".");
        timeout++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        WiFi.setSleep(false);
        WiFi.setTxPower(WIFI_POWER_17dBm);
        Serial.println("\n[+] WiFi Connected successfully!");
        Serial.printf("[+] Signal Strength (RSSI): %d dBm\n", WiFi.RSSI());
        Serial.print("[+] Camera Stream URL: http://");
        Serial.print(WiFi.localIP());
        Serial.println(":81/stream");
    } else {
        Serial.println("\n[-] WiFi connection failed. Starting SoftAP fallback...");
        WiFi.mode(WIFI_AP);
        WiFi.softAP(ap_ssid, ap_pass);
        Serial.print("[+] Hotspot created: ");
        Serial.println(ap_ssid);
        Serial.print("[+] Camera Stream URL: http://");
        Serial.print(WiFi.softAPIP());
        Serial.println(":81/stream");
    }

    // Start MJPEG Streaming Web Server on Port 81
    startCameraServer();
    Serial.println("\n========================================");
    Serial.println("[+] STREAM READY AND LISTENING ON PORT 81");
    Serial.println("========================================\n");
}

void loop() {
    // Watchdog: if WiFi drops, reconnect
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[!] WiFi disconnected, reconnecting...");
        WiFi.reconnect();
        int retry = 0;
        while (WiFi.status() != WL_CONNECTED && retry < 20) {
            delay(500);
            retry++;
        }
        if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("[+] WiFi reconnected! RSSI: %d dBm\n", WiFi.RSSI());
        } else {
            Serial.println("[!] WiFi reconnect failed, restarting...");
            ESP.restart();
        }
    }
    vTaskDelay(pdMS_TO_TICKS(5000));
}
