import React, { useState, useEffect } from 'react';

export default function TurretCard({
  telemetry,
  onNudge,
  onCenter,
  onDistanceChange,
  onStartCalibration,
  onStopCalibration,
  onOpenDigitalTwin,
}) {
  const pan = telemetry?.pan !== undefined ? Number(telemetry.pan).toFixed(1) : '90.0';
  const tilt = telemetry?.tilt !== undefined ? Number(telemetry.tilt).toFixed(1) : '90.0';
  const isSimulated = telemetry?.is_simulated ?? true;

  const servoDistance = telemetry?.servo_distance_mm ?? 45.0;
  const isCalibrating = !!telemetry?.is_calibrating;
  const calProgress = telemetry?.calibration_progress ?? 0;
  const calStage = telemetry?.calibration_stage || 'IDLE';

  const [localDistance, setLocalDistance] = useState(servoDistance);

  useEffect(() => {
    if (telemetry?.servo_distance_mm !== undefined) {
      setLocalDistance(telemetry.servo_distance_mm);
    }
  }, [telemetry?.servo_distance_mm]);

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    setLocalDistance(val);
  };

  const handleSliderCommit = () => {
    if (onDistanceChange) {
      onDistanceChange(localDistance);
    }
  };

  const handlePreset = (val) => {
    setLocalDistance(val);
    if (onDistanceChange) {
      onDistanceChange(val);
    }
  };

  // Convert angles to rotation degrees for SVG elements
  const panNum = parseFloat(pan);
  const tiltNum = parseFloat(tilt);
  const panRot = panNum - 90; // Azimuth deviation
  const tiltRot = (90 - tiltNum) * 0.9; // Elevation pitch

  // Proportional height mapping for clean blueprint aesthetics (no overlapping text!)
  const normDist = Math.max(15, Math.min(150, localDistance));
  const linkLength = 22 + ((normDist - 15) / 135) * 44; // 22px to 66px
  const basePanY = 120;
  const tiltServoY = basePanY - linkLength;

  // Optics laser head calculation
  const tiltRad = (tiltRot * Math.PI) / 180;
  const headEndX = 100 + Math.cos(tiltRad) * 32;
  const headEndY = tiltServoY - Math.sin(tiltRad) * 32;
  const laserBeamEndX = 270;
  const laserBeamEndY = headEndY - (laserBeamEndX - headEndX) * Math.tan(tiltRad * 0.4);

  return (
    <div className="tactical-card turret-card-fixed">
      <div className="card-header">
        <div className="card-title-group">
          <svg className="card-title-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="3" />
            <path d="M12 8v3" />
          </svg>
          <h2 className="card-title">DUAL-SERVO KINEMATICS</h2>
        </div>
        <span className={`card-badge ${isCalibrating ? 'badge-pulse-amber' : ''}`}>
          {isCalibrating ? 'CALIBRATING' : isSimulated ? 'SIMULATION' : 'SERIAL HARDWARE'}
        </span>
      </div>

      <div className="card-body">
        {/* Tactical Blueprint Schematic (Clean, Crisp, No Collisions) */}
        <div className="tactical-blueprint-box">
          <svg className="blueprint-svg" viewBox="0 0 320 155">
            <defs>
              <pattern id="card-blueprint-grid" width="14" height="14" patternUnits="userSpaceOnUse">
                <path d="M 14 0 L 0 0 0 14" fill="none" stroke="rgba(255, 15, 60, 0.08)" strokeWidth="0.8" />
              </pattern>
              <linearGradient id="opticsLaserGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#ff0f3d" stopOpacity="1" />
                <stop offset="65%" stopColor="#ff0f3d" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#ff0f3d" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Tactical Grid Background */}
            <rect width="100%" height="100%" fill="url(#card-blueprint-grid)" />

            {/* Base Pedestal Mount */}
            <rect x="65" y="138" width="70" height="7" rx="2" fill="#1b0e15" stroke="rgba(255, 15, 60, 0.4)" strokeWidth="1" />
            <line x1="100" y1="145" x2="100" y2="152" stroke="#ff0f3d" strokeWidth="1.5" />

            {/* SERVO 1 (PAN / AZIMUTH BASE) */}
            <rect x="76" y={basePanY} width="48" height="18" rx="3" fill="#12080e" stroke="#ff0f3d" strokeWidth="1.2" />
            <circle cx="100" cy={basePanY + 9} r="4" fill="#2d131f" stroke="#ff0f3d" strokeWidth="1" />
            <text x="68" y={basePanY + 13} textAnchor="end" fill="#ff0f3d" fontSize="7.5" fontWeight="700" fontFamily="JetBrains Mono">
              SERVO 1 (PAN)
            </text>

            {/* Pan Rotary Horn Indicator */}
            <g transform={`translate(100, ${basePanY}) rotate(${panRot})`} className="servo-motion-element">
              <line x1="-16" y1="0" x2="16" y2="0" stroke="#f5f6fa" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="0" cy="0" r="2.5" fill="#ff0f3d" />
            </g>

            {/* Pan Rotation Guide Arc */}
            <path
              d={`M 74 ${basePanY - 4} A 26 26 0 0 1 126 ${basePanY - 4}`}
              fill="none"
              stroke="rgba(255, 15, 60, 0.25)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />

            {/* STANCHION / INTER-SERVO MECHANICAL LINKAGE */}
            <line
              x1="100"
              y1={basePanY}
              x2="100"
              y2={tiltServoY + 6}
              stroke="#e6002e"
              strokeWidth="4"
              strokeLinecap="round"
              className="servo-linkage-spar"
            />
            <line
              x1="100"
              y1={basePanY}
              x2="100"
              y2={tiltServoY + 6}
              stroke="#ffaa33"
              strokeWidth="1.2"
              className="servo-linkage-spar"
            />

            {/* SERVO 2 (TILT / ELEVATION GIMBAL) */}
            <rect x="80" y={tiltServoY - 8} width="40" height="16" rx="3" fill="#180a12" stroke="#ff6600" strokeWidth="1.2" />
            <circle cx="100" cy={tiltServoY} r="4.5" fill="#2b1106" stroke="#ffaa33" strokeWidth="1.2" />
            <text x="72" y={tiltServoY + 3} textAnchor="end" fill="#ffaa33" fontSize="7.5" fontWeight="700" fontFamily="JetBrains Mono">
              SERVO 2 (TILT)
            </text>

            {/* Pivoting Tilt Arm, Optics Head & Laser Sightline */}
            <g transform={`translate(100, ${tiltServoY}) rotate(${-tiltRot})`} className="servo-motion-element">
              {/* Rotating arm to optics */}
              <line x1="0" y1="0" x2="26" y2="0" stroke="#f5f6fa" strokeWidth="3" strokeLinecap="round" />
              {/* Laser Optics Housing */}
              <rect x="22" y="-5" width="10" height="10" rx="2" fill="#200d18" stroke="#ff0f3d" strokeWidth="1.2" />
              <circle cx="27" cy="0" r="2.5" fill="#ff0f3d" />
              {/* Collimated Laser Beam */}
              <line
                x1="32"
                y1="0"
                x2="170"
                y2="0"
                stroke="url(#opticsLaserGrad)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <circle cx="170" cy="0" r="2" fill="#ff0f3d" opacity="0.8" />
            </g>

            {/* DYNAMIC CALIPER MEASUREMENT (Positioned cleanly on the right) */}
            <g transform="translate(142, 0)">
              {/* Top & Bottom caliper ticks */}
              <line x1="0" y1={tiltServoY} x2="14" y2={tiltServoY} stroke="#ffaa33" strokeWidth="1" />
              <line x1="0" y1={basePanY} x2="14" y2={basePanY} stroke="#ffaa33" strokeWidth="1" />
              {/* Vertical dimension line with arrowheads */}
              <line x1="7" y1={tiltServoY + 2} x2="7" y2={basePanY - 2} stroke="#ffaa33" strokeWidth="1.2" />
              <polygon points={`4,${tiltServoY + 5} 10,${tiltServoY + 5} 7,${tiltServoY}`} fill="#ffaa33" />
              <polygon points={`4,${basePanY - 5} 10,${basePanY - 5} 7,${basePanY}`} fill="#ffaa33" />
              {/* Dimension Readout Badge */}
              <rect
                x="15"
                y={(tiltServoY + basePanY) / 2 - 9}
                width="54"
                height="18"
                rx="3"
                fill="rgba(14, 7, 11, 0.95)"
                stroke="#ffaa33"
                strokeWidth="1"
              />
              <text
                x="42"
                y={(tiltServoY + basePanY) / 2 + 3.5}
                textAnchor="middle"
                fill="#ffaa33"
                fontSize="8"
                fontWeight="700"
                fontFamily="JetBrains Mono"
              >
                d = {localDistance}mm
              </text>
            </g>

            {/* CURRENT ANGLES HUD OVERLAY (Top right corner) */}
            <g transform="translate(242, 14)">
              <rect x="-8" y="-6" width="76" height="46" rx="4" fill="rgba(10, 4, 8, 0.88)" stroke="rgba(255, 15, 60, 0.25)" strokeWidth="1" />
              <text x="30" y="6" textAnchor="middle" fill="#6b555d" fontSize="6.5" fontFamily="JetBrains Mono">
                CURRENT ANGLES
              </text>
              <text x="0" y="21" fill="#ff0f3d" fontSize="7.8" fontFamily="JetBrains Mono" fontWeight="700">
                PAN : <tspan fill="#f5f6fa">{pan}°</tspan>
              </text>
              <text x="0" y="34" fill="#ffaa33" fontSize="7.8" fontFamily="JetBrains Mono" fontWeight="700">
                TILT: <tspan fill="#f5f6fa">{tilt}°</tspan>
              </text>
            </g>
          </svg>
        </div>

        {/* DISTANCE ADJUSTMENT CONTROLS */}
        <div className="compact-distance-row">
          <div className="dist-slider-header">
            <span className="dist-title">SERVO DISTANCE:</span>
            <span className="dist-badge">{localDistance} mm</span>
            <div className="compact-presets">
              {[30, 45, 75, 110].map((d) => (
                <button
                  key={d}
                  type="button"
                  className={`pill-btn ${localDistance === d ? 'active' : ''}`}
                  onClick={() => handlePreset(d)}
                  disabled={isCalibrating}
                >
                  {d}mm
                </button>
              ))}
            </div>
          </div>
          <input
            id="servo-distance-slider"
            type="range"
            min="15"
            max="150"
            step="1"
            value={localDistance}
            onChange={handleSliderChange}
            onMouseUp={handleSliderCommit}
            onTouchEnd={handleSliderCommit}
            disabled={isCalibrating}
          />
        </div>

        {/* CALIBRATION & 3D DIGITAL TWIN LAUNCHER */}
        <div className="actuation-action-row">
          {isCalibrating ? (
            <div className="calibrating-mini-bar">
              <div className="cal-mini-info">
                <span className="cal-stage-label">{calStage}</span>
                <span className="cal-pct-val">{calProgress}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill cal-fill" style={{ width: `${calProgress}%` }}></div>
              </div>
              <button
                type="button"
                className="btn btn-abort btn-sm mt-1"
                onClick={onStopCalibration}
              >
                ABORT
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-calibrate"
              onClick={onStartCalibration}
            >
              <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              <span>AUTO-CALIBRATE 2-SERVO</span>
            </button>
          )}

          {/* D-Pad Manual Jog */}
          <div className="compact-dpad-wrap">
            <button
              type="button"
              className="dpad-btn-sm"
              onClick={() => onNudge(0, 5)}
              disabled={isCalibrating}
              title="Tilt Up"
            >
              <svg className="dpad-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </button>
            <div className="dpad-mid-row">
              <button
                type="button"
                className="dpad-btn-sm"
                onClick={() => onNudge(-5, 0)}
                disabled={isCalibrating}
                title="Pan Left"
              >
                <svg className="dpad-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <button
                type="button"
                className="dpad-btn-sm center"
                onClick={onCenter}
                title="Center (90°, 90°)"
              >
                <svg className="dpad-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="4" />
                </svg>
              </button>
              <button
                type="button"
                className="dpad-btn-sm"
                onClick={() => onNudge(5, 0)}
                disabled={isCalibrating}
                title="Pan Right"
              >
                <svg className="dpad-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
            <button
              type="button"
              className="dpad-btn-sm"
              onClick={() => onNudge(0, -5)}
              disabled={isCalibrating}
              title="Tilt Down"
            >
              <svg className="dpad-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>
        </div>

        {/* Direct Digital Twin Shortcut */}
        {onOpenDigitalTwin && (
          <button
            type="button"
            className="btn btn-outline full-width dt-shortcut-btn"
            onClick={onOpenDigitalTwin}
          >
            <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            <span>OPEN 3D MOTION DIGITAL TWIN</span>
          </button>
        )}
      </div>
    </div>
  );
}
