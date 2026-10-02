import React, { useState, useEffect } from 'react';

export default function ControlsCard({
  confThreshold,
  onConfChange,
  currentSource,
  onSaveSource,
  onDiscover,
  isDiscovering,
}) {
  const [sourceInput, setSourceInput] = useState(currentSource || 'http://10.96.117.1:81/stream');

  useEffect(() => {
    if (currentSource) {
      setSourceInput(currentSource);
    }
  }, [currentSource]);

  const handleConnect = (e) => {
    e.preventDefault();
    onSaveSource(sourceInput);
  };

  return (
    <div className="tactical-card controls-card-compact">
      <div className="card-header">
        <div className="card-title-group">
          <svg className="card-title-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="4" y1="21" x2="4" y2="14" />
            <line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" />
            <line x1="20" y1="12" x2="20" y2="3" />
          </svg>
          <h2 className="card-title">STREAM & DETECTION THRESHOLD</h2>
        </div>
      </div>

      <div className="card-body">
        {/* Confidence Threshold Slider */}
        <div className="slider-group-compact">
          <div className="slider-header">
            <span className="slider-title">MIN CONFIDENCE:</span>
            <span className="slider-val">{Number(confThreshold).toFixed(2)}</span>
          </div>
          <input
            type="range"
            id="slider-conf"
            min="0.10"
            max="0.90"
            step="0.05"
            value={confThreshold}
            onChange={(e) => onConfChange(parseFloat(e.target.value))}
          />
        </div>

        {/* Camera Stream Source Input */}
        <form className="stream-form-compact" onSubmit={handleConnect}>
          <div className="input-action-row">
            <input
              type="text"
              id="input-stream-url"
              value={sourceInput}
              onChange={(e) => setSourceInput(e.target.value)}
              placeholder="Stream URL / IP"
              spellCheck="false"
            />
            <button type="submit" className="btn btn-secondary btn-sm" title="Connect to Stream">
              CONNECT
            </button>
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={onDiscover}
              disabled={isDiscovering}
              title="Auto-Discover ESP32 on Local Network"
            >
              <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <span>{isDiscovering ? 'SCANNING...' : 'AUTO-FIND'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
