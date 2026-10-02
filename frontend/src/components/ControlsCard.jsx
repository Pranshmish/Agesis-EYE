import React, { useState } from 'react';

export default function ControlsCard({
  confThreshold,
  onConfChange,
  currentSource,
  onSaveSource,
  onDiscover,
  isDiscovering,
}) {
  const [sourceInput, setSourceInput] = useState(currentSource || 'http://10.96.117.1:81/stream');

  const handleConnect = (e) => {
    e.preventDefault();
    onSaveSource(sourceInput);
  };

  return (
    <div className="tactical-card">
      <div className="card-header">
        <h2 className="card-title">STREAM & THRESHOLD CONTROLS</h2>
      </div>
      <div className="card-body">
        {/* Confidence Threshold Slider */}
        <div className="slider-group">
          <div className="slider-header">
            <label htmlFor="slider-conf">Confidence Threshold:</label>
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
          <div className="slider-ticks">
            <span>0.10</span>
            <span>0.35 (Optimal)</span>
            <span>0.90</span>
          </div>
        </div>

        {/* Camera Stream Source Input */}
        <form className="input-group" onSubmit={handleConnect}>
          <label htmlFor="input-stream-url">Camera Stream URL / Source:</label>
          <div className="input-action-row">
            <input
              type="text"
              id="input-stream-url"
              value={sourceInput}
              onChange={(e) => setSourceInput(e.target.value)}
            />
            <button type="submit" className="btn btn-secondary btn-sm">
              CONNECT
            </button>
          </div>
          <button
            type="button"
            className="btn btn-outline btn-sm full-width mt-2"
            onClick={onDiscover}
            disabled={isDiscovering}
          >
            {isDiscovering ? 'SCANNING NETWORK...' : '🔍 AUTO-DISCOVER ESP32'}
          </button>
        </form>
      </div>
    </div>
  );
}
