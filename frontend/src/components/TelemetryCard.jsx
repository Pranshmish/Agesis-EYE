import React from 'react';

export default function TelemetryCard({ telemetry }) {
  const isLocked = telemetry?.locked;
  const streak = telemetry?.streak || 0;
  const dx = telemetry?.dx || 0;
  const dy = telemetry?.dy || 0;
  const conf = telemetry?.conf || 0;
  const targetPos = telemetry?.target_pos || 'CENTER';

  let lockStateLabel = 'SEARCHING';
  let lockStateClass = 'searching';
  if (isLocked) {
    lockStateLabel = 'LOCKED';
    lockStateClass = 'locked';
  } else if (streak > 0) {
    lockStateLabel = 'ACQUIRING';
    lockStateClass = 'acquiring';
  }

  // Calculate visual displacement bars (Center = 50%)
  const pctX = Math.max(0, Math.min(100, (dx / 160) * 50));
  const barXStyle = dx >= 0
    ? { left: '50%', width: `${pctX}%` }
    : { left: `${50 - Math.abs(pctX)}%`, width: `${Math.abs(pctX)}%` };

  const pctY = Math.max(0, Math.min(100, (dy / 120) * 50));
  const barYStyle = dy >= 0
    ? { left: '50%', width: `${pctY}%` }
    : { left: `${50 - Math.abs(pctY)}%`, width: `${Math.abs(pctY)}%` };

  const confPct = Math.round(conf * 100);

  return (
    <div className="tactical-card">
      <div className="card-header">
        <h2 className="card-title">TARGET TELEMETRY</h2>
        <span className="card-badge">SECTOR: {targetPos}</span>
      </div>
      <div className="card-body">
        <div className="stat-row">
          <div className="stat-block">
            <span className="stat-label">LOCK STATE</span>
            <span className={`stat-val status-badge-inline ${lockStateClass}`}>
              {lockStateLabel}
            </span>
          </div>
          <div className="stat-block">
            <span className="stat-label">STREAK / LOCK</span>
            <div className="streak-meter">
              <span className="stat-val">{streak}</span>
              <span className="stat-sub">/ 3 FRAMES</span>
            </div>
          </div>
        </div>

        {/* Aiming Vector Coordinate Displacements */}
        <div className="vector-grid">
          <div className="vector-item">
            <span className="vector-name">ΔX (AZIMUTH)</span>
            <div className="vector-bar-wrap">
              <div className="vector-bar-fill x-axis" style={barXStyle}></div>
            </div>
            <span className="vector-val">{dx >= 0 ? `+${dx}` : dx} px</span>
          </div>
          <div className="vector-item">
            <span className="vector-name">ΔY (ELEVATION)</span>
            <div className="vector-bar-wrap">
              <div className="vector-bar-fill y-axis" style={barYStyle}></div>
            </div>
            <span className="vector-val">{dy >= 0 ? `+${dy}` : dy} px</span>
          </div>
        </div>

        {/* Confidence Meter */}
        <div className="confidence-container">
          <div className="conf-header">
            <span className="conf-label">DETECTION CONFIDENCE</span>
            <span className="conf-val">{confPct}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${confPct}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
