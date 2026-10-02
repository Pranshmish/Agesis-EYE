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
    <div className="tactical-card telemetry-card-compact">
      <div className="card-header">
        <div className="card-title-group">
          <svg className="card-title-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <h2 className="card-title">TARGET TELEMETRY</h2>
        </div>
        <div className="header-status-group">
          <span className="card-badge">SECTOR: {targetPos}</span>
          <span className={`status-badge-pill ${lockStateClass}`}>
            {lockStateLabel} {streak > 0 && !isLocked ? `(${streak}/3)` : ''}
          </span>
        </div>
      </div>

      <div className="card-body">
        {/* Aiming Vector Coordinate Displacements */}
        <div className="vector-grid-compact">
          <div className="vector-row">
            <span className="vector-name">AZIMUTH ΔX</span>
            <div className="vector-bar-wrap">
              <div className="vector-bar-fill x-axis" style={barXStyle}></div>
            </div>
            <span className="vector-val">{dx >= 0 ? `+${dx}` : dx}px</span>
          </div>

          <div className="vector-row">
            <span className="vector-name">ELEVATION ΔY</span>
            <div className="vector-bar-wrap">
              <div className="vector-bar-fill y-axis" style={barYStyle}></div>
            </div>
            <span className="vector-val">{dy >= 0 ? `+${dy}` : dy}px</span>
          </div>
        </div>

        {/* Confidence Meter Inline */}
        <div className="confidence-row-compact">
          <div className="conf-label-inline">
            <span>AI CONFIDENCE</span>
            <span className="conf-pct-num">{confPct}%</span>
          </div>
          <div className="progress-track conf-track">
            <div className="progress-fill" style={{ width: `${confPct}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
