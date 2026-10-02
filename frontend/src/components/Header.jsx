import React from 'react';

export default function Header({
  telemetry,
  connected,
  viewMode = 'FEED',
  onViewModeChange,
}) {
  const isCalibrating = !!telemetry?.is_calibrating;

  return (
    <header className="tactical-header">
      <div className="header-brand">
        <div className="brand-radar-icon">
          <div className="radar-sweep"></div>
          <div className="radar-blip"></div>
        </div>
        <div>
          <h1 className="brand-title">AGESIS <span className="accent-text">EYE</span></h1>
          <p className="brand-subtitle">AUTONOMOUS TARGETING SYSTEM // KINEMATIC DIGITAL TWIN</p>
        </div>
      </div>

      {/* View Mode Selector Tabs */}
      <div className="view-mode-tabs">
        <button
          type="button"
          className={`vm-tab ${viewMode === 'FEED' ? 'active' : ''}`}
          onClick={() => onViewModeChange?.('FEED')}
        >
          <svg className="vm-tab-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
          <span>CAMERA HUD</span>
        </button>

        <button
          type="button"
          className={`vm-tab ${viewMode === 'TWIN' ? 'active' : ''}`}
          onClick={() => onViewModeChange?.('TWIN')}
        >
          <svg className="vm-tab-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
          <span>3D DIGITAL TWIN</span>
        </button>

        <button
          type="button"
          className={`vm-tab ${viewMode === 'SPLIT' ? 'active' : ''}`}
          onClick={() => onViewModeChange?.('SPLIT')}
        >
          <svg className="vm-tab-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="12" y1="3" x2="12" y2="21" />
          </svg>
          <span>SPLIT VIEW</span>
        </button>
      </div>

      <div className="header-telemetry-badges">
        <div className="badge-item">
          <span className="badge-label">AI MODEL</span>
          <span className="badge-value">agesis06.onnx</span>
        </div>
        <div className="badge-item">
          <span className="badge-label">LATENCY</span>
          <span className="badge-value">
            {telemetry?.latency_ms !== undefined ? `${telemetry.latency_ms} ms` : '-- ms'}
          </span>
        </div>
        <div className="badge-item">
          <span className="badge-label">STREAM FPS</span>
          <span className="badge-value">
            {telemetry?.cam_fps !== undefined ? `${telemetry.cam_fps} FPS` : '-- FPS'}
          </span>
        </div>
        <div className="badge-item">
          <span className="badge-label">SERVO DIST</span>
          <span className="badge-value">
            {telemetry?.servo_distance_mm !== undefined ? `${telemetry.servo_distance_mm} mm` : '45.0 mm'}
          </span>
        </div>
        <div className={`badge-item status-pill ${connected ? '' : 'disconnected'} ${isCalibrating ? 'status-calibrating' : ''}`}>
          <span className="status-dot"></span>
          <span>{isCalibrating ? 'CALIBRATING' : connected ? 'ONLINE' : 'OFFLINE'}</span>
        </div>
      </div>
    </header>
  );
}
