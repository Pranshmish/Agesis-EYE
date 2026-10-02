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

  // Target 3D coordinates & motion state
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
  });

  // Turret body joint angles
  const turretAnglesRef = useRef({
    pan: telemetry?.pan ?? 90.0,
    tilt: telemetry?.tilt ?? 90.0,
  });

  // Space depth particles
  const particlesRef = useRef(
    Array.from({ length: 40 }, () => ({
      x: (Math.random() - 0.5) * 800,
      y: Math.random() * 320,
      z: (Math.random() - 0.5) * 800,
      speed: 0.2 + Math.random() * 0.35,
      size: 1 + Math.random() * 1.5,
    }))
  );

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

      // 1. Update Target Trajectory & Motion
      const tgt = targetStateRef.current;
      const dt = 0.016 * targetSpeed;
      tgt.simTime += dt;

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

      // Laser impact spark particles
      if (tgt.sparks.length < 20) {
        tgt.sparks.push({
          x: tgt.x + (Math.random() - 0.5) * 5,
          y: tgt.y + (Math.random() - 0.5) * 5,
          z: tgt.z + (Math.random() - 0.5) * 5,
          vx: (Math.random() - 0.5) * 50,
          vy: (Math.random() - 0.5) * 50,
          vz: (Math.random() - 0.5) * 50,
          life: 1.0,
        });
      }
      for (let i = tgt.sparks.length - 1; i >= 0; i--) {
        const sp = tgt.sparks[i];
        sp.x += sp.vx * dt;
        sp.y += sp.vy * dt;
        sp.z += sp.vz * dt;
        sp.life -= dt * 3.5;
        if (sp.life <= 0) tgt.sparks.splice(i, 1);
      }

      // 2. Inverse Kinematics for Turret Body (1.35x visual size for commanding presence)
      const stanchionHeight = Math.max(15, Math.min(200, localDistance)) * 1.1;
      const baseElev = 45; // Pan servo pivot height
      const pivotY = baseElev + stanchionHeight; // Tilt gimbal pivot height

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

      // 3. Render Floating Ambient Space Particles
      ctx.save();
      const parts = particlesRef.current;
      for (let p of parts) {
        p.y -= p.speed;
        if (p.y < 0) p.y = 320;
        const proj = project3D(p.x, p.y, p.z, width, height);
        if (proj.visible) {
          ctx.beginPath();
          ctx.arc(proj.x, proj.y, p.size * proj.scale, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255, 15, 60, 0.25)';
          ctx.fill();
        }
      }
      ctx.restore();

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

      // 7. Render 3D Turret Body Model (Prominent & Detailed)
      ctx.save();

      // (A) Base Turntable Platform
      const baseR = 64;
      ctx.beginPath();
      for (let a = 0; a <= 360; a += 10) {
        const rad = (a * Math.PI) / 180;
        const pt = project3D(baseR * Math.cos(rad), 4, baseR * Math.sin(rad), width, height);
        if (a === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.fillStyle = '#160810';
      ctx.fill();
      ctx.strokeStyle = '#ff0f3d';
      ctx.lineWidth = 2.2;
      ctx.stroke();

      // Base Pedestal Volumetric Cylinder
      const pB1 = project3D(-32, 4, 0, width, height);
      const pB2 = project3D(32, 4, 0, width, height);
      const pB3 = project3D(32, baseElev, 0, width, height);
      const pB4 = project3D(-32, baseElev, 0, width, height);

      ctx.beginPath();
      ctx.moveTo(pB1.x, pB1.y);
      ctx.lineTo(pB2.x, pB2.y);
      ctx.lineTo(pB3.x, pB3.y);
      ctx.lineTo(pB4.x, pB4.y);
      ctx.closePath();
      const pedGrad = ctx.createLinearGradient(pB1.x, pB1.y, pB2.x, pB2.y);
      pedGrad.addColorStop(0, '#160810');
      pedGrad.addColorStop(0.5, '#351224');
      pedGrad.addColorStop(1, '#0e040a');
      ctx.fillStyle = pedGrad;
      ctx.fill();
      ctx.strokeStyle = 'rgba(255, 15, 60, 0.6)';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // (B) Pan Servo Rotating Turntable Horn
      const panRad = ((curPan - 90) * Math.PI) / 180;
      const hornR = 34;
      const pHornA = project3D(hornR * Math.sin(panRad), baseElev + 3, -hornR * Math.cos(panRad), width, height);
      const pHornB = project3D(-hornR * Math.sin(panRad), baseElev + 3, hornR * Math.cos(panRad), width, height);
      const pPanPivot = project3D(0, baseElev + 3, 0, width, height);

      ctx.beginPath();
      ctx.moveTo(pHornA.x, pHornA.y);
      ctx.lineTo(pHornB.x, pHornB.y);
      ctx.strokeStyle = '#f5f6fa';
      ctx.lineWidth = 6 * pPanPivot.scale;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Spline gear
      ctx.beginPath();
      ctx.arc(pPanPivot.x, pPanPivot.y, 7 * pPanPivot.scale, 0, Math.PI * 2);
      ctx.fillStyle = '#ff0f3d';
      ctx.fill();

      // (C) Telescopic Mechanical Stanchion Linkage (Height d mm)
      const pTiltPivot = project3D(0, pivotY, 0, width, height);

      // Twin Structural Carbon Columns
      const pCol1_A = project3D(-7, baseElev + 4, 0, width, height);
      const pCol1_B = project3D(-7, pivotY, 0, width, height);
      const pCol2_A = project3D(7, baseElev + 4, 0, width, height);
      const pCol2_B = project3D(7, pivotY, 0, width, height);

      ctx.beginPath();
      ctx.moveTo(pCol1_A.x, pCol1_A.y);
      ctx.lineTo(pCol1_B.x, pCol1_B.y);
      ctx.strokeStyle = '#e6002e';
      ctx.lineWidth = 5 * pPanPivot.scale;
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(pCol2_A.x, pCol2_A.y);
      ctx.lineTo(pCol2_B.x, pCol2_B.y);
      ctx.strokeStyle = '#e6002e';
      ctx.lineWidth = 5 * pPanPivot.scale;
      ctx.stroke();

      // Center Guide Screw
      ctx.beginPath();
      ctx.moveTo(pPanPivot.x, pPanPivot.y);
      ctx.lineTo(pTiltPivot.x, pTiltPivot.y);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2 * pPanPivot.scale;
      ctx.stroke();

      // 3D Dimension Caliper Tag on Linkage
      const pDimA = project3D(44, baseElev + 4, 0, width, height);
      const pDimB = project3D(44, pivotY, 0, width, height);
      if (pDimA.visible && pDimB.visible) {
        ctx.beginPath();
        ctx.moveTo(pDimA.x, pDimA.y);
        ctx.lineTo(pDimB.x, pDimB.y);
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pDimA.x - 5, pDimA.y);
        ctx.lineTo(pDimA.x + 5, pDimA.y);
        ctx.moveTo(pDimB.x - 5, pDimB.y);
        ctx.lineTo(pDimB.x + 5, pDimB.y);
        ctx.stroke();

        const midX = (pDimA.x + pDimB.x) / 2;
        const midY = (pDimA.y + pDimB.y) / 2;
        ctx.fillStyle = 'rgba(14, 7, 11, 0.94)';
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1;
        ctx.fillRect(midX + 5, midY - 9, 58, 18);
        ctx.strokeRect(midX + 5, midY - 9, 58, 18);
        ctx.fillStyle = '#f5f6fa';
        ctx.font = 'bold 9px JetBrains Mono';
        ctx.fillText(`d = ${localDistance}mm`, midX + 9, midY + 4);
      }

      // (D) Tilt Servo Gimbal Yoke & Optical Sensor Emitter Head
      const tiltRad = ((curTilt - 90) * Math.PI) / 180;
      const dirX = Math.cos(tiltRad) * Math.sin(panRad);
      const dirY = Math.sin(tiltRad);
      const dirZ = Math.cos(tiltRad) * Math.cos(panRad);

      const headLen = 48;
      const pHeadEnd = project3D(dirX * headLen, pivotY + dirY * headLen, dirZ * headLen, width, height);

      // Tilt Gimbal Yoke Pivot Sphere
      ctx.beginPath();
      ctx.arc(pTiltPivot.x, pTiltPivot.y, 11 * pTiltPivot.scale, 0, Math.PI * 2);
      ctx.fillStyle = '#280c1b';
      ctx.fill();
      ctx.strokeStyle = '#ff0f3d';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Optical Laser Housing Barrel
      ctx.beginPath();
      ctx.moveTo(pTiltPivot.x, pTiltPivot.y);
      ctx.lineTo(pHeadEnd.x, pHeadEnd.y);
      ctx.strokeStyle = '#f5f6fa';
      ctx.lineWidth = 8 * pTiltPivot.scale;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Aperture Shroud
      ctx.beginPath();
      ctx.arc(pHeadEnd.x, pHeadEnd.y, 6 * pHeadEnd.scale, 0, Math.PI * 2);
      ctx.fillStyle = '#ff0f3d';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // (E) High-Intensity Collimated Targeting Laser Beam
      if (beamEnabled && pHeadEnd.visible && pTgt.visible) {
        // Atmospheric Scattering Aura
        ctx.beginPath();
        ctx.moveTo(pHeadEnd.x, pHeadEnd.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = 'rgba(255, 15, 60, 0.25)';
        ctx.lineWidth = 14 * pHeadEnd.scale;
        ctx.stroke();

        // Intense Red Core with Bloom
        ctx.beginPath();
        ctx.moveTo(pHeadEnd.x, pHeadEnd.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 3.8 * pHeadEnd.scale;
        ctx.shadowColor = '#ff0f3d';
        ctx.shadowBlur = 18;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Hyper-White Concentrated Core
        ctx.beginPath();
        ctx.moveTo(pHeadEnd.x, pHeadEnd.y);
        ctx.lineTo(pTgt.x, pTgt.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.4;
        ctx.stroke();

        // Traveling Energy Photon Pulse
        const waveFrac = (tgt.simTime * 2.8) % 1.0;
        const waveX = pHeadEnd.x + (pTgt.x - pHeadEnd.x) * waveFrac;
        const waveY = pHeadEnd.y + (pTgt.y - pHeadEnd.y) * waveFrac;
        ctx.beginPath();
        ctx.arc(waveX, waveY, 4.5 * pHeadEnd.scale, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ff0f3d';
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.restore();

      // 8. Render Target Entity (Tactical Stealth Drone / Balloon)
      if (pTgt.visible) {
        ctx.save();
        const tgtSize = Math.max(16, 22 * pTgt.scale);

        // Concentric Target Acquisition Rings
        ctx.beginPath();
        ctx.arc(pTgt.x, pTgt.y, tgtSize * 1.6, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 15, 60, 0.5)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Target Body Shaded Sphere
        const tgtGrad = ctx.createRadialGradient(
          pTgt.x - tgtSize * 0.35,
          pTgt.y - tgtSize * 0.35,
          2,
          pTgt.x,
          pTgt.y,
          tgtSize
        );
        tgtGrad.addColorStop(0, '#ffffff');
        tgtGrad.addColorStop(0.3, '#ff2250');
        tgtGrad.addColorStop(0.7, '#990020');
        tgtGrad.addColorStop(1, '#33000a');

        ctx.beginPath();
        ctx.arc(pTgt.x, pTgt.y, tgtSize, 0, Math.PI * 2);
        ctx.fillStyle = tgtGrad;
        ctx.fill();
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.6;
        ctx.stroke();

        // Spinning Rotor Arms
        const rotorR = tgtSize * 1.5;
        const rAngle = tgt.simTime * 18;
        for (let i = 0; i < 4; i++) {
          const a = (i * Math.PI) / 2 + rAngle;
          const rx = pTgt.x + rotorR * Math.cos(a);
          const ry = pTgt.y + rotorR * 0.5 * Math.sin(a);
          ctx.beginPath();
          ctx.moveTo(pTgt.x, pTgt.y);
          ctx.lineTo(rx, ry);
          ctx.strokeStyle = 'rgba(255, 15, 60, 0.6)';
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(rx, ry, 3.5 * pTgt.scale, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
        }

        // Render Laser Impact Sparks
        tgt.sparks.forEach((sp) => {
          const pSpark = project3D(sp.x, sp.y, sp.z, width, height);
          if (pSpark.visible) {
            ctx.beginPath();
            ctx.arc(pSpark.x, pSpark.y, 2 * pSpark.scale, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, ${Math.floor(sp.life * 255)}, ${Math.floor(sp.life * 200)}, ${sp.life})`;
            ctx.fill();
          }
        });

        // 3D Holographic Target HUD Tag (Unified Crimson & White)
        const tagX = pTgt.x + tgtSize + 12;
        const tagY = pTgt.y - 18;
        ctx.fillStyle = 'rgba(10, 4, 8, 0.92)';
        ctx.strokeStyle = '#ff0f3d';
        ctx.lineWidth = 1.2;
        ctx.fillRect(tagX, tagY, 125, 46);
        ctx.strokeRect(tagX, tagY, 125, 46);

        // Header strip
        ctx.fillStyle = 'rgba(255, 15, 60, 0.2)';
        ctx.fillRect(tagX, tagY, 125, 14);

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 8.5px JetBrains Mono';
        ctx.fillText('TARGET // TGT-01', tagX + 6, tagY + 10);

        ctx.fillStyle = '#f5f6fa';
        ctx.font = '7.5px JetBrains Mono';
        const distM = (Math.hypot(tgt.x, tgt.y - pivotY, tgt.z) / 100).toFixed(2);
        const velM = (Math.hypot(tgt.vx, tgt.vy, tgt.vz) / 100).toFixed(1);
        ctx.fillText(`RANGE : ${distM} m`, tagX + 6, tagY + 24);
        ctx.fillText(`ALT   : ${(tgt.y / 100).toFixed(2)} m`, tagX + 6, tagY + 34);
        ctx.fillText(`VEL   : ${velM} m/s`, tagX + 6, tagY + 44);

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
  }, [project3D, localDistance, simMode, targetSpeed, targetAltitude, targetRadius, beamEnabled, autoOrbit]);

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
        <div className="dt-floating-controls">
          {/* Flight Trajectory Mode Selector */}
          <div className="dt-mode-selector">
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
          <div className="dt-slider-card">
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
          <div className="dt-flight-controls">
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
        </div>
      </div>
    </div>
  );
}
