import React from 'react';

export default function Header({ telemetry, connected }) {
  return (
    <header className="tactical-header">
      <div className="header-brand">
        <div className="brand-radar-icon">
          <div className="radar-sweep"></div>
        </div>
        <div>
          <h1 className="brand-title">AGESIS <span className="accent-text">EYE</span></h1>
          <p className="brand-subtitle">AUTONOMOUS TARGETING SYSTEM // REACT GROUND STATION</p>
        </div>
      </div>

      <div className="header-telemetry-badges">
        <div className="badge-item">
          <span className="badge-label">MODEL</span>
          <span className="badge-value">agesis06.onnx</span>
        </div>
        <div className="badge-item">
          <span className="badge-label">LATENCY</span>
          <span className="badge-value text-cyan">
            {telemetry?.latency_ms !== undefined ? `${telemetry.latency_ms} ms` : '-- ms'}
          </span>
        </div>
        <div className="badge-item">
          <span className="badge-label">STREAM FPS</span>
          <span className="badge-value text-emerald">
            {telemetry?.cam_fps !== undefined ? `${telemetry.cam_fps} FPS` : '-- FPS'}
          </span>
        </div>
        <div className={`badge-item status-pill ${connected ? '' : 'disconnected'}`}>
          <span className="status-dot"></span>
          <span>{connected ? 'CONNECTED' : 'DISCONNECTED'}</span>
        </div>
      </div>
    </header>
  );
}
