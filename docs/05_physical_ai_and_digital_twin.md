# Chapter 5: Physical AI & 3D Kinematic Digital Twin

**Physical AI** refers to artificial intelligence systems embodied in physical hardware that interact dynamically with the real physical world—navigating friction, inertia, motor torque limits, and power constraints.

This chapter explores how Agesis EYE embodies Physical AI, bridging real-world neural perception with a real-time **3D Kinematic Digital Twin** implemented in [DigitalTwin.jsx](file:///c:/Users/ASUS/Desktop/Agesis%20EYE/frontend/src/components/DigitalTwin.jsx).

---

## 1. Physical AI vs. Disembodied AI

| Attribute | Disembodied AI (e.g. Chatbots, Static Vision) | Physical AI (Agesis EYE) |
| :--- | :--- | :--- |
| **Output** | Text tokens, static bounding box coordinates | Real motor torque, angular velocity, laser firing |
| **Feedback Loop** | Open-loop (User prompts $\to$ Model responds) | Closed-loop (Action alters the physical world $\to$ Sensor perceives change) |
| **Constraints** | Token compute limits, memory bandwidth | Slew rate, gear backlash, inrush current, 5V 2A power rail limits |
| **Safety Risks** | Hallucinations, incorrect text | Motor burnouts, electrical brownouts, optical laser hazards |

In Agesis EYE, perception directly dictates action:
```
[Perception: ONNX Vision] 
       │ 
       ▼ (Sub-50ms IBVS Law)
[Actuation: Dual SG90 Servos] 
       │ 
       ▼ (Physical World State Change)
[Sensing: OV2640 Camera Sensor]
```

---

## 2. Role of the 3D Kinematic Digital Twin

A **Digital Twin** is a high-fidelity virtual replica of a physical physical system that mirrors its real-time kinematics, geometry, and environment.

Agesis EYE’s digital twin serves three crucial roles:
1. **Hardware-in-the-Loop (HIL) Pre-Validation**: Operators can test aggressive tracking algorithms on synthetic 3D trajectories (`FIGURE-8`, `ORBIT`, `EVASIVE`) before deploying physical hardware.
2. **Real-Time Telemetry Mirroring (`LIVE_SYNC`)**: When connected to the physical turret, the 3D model matches the exact physical Pan/Tilt angles reported by the hardware over WebSocket.
3. **Kinematic Clearance Verification**: By adjusting the on-screen distance slider $d$, operators can visually inspect physical stanchion clearances across all rotational extremes.

---

## 3. Mathematical 3D Perspective Projection Engine

The digital twin uses a custom, zero-dependency 3D perspective projection pipeline written in pure JavaScript, rendering at 60 FPS on HTML5 Canvas:

```
World Space (x, y, z) 
   ──> Camera Pan/Translation 
   ──> Yaw Rotation (rotY) 
   ──> Pitch Rotation (rotX) 
   ──> Perspective Division (fov / Z2) 
   ──> Screen Pixels (projX, projY)
```

### Projection Equations
Given a 3D point $\mathbf{P} = [x, y, z]^T$, camera pan offsets $(\Delta x_p, \Delta y_p)$, camera rotation angles $(\theta_{\text{pitch}}, \theta_{\text{yaw}})$, and distance $D$:

1. **Camera Translation**:
   $$t_x = x + \Delta x_p, \quad t_y = y - \Delta y_p, \quad t_z = z$$
2. **Yaw (Y-Axis) Rotation**:
   $$x_1 = t_x \cos\theta_{\text{yaw}} - t_z \sin\theta_{\text{yaw}}$$
   $$z_1 = t_x \sin\theta_{\text{yaw}} + t_z \cos\theta_{\text{yaw}}$$
3. **Pitch (X-Axis) Rotation & Depth Offset**:
   $$y_2 = t_y \cos\theta_{\text{pitch}} - z_1 \sin\theta_{\text{pitch}}$$
   $$z_2 = t_y \sin\theta_{\text{pitch}} + z_1 \cos\theta_{\text{pitch}} + D$$
4. **Perspective Division**:
   $$\text{Scale} = \frac{f_{\text{fov}}}{\max(50, z_2)}$$
   $$\text{Screen } X = \frac{W}{2} + x_1 \cdot \text{Scale}, \quad \text{Screen } Y = \frac{H}{2} - y_2 \cdot \text{Scale}$$

---

## 4. CAD Mechanical Assembly Modeling

The digital twin directly replicates the Tinkercad CAD mechanical assembly:

```
                       [Red C-Arm & Emitter]
                                 |
                        [Purple SG90 Tilt]
                                 |
                        [Standoff Riser d]
                                 |
                        [Purple SG90 Pan]
                                 |
                       [Orange Cyl. Pedestal]
                     +-----------------------+
   [Red Baseplate]   | [Peach ESP32 Module]  |
=================================================
```

1. **Red Baseplate**: Rectangular foundation (`#d9232a`) with tactical workplane grid inscription.
2. **Peach Electronics Compartment**: Mounted on the right side (`#f6ad85`), modeling the ESP32-CAM controller and power regulation block.
3. **Orange Upright Pedestal**: 16-segmented cylindrical pillar (`#ea580c` / `#f97316`) providing base elevation.
4. **Pan SG90 Servo**: Casing rendered in signature purple (`#432371`) with blue mounting flanges and top spline horn.
5. **Rotating Riser Spar**: Vertical gunmetal spar with live Vernier caliper HUD displaying $d\text{ mm}$ in real time.
6. **Tilt SG90 Servo**: Horizontally oriented micro-servo mounted to the upper riser spar.
7. **Red C-Shaped Cantilever Arm**: Distinctive pivoting C-cradle holding the optical vision lens and laser collimator nozzle.

---

## 5. Target Physics, Explosion & Respawn Engine

When the laser beam engages the aerial target, the simulation applies continuous physical modeling:

1. **Thermal Absorption**:
   The target accumulates thermal load:
   $$\text{Heat}_{t+\Delta t} = \text{Heat}_t + 0.75 \cdot \Delta t$$
   At $\text{Heat} \ge 1.0$ ($\approx 1.3\text{ seconds}$ of sustained fire), the hull reaches catastrophic failure.
2. **Target Detonation**:
   * **3D Shockwaves**: Expanding concentric plasma rings fade radially into space.
   * **45 Shrapnel Fragments**: Particle velocities are calculated in spherical coordinates:
     $$v_x = s \cos\phi \cos\theta, \quad v_y = s \sin\phi + 45, \quad v_z = s \cos\phi \sin\theta$$
     where speed $s \in [75, 200]\text{ mm/s}$.
   * **Gravity Decay**: Particles decelerate under simulated gravity ($g = 140\text{ mm/s}^2$).
3. **Clean Respawn**:
   After a 1.2-second dispersal period, the target executes a digital materialization cycle (`respawnWarp`), resetting heat and re-entering the tactical engagement area.
