# Chapter 4: Robotics, Kinematics & Visual Servoing

The mechanical tracking head of Agesis EYE is a **Two-Degree-of-Freedom (2-DoF) Pan-Tilt Robotic Manipulator**. 

This chapter presents the mathematical foundations of the targeting kinematics, Image-Based Visual Servoing (IBVS), and the formal proof of **inter-servo distance $d$ invariance** implemented in [turret.py](file:///c:/Users/ASUS/Desktop/Agesis%20EYE/backend/turret.py).

---

## 1. 2-DoF Pan-Tilt Manipulator Coordinate Frames

The mechanical assembly comprises two rotational joints separated by a vertical standoff spar of variable height $d$:

```
                       [ Laser / Camera Head ]
                                  |
                           (Tilt Joint J2)
                                  |
                                  |  <--- Variable Standoff Distance d
                                  |
                           (Pan Joint J1)
                                  |
                        [ Ground Pedestal ]
```

1. **Joint 1 (Pan / Azimuth)**: Revolute joint rotating about the vertical $Z_0$-axis:
   $$\theta_{\text{pan}} \in [0^\circ, 180^\circ] \quad (\text{Neutral } 90^\circ)$$
2. **Joint 2 (Tilt / Elevation)**: Revolute joint mounted at height $d$ above Joint 1, rotating about a horizontal axis orthogonal to the stanchion:
   $$\theta_{\text{tilt}} \in [25^\circ, 155^\circ] \quad (\text{Neutral } 90^\circ)$$

---

## 2. Mathematical Proof of Distance $d$ Invariance

A common flaw in pan-tilt turret software is hardcoding the physical distance $d$ between the pan servo and tilt servo into the control loop. If the user changes the stanchion height, tracking becomes unstable or develops steady-state error.

Agesis EYE uses **Image-Based Visual Servoing (IBVS)** with an **eye-in-hand** sensor configuration, making optical tracking **mathematically invariant to the distance $d$**.

### Theorem
*The closed-loop visual tracking error nulling law is independent of the vertical separation distance $d$ between the Pan and Tilt servo axes when the optical sensor is co-mounted on the tilt arm.*

### Proof

#### 1. Pinhole Projection Model
Let a point target in the camera frame be denoted by $\mathbf{P}_c = [X_c, Y_c, Z_c]^T$. Its projected image coordinates $(u, v)$ on the sensor are given by:
$$u = f_x \frac{X_c}{Z_c} + c_x, \quad v = f_y \frac{Y_c}{Z_c} + c_y$$
where $(f_x, f_y)$ are the focal lengths in pixels and $(c_x, c_y) = (W/2, H/2)$ is the optical principal center.

The pixel error vector $\mathbf{e} = [\Delta x, \Delta y]^T$ from the optical center is:
$$\Delta x = u - c_x = f_x \frac{X_c}{Z_c}, \quad \Delta y = v - c_y = f_y \frac{Y_c}{Z_c}$$

#### 2. Azimuth (Pan) Invariance
The Pan axis rotates around the vertical world axis $\mathbf{Z}_{\text{world}}$.
Consider the translation from the Pan joint origin $O_{\text{pan}}$ to the Tilt joint origin $O_{\text{tilt}}$:
$$\mathbf{T}_{\text{pan}\to\text{tilt}} = \begin{bmatrix} 0 \\ 0 \\ d \end{bmatrix}$$

Because the translation vector is **strictly parallel to the axis of rotation** $\mathbf{Z}_{\text{world}}$, the rotation matrix $\mathbf{R}_z(\theta_{\text{pan}})$ commutes with the vertical translation:
$$\mathbf{R}_z(\theta_{\text{pan}}) \cdot \begin{bmatrix} 0 \\ 0 \\ d \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \\ d \end{bmatrix}$$

Therefore, rotating about the Pan axis by an angle $\Delta \theta_{\text{pan}}$ produces an identical angular change in the target's azimuth angle regardless of whether $d = 10\text{ mm}$ or $d = 200\text{ mm}$:
$$\Delta \theta_{\text{pan}} = -\arctan\left(\frac{\Delta x}{f_x}\right) \approx -\frac{\Delta x}{f_x}$$
The distance $d$ does not appear anywhere in the azimuth angular correction equation. $\quad \blacksquare$

#### 3. Elevation (Tilt) Invariance
Because the camera and laser are physically mounted to the C-shaped cradle on Joint 2's horn (eye-in-hand):
1. The camera frame origin $O_c$ coincides with (or is fixed rigidly to) Joint 2's rotation center.
2. An elevation angular change $\Delta \theta_{\text{tilt}}$ rotates the camera directly about its own pitch axis.
3. The vertical error angle is:
   $$\Delta \theta_{\text{tilt}} = \arctan\left(\frac{\Delta y}{f_y}\right) \approx \frac{\Delta y}{f_y}$$

The standoff length $d$ simply translates the entire elevation gimbal vertically in world space; **it does not rotate or alter the local angular line-of-sight vector from the camera lens to the target**.

Hence, the closed-loop visual servo update:
$$\theta_{\text{pan}}^{(k+1)} = \theta_{\text{pan}}^{(k)} - K_p \cdot \Delta x$$
$$\theta_{\text{tilt}}^{(k+1)} = \theta_{\text{tilt}}^{(k)} + K_p \cdot \Delta y$$
is **completely invariant to the physical inter-servo distance $d$**. $\quad \blacksquare$

---

## 3. Spatial Parallax & 3D Envelope Compensation

While visual tracking is $d$-invariant, the physical clearance envelope and world-frame spatial kinematics do depend on $d$:

```
                   Target
                   *
                  /|
                 / |
                /  | (Y_tgt - Y_pivot)
               /   |
   Tilt Axis  O----+
              |    R_xz (Horizontal Range)
              |
              | d (Standoff)
              |
   Pan Axis   O (Base)
```

1. **3D World Target Elevation**:
   For synthetic tracking or digital twin simulation, the inverse kinematics solver computes:
   $$\theta_{\text{tilt}} = 90^\circ + \arctan\left(\frac{Y_{\text{tgt}} - (Y_{\text{base}} + d)}{\sqrt{X_{\text{tgt}}^2 + Z_{\text{tgt}}^2}}\right)$$
2. **Clearance Envelope Auto-Adjustment**:
   As the riser height $d$ increases, the lever arm expands. The controller automatically narrows the allowable Pan/Tilt limits to prevent physical collisions:
   $$\text{Pan Margin} = \max(5.0^\circ, 10.0^\circ + (d - 45.0) \times 0.06)$$
   $$\text{Tilt Margin} = \max(15.0^\circ, 35.0^\circ - (d - 20.0) \times 0.15)$$
3. **Parallax Offset**:
   At a nominal engagement range of $1.2\text{ m}$ ($1200\text{ mm}$), the parallax angle $\phi$ between the base and head is auto-computed:
   $$\phi = \arctan\left(\frac{d}{1200\text{ mm}}\right)$$

---

## 4. S-Curve Trajectory & Slew-Rate Limiting

To safeguard the 5V 2A power adapter from voltage dips caused by motor stalls, the backend applies a slew-rate acceleration limit:

$$\Delta \theta_{\max} = 3.5^\circ \text{ per inference frame} \quad (\approx 120^\circ/\text{s at } 35\text{ FPS})$$

```python
# Extract from turret.py
raw_dpan = -dx * self.kp
raw_dtilt = dy * self.kp

# Clamp step size to prevent instantaneous motor current spikes
step_pan = max(-self.max_slew_step_deg, min(self.max_slew_step_deg, raw_dpan))
step_tilt = max(-self.max_slew_step_deg, min(self.max_slew_step_deg, raw_dtilt))

self.pan_angle += step_pan
self.tilt_angle += step_tilt
```

This dual-layer protection (backend rate limiting + firmware interpolation) ensures that even sudden target jumps across the field of view produce smooth, brownout-safe tracking trajectories.
