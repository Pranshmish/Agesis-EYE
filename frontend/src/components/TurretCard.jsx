import React, { useState, useEffect } from 'react';

export default function TurretCard({
  telemetry,
  onNudge,
  onCenter,
  onHome,
  onDistanceChange,
  onStructureUpdate,
  onZeroTilt,
  onToggleTracking,
  onToggleManualLaser,
  onStartCalibration,
  onStopCalibration,
  onStartRLAlignment,
  onStopRLAlignment,
  onApplyRLCalibration,
  onOpenDigitalTwin,
}) {
  const pan = telemetry?.pan !== undefined ? Number(telemetry.pan).toFixed(1) : '90.0';
  const tilt = telemetry?.tilt !== undefined ? Number(telemetry.tilt).toFixed(1) : '90.0';
  const isSimulated = telemetry?.is_simulated ?? true;

  const servoDistance = telemetry?.servo_distance_mm ?? 55.0;
  const baseHeight = telemetry?.base_height_mm ?? 190.0;
  const isCalibrating = !!telemetry?.is_calibrating;
  const calProgress = telemetry?.calibration_progress ?? 0;
  const calStage = telemetry?.calibration_stage || 'IDLE';

  const rlActive = !!telemetry?.rl_active;
  const rlStage = telemetry?.rl_stage || 'IDLE';
  const rlReward = telemetry?.rl_reward !== undefined ? Number(telemetry.rl_reward).toFixed(1) : '0.0';
  const rlAlignmentPct = telemetry?.rl_alignment_pct !== undefined ? Number(telemetry.rl_alignment_pct).toFixed(0) : '0';
  const rlStreak = telemetry?.rl_streak ?? 0;
  const rlDist = telemetry?.rl_dist_px !== undefined ? Number(telemetry.rl_dist_px).toFixed(1) : '0.0';

  const invertPan = telemetry?.invert_pan !== false;
  const invertTilt = !!telemetry?.invert_tilt;
  const isTracking = telemetry?.tracking_enabled !== false;
  const isManualLaser = !!telemetry?.manual_laser;
  const smoothFactor = telemetry?.smooth_factor ?? 0.25;
  const kpVal = telemetry?.kp ?? 0.06;
  const tiltOffset = telemetry?.tilt_offset !== undefined ? Number(telemetry.tilt_offset) : 0.0;

  const [localDistance, setLocalDistance] = useState(servoDistance);
  const [localSmooth, setLocalSmooth] = useState(smoothFactor);
  const [localKp, setLocalKp] = useState(kpVal);
  const [localTiltOffset, setLocalTiltOffset] = useState(tiltOffset);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (telemetry?.servo_distance_mm !== undefined) {
      setLocalDistance(telemetry.servo_distance_mm);
    }
  }, [telemetry?.servo_distance_mm]);

  useEffect(() => {
    if (telemetry?.smooth_factor !== undefined) {
      setLocalSmooth(telemetry.smooth_factor);
    }
  }, [telemetry?.smooth_factor]);

  useEffect(() => {
    if (telemetry?.kp !== undefined) {
      setLocalKp(telemetry.kp);
    }
  }, [telemetry?.kp]);

  useEffect(() => {
    if (telemetry?.tilt_offset !== undefined) {
      setLocalTiltOffset(Number(telemetry.tilt_offset));
    }
  }, [telemetry?.tilt_offset]);

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

  const togglePanInvert = () => {
    if (onStructureUpdate) {
      onStructureUpdate({ invert_pan: !invertPan });
    }
  };

  const toggleTiltInvert = () => {
    if (onStructureUpdate) {
      onStructureUpdate({ invert_tilt: !invertTilt });
    }
  };

  const handleSmoothCommit = () => {
    if (onStructureUpdate) {
      onStructureUpdate({ smooth_factor: localSmooth });
    }
  };

  const handleKpCommit = () => {
    if (onStructureUpdate) {
      onStructureUpdate({ kp: localKp });
    }
  };

  const handleTiltOffsetCommit = (val) => {
    const targetVal = typeof val === 'number' ? val : localTiltOffset;
    if (onStructureUpdate) {
      onStructureUpdate({ tilt_offset: targetVal });
    }
  };

  const handleNudgeTiltOffset = (delta) => {
    const nextVal = Math.round((localTiltOffset + delta) * 10) / 10;
    setLocalTiltOffset(nextVal);
    if (onStructureUpdate) {
      onStructureUpdate({ tilt_offset: nextVal });
    }
  };

  // Convert angles to rotation degrees for SVG elements
  const panNum = parseFloat(pan);
  const tiltNum = parseFloat(tilt);
  const panRot = panNum - 90; // Azimuth deviation
  const tiltRot = (90 - tiltNum) * 0.9; // Elevation pitch

  // Proportional height mapping for clean blueprint aesthetics
  const normDist = Math.max(15, Math.min(150, localDistance));
  const linkLength = 22 + ((normDist - 15) / 135) * 44; // 22px to 66px
  const basePanY = 120;
  const tiltServoY = basePanY - linkLength;

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
        {/* Tactical Blueprint Schematic */}
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
            <g transform={`translate(100, ${tiltServoY}) rotate(${tiltRot})`} className="servo-motion-element">
              <line x1="0" y1="0" x2="26" y2="0" stroke="#f5f6fa" strokeWidth="3" strokeLinecap="round" />
              <rect x="22" y="-5" width="10" height="10" rx="2" fill="#200d18" stroke="#ff0f3d" strokeWidth="1.2" />
              <circle cx="27" cy="0" r="2.5" fill="#ff0f3d" />
              <line
                x1="32"
                y1="0"
                x2="170"
                y2="0"
                stroke="url(#opticsLaserGrad)"
                strokeWidth={isManualLaser ? '3.5' : '2.5'}
                strokeLinecap="round"
              />
              <circle cx="170" cy="0" r={isManualLaser ? 3 : 2} fill="#ff0f3d" opacity="0.9" />
            </g>

            {/* DYNAMIC CALIPER MEASUREMENT */}
            <g transform="translate(142, 0)">
              <line x1="0" y1={tiltServoY} x2="14" y2={tiltServoY} stroke="#ffaa33" strokeWidth="1" />
              <line x1="0" y1={basePanY} x2="14" y2={basePanY} stroke="#ffaa33" strokeWidth="1" />
              <line x1="7" y1={tiltServoY + 2} x2="7" y2={basePanY - 2} stroke="#ffaa33" strokeWidth="1.2" />
              <polygon points={`4,${tiltServoY + 5} 10,${tiltServoY + 5} 7,${tiltServoY}`} fill="#ffaa33" />
              <polygon points={`4,${basePanY - 5} 10,${basePanY - 5} 7,${basePanY}`} fill="#ffaa33" />
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

            {/* CURRENT ANGLES HUD OVERLAY */}
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

        {/* CALIBRATION DECK: TARGET LOCK, SIGHTING LASER & DIRECTION INVERSION */}
        <div className="calibration-deck">
          <div className="cal-header-row">
            <span className="cal-title">TARGET SIGHTING & CALIBRATION</span>
            <span className="cal-status-tag">
              {isTracking ? 'TRACKING ACTIVE' : 'TARGET FROZEN'}
            </span>
          </div>

          <div className="cal-grid-2col">
            {/* Target Lock / Freeze */}
            <button
              type="button"
              className={`cal-toggle-btn ${!isTracking ? 'active' : ''}`}
              onClick={onToggleTracking}
              title="Freeze turret position to inspect balloon target alignment"
            >
              <span className="cal-btn-title">TARGET LOCK</span>
              <span className="cal-btn-state">{!isTracking ? 'HOLD / FROZEN' : 'ACTIVE'}</span>
            </button>

            {/* Manual Sighting Laser */}
            <button
              type="button"
              className={`cal-toggle-btn ${isManualLaser ? 'active' : ''}`}
              onClick={onToggleManualLaser}
              title="Continuous Laser ON for physical targeting calibration"
            >
              <span className="cal-btn-title">SIGHTING LASER</span>
              <span className="cal-btn-state">{isManualLaser ? 'EMITTING (ON)' : 'OFF'}</span>
            </button>

            {/* Pan Inversion Toggle */}
            <button
              type="button"
              className={`cal-toggle-btn ${invertPan ? 'active' : ''}`}
              onClick={togglePanInvert}
              title="Toggle Pan tracking direction (Inverted fixes opposite direction)"
            >
              <span className="cal-btn-title">PAN DIRECTION</span>
              <span className="cal-btn-state">{invertPan ? 'INVERTED (FIX)' : 'NORMAL'}</span>
            </button>

            {/* Tilt Inversion Toggle */}
            <button
              type="button"
              className={`cal-toggle-btn ${invertTilt ? 'active' : ''}`}
              onClick={toggleTiltInvert}
              title="Toggle Tilt tracking direction"
            >
              <span className="cal-btn-title">TILT DIRECTION</span>
              <span className="cal-btn-state">{invertTilt ? 'INVERTED' : 'NORMAL'}</span>
            </button>
          </div>

          {/* Quick Home Calibration Button */}
          <button
            type="button"
            className="cal-home-btn"
            onClick={onHome || onCenter}
            title="Calibrate servos directly to Neutral Home (90.0°, 90.0°)"
          >
            <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            <span>CALIBRATE HOME POSITION (90°, 90°)</span>
          </button>

          {/* TILT MECHANICAL LEVEL TRIM & ZERO-POINT CALIBRATION */}
          <div className="cal-trim-section">
            <div className="cal-trim-header">
              <span className="cal-trim-title">TILT LEVEL TRIM:</span>
              <span className={`cal-trim-badge ${localTiltOffset !== 0 ? 'active' : ''}`}>
                {localTiltOffset > 0 ? `+${localTiltOffset.toFixed(1)}°` : `${localTiltOffset.toFixed(1)}°`}
              </span>
            </div>

            {/* Quick Trim Micro-Jog Nudge Buttons */}
            <div className="cal-trim-btn-row">
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(-5.0)}
                title="Trim down 5°"
              >
                -5°
              </button>
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(-1.0)}
                title="Trim down 1°"
              >
                -1°
              </button>
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(-0.5)}
                title="Trim down 0.5°"
              >
                -0.5°
              </button>
              <button
                type="button"
                className="cal-trim-btn reset"
                onClick={() => handleTiltOffsetCommit(0.0)}
                title="Reset trim to 0.0°"
              >
                0°
              </button>
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(0.5)}
                title="Trim up 0.5°"
              >
                +0.5°
              </button>
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(1.0)}
                title="Trim up 1°"
              >
                +1°
              </button>
              <button
                type="button"
                className="cal-trim-btn"
                onClick={() => handleNudgeTiltOffset(5.0)}
                title="Trim up 5°"
              >
                +5°
              </button>
            </div>

            {/* Tilt Trim Fine Slider */}
            <input
              type="range"
              min="-20.0"
              max="20.0"
              step="0.5"
              value={localTiltOffset}
              onChange={(e) => setLocalTiltOffset(parseFloat(e.target.value))}
              onMouseUp={() => handleTiltOffsetCommit()}
              onTouchEnd={() => handleTiltOffsetCommit()}
              className="cal-trim-slider"
            />

            {/* Set Current Position as Level Home (90°) */}
            {onZeroTilt && (
              <button
                type="button"
                className="cal-zero-level-btn"
                onClick={onZeroTilt}
                title="Set current physical tilt angle as 90.0° horizontal level reference"
              >
                <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="22" y1="12" x2="18" y2="12" />
                  <line x1="6" y1="12" x2="2" y2="12" />
                  <line x1="12" y1="6" x2="12" y2="2" />
                  <line x1="12" y1="22" x2="12" y2="18" />
                </svg>
                <span>SET CURRENT AS LEVEL (90° REF)</span>
              </button>
            )}
          </div>
        </div>

        {/* DISTANCE & STRUCTURE ADJUSTMENT */}
        <div className="compact-distance-row">
          <div className="dist-slider-header">
            <span className="dist-title">SERVO DISTANCE:</span>
            <span className="dist-badge">{localDistance} mm</span>
            <div className="compact-presets">
              {[30, 45, 55, 75, 110].map((d) => (
                <button
                  key={d}
                  type="button"
                  className={`pill-btn ${d === 55 ? 'preset-badge' : ''} ${localDistance === d ? 'active' : ''}`}
                  onClick={() => handlePreset(d)}
                  disabled={isCalibrating}
                  title={d === 55 ? "Calibrated Structure Preset (5.5cm)" : `${d}mm`}
                >
                  {d}mm{d === 55 ? ' ★' : ''}
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

        {/* MOTION SMOOTHNESS & DYNAMICS CONTROLS */}
        <div className="slider-group-compact mt-2">
          <div className="slider-header">
            <span className="slider-title">MOTION SMOOTHING (EMA):</span>
            <span className="slider-val">{localSmooth.toFixed(2)} (LOW = SILKY)</span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.65"
            step="0.05"
            value={localSmooth}
            onChange={(e) => setLocalSmooth(parseFloat(e.target.value))}
            onMouseUp={handleSmoothCommit}
            onTouchEnd={handleSmoothCommit}
          />
        </div>

        <div className="slider-group-compact mt-1">
          <div className="slider-header">
            <span className="slider-title">TRACKING GAIN (Kp):</span>
            <span className="slider-val">{localKp.toFixed(3)}</span>
          </div>
          <input
            type="range"
            min="0.02"
            max="0.14"
            step="0.005"
            value={localKp}
            onChange={(e) => setLocalKp(parseFloat(e.target.value))}
            onMouseUp={handleKpCommit}
            onTouchEnd={handleKpCommit}
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

        {/* REINFORCEMENT ACTIVE VISUAL CENTERING ALIGNMENT */}
        <div className="rl-centering-card" style={{
          background: 'rgba(255, 170, 0, 0.05)',
          border: '1px solid rgba(255, 170, 0, 0.25)',
          borderRadius: '6px',
          padding: '10px',
          margin: '8px 0'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: '700', color: '#ffaa00', letterSpacing: '0.05em' }}>
              RL TARGET CENTERING ALIGNMENT
            </span>
            <span style={{
              fontSize: '10px',
              padding: '2px 6px',
              borderRadius: '3px',
              background: rlActive ? 'rgba(0, 255, 136, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              color: rlActive ? '#00ff88' : '#888',
              border: `1px solid ${rlActive ? '#00ff88' : '#444'}`,
              fontWeight: '700'
            }}>
              {rlActive ? rlStage : 'READY'}
            </span>
          </div>

          {rlActive ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#ccc' }}>
                <span>Alignment: <strong>{rlAlignmentPct}%</strong></span>
                <span>Reward: <strong>+{rlReward}</strong></span>
                <span>Err: <strong>{rlDist}px</strong></span>
              </div>
              <div style={{ background: '#1a0e14', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  width: `${rlAlignmentPct}%`,
                  height: '100%',
                  background: rlStage === 'CENTER_LOCKED' ? '#00ff88' : '#ffaa00',
                  transition: 'width 0.1s ease-out'
                }} />
              </div>
              <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                {rlStage === 'CENTER_LOCKED' && onApplyRLCalibration ? (
                  <button
                    type="button"
                    className="btn btn-sm"
                    style={{ background: '#00ff88', color: '#000', fontWeight: '700', flex: 1 }}
                    onClick={onApplyRLCalibration}
                  >
                    LOCK & ZERO AS HOME REFERENCE
                  </button>
                ) : null}
                <button
                  type="button"
                  className="btn btn-abort btn-sm"
                  style={{ flex: rlStage === 'CENTER_LOCKED' ? '0 0 70px' : '1' }}
                  onClick={onStopRLAlignment}
                >
                  HALT
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ width: '100%', border: '1px solid #ffaa00', color: '#ffaa00' }}
              onClick={onStartRLAlignment}
              title="Drive turret with reinforcement policy gradient until target balloon center aligns perfectly with camera reticle"
            >
              🎯 START ACTIVE RL CENTERING ALIGNMENT
            </button>
          )}
        </div>

          {/* D-Pad Manual Jog */}
          <div className="compact-dpad-wrap">
            <button
              type="button"
              className="dpad-btn-sm"
              onClick={() => onNudge(0, invertTilt ? 5 : -5)}
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
                onClick={() => onNudge(invertPan ? 5 : -5, 0)}
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
                onClick={() => onNudge(invertPan ? -5 : 5, 0)}
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
              onClick={() => onNudge(0, invertTilt ? -5 : 5)}
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
