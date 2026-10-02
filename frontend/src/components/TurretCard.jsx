import React from 'react';

export default function TurretCard({ telemetry, onNudge, onCenter }) {
  const pan = telemetry?.pan !== undefined ? Number(telemetry.pan).toFixed(1) : '90.0';
  const tilt = telemetry?.tilt !== undefined ? Number(telemetry.tilt).toFixed(1) : '90.0';
  const isSimulated = telemetry?.is_simulated ?? true;

  return (
    <div className="tactical-card">
      <div className="card-header">
        <h2 className="card-title">TURRET KINEMATICS</h2>
        <span className="card-badge">
          {isSimulated ? 'SIMULATED' : 'HARDWARE SERIAL'}
        </span>
      </div>
      <div className="card-body">
        <div className="servo-angles-display">
          <div className="servo-box">
            <span className="servo-label">PAN (AZIMUTH)</span>
            <span className="servo-deg">{pan}°</span>
          </div>
          <div className="servo-box">
            <span className="servo-label">TILT (ELEVATION)</span>
            <span className="servo-deg">{tilt}°</span>
          </div>
        </div>

        {/* Manual D-Pad Test Controls */}
        <div className="dpad-container">
          <div className="dpad-row">
            <button className="dpad-btn" onClick={() => onNudge(0, 5)} title="Tilt Up">▲</button>
          </div>
          <div className="dpad-row">
            <button className="dpad-btn" onClick={() => onNudge(-5, 0)} title="Pan Left">◀</button>
            <button className="dpad-btn center-btn" onClick={onCenter} title="Center Turret">◉</button>
            <button className="dpad-btn" onClick={() => onNudge(5, 0)} title="Pan Right">▶</button>
          </div>
          <div className="dpad-row">
            <button className="dpad-btn" onClick={() => onNudge(0, -5)} title="Tilt Down">▼</button>
          </div>
        </div>
      </div>
    </div>
  );
}
