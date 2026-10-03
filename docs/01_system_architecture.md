# Chapter 1: System Architecture & End-to-End Integration

Agesis EYE is engineered as a distributed, real-time autonomous system. It bridges low-power microcontrollers, high-speed neural networks, and interactive browser-based tactical command interfaces.

---

## 1. High-Level Topological Overview

The system is decomposed into three primary physical and logical tiers:

```mermaid
flowchart TB
    subgraph EdgeNode["1. Hardware Edge Node (ESP32-CAM)"]
        CAM["OV2640 Sensor\n(QVGA 320x240 @ 30 FPS)"]
        MCU["ESP32 Dual-Core Xtensa LX6\n(Brownout Protection & Slew Engine)"]
        PWM_P["Pan Servo (IO12)\nSG90 (360°/180°)"]
        PWM_T["Tilt Servo (IO13)\nSG90 (180°)"]
        LASER["Laser Emitter (IO14)\nOptical Target Beam"]
        CAM -->|DRAM/PSRAM DMA| MCU
        MCU --> PWM_P
        MCU --> PWM_T
        MCU --> LASER
    end

    subgraph Network["2. Local Network Backbone (Wi-Fi 802.11 b/g/n)"]
        STREAM["MJPEG Stream HTTP :81/stream"]
        UDP_PIPE["High-Speed UDP Commands :8888\nP:<pan>,T:<tilt>,L:<laser>"]
        HTTP_API["REST Fallback :81/servo"]
    end

    subgraph GroundStation["3. Ground AI & Control Station (Host PC)"]
        ZR["ZeroLagStreamReader\n(Buffer-Draining Daemon)"]
        ONNX_ENG["ONNX Runtime Engine\n(agesis06.onnx @ 45+ FPS)"]
        KIN["TurretController\n(d-Invariant Kinematics & Interlocks)"]
        FAST_API["FastAPI Web Server :8000"]
        
        ZR --> ONNX_ENG
        ONNX_ENG -->|Error (dx, dy)| KIN
        KIN -->|UDP Datagrams| UDP_PIPE
    end

    subgraph OperatorHUD["4. Operator Station & Digital Twin (Browser)"]
        UI["Tactical React HUD (Vite :5173 / :8000)"]
        TWIN["3D Kinematic Digital Twin\n(Tinkercad CAD Matching + Burst Physics)"]
        WS["WebSocket Telemetry Stream\n(/ws/telemetry @ 25 Hz)"]
        
        FAST_API -->|HUD State| WS
        WS --> UI
        UI --> TWIN
    end

    MCU -->|HTTP MJPEG| STREAM
    STREAM --> ZR
    UDP_PIPE --> MCU
    HTTP_API --> MCU
```

---

## 2. Subsystem Breakdown

### Tier 1: Hardware Edge Node (ESP32-CAM)
* **Processor**: ESP32-D0WDQ6-V3 dual-core 32-bit Xtensa LX6 running at 240 MHz.
* **Camera Module**: OmniVision OV2640 2-Megapixel CMOS sensor configured in QVGA mode ($320 \times 240$) with hardware JPEG compression.
* **Actuation**: Dual SG90 micro-servos driven by hardware LEDC PWM timers at 50 Hz with 14-bit resolution.
* **Firmware Responsibilities**:
  1. Capture JPEG frames and stream them over HTTP port `81` using multipart boundary chunks.
  2. Listen asynchronously on UDP port `8888` for targeting packets.
  3. Execute 50 Hz motion smoothing (slew-rate limiter) to prevent inrush current spikes on the 5V 2A adapter.

### Tier 2: Ground AI Inference & Kinematics Engine (Python / FastAPI)
* **Zero-Lag Ingestion**: A dedicated thread drains the incoming MJPEG socket continuously, discarding stale buffered frames to ensure the vision model always processes the absolute freshest image available ($<2\text{ms}$ ingestion latency).
* **Neural Vision Core**: Executes `agesis06.onnx` via the ONNX Runtime execution provider, utilizing multi-threaded CPU SIMD instructions to achieve $>45\text{ FPS}$.
* **Closed-Loop Servoing**: Computes image-space tracking deltas $(\Delta x, \Delta y)$ and translates them into angular corrections via Image-Based Visual Servoing (IBVS).
* **Kinematics Engine**: Mathematically normalizes the vertical inter-servo separation distance $d$, decoupling physical mount geometry from tracking stability.

### Tier 3: Tactical Ground Station HUD & Digital Twin (React / Vite)
* **Real-Time Telemetry Pipeline**: Subscribes to `/ws/telemetry` over WebSocket at 25 Hz, updating dials, coordinate reticles, and lock streaks.
* **3D Perspective Digital Twin**: Replicates the physical Tinkercad CAD mechanical assembly in real-time, allowing operators to visualize line-of-sight pointing, test synthetic flight paths, adjust standoff height $d$, and observe target destruction dynamics.

---

## 3. End-to-End Latency Budget

To maintain closed-loop tracking stability on high-speed targets (such as swaying balloons or drones), total system latency from optical capture to physical servo movement must remain strictly below $50\text{ ms}$.

| Stage | Subsystem | Latency (Typical) | Optimization Technique |
| :--- | :--- | :--- | :--- |
| **1. Sensor Exposure & Readout** | OV2640 Sensor | $12.0\text{ ms}$ | QVGA resolution ($320\times 240$), high-gain AGC ceiling |
| **2. JPEG Compression** | ESP32 Hardware | $4.5\text{ ms}$ | Hardware JPEG engine, quality factor $14$ |
| **3. Wi-Fi Packet Transmission** | 802.11b/g/n LAN | $3.5\text{ ms}$ | TCP_NODELAY, direct socket streaming |
| **4. Ingestion & JPEG Decode** | `ZeroLagStreamReader` | $1.8\text{ ms}$ | Buffer draining thread, OpenCV fast turbo-JPEG |
| **5. Domain Preprocessing** | EP-CLAHE Transform | $1.2\text{ ms}$ | Vectorized NumPy tile contrast equalization |
| **6. Neural Network Inference** | ONNX Runtime | $14.5\text{ ms}$ | Quantized weights, CPU multi-threading ($4$ threads) |
| **7. Kinematics & PID Solvers** | `TurretController` | $0.2\text{ ms}$ | Analytical IBVS equations, $O(1)$ complexity |
| **8. UDP Command Dispatch** | Network Socket | $0.6\text{ ms}$ | Raw UDP datagram, port $8888$, zero handshake |
| **9. ESP32 Parsing & PWM Update**| ESP32 LEDC Driver | $0.4\text{ ms}$ | In-place C string pointer parsing |
| **10. SG90 Mechanical Response**| Micro-Servo Gearbox | $10.0\text{ ms}$ | Slew-rate smoothed step to eliminate inrush current |
| **Total Closed-Loop Latency** | **End-to-End** | **$\approx 48.7\text{ ms}$** | **Sub-50ms deterministic tracking** |

---

## 4. Network Protocol Topology

```
                  +-----------------------------------------+
                  |            ESP32 Edge Node              |
                  |             (10.96.117.X)               |
                  +--------------------+--------------------+
                                       |
                   HTTP :81/stream     |    UDP :8888 (Commands)
                   (MJPEG 30 FPS)      |    (Sub-ms latency)
                                       v
                  +--------------------+--------------------+
                  |       Ground Station (127.0.0.1)        |
                  |                                         |
                  |  - Port 8000: FastAPI Backend / Stream  |
                  |  - Port 5173: Vite Development Server   |
                  |  - Port 8888: Outbound UDP Dispatch     |
                  +-----------------------------------------+
```

1. **Video Stream**: Standard HTTP GET on port `81` serving `multipart/x-mixed-replace;boundary=...`.
2. **Servo & Laser Commands**: High-speed UDP datagrams sent to destination port `8888`. Each packet is an ASCII payload:
   ```
   P:<pan_angle>,T:<tilt_angle>,L:<laser_bool>\n
   ```
   *Example*: `P:94.2,T:87.5,L:1\n`
3. **Telemetry WebSocket**: Bidirectional JSON socket at `ws://127.0.0.1:8000/ws/telemetry` streaming camera FPS, tracking latency, servo coordinates, and safety states.
