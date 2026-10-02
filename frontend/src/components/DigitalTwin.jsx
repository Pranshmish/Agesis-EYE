import React, { useRef, useEffect, useState, useCallback } from 'react';

/**
 * DigitalTwin Component v3.0
 * High-Impact 3D Perspective Kinematic Digital Twin
 *
 * Visual Enhancements:
 * - Unified tactical color scheme (Eliminates multi-color text rainbow)
 * - Full-height immersive viewport fitting 100% of available screen space
 * - Large, prominent, detailed 3D multi-body turret assembly
 * - High-intensity atmospheric collimated laser beam with traveling pulse
 * - 3D Aerial Target with altitude drop curtain & breadcrumb flight trail
 * - Ground radar concentric grid with animated sweep pulse wave
 * - Camera view presets & auto-orbit inspection
 */
export default function DigitalTwin({
  telemetry,
  onDistanceChange,
  isLaserArmed = false,
  isLaserFiring = false,
}) {
  const canvasRef = useRef(null);

  // Kinematic parameters
  const servoDistance = telemetry?.servo_distance_mm ?? 45.0;
  const [localDistance, setLocalDistance] = useState(servoDistance);
  const [simMode, setSimMode] = useState('SIM_FIGURE8'); // 'SIM_FIGURE8' | 'SIM_ORBIT' | 'SIM_EVASIVE' | 'LIVE_SYNC'
  const [targetSpeed, setTargetSpeed] = useState(1.0);
  const [targetAltitude, setTargetAltitude] = useState(190);
  const [targetRadius, setTargetRadius] = useState(300);
  const [beamEnabled, setBeamEnabled] = useState(true);
  const [autoOrbit, setAutoOrbit] = useState(false);
  const [cameraPreset, setCameraPreset] = useState('ISO');
  const [controlsOpen, setControlsOpen] = useState(true);

  // 3D Camera viewpoint state (Closer & more prominent)
  const cameraRef = useRef({
    rotX: 20 * (Math.PI / 180), // pitch
    rotY: -30 * (Math.PI / 180), // yaw
    distance: 490, // Brought significantly closer for high visual impact
    panX: 0,
    panY: 20,
    isDragging: false,
    lastX: 0,
    lastY: 0,
  });

  // Target 3D coordinates & kinematic state with Burst & Respawn dynamics
  const targetStateRef = useRef({
    x: 200,
    y: 190,
    z: 180,
    vx: 0,
    vy: 0,
    vz: 0,
    trail: [],
    maxTrail: 100,
    simTime: 0,
    sparks: [],
    heat: 0, // 0.0 to 1.0 (thermal load from laser attack)
    isDestroyed: false,
    burstTimer: 0,
    killCount: 0,
    debris: [], // Flying incandescent shrapnel pieces
    shockwaves: [], // Expanding plasma shockwave rings
    respawnWarp: 1.0, // Digital materialization factor
  });

  // Turret body joint angles
  const turretAnglesRef = useRef({
    pan: telemetry?.pan ?? 90.0,
    tilt: telemetry?.tilt ?? 90.0,
  });

  // Sync external servo distance
  useEffect(() => {
    if (telemetry?.servo_distance_mm !== undefined) {
      setLocalDistance(telemetry.servo_distance_mm);
    }
  }, [telemetry?.servo_distance_mm]);

  // Sync external angles when in LIVE_SYNC mode
  useEffect(() => {
    if (simMode === 'LIVE_SYNC' && telemetry?.pan !== undefined && telemetry?.tilt !== undefined) {
      turretAnglesRef.current.pan = telemetry.pan;
      turretAnglesRef.current.tilt = telemetry.tilt;
    }
  }, [simMode, telemetry?.pan, telemetry?.tilt]);

  const handleDistanceSlider = (val) => {
    setLocalDistance(val);
    if (onDistanceChange) onDistanceChange(val);
  };

  // Camera preset switcher
  const applyCameraPreset = (preset) => {
    setCameraPreset(preset);
    const cam = cameraRef.current;
    if (preset === 'ISO') {
      cam.rotX = 20 * (Math.PI / 180);
      cam.rotY = -30 * (Math.PI / 180);
      cam.distance = 490;
      cam.panX = 0;
      cam.panY = 20;
    } else if (preset === 'TOP') {
      cam.rotX = 85 * (Math.PI / 180);
      cam.rotY = 0;
      cam.distance = 560;
      cam.panX = 0;
      cam.panY = 0;
    } else if (preset === 'SIDE') {
      cam.rotX = 2 * (Math.PI / 180);
      cam.rotY = -90 * (Math.PI / 180);
      cam.distance = 460;
      cam.panX = 0;
      cam.panY = 25;
    } else if (preset === 'TURRET_POV') {
      const panRad = ((turretAnglesRef.current.pan - 90) * Math.PI) / 180;
      cam.rotX = 12 * (Math.PI / 180);
      cam.rotY = -panRad;
      cam.distance = 320;
      cam.panX = 0;
      cam.panY = 40;
    }
  };

  // Mouse interaction for 3D orbital camera
  const handleMouseDown = (e) => {
    cameraRef.current.isDragging = true;
    cameraRef.current.lastX = e.clientX;
    cameraRef.current.lastY = e.clientY;
  };

  const handleMouseMove = (e) => {
    if (!cameraRef.current.isDragging) return;
    const dx = e.clientX - cameraRef.current.lastX;
    const dy = e.clientY - cameraRef.current.lastY;
    cameraRef.current.lastX = e.clientX;
    cameraRef.current.lastY = e.clientY;

    if (e.buttons === 1) {
      cameraRef.current.rotY += dx * 0.007;
      cameraRef.current.rotX = Math.max(-1.3, Math.min(1.3, cameraRef.current.rotX + dy * 0.007));
    } else if (e.buttons === 2) {
      cameraRef.current.panX += dx * 0.65;
      cameraRef.current.panY -= dy * 0.65;
    }
  };

  const handleMouseUp = () => {
    cameraRef.current.isDragging = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    cameraRef.current.distance = Math.max(220, Math.min(1300, cameraRef.current.distance + e.deltaY * 0.6));
  };

  // 3D Perspective Projection Engine
  const project3D = useCallback((x, y, z, width, height) => {
    const cam = cameraRef.current;
    const tx = x + cam.panX;
    const ty = y - cam.panY;
    const tz = z;

    const cosY = Math.cos(cam.rotY);
    const sinY = Math.sin(cam.rotY);
    const x1 = tx * cosY - tz * sinY;
    const z1 = tx * sinY + tz * cosY;

    const cosX = Math.cos(cam.rotX);
    const sinX = Math.sin(cam.rotX);
    const y2 = ty * cosX - z1 * sinX;
    const z2 = ty * sinX + z1 * cosX + cam.distance;

    const fov = 680;
    const scale = fov / Math.max(50, z2);
    const projX = width / 2 + x1 * scale;
    const projY = height / 2 - y2 * scale;

    return { x: projX, y: projY, z: z2, scale, visible: z2 > 15 };
  }, []);

  // 60 FPS Render Loop
  useEffect(() => {
    let animId;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const render = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      // Deep atmospheric background vignette
      const bg = ctx.createRadialGradient(width / 2, height / 2, 40, width / 2, height / 2, width * 0.85);
      bg.addColorStop(0, '#0d050a');
      bg.addColorStop(0.55, '#060205');
      bg.addColorStop(1, '#020003');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      // Auto Orbit Camera
      if (autoOrbit && !cameraRef.current.isDragging) {
        cameraRef.current.rotY += 0.003;
      }

      // 1. Update Target Trajectory, Laser Attack Damage & Burst Mechanics
      const tgt = targetStateRef.current;
      const dt = 0.016 * targetSpeed;
      tgt.simTime += dt;

      if (tgt.isDestroyed) {
        tgt.burstTimer += dt;

        // Update Debris Shrapnel Simulation
        for (let i = tgt.debris.length - 1; i >= 0; i--) {
          const deb = tgt.debris[i];
          deb.x += deb.vx * dt;
          deb.y += deb.vy * dt;
          deb.z += deb.vz * dt;
          deb.vy -= 160 * dt; // Gravity
          deb.vx *= 0.98; // Air resistance
          deb.vz *= 0.98;
          deb.life -= dt / deb.maxLife;
          if (deb.life <= 0) tgt.debris.splice(i, 1);
        }

        // Update Expanding Shockwave Rings
        for (let i = tgt.shockwaves.length - 1; i >= 0; i--) {
          const sw = tgt.shockwaves[i];
          sw.r += 115 * dt;
          sw.life -= dt * 1.7;
          if (sw.life <= 0) tgt.shockwaves.splice(i, 1);
        }

        // Target Again Comes Back! (Respawn Cycle)
        if (tgt.burstTimer >= 1.4) {
          tgt.isDestroyed = false;
          tgt.heat = 0;
          tgt.burstTimer = 0;
          tgt.debris = [];
          tgt.shockwaves = [];
          tgt.respawnWarp = 0.05; // Trigger warp-in animation
          tgt.trail = [];
          tgt.simTime += 0.75; // Advance phase slightly
        }
      } else {
        // Target is active & maneuvering in 3D
        tgt.respawnWarp = Math.min(1.0, (tgt.respawnWarp || 1.0) + dt * 2.2);

        const prevX = tgt.x;
        const prevY = tgt.y;
        const prevZ = tgt.z;

        if (simMode === 'SIM_FIGURE8') {
          const t = tgt.simTime * 0.75;
          const R = targetRadius;
          tgt.x = R * Math.sin(t);
          tgt.z = R * 0.65 * Math.sin(2 * t) + 140;
          tgt.y = targetAltitude + 40 * Math.sin(t * 1.4);
        } else if (simMode === 'SIM_ORBIT') {
          const t = tgt.simTime * 0.85;
          const R = targetRadius;
          tgt.x = R * Math.cos(t);
          tgt.z = R * Math.sin(t) + 100;
          tgt.y = targetAltitude + 22 * Math.sin(t * 2);
        } else if (simMode === 'SIM_EVASIVE') {
          const t = tgt.simTime * 1.1;
          const R = targetRadius * 0.9;
          tgt.x = R * Math.sin(t * 0.9) + 40 * Math.sin(t * 3);
          tgt.z = R * 0.7 * Math.cos(t * 0.8) + 120;
          tgt.y = targetAltitude + 60 * Math.sin(t * 2.4);
        } else if (simMode === 'LIVE_SYNC') {
          const panRad = (turretAnglesRef.current.pan * Math.PI) / 180;
          const tiltRad = (turretAnglesRef.current.tilt * Math.PI) / 180;
          const dist = 340;
          tgt.x = dist * Math.cos(panRad);
          tgt.z = dist * Math.sin(panRad);
          tgt.y = 110 + dist * Math.sin((tiltRad - Math.PI / 2) * 0.85);
        }

        tgt.vx = (tgt.x - prevX) / dt;
        tgt.vy = (tgt.y - prevY) / dt;
        tgt.vz = (tgt.z - prevZ) / dt;

        // Trajectory breadcrumbs
        if (
          tgt.trail.length === 0 ||
          Math.hypot(tgt.x - tgt.trail[tgt.trail.length - 1].x, tgt.z - tgt.trail[tgt.trail.length - 1].z) > 4
        ) {
          tgt.trail.push({ x: tgt.x, y: tgt.y, z: tgt.z });
          if (tgt.trail.length > tgt.maxTrail) tgt.trail.shift();
        }

        // Laser Beam Attack: Heat accumulation & Burst Trigger
        const isLaserAttacking = beamEnabled || isLaserFiring;
        if (isLaserAttacking) {
          tgt.heat = Math.min(1.0, (tgt.heat || 0) + dt * 0.75); // ~1.3s to burst!

          // Slag Sparks under fire
          if (tgt.sparks.length < 32) {
            const dirMag = Math.hypot(tgt.x, tgt.z) || 1;
            tgt.sparks.push({
              x: tgt.x,
              y: tgt.y,
              z: tgt.z,
              vx: (Math.random() - 0.5) * 85 - (tgt.x / dirMag) * 35,
              vy: Math.random() * 70 + 25,
              vz: (Math.random() - 0.5) * 85 - (tgt.z / dirMag) * 35,
              life: 1.0,
              maxLife: 0.45 + Math.random() * 0.45,
              size: 1.2 + Math.random() * 2.2,
            });
          }

          // BURST TRIGGER: Target explodes into pieces!
          if (tgt.heat >= 1.0) {
            tgt.isDestroyed = true;
            tgt.burstTimer = 0;
            tgt.killCount = (tgt.killCount || 0) + 1;
            tgt.sparks = [];

            // 3D Expanding Shockwave
            tgt.shockwaves.push({
              x: tgt.x,
              y: tgt.y,
              z: tgt.z,
              r: 4,
              life: 1.0,
            });

            // 45 High-Velocity Shrapnel Fragments
            tgt.debris = [];
            for (let k = 0; k < 45; k++) {
              const theta = Math.random() * Math.PI * 2;
              const phi = (Math.random() - 0.5) * Math.PI;
              const speed = 75 + Math.random() * 125;
              tgt.debris.push({
                x: tgt.x + (Math.random() - 0.5) * 8,
                y: tgt.y + (Math.random() - 0.5) * 8,
                z: tgt.z + (Math.random() - 0.5) * 8,
                vx: speed * Math.cos(phi) * Math.cos(theta),
                vy: speed * Math.sin(phi) + 45,
                vz: speed * Math.cos(phi) * Math.sin(theta),
                size: 2.0 + Math.random() * 3.5,
                life: 1.0,
                maxLife: 0.7 + Math.random() * 0.7,
              });
            }
          }
        } else {
          tgt.heat = Math.max(0, (tgt.heat || 0) - dt * 0.5);
        }
      }

      // Update remaining slag sparks
      for (let i = tgt.sparks.length - 1; i >= 0; i--) {
        const sp = tgt.sparks[i];
        sp.x += sp.vx * dt;
        sp.y += sp.vy * dt;
        sp.z += sp.vz * dt;
        sp.vy -= 140 * dt; // Gravity
        sp.life -= dt / sp.maxLife;
        if (sp.life <= 0) tgt.sparks.splice(i, 1);
      }

      // 2. Inverse Kinematics for Turret Body (Volumetric Heavy Autonomous Turret)
      const stanchionHeight = Math.max(20, Math.min(220, localDistance)) * 1.15;
      const baseElev = 42; // Pan servo & turntable deck height
      const pivotY = baseElev + stanchionHeight; // Tilt gimbal trunnion pivot height

      if (simMode !== 'LIVE_SYNC') {
        const dx = tgt.x;
        const dz = tgt.z;
        const dy = tgt.y - pivotY;
        const horizDist = Math.hypot(dx, dz);

        let aimPan = 90 - (Math.atan2(dx, dz) * 180) / Math.PI;
        aimPan = Math.max(5, Math.min(175, aimPan));

        let aimTilt = 90 + (Math.atan2(dy, horizDist) * 180) / Math.PI;
        aimTilt = Math.max(15, Math.min(165, aimTilt));

        const smooth = 0.15;
        turretAnglesRef.current.pan += (aimPan - turretAnglesRef.current.pan) * smooth;
        turretAnglesRef.current.tilt += (aimTilt - turretAnglesRef.current.tilt) * smooth;
      }

      const curPan = turretAnglesRef.current.pan;
      const curTilt = turretAnglesRef.current.tilt;

      // 4. Render Ground Tactical Radar Grid
      ctx.save();
      const gridR = 480;
      const ringSteps = [80, 160, 240, 320, 400, 480];

      // Radar Concentric Rings with Unified Crimson Glow
      ringSteps.forEach((r, idx) => {
        ctx.beginPath();
        for (let a = 0; a <= 360; a += 6) {
          const rad = (a * Math.PI) / 180;
          const pt = project3D(r * Math.cos(rad), 0, r * Math.sin(rad), width, height);
          if (a === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        const isOuter = idx === ringSteps.length - 1;
        ctx.strokeStyle = isOuter ? 'rgba(255, 15, 60, 0.45)' : 'rgba(255, 15, 60, 0.14)';
        ctx.lineWidth = isOuter ? 1.6 : 0.8;
        ctx.stroke();

        // Distance label in unified white/muted style
        const pMetric = project3D(r, 0, 0, width, height);
        if (pMetric.visible) {
          ctx.fillStyle = 'rgba(245, 246, 250, 0.4)';
          ctx.font = '8px JetBrains Mono';
          ctx.fillText(`${Math.round(r * 2.5)}mm`, pMetric.x + 4, pMetric.y - 3);
        }
      });

      // Animated Radar Pulse Wave expanding across the grid
      const pulseWaveR = ((tgt.simTime * 90) % gridR);
      ctx.beginPath();
      for (let a = 0; a <= 360; a += 8) {
        const rad = (a * Math.PI) / 180;
        const pt = project3D(pulseWaveR * Math.cos(rad), 0, pulseWaveR * Math.sin(rad), width, height);
        if (a === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.strokeStyle = `rgba(255, 15, 60, ${0.4 * (1 - pulseWaveR / gridR)})`;
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Cardinal axes
      const cardinalAxes = [
        { label: '090° [E]', x: gridR, z: 0 },
        { label: '270° [W]', x: -gridR, z: 0 },
        { label: '000° [N]', x: 0, z: gridR },
        { label: '180° [S]', x: 0, z: -gridR },
      ];
      cardinalAxes.forEach((ax) => {
        const p0 = project3D(0, 0, 0, width, height);
        const p1 = project3D(ax.x, 0, ax.z, width, height);
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p1.x, p1.y);
        ctx.strokeStyle = 'rgba(255, 15, 60, 0.22)';
        ctx.lineWidth = 1;
        ctx.stroke();

        if (p1.visible) {
          ctx.fillStyle = '#ff0f3d';
          ctx.font = 'bold 9px JetBrains Mono';
          ctx.fillText(ax.label, p1.x + 5, p1.y + 3);
        }
      });
      ctx.restore();

      // 5. Render Trajectory Drop Curtain & Glowing Flight Trail
      if (tgt.trail.length > 3) {
        ctx.save();
        for (let i = 1; i < tgt.trail.length; i++) {
          const ptA = tgt.trail[i - 1];
          const ptB = tgt.trail[i];

          const pA_top = project3D(ptA.x, ptA.y, ptA.z, width, height);
          const pB_top = project3D(ptB.x, ptB.y, ptB.z, width, height);
          const pA_bot = project3D(ptA.x, 0, ptA.z, width, height);
          const pB_bot = project3D(ptB.x, 0, ptB.z, width, height);

          if (!pA_top.visible || !pB_top.visible) continue;

          // Vertical altitude curtain
          const alpha = (i / tgt.trail.length) * 0.16;
          ctx.beginPath();
          ctx.moveTo(pA_top.x, pA_top.y);
          ctx.lineTo(pB_top.x, pB_top.y);
          ctx.lineTo(pB_bot.x, pB_bot.y);
          ctx.lineTo(pA_bot.x, pA_bot.y);
          ctx.closePath();
          ctx.fillStyle = `rgba(255, 15, 60, ${alpha})`;
          ctx.fill();

          // Flight trajectory line
          ctx.beginPath();
          ctx.moveTo(pA_top.x, pA_top.y);
          ctx.lineTo(pB_top.x, pB_top.y);
          ctx.strokeStyle = `rgba(255, 80, 110, ${(i / tgt.trail.length) * 0.9})`;
          ctx.lineWidth = (i / tgt.trail.length) * 2.8;
          ctx.stroke();
        }
        ctx.restore();
      }

      // 6. Target Altitude Dropline & Ground Shadow
      const pTgtGround = project3D(tgt.x, 0, tgt.z, width, height);
      const pTgt = project3D(tgt.x, tgt.y, tgt.z, width, height);

      if (pTgtGround.visible && pTgt.visible) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(pTgtGround.x, pTgtGround.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = 'rgba(255, 80, 110, 0.45)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Ground shadow reticle
        const pingR = 18 * pTgtGround.scale;
        ctx.beginPath();
        ctx.ellipse(pTgtGround.x, pTgtGround.y, pingR * 1.5, pingR * 0.8, 0, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 15, 60, 0.16)';
        ctx.fill();
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.restore();
      }

      // 7. Render 3D Turret Body Model (Military Grade High-Energy Laser Turret)
      ctx.save();

      // Kinematic coordinate basis
      const yawAngle = ((90 - curPan) * Math.PI) / 180;
      const pitchAngle = ((curTilt - 90) * Math.PI) / 180;

      // Turntable horizontal axes (Forward & Right in world space)
      const fwdX = Math.sin(yawAngle);
      const fwdZ = Math.cos(yawAngle);
      const rtX = Math.cos(yawAngle);
      const rtZ = -Math.sin(yawAngle);

      // Gun 3D orthonormal frame (Bore direction, Right, Up)
      const dirX = fwdX * Math.cos(pitchAngle);
      const dirY = Math.sin(pitchAngle);
      const dirZ = fwdZ * Math.cos(pitchAngle);

      const gunRtX = rtX;
      const gunRtY = 0;
      const gunRtZ = rtZ;

      const gunUpX = -Math.sin(pitchAngle) * fwdX;
      const gunUpY = Math.cos(pitchAngle);
      const gunUpZ = -Math.sin(pitchAngle) * fwdZ;

      // 3D Point transformation helpers
      // Turntable frame: (u along rt, Y vertical, w along fwd)
      const toWorldTurntable = (u, y, w) => ({
        x: u * rtX + w * fwdX,
        y: y,
        z: u * rtZ + w * fwdZ,
      });

      // Gun frame: (u along gunRt, v along gunUp, w along dir) centered at (0, pivotY, 0)
      const toWorldGun = (u, v, w) => ({
        x: u * gunRtX + v * gunUpX + w * dirX,
        y: pivotY + u * gunRtY + v * gunUpY + w * dirY,
        z: u * gunRtZ + v * gunUpZ + w * dirZ,
      });

      // 3D Polygonal Face drawing helper
      const draw3DFace = (pts3D, fillStyle, strokeStyle, lineWidth = 1) => {
        if (!pts3D || pts3D.length < 3) return;
        const pts2D = pts3D.map((p) => project3D(p.x, p.y, p.z, width, height));
        if (!pts2D.some((p) => p.visible)) return;
        ctx.beginPath();
        ctx.moveTo(pts2D[0].x, pts2D[0].y);
        for (let i = 1; i < pts2D.length; i++) {
          ctx.lineTo(pts2D[i].x, pts2D[i].y);
        }
        ctx.closePath();
        if (fillStyle) {
          ctx.fillStyle = fillStyle;
          ctx.fill();
        }
        if (strokeStyle) {
          ctx.strokeStyle = strokeStyle;
          ctx.lineWidth = lineWidth;
          ctx.stroke();
        }
      };

      // Helper to draw a shaded 3D prism / box in any coordinate basis
      const draw3DBox = (corners, topFill, sideFillA, sideFillB, strokeStyle, lineWidth = 1) => {
        // corners: [b0, b1, b2, b3, t0, t1, t2, t3] (bottom 4, top 4)
        draw3DFace([corners[4], corners[5], corners[6], corners[7]], topFill, strokeStyle, lineWidth);
        draw3DFace([corners[0], corners[1], corners[5], corners[4]], sideFillA, strokeStyle, lineWidth);
        draw3DFace([corners[1], corners[2], corners[6], corners[5]], sideFillB, strokeStyle, lineWidth);
        draw3DFace([corners[2], corners[3], corners[7], corners[6]], sideFillA, strokeStyle, lineWidth);
        draw3DFace([corners[3], corners[0], corners[4], corners[7]], sideFillB, strokeStyle, lineWidth);
      };

      // ==========================================
      // (A) STATIONARY HEAVY GROUND PEDESTAL & BEARING
      // ==========================================
      // Octagonal fortified foundation baseplate (Y = 0 to Y = 12)
      const baseR_bot = 88;
      const baseR_top = 78;
      const octPts_bot = [];
      const octPts_top = [];
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI) / 4 + Math.PI / 8;
        octPts_bot.push({ x: baseR_bot * Math.cos(a), y: 0, z: baseR_bot * Math.sin(a) });
        octPts_top.push({ x: baseR_top * Math.cos(a), y: 12, z: baseR_top * Math.sin(a) });
      }

      // Draw octagonal side chamfered armor plates
      for (let i = 0; i < 8; i++) {
        const next = (i + 1) % 8;
        const shade = i % 2 === 0 ? '#1b0e18' : '#261222';
        draw3DFace([octPts_bot[i], octPts_bot[next], octPts_top[next], octPts_top[i]], shade, 'rgba(255, 15, 60, 0.45)', 1);
      }
      // Top face of ground baseplate
      draw3DFace(octPts_top, '#160913', '#ff0f3d', 1.5);

      // Heavy anchor bolt studs at the 8 vertices
      for (let i = 0; i < 8; i++) {
        const pBolt = project3D(octPts_top[i].x * 0.92, 13, octPts_top[i].z * 0.92, width, height);
        if (pBolt.visible) {
          ctx.beginPath();
          ctx.arc(pBolt.x, pBolt.y, 2.5 * pBolt.scale, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
        }
      }

      // Slewing Azimuth Bearing Collar (Y = 12 to Y = 30, radius 54)
      const azR = 54;
      const azSegs = 12;
      const azBot = [];
      const azTop = [];
      for (let i = 0; i < azSegs; i++) {
        const a = (i * 2 * Math.PI) / azSegs;
        azBot.push({ x: azR * Math.cos(a), y: 12, z: azR * Math.sin(a) });
        azTop.push({ x: azR * Math.cos(a), y: 30, z: azR * Math.sin(a) });
      }
      for (let i = 0; i < azSegs; i++) {
        const next = (i + 1) % azSegs;
        const shade = i % 2 === 0 ? '#120710' : '#1f0d1b';
        draw3DFace([azBot[i], azBot[next], azTop[next], azTop[i]], shade, 'rgba(255, 15, 60, 0.25)', 0.8);
      }

      // Recessed Crimson Azimuth LED Status Channel (Y = 22)
      ctx.beginPath();
      for (let a = 0; a <= 360; a += 15) {
        const rad = (a * Math.PI) / 180;
        const pt = project3D(55 * Math.cos(rad), 22, 55 * Math.sin(rad), width, height);
        if (a === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.strokeStyle = `rgba(255, 15, 60, ${0.5 + 0.35 * Math.sin(tgt.simTime * 3.5)})`;
      ctx.lineWidth = 2.2;
      ctx.stroke();

      // ==========================================
      // (B) ROTATING PAN TURNTABLE DECK & SERVO (Y = 30 to Y = 42)
      // ==========================================
      // Turntable disk (radius 46)
      const deckR = 46;
      const deckSegs = 12;
      const deckBot = [];
      const deckTop = [];
      for (let i = 0; i < deckSegs; i++) {
        const a = (i * 2 * Math.PI) / deckSegs + yawAngle;
        deckBot.push({ x: deckR * Math.cos(a), y: 30, z: deckR * Math.sin(a) });
        deckTop.push({ x: deckR * Math.cos(a), y: 42, z: deckR * Math.sin(a) });
      }
      for (let i = 0; i < deckSegs; i++) {
        const next = (i + 1) % deckSegs;
        const shade = i % 2 === 0 ? '#220f1e' : '#2e1428';
        draw3DFace([deckBot[i], deckBot[next], deckTop[next], deckTop[i]], shade, 'rgba(255, 15, 60, 0.5)', 1);
      }
      draw3DFace(deckTop, '#190a16', '#ff0f3d', 1.8);

      // Pan Servo Motor Gearbox Block on rear of turntable deck (w = -28 to -8, u = -18 to 18, Y = 42 to 58)
      const srvC = [
        toWorldTurntable(-18, 42, -28),
        toWorldTurntable(18, 42, -28),
        toWorldTurntable(18, 42, -8),
        toWorldTurntable(-18, 42, -8),
        toWorldTurntable(-18, 58, -28),
        toWorldTurntable(18, 58, -28),
        toWorldTurntable(18, 58, -8),
        toWorldTurntable(-18, 58, -8),
      ];
      draw3DBox(srvC, '#2c1226', '#1a0917', '#250f20', '#ff0f3d', 1.2);

      // Servo Cooling Fins (3 parallel lines on side)
      for (let f = 0; f < 3; f++) {
        const yFin = 46 + f * 4;
        const pF1 = project3D(...Object.values(toWorldTurntable(18.5, yFin, -26)), width, height);
        const pF2 = project3D(...Object.values(toWorldTurntable(18.5, yFin, -10)), width, height);
        if (pF1.visible && pF2.visible) {
          ctx.beginPath();
          ctx.moveTo(pF1.x, pF1.y);
          ctx.lineTo(pF2.x, pF2.y);
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.2;
          ctx.stroke();
        }
      }

      // ==========================================
      // (C) DUAL-PYLON STANCHION & LEAD SCREW (Height d mm)
      // ==========================================
      const pylonTopY = pivotY - 8;

      // Left Heavy Armored Pylon (u = -28 to -16, w = -8 to 8)
      const pylonLeft = [
        toWorldTurntable(-28, 42, -8),
        toWorldTurntable(-16, 42, -8),
        toWorldTurntable(-16, 42, 8),
        toWorldTurntable(-28, 42, 8),
        toWorldTurntable(-28, pylonTopY, -8),
        toWorldTurntable(-16, pylonTopY, -8),
        toWorldTurntable(-16, pylonTopY, 8),
        toWorldTurntable(-28, pylonTopY, 8),
      ];
      draw3DBox(pylonLeft, '#381630', '#1c0a18', '#260e21', '#ff0f3d', 1.4);

      // Right Heavy Armored Pylon (u = 16 to 28, w = -8 to 8)
      const pylonRight = [
        toWorldTurntable(16, 42, -8),
        toWorldTurntable(28, 42, -8),
        toWorldTurntable(28, 42, 8),
        toWorldTurntable(16, 42, 8),
        toWorldTurntable(16, pylonTopY, -8),
        toWorldTurntable(28, pylonTopY, -8),
        toWorldTurntable(28, pylonTopY, 8),
        toWorldTurntable(16, pylonTopY, 8),
      ];
      draw3DBox(pylonRight, '#381630', '#1c0a18', '#260e21', '#ff0f3d', 1.4);

      // Center Chrome Precision Ball-Screw Shaft
      const pScrewBot = project3D(...Object.values(toWorldTurntable(0, 42, 0)), width, height);
      const pScrewTop = project3D(...Object.values(toWorldTurntable(0, pylonTopY + 2, 0)), width, height);
      if (pScrewBot.visible && pScrewTop.visible) {
        ctx.beginPath();
        ctx.moveTo(pScrewBot.x, pScrewBot.y);
        ctx.lineTo(pScrewTop.x, pScrewTop.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 4 * pScrewBot.scale;
        ctx.stroke();

        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Ball screw thread ridges
        const threadCount = Math.floor(stanchionHeight / 14);
        for (let t = 1; t <= threadCount; t++) {
          const yT = 42 + (stanchionHeight * t) / (threadCount + 1);
          const pTh1 = project3D(...Object.values(toWorldTurntable(-4, yT, 0)), width, height);
          const pTh2 = project3D(...Object.values(toWorldTurntable(4, yT, 0)), width, height);
          if (pTh1.visible && pTh2.visible) {
            ctx.beginPath();
            ctx.moveTo(pTh1.x, pTh1.y);
            ctx.lineTo(pTh2.x, pTh2.y);
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.4;
            ctx.stroke();
          }
        }
      }

      // Structural X-Truss Cross Bracing Between Pylons
      const yTrussA = 42 + stanchionHeight * 0.28;
      const yTrussB = 42 + stanchionHeight * 0.72;
      const pT1 = project3D(...Object.values(toWorldTurntable(-16, yTrussA, 0)), width, height);
      const pT2 = project3D(...Object.values(toWorldTurntable(16, yTrussB, 0)), width, height);
      const pT3 = project3D(...Object.values(toWorldTurntable(-16, yTrussB, 0)), width, height);
      const pT4 = project3D(...Object.values(toWorldTurntable(16, yTrussA, 0)), width, height);
      if (pT1.visible && pT2.visible) {
        ctx.beginPath();
        ctx.moveTo(pT1.x, pT1.y);
        ctx.lineTo(pT2.x, pT2.y);
        ctx.moveTo(pT3.x, pT3.y);
        ctx.lineTo(pT4.x, pT4.y);
        ctx.strokeStyle = 'rgba(255, 15, 60, 0.7)';
        ctx.lineWidth = 2 * pT1.scale;
        ctx.stroke();
      }

      // Vernier Millimeter Height Scale along Right Pylon
      for (let mm = 0; mm <= 200; mm += 40) {
        const yVal = 42 + (mm / 200) * stanchionHeight;
        const pTickA = project3D(...Object.values(toWorldTurntable(28, yVal, 8)), width, height);
        const pTickB = project3D(...Object.values(toWorldTurntable(34, yVal, 8)), width, height);
        if (pTickA.visible && pTickB.visible) {
          ctx.beginPath();
          ctx.moveTo(pTickA.x, pTickA.y);
          ctx.lineTo(pTickB.x, pTickB.y);
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }

      // Tactical Caliper HUD Bracket for d mm
      const pDimA = project3D(...Object.values(toWorldTurntable(46, 42, 0)), width, height);
      const pDimB = project3D(...Object.values(toWorldTurntable(46, pivotY, 0)), width, height);
      if (pDimA.visible && pDimB.visible) {
        ctx.beginPath();
        ctx.moveTo(pDimA.x, pDimA.y);
        ctx.lineTo(pDimB.x, pDimB.y);
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.4;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pDimA.x - 6, pDimA.y);
        ctx.lineTo(pDimA.x + 6, pDimA.y);
        ctx.moveTo(pDimB.x - 6, pDimB.y);
        ctx.lineTo(pDimB.x + 6, pDimB.y);
        ctx.stroke();

        const midX = (pDimA.x + pDimB.x) / 2;
        const midY = (pDimA.y + pDimB.y) / 2;
        ctx.fillStyle = 'rgba(12, 5, 10, 0.95)';
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.2;
        ctx.fillRect(midX + 6, midY - 11, 74, 22);
        ctx.strokeRect(midX + 6, midY - 11, 74, 22);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px JetBrains Mono';
        ctx.fillText(`d = ${localDistance}mm`, midX + 11, midY + 4);
      }

      // ==========================================
      // (D) ELEVATION GIMBAL U-CRADLE & TRUNNIONS
      // ==========================================
      // Horizontal Gimbal Saddle Bridge (u = -32 to 32, Y = pivotY - 12 to pivotY - 2, w = -10 to 10)
      const saddle = [
        toWorldTurntable(-32, pivotY - 12, -10),
        toWorldTurntable(32, pivotY - 12, -10),
        toWorldTurntable(32, pivotY - 12, 10),
        toWorldTurntable(-32, pivotY - 12, 10),
        toWorldTurntable(-32, pivotY - 2, -10),
        toWorldTurntable(32, pivotY - 2, -10),
        toWorldTurntable(32, pivotY - 2, 10),
        toWorldTurntable(-32, pivotY - 2, 10),
      ];
      draw3DBox(saddle, '#34152c', '#180814', '#260f21', '#ff0f3d', 1.4);

      // Left Trunnion Bearing Arm (u = -30 to -24, Y = pivotY - 2 to pivotY + 12, w = -8 to 8)
      const armLeft = [
        toWorldTurntable(-30, pivotY - 2, -8),
        toWorldTurntable(-24, pivotY - 2, -8),
        toWorldTurntable(-24, pivotY - 2, 8),
        toWorldTurntable(-30, pivotY - 2, 8),
        toWorldTurntable(-30, pivotY + 12, -8),
        toWorldTurntable(-24, pivotY + 12, -8),
        toWorldTurntable(-24, pivotY + 12, 8),
        toWorldTurntable(-30, pivotY + 12, 8),
      ];
      draw3DBox(armLeft, '#3d1834', '#1f0a1b', '#2a0e24', '#ff0f3d', 1.2);

      // Right Trunnion Bearing Arm (u = 24 to 30, Y = pivotY - 2 to pivotY + 12, w = -8 to 8)
      const armRight = [
        toWorldTurntable(24, pivotY - 2, -8),
        toWorldTurntable(30, pivotY - 2, -8),
        toWorldTurntable(30, pivotY - 2, 8),
        toWorldTurntable(24, pivotY - 2, 8),
        toWorldTurntable(24, pivotY + 12, -8),
        toWorldTurntable(30, pivotY + 12, -8),
        toWorldTurntable(30, pivotY + 12, 8),
        toWorldTurntable(24, pivotY + 12, 8),
      ];
      draw3DBox(armRight, '#3d1834', '#1f0a1b', '#2a0e24', '#ff0f3d', 1.2);

      // Bilateral Trunnion Bearing Hubs (Large Heavy Axis Bearings)
      const pPivotL = project3D(...Object.values(toWorldTurntable(-28, pivotY, 0)), width, height);
      const pPivotR = project3D(...Object.values(toWorldTurntable(28, pivotY, 0)), width, height);
      if (pPivotL.visible) {
        ctx.beginPath();
        ctx.arc(pPivotL.x, pPivotL.y, 8.5 * pPivotL.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#220e1e';
        ctx.fill();
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.8;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(pPivotL.x, pPivotL.y, 3 * pPivotL.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
      }
      if (pPivotR.visible) {
        // Elevation Servo Motor Canister on right trunnion
        ctx.beginPath();
        ctx.arc(pPivotR.x, pPivotR.y, 11 * pPivotR.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#311228';
        ctx.fill();
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 2.2;
        ctx.stroke();

        // Rotary Encoder Dial
        ctx.beginPath();
        ctx.arc(pPivotR.x, pPivotR.y, 4.5 * pPivotR.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
      }

      // ==========================================
      // (E) VOLUMETRIC ARMORED LASER CANNON POD
      // ==========================================
      // 1. Rear Counterweight & Radiator Chassis (w = -44 to -6, u = -18 to 18, v = -12 to 14)
      const rearPod = [
        toWorldGun(-18, -12, -44),
        toWorldGun(18, -12, -44),
        toWorldGun(18, -12, -6),
        toWorldGun(-18, -12, -6),
        toWorldGun(-16, 14, -44),
        toWorldGun(16, 14, -44),
        toWorldGun(18, 14, -6),
        toWorldGun(-18, 14, -6),
      ];
      draw3DBox(rearPod, '#32142b', '#180815', '#240d1f', '#ff0f3d', 1.4);

      // Glowing Rear Thermal Dissipation Vents
      for (let v = 0; v < 3; v++) {
        const wVent = -36 + v * 10;
        const pV1 = project3D(...Object.values(toWorldGun(-15, 14.5, wVent)), width, height);
        const pV2 = project3D(...Object.values(toWorldGun(15, 14.5, wVent)), width, height);
        if (pV1.visible && pV2.visible) {
          ctx.beginPath();
          ctx.moveTo(pV1.x, pV1.y);
          ctx.lineTo(pV2.x, pV2.y);
          ctx.strokeStyle = `rgba(255, 30, 70, ${0.5 + 0.4 * Math.sin(tgt.simTime * 5 + v)})`;
          ctx.lineWidth = 3.5 * pV1.scale;
          ctx.stroke();
        }
      }

      // Dual High-Voltage Capacitors on Top-Rear
      const pCapL1 = project3D(...Object.values(toWorldGun(-10, 16, -34)), width, height);
      const pCapL2 = project3D(...Object.values(toWorldGun(-10, 16, -12)), width, height);
      const pCapR1 = project3D(...Object.values(toWorldGun(10, 16, -34)), width, height);
      const pCapR2 = project3D(...Object.values(toWorldGun(10, 16, -12)), width, height);
      if (pCapL1.visible && pCapL2.visible) {
        ctx.beginPath();
        ctx.moveTo(pCapL1.x, pCapL1.y);
        ctx.lineTo(pCapL2.x, pCapL2.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 5 * pCapL1.scale;
        ctx.lineCap = 'round';
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pCapR1.x, pCapR1.y);
        ctx.lineTo(pCapR2.x, pCapR2.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 5 * pCapR1.scale;
        ctx.lineCap = 'round';
        ctx.stroke();
      }

      // 2. Main Armored Laser Receiver Chassis (w = -6 to 38, u = -22 to 22, v = -14 to 16)
      const mainChassis = [
        toWorldGun(-22, -14, -6),
        toWorldGun(22, -14, -6),
        toWorldGun(22, -14, 38),
        toWorldGun(-22, -14, 38),
        toWorldGun(-22, 16, -6),
        toWorldGun(22, 16, -6),
        toWorldGun(20, 15, 38),
        toWorldGun(-20, 15, 38),
      ];
      draw3DBox(mainChassis, '#3a1732', '#1a0917', '#290f23', '#ff0f3d', 1.6);

      // 3. Co-Axial Electro-Optical Sensor Turret (Agesis "EYE" Tracking Gimbal)
      // Mounted atop receiver at v = 16 to 27, w = 10 to 28, u = -9 to 9
      const optPod = [
        toWorldGun(-9, 16, 10),
        toWorldGun(9, 16, 10),
        toWorldGun(9, 16, 28),
        toWorldGun(-9, 16, 28),
        toWorldGun(-8, 27, 10),
        toWorldGun(8, 27, 10),
        toWorldGun(8, 27, 28),
        toWorldGun(-8, 27, 28),
      ];
      draw3DBox(optPod, '#481c3e', '#220b1f', '#32102c', '#ff0f3d', 1.2);

      // Sapphire Glass Sensor Objective Lens (Facing forward at w = 28.5)
      const pLens = project3D(...Object.values(toWorldGun(0, 21.5, 28.5)), width, height);
      if (pLens.visible) {
        ctx.beginPath();
        ctx.arc(pLens.x, pLens.y, 6.5 * pLens.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#061a28';
        ctx.fill();
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 1.6;
        ctx.stroke();

        // Antireflective coating glare
        ctx.beginPath();
        ctx.arc(pLens.x, pLens.y, 4 * pLens.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ff0f3d';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(pLens.x - 2 * pLens.scale, pLens.y - 2 * pLens.scale, 1.8 * pLens.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
      }

      // 4. Stepped High-Energy Laser Emitter Barrel (w = 38 to 96)
      // Stage 1: Hexagonal Heavy Collar (w = 38 to 54, radius 15)
      const colSegs = 6;
      const colBot = [];
      const colTop = [];
      for (let i = 0; i < colSegs; i++) {
        const a = (i * 2 * Math.PI) / colSegs;
        const u = 15 * Math.cos(a);
        const v = 15 * Math.sin(a);
        colBot.push(toWorldGun(u, v, 38));
        colTop.push(toWorldGun(u, v, 54));
      }
      for (let i = 0; i < colSegs; i++) {
        const next = (i + 1) % colSegs;
        const shade = i % 2 === 0 ? '#2a0f25' : '#381531';
        draw3DFace([colBot[i], colBot[next], colTop[next], colTop[i]], shade, 'rgba(255, 15, 60, 0.6)', 1.2);
      }

      // Stage 2: Magnetic Beam-Focusing Shroud (w = 54 to 76, radius 11)
      const shrSegs = 8;
      const shrBot = [];
      const shrTop = [];
      for (let i = 0; i < shrSegs; i++) {
        const a = (i * 2 * Math.PI) / shrSegs;
        const u = 11 * Math.cos(a);
        const v = 11 * Math.sin(a);
        shrBot.push(toWorldGun(u, v, 54));
        shrTop.push(toWorldGun(u, v, 76));
      }
      for (let i = 0; i < shrSegs; i++) {
        const next = (i + 1) % shrSegs;
        const shade = i % 2 === 0 ? '#1b0918' : '#260e22';
        draw3DFace([shrBot[i], shrBot[next], shrTop[next], shrTop[i]], shade, 'rgba(255, 15, 60, 0.5)', 1);
      }

      // Gold Magnetic Focusing Coils on Shroud
      for (let c = 0; c < 2; c++) {
        const wCoil = 60 + c * 10;
        ctx.beginPath();
        for (let a = 0; a <= 360; a += 30) {
          const rad = (a * Math.PI) / 180;
          const pt = project3D(...Object.values(toWorldGun(11.5 * Math.cos(rad), 11.5 * Math.sin(rad), wCoil)), width, height);
          if (a === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.4;
        ctx.stroke();
      }

      // Stage 3: Collimator Barrel & Muzzle Shroud (w = 76 to 96, radius 8)
      const pBrlBase = project3D(...Object.values(toWorldGun(0, 0, 76)), width, height);
      const pMuzzle = project3D(...Object.values(toWorldGun(0, 0, 96)), width, height);
      if (pBrlBase.visible && pMuzzle.visible) {
        ctx.beginPath();
        ctx.moveTo(pBrlBase.x, pBrlBase.y);
        ctx.lineTo(pMuzzle.x, pMuzzle.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 8.5 * pMuzzle.scale;
        ctx.lineCap = 'butt';
        ctx.stroke();

        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 3.5 * pMuzzle.scale;
        ctx.stroke();
      }

      // Muzzle Aperture Face & Collimation Quartz Lens Ring (w = 96)
      if (pMuzzle.visible) {
        ctx.beginPath();
        ctx.arc(pMuzzle.x, pMuzzle.y, 7.5 * pMuzzle.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#220819';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.8;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(pMuzzle.x, pMuzzle.y, 4 * pMuzzle.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ff0f3d';
        ctx.fill();
      }

      // ==========================================
      // (F) HIGH-POWER COHERENT TARGETING LASER BEAM
      // ==========================================
      const isBeamFiring = (beamEnabled || isLaserFiring) && !tgt.isDestroyed;
      if (isBeamFiring && pMuzzle.visible && pTgt.visible) {
        // 1. Muzzle Ionization Starburst & Corona Flare
        ctx.save();
        const mScale = pMuzzle.scale;

        // Wide Atmospheric Ionization Corona
        const flareGrad = ctx.createRadialGradient(
          pMuzzle.x,
          pMuzzle.y,
          2,
          pMuzzle.x,
          pMuzzle.y,
          36 * mScale
        );
        flareGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
        flareGrad.addColorStop(0.2, 'rgba(255, 15, 60, 0.9)');
        flareGrad.addColorStop(0.55, 'rgba(255, 15, 60, 0.35)');
        flareGrad.addColorStop(1, 'rgba(255, 15, 60, 0)');

        ctx.beginPath();
        ctx.arc(pMuzzle.x, pMuzzle.y, 36 * mScale, 0, Math.PI * 2);
        ctx.fillStyle = flareGrad;
        ctx.fill();

        // 4-Point Anamorphic Diffraction Flare Needles
        ctx.beginPath();
        ctx.moveTo(pMuzzle.x - 55 * mScale, pMuzzle.y);
        ctx.lineTo(pMuzzle.x + 55 * mScale, pMuzzle.y);
        ctx.moveTo(pMuzzle.x, pMuzzle.y - 35 * mScale);
        ctx.lineTo(pMuzzle.x, pMuzzle.y + 35 * mScale);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pMuzzle.x - 30 * mScale, pMuzzle.y);
        ctx.lineTo(pMuzzle.x + 30 * mScale, pMuzzle.y);
        ctx.moveTo(pMuzzle.x, pMuzzle.y - 20 * mScale);
        ctx.lineTo(pMuzzle.x, pMuzzle.y + 20 * mScale);
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 3.5 * mScale;
        ctx.stroke();

        // 2. Collinear High-Intensity Laser Beam
        // Layer A: Atmospheric Ionization Tube Bloom
        ctx.beginPath();
        ctx.moveTo(pMuzzle.x, pMuzzle.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = 'rgba(255, 15, 60, 0.22)';
        ctx.lineWidth = 22 * mScale;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Layer B: Intense Crimson Coherent Plasma Channel
        ctx.beginPath();
        ctx.moveTo(pMuzzle.x, pMuzzle.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 5.5 * mScale;
        ctx.shadowColor = '#ff0f3d';
        ctx.shadowBlur = 24;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Layer C: Ultra-Dense Concentrated Diamond-White Core
        ctx.beginPath();
        ctx.moveTo(pMuzzle.x, pMuzzle.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.8;
        ctx.stroke();

        // Layer D: Traveling High-Energy Photon Packets (3 staggered ripple pulses)
        for (let k = 0; k < 3; k++) {
          const waveFrac = ((tgt.simTime * 3.4 + k * 0.33) % 1.0);
          const waveX = pMuzzle.x + (pTgt.x - pMuzzle.x) * waveFrac;
          const waveY = pMuzzle.y + (pTgt.y - pMuzzle.y) * waveFrac;
          ctx.beginPath();
          ctx.arc(waveX, waveY, (5 + (1 - waveFrac) * 3) * mScale, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#ff0f3d';
          ctx.shadowBlur = 14;
          ctx.fill();
          ctx.shadowBlur = 0;
        }

        // Layer E: 3D Helical Magnetic Confinement Filaments
        ctx.beginPath();
        const helixSteps = 24;
        const muzW = toWorldGun(0, 0, 96);
        for (let s = 0; s <= helixSteps; s++) {
          const frac = s / helixSteps;
          const hX = muzW.x + (tgt.x - muzW.x) * frac;
          const hY = muzW.y + (tgt.y - muzW.y) * frac;
          const hZ = muzW.z + (tgt.z - muzW.z) * frac;
          const theta = frac * Math.PI * 10 + tgt.simTime * 14;
          const hR = 4.5 + Math.sin(frac * Math.PI) * 3.5;
          const offX = hR * (Math.cos(theta) * gunRtX + Math.sin(theta) * gunUpX);
          const offY = hR * (Math.cos(theta) * gunRtY + Math.sin(theta) * gunUpY);
          const offZ = hR * (Math.cos(theta) * gunRtZ + Math.sin(theta) * gunUpZ);
          const pH = project3D(hX + offX, hY + offY, hZ + offZ, width, height);
          if (s === 0) ctx.moveTo(pH.x, pH.y);
          else ctx.lineTo(pH.x, pH.y);
        }
        ctx.strokeStyle = 'rgba(255, 80, 110, 0.45)';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // 3. Focal Impact Flash on Target
        ctx.beginPath();
        ctx.arc(pTgt.x, pTgt.y, 9 * pTgt.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ff0f3d';
        ctx.shadowBlur = 22;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.restore();
      }
      ctx.restore();

      // 8. Render Target Entity (Tactical Drone / Burst & Respawn Dynamics)
      if (pTgt.visible) {
        ctx.save();
        const tgtSize = Math.max(16, 22 * pTgt.scale);

        if (tgt.isDestroyed) {
          // ============================================
          // TARGET BURST / EXPLOSION VISUAL EFFECTS
          // ============================================
          // 1. Concentric Expanding Shockwave Rings in 3D
          tgt.shockwaves.forEach((sw) => {
            const pSw = project3D(sw.x, sw.y, sw.z, width, height);
            if (pSw.visible && sw.life > 0) {
              const swR = sw.r * pSw.scale;
              ctx.beginPath();
              ctx.arc(pSw.x, pSw.y, swR, 0, Math.PI * 2);
              ctx.strokeStyle = `rgba(255, 255, 255, ${sw.life * 0.9})`;
              ctx.lineWidth = 2.5 * pSw.scale;
              ctx.stroke();

              ctx.beginPath();
              ctx.arc(pSw.x, pSw.y, swR * 1.25, 0, Math.PI * 2);
              ctx.strokeStyle = `rgba(255, 15, 60, ${sw.life * 0.6})`;
              ctx.lineWidth = 4 * pSw.scale;
              ctx.stroke();
            }
          });

          // 2. High-Velocity Incandescent Debris & Shrapnel
          tgt.debris.forEach((deb) => {
            const pDeb = project3D(deb.x, deb.y, deb.z, width, height);
            if (pDeb.visible && deb.life > 0) {
              ctx.beginPath();
              ctx.arc(pDeb.x, pDeb.y, deb.size * pDeb.scale, 0, Math.PI * 2);
              const r = 255;
              const g = deb.life > 0.4 ? Math.floor(deb.life * 255) : 30;
              const b = deb.life > 0.7 ? Math.floor(deb.life * 255) : 0;
              ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${Math.min(1, deb.life * 1.5)})`;
              ctx.shadowColor = '#ff0f3d';
              ctx.shadowBlur = 10;
              ctx.fill();
              ctx.shadowBlur = 0;
            }
          });

          // 3. Central Detonation Plasma Flash (first 0.35s)
          if (tgt.burstTimer < 0.35) {
            const flashAlpha = 1.0 - tgt.burstTimer / 0.35;
            ctx.beginPath();
            ctx.arc(pTgt.x, pTgt.y, tgtSize * 2.8 * (1 + tgt.burstTimer * 1.8), 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha * 0.95})`;
            ctx.shadowColor = '#ff0f3d';
            ctx.shadowBlur = 35;
            ctx.fill();
            ctx.shadowBlur = 0;
          }

          // 4. Tactical Destruction / Respawn HUD Badge
          const tagX = pTgt.x + tgtSize + 12;
          const tagY = pTgt.y - 18;
          ctx.fillStyle = 'rgba(18, 5, 10, 0.95)';
          ctx.strokeStyle = '#ff0f3d';
          ctx.lineWidth = 1.4;
          ctx.fillRect(tagX, tagY, 138, 48);
          ctx.strokeRect(tagX, tagY, 138, 48);

          ctx.fillStyle = 'rgba(255, 15, 60, 0.3)';
          ctx.fillRect(tagX, tagY, 138, 14);

          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 8.5px JetBrains Mono';
          ctx.fillText('TARGET BURST // DETONATED', tagX + 6, tagY + 10);

          ctx.fillStyle = '#ff0f3d';
          ctx.font = 'bold 8px JetBrains Mono';
          ctx.fillText(`KILLS: ${tgt.killCount || 1}`, tagX + 6, tagY + 26);

          ctx.fillStyle = '#ffffff';
          ctx.font = '7.5px JetBrains Mono';
          const respawnRemaining = Math.max(0, 1.4 - tgt.burstTimer).toFixed(1);
          ctx.fillText(`RESPAWN IN: ${respawnRemaining}s`, tagX + 6, tagY + 38);

        } else {
          // ============================================
          // TARGET IN FLIGHT (PRESERVE AESTHETIC 100%)
          // ============================================
          const renderX = pTgt.x + (tgt.heat > 0.1 ? (Math.random() - 0.5) * tgt.heat * 4 : 0);
          const renderY = pTgt.y + (tgt.heat > 0.1 ? (Math.random() - 0.5) * tgt.heat * 4 : 0);

          // Concentric Target Acquisition Rings
          ctx.beginPath();
          ctx.arc(renderX, renderY, tgtSize * 1.6, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(255, 15, 60, ${0.45 + 0.3 * Math.sin(tgt.simTime * 6)})`;
          ctx.lineWidth = 1.2;
          ctx.setLineDash([4, 4]);
          ctx.stroke();
          ctx.setLineDash([]);

          // Respawn Warp-in Matrix Ring (if newly respawned)
          if (tgt.respawnWarp < 1.0) {
            const warpR = tgtSize * (1.0 + (1.0 - tgt.respawnWarp) * 2.5);
            ctx.beginPath();
            ctx.arc(renderX, renderY, warpR, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(255, 255, 255, ${1.0 - tgt.respawnWarp})`;
            ctx.lineWidth = 2;
            ctx.stroke();
          }

          // Target Body Shaded Sphere with Heat Transition
          const tgtGrad = ctx.createRadialGradient(
            renderX - tgtSize * 0.35,
            renderY - tgtSize * 0.35,
            2,
            renderX,
            renderY,
            tgtSize
          );
          if (tgt.heat > 0.4) {
            // White-hot melting thermite core under intense laser attack
            tgtGrad.addColorStop(0, '#ffffff');
            tgtGrad.addColorStop(0.3, '#ffaa44');
            tgtGrad.addColorStop(0.7, '#ff0f3d');
            tgtGrad.addColorStop(1, '#550011');
          } else {
            // Crisp tactical crimson aesthetic
            tgtGrad.addColorStop(0, '#ffffff');
            tgtGrad.addColorStop(0.3, '#ff2250');
            tgtGrad.addColorStop(0.7, '#990020');
            tgtGrad.addColorStop(1, '#33000a');
          }

          ctx.beginPath();
          ctx.arc(renderX, renderY, tgtSize, 0, Math.PI * 2);
          ctx.fillStyle = tgtGrad;
          ctx.fill();
          ctx.strokeStyle = tgt.heat > 0.5 ? '#ffffff' : '#ff0f3d';
          ctx.lineWidth = 1.6;
          ctx.stroke();

          // Spinning Rotor Arms
          const rotorR = tgtSize * 1.5;
          const rAngle = tgt.simTime * 18;
          for (let i = 0; i < 4; i++) {
            const a = (i * Math.PI) / 2 + rAngle;
            const rx = renderX + rotorR * Math.cos(a);
            const ry = renderY + rotorR * 0.5 * Math.sin(a);
            ctx.beginPath();
            ctx.moveTo(renderX, renderY);
            ctx.lineTo(rx, ry);
            ctx.strokeStyle = 'rgba(255, 15, 60, 0.6)';
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(rx, ry, 3.5 * pTgt.scale, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
          }

          // Laser Impact Sparks (Molten Slag Glow)
          tgt.sparks.forEach((sp) => {
            const pSpark = project3D(sp.x, sp.y, sp.z, width, height);
            if (pSpark.visible) {
              ctx.beginPath();
              ctx.arc(pSpark.x, pSpark.y, (sp.size || 2) * pSpark.scale, 0, Math.PI * 2);
              const r = 255;
              const g = sp.life > 0.45 ? Math.floor((sp.life - 0.45) * 2 * 255) : 0;
              const b = sp.life > 0.75 ? Math.floor((sp.life - 0.75) * 4 * 255) : 0;
              ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${Math.min(1, sp.life * 1.6)})`;
              ctx.fill();
            }
          });

          // 3D Holographic Target HUD Tag (Unified Crimson & White)
          const tagX = renderX + tgtSize + 12;
          const tagY = renderY - 18;
          ctx.fillStyle = 'rgba(10, 4, 8, 0.94)';
          ctx.strokeStyle = '#ff0f3d';
          ctx.lineWidth = 1.2;
          ctx.fillRect(tagX, tagY, 138, 54);
          ctx.strokeRect(tagX, tagY, 138, 54);

          // Header strip
          ctx.fillStyle = 'rgba(255, 15, 60, 0.2)';
          ctx.fillRect(tagX, tagY, 138, 14);

          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 8.5px JetBrains Mono';
          const tgtId = `TGT-${String((tgt.killCount || 0) + 1).padStart(2, '0')}`;
          ctx.fillText(`TARGET // ${tgtId}`, tagX + 6, tagY + 10);

          ctx.fillStyle = '#f5f6fa';
          ctx.font = '7.5px JetBrains Mono';
          const distM = (Math.hypot(tgt.x, tgt.y - pivotY, tgt.z) / 100).toFixed(2);
          const velM = (Math.hypot(tgt.vx, tgt.vy, tgt.vz) / 100).toFixed(1);
          ctx.fillText(`RANGE : ${distM} m`, tagX + 6, tagY + 23);
          ctx.fillText(`ALT   : ${(tgt.y / 100).toFixed(2)} m`, tagX + 6, tagY + 32);

          // Thermal Integrity Bar
          const healthFrac = Math.max(0, 1 - (tgt.heat || 0));
          ctx.fillStyle = tgt.heat > 0.6 ? '#ff0f3d' : '#ffffff';
          ctx.fillText(`HULL  : ${(healthFrac * 100).toFixed(0)}%`, tagX + 6, tagY + 41);
          
          // Mini integrity bar
          ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
          ctx.fillRect(tagX + 6, tagY + 45, 126, 4);
          ctx.fillStyle = tgt.heat > 0.6 ? '#ff0f3d' : '#ffffff';
          ctx.fillRect(tagX + 6, tagY + 45, 126 * healthFrac, 4);
        }

        ctx.restore();
      }

      // 9. Navigation Legend
      ctx.save();
      ctx.fillStyle = 'rgba(166, 146, 152, 0.6)';
      ctx.font = '8px JetBrains Mono';
      ctx.fillText('DRAG: ORBIT 3D // SCROLL: ZOOM // RIGHT-DRAG: PAN', 16, height - 16);
      ctx.restore();

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [project3D, localDistance, simMode, targetSpeed, targetAltitude, targetRadius, beamEnabled, autoOrbit, isLaserFiring, isLaserArmed]);

  return (
    <div className="digital-twin-container">
      {/* Top HUD Header with Real-Time Kinematic Readouts */}
      <div className="dt-hud-header">
        <div className="dt-title-block">
          <div className="dt-radar-icon">
            <div className="dt-pulse-circle"></div>
          </div>
          <div>
            <h2 className="dt-title">3D KINEMATIC DIGITAL TWIN</h2>
            <p className="dt-subtitle">AEROSPACE TRAJECTORY SIMULATION & INVERSE KINEMATICS ENGINE</p>
          </div>
        </div>

        {/* Camera Preset Quick Bar */}
        <div className="dt-camera-presets">
          <span className="dt-cam-label">CAM VIEW:</span>
          {[
            { id: 'ISO', label: 'ISOMETRIC' },
            { id: 'TOP', label: 'RADAR TOP' },
            { id: 'SIDE', label: 'SIDE PROFILE' },
            { id: 'TURRET_POV', label: 'TURRET POV' },
          ].map((c) => (
            <button
              key={c.id}
              type="button"
              className={`dt-cam-btn ${cameraPreset === c.id ? 'active' : ''}`}
              onClick={() => applyCameraPreset(c.id)}
            >
              {c.label}
            </button>
          ))}
          <button
            type="button"
            className={`dt-cam-btn ${autoOrbit ? 'orbit-active' : ''}`}
            onClick={() => setAutoOrbit(!autoOrbit)}
            title="Auto-rotate orbital camera"
          >
            AUTO-ORBIT: {autoOrbit ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Live Kinematic Stat Chips (Unified Monochrome Values) */}
        <div className="dt-stats-bar">
          <div className="dt-stat-chip">
            <span className="dt-stat-label">SERVO 1 PAN</span>
            <span className="dt-stat-val">
              {Number(turretAnglesRef.current.pan).toFixed(1)}°
            </span>
          </div>
          <div className="dt-stat-chip">
            <span className="dt-stat-label">SERVO 2 TILT</span>
            <span className="dt-stat-val">
              {Number(turretAnglesRef.current.tilt).toFixed(1)}°
            </span>
          </div>
          <div className="dt-stat-chip">
            <span className="dt-stat-label">STANCHION LINKAGE</span>
            <span className="dt-stat-val">{localDistance} mm</span>
          </div>
          <div className="dt-stat-chip">
            <span className="dt-stat-label">LASER EMITTER</span>
            <span className="dt-stat-val">
              {isLaserFiring ? 'EMITTING' : isLaserArmed ? 'ARMED' : 'STANDBY'}
            </span>
          </div>
        </div>
      </div>

      {/* Main 3D Canvas Viewport */}
      <div className="dt-canvas-wrapper">
        <canvas
          ref={canvasRef}
          className="dt-3d-canvas"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          onContextMenu={(e) => e.preventDefault()}
        />

        {/* Floating Interactive Controls Over Canvas */}
        <div className={`dt-floating-controls ${controlsOpen ? 'expanded' : 'collapsed'}`}>
          <button
            type="button"
            className="dt-controls-toggle"
            onClick={() => setControlsOpen(!controlsOpen)}
            title={controlsOpen ? 'Collapse HUD Controls' : 'Expand HUD Controls'}
          >
            {controlsOpen ? '▼ HUD CONTROLS' : '▲ HUD CONTROLS'}
          </button>

          {controlsOpen && (
            <>
              {/* Flight Trajectory Mode Selector */}
              <div className="dt-mode-selector dt-controls-card">
                <span className="dt-control-label">TRAJECTORY PATTERN:</span>
                <div className="dt-btn-group">
                  <button
                    type="button"
                    className={`dt-btn ${simMode === 'SIM_FIGURE8' ? 'active' : ''}`}
                    onClick={() => setSimMode('SIM_FIGURE8')}
                  >
                    FIGURE-8 PATROL
                  </button>
                  <button
                    type="button"
                    className={`dt-btn ${simMode === 'SIM_ORBIT' ? 'active' : ''}`}
                    onClick={() => setSimMode('SIM_ORBIT')}
                  >
                    ORBITAL FLIGHT
                  </button>
                  <button
                    type="button"
                    className={`dt-btn ${simMode === 'SIM_EVASIVE' ? 'active' : ''}`}
                    onClick={() => setSimMode('SIM_EVASIVE')}
                  >
                    EVASIVE SLALOM
                  </button>
                  <button
                    type="button"
                    className={`dt-btn ${simMode === 'LIVE_SYNC' ? 'active' : ''}`}
                    onClick={() => setSimMode('LIVE_SYNC')}
                  >
                    SYNC LIVE HARDWARE
                  </button>
                </div>
              </div>

              {/* Stanchion Height / Servo Distance Interactive Slider */}
              <div className="dt-slider-card dt-controls-card">
                <div className="dt-slider-head">
                  <span className="dt-control-label">INTER-SERVO DISTANCE (d):</span>
                  <span className="dt-val-highlight">{localDistance} mm</span>
                </div>
                <input
                  type="range"
                  min="15"
                  max="150"
                  step="1"
                  value={localDistance}
                  onChange={(e) => handleDistanceSlider(parseFloat(e.target.value))}
                />
                <div className="dt-presets-mini">
                  {[30, 45, 75, 110].map((d) => (
                    <button
                      key={d}
                      type="button"
                      className={`dt-chip ${localDistance === d ? 'active' : ''}`}
                      onClick={() => handleDistanceSlider(d)}
                    >
                      {d}mm
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Flight Modifiers & Laser Beam Toggle */}
              <div className="dt-flight-controls dt-controls-card">
                <div className="dt-param-item">
                  <label>MANEUVER SPEED: {targetSpeed.toFixed(1)}x</label>
                  <input
                    type="range"
                    min="0.2"
                    max="3.0"
                    step="0.2"
                    value={targetSpeed}
                    onChange={(e) => setTargetSpeed(parseFloat(e.target.value))}
                  />
                </div>
                <div className="dt-param-item">
                  <label>ALTITUDE: {targetAltitude}px</label>
                  <input
                    type="range"
                    min="60"
                    max="300"
                    step="10"
                    value={targetAltitude}
                    onChange={(e) => setTargetAltitude(parseFloat(e.target.value))}
                  />
                </div>
                <button
                  type="button"
                  className={`dt-btn-toggle ${beamEnabled ? 'active' : ''}`}
                  onClick={() => setBeamEnabled(!beamEnabled)}
                >
                  LASER BEAM: {beamEnabled ? 'ACTIVE' : 'MUTED'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
