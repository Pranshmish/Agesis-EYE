/**
 * Agesis EYE - Autonomous Pan-Tilt Turret Firmware (Test & Live Tracking Mode)
 * Folder: firmware/test/test.ino
 * 
 * Hardware:
 *   - Pan  Servo (Joint 1 / Azimuth):   GPIO 18 (LEDC Channel 0, 50Hz, 14-Bit)
 *   - Tilt Servo (Joint 2 / Elevation): GPIO 19 (LEDC Channel 1, 50Hz, 14-Bit)
 *   - Laser Weapon Emitter / LED:       GPIO 14 (Digital Out / Active HIGH)
 *   - Power Supply: Shared 5V / USB with S-curve Slew Limiting
 * 
 * Supported Serial Commands (115200 baud):
 *   1. "P<pan> T<tilt> L<laser>\n"     (e.g., "P95 T85 L1" or "P120 T60 L0")
 *   2. "P:<pan>,T:<tilt>,L:<laser>\n" (e.g., "P:90.0,T:90.0,L:0")
 *   3. "<pan>,<tilt>\n"               (e.g., "90,90")
 */

#include <Arduino.h>

// --- PIN DEFINITIONS ---
#define PAN_PIN    18
#define TILT_PIN   19
#define LASER_PIN  14

// --- 50Hz 14-BIT PWM CONSTANTS ---
#define PWM_FREQ     50
#define PWM_RES      14     // 0 to 16,383 counts
#define SERVO_MIN_US 544    // 0 deg
#define SERVO_MAX_US 2400   // 180 deg
#define PERIOD_US    20000  // 20ms period

// Core 2.x compatibility channels
#define PAN_CH  0
#define TILT_CH 1

// --- SERVO LIMITS & SPEEDS ---
#define PAN_MIN_DEG  10.0f
#define PAN_MAX_DEG  170.0f
#define TILT_MIN_DEG 25.0f
#define TILT_MAX_DEG 155.0f

// Slew rate cap: max 3.5 deg per 20ms loop tick (~175 deg/sec)
// Keeps peak current draw strictly under 280mA to protect USB rail from brownout
#define MAX_SLEW_STEP 3.0f

// Current and Target State
float currentPan  = 90.0f;
float currentTilt = 90.0f;
float targetPan   = 90.0f;
float targetTilt  = 90.0f;
bool  laserActive = false;

// Serial Buffer
char serialBuffer[64];
uint8_t bufferIdx = 0;
unsigned long lastTickMs = 0;

// Convert Angle to 14-Bit Hardware PWM Duty Ticks
uint32_t angleToDuty(float angle) {
  angle = constrain(angle, 0.0f, 180.0f);
  float us = SERVO_MIN_US + (angle / 180.0f) * (SERVO_MAX_US - SERVO_MIN_US);
  return (uint32_t)((us / (float)PERIOD_US) * 16383.0f);
}

void writeMotors(float pan, float tilt, bool laser) {
  uint32_t panTicks  = angleToDuty(pan);
  uint32_t tiltTicks = angleToDuty(tilt);

  #if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcWrite(PAN_PIN, panTicks);
    ledcWrite(TILT_PIN, tiltTicks);
  #else
    ledcWrite(PAN_CH, panTicks);
    ledcWrite(TILT_CH, tiltTicks);
  #endif

  digitalWrite(LASER_PIN, laser ? HIGH : LOW);
}

// Parse Command String ("P120 T75 L1", "P:90,T:90,L:0", or "90,90")
void parseCommand(const char* cmd) {
  float p = targetPan;
  float t = targetTilt;
  int   l = laserActive ? 1 : 0;

  // Check simple comma format: "90,90"
  const char* comma = strchr(cmd, ',');
  if (comma && !strchr(cmd, 'P') && !strchr(cmd, 'p')) {
    p = atof(cmd);
    t = atof(comma + 1);
    targetPan  = constrain(p, PAN_MIN_DEG, PAN_MAX_DEG);
    targetTilt = constrain(t, TILT_MIN_DEG, TILT_MAX_DEG);
    Serial.printf("[ACK] PAN:%.1f TILT:%.1f LASER:%d\n", targetPan, targetTilt, laserActive ? 1 : 0);
    return;
  }

  // Parse Pan
  const char* ptrP = strchr(cmd, 'P');
  if (!ptrP) ptrP = strchr(cmd, 'p');
  if (ptrP) {
    if (*(ptrP + 1) == ':') ptrP++;
    p = atof(ptrP + 1);
  }

  // Parse Tilt
  const char* ptrT = strchr(cmd, 'T');
  if (!ptrT) ptrT = strchr(cmd, 't');
  if (ptrT) {
    if (*(ptrT + 1) == ':') ptrT++;
    t = atof(ptrT + 1);
  }

  // Parse Laser
  const char* ptrL = strchr(cmd, 'L');
  if (!ptrL) ptrL = strchr(cmd, 'l');
  if (ptrL) {
    if (*(ptrL + 1) == ':') ptrL++;
    l = atoi(ptrL + 1);
  }

  targetPan   = constrain(p, PAN_MIN_DEG, PAN_MAX_DEG);
  targetTilt  = constrain(t, TILT_MIN_DEG, TILT_MAX_DEG);
  laserActive = (l > 0);

  Serial.printf("[ACK] PAN:%.1f TILT:%.1f LASER:%d\n", targetPan, targetTilt, laserActive ? 1 : 0);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);

  // Initialize 14-Bit 50Hz LEDC PWM Channels
  #if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcAttach(PAN_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(TILT_PIN, PWM_FREQ, PWM_RES);
  #else
    ledcSetup(PAN_CH, PWM_FREQ, PWM_RES);
    ledcAttachPin(PAN_PIN, PAN_CH);
    ledcSetup(TILT_CH, PWM_FREQ, PWM_RES);
    ledcAttachPin(TILT_PIN, TILT_CH);
  #endif

  // Initial neutral alignment
  currentPan  = 90.0f;
  currentTilt = 90.0f;
  targetPan   = 90.0f;
  targetTilt  = 90.0f;
  laserActive = false;
  writeMotors(currentPan, currentTilt, laserActive);

  Serial.println("\n=============================================");
  Serial.println("  AGESIS EYE: TURRET SERIAL LISTENER READY   ");
  Serial.println("=============================================");
  Serial.println("[*] Pan  Servo: GPIO 18 (14-Bit PWM, 50Hz)");
  Serial.println("[*] Tilt Servo: GPIO 19 (14-Bit PWM, 50Hz)");
  Serial.println("[*] Laser Pin:  GPIO 14");
  Serial.println("[*] Ready for USB Serial commands at 115200 baud.");
  Serial.println("[READY]");
}

void loop() {
  // Read incoming Serial characters
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufferIdx > 0) {
        serialBuffer[bufferIdx] = '\0';
        parseCommand(serialBuffer);
        bufferIdx = 0;
      }
    } else if (bufferIdx < sizeof(serialBuffer) - 1) {
      serialBuffer[bufferIdx++] = c;
    }
  }

  // 50Hz S-Curve Servo Motion Tick (Every 20ms)
  unsigned long now = millis();
  if (now - lastTickMs >= 20) {
    lastTickMs = now;

    // Apply slew rate step to Pan
    if (abs(currentPan - targetPan) > 0.1f) {
      float dPan = targetPan - currentPan;
      dPan = constrain(dPan, -MAX_SLEW_STEP, MAX_SLEW_STEP);
      currentPan += dPan;
    }

    // Apply slew rate step to Tilt
    if (abs(currentTilt - targetTilt) > 0.1f) {
      float dTilt = targetTilt - currentTilt;
      dTilt = constrain(dTilt, -MAX_SLEW_STEP, MAX_SLEW_STEP);
      currentTilt += dTilt;
    }

    writeMotors(currentPan, currentTilt, laserActive);
  }
}
