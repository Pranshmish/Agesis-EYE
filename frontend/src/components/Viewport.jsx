import React, { useRef } from 'react';

export default function Viewport({
  telemetry,
  streamSrc,
  onSnapshot,
  onToggleEnhance,
  onToggleLaser,
}) {
  const videoBoxRef = useRef(null);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoBoxRef.current?.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  };

  const isLocked = telemetry?.locked;
  const streak = telemetry?.streak || 0;
  const lockThresh = telemetry?.lock_threshold || 3;
  const targetPos = telemetry?.target_pos || 'CENTER';
  const isEnhance = !!telemetry?.enhance;
  const isArmed = !!telemetry?.laser_armed;
  const isFiring = !!telemetry?.laser_firing;
  const isCalibrating = !!telemetry?.is_calibrating;

  let lockClass = 'searching';
  let lockText = 'SEARCHING AIRSPACE...';
  if (isCalibrating) {
    lockClass = 'acquiring';
    lockText = `KINEMATIC CALIBRATION IN PROGRESS: ${telemetry?.calibration_stage || ''}`;
  } else if (isLocked) {
    lockClass = 'locked';
    lockText = `TARGET LOCKED (STREAK: ${streak})`;
  } else if (streak > 0) {
    lockClass = 'acquiring';
    lockText = `ACQUIRING TARGET (${streak}/${lockThresh})`;
  }

  return (
    <section className="viewport-section">
      <div className="video-container" ref={videoBoxRef} id="video-frame-box">
        {/* Live Camera MJPEG Stream */}
        <img
          id="video-stream"
          className="stream-media"
          src={streamSrc}
          alt="Agesis EYE Live Tracking Feed"
        />

        {/* Tactical Corner Brackets */}
        <div className="hud-corners">
          <div className="corner corner-tl"></div>
          <div className="corner corner-tr"></div>
          <div className="corner corner-bl"></div>
          <div className="corner corner-br"></div>
        </div>

        {/* Center Crosshair Reticle */}
        <div className="crosshair-wrapper">
          <div className="crosshair-circle"></div>
          <div className="crosshair-dot"></div>
          <div className="crosshair-line line-h"></div>
          <div className="crosshair-line line-v"></div>
          <div className="crosshair-ticks tick-t"></div>
          <div className="crosshair-ticks tick-b"></div>
          <div className="crosshair-ticks tick-l"></div>
          <div className="crosshair-ticks tick-r"></div>
        </div>

        {/* Dynamic Lock Banner */}
        <div className={`lock-banner ${lockClass}`}>
          <svg className="lock-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="3" />
            <line x1="12" y1="1" x2="12" y2="5" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="1" y1="12" x2="5" y2="12" />
            <line x1="19" y1="12" x2="23" y2="12" />
          </svg>
          <span>{lockText}</span>
        </div>

        {/* FOV Peripheral Sector Edge Labels */}
        <div
          className="fov-edge-label left"
          style={{ color: targetPos === 'EXTREME LEFT' ? 'var(--blood-red)' : 'var(--text-dim)' }}
        >
          SECTOR: L-EXTREME
        </div>
        <div
          className="fov-edge-label right"
          style={{ color: targetPos === 'EXTREME RIGHT' ? 'var(--blood-red)' : 'var(--text-dim)' }}
        >
          SECTOR: R-EXTREME
        </div>
      </div>

      {/* Quick Action Toolbar */}
      <div className="viewport-toolbar">
        <div className="toolbar-left">
          <button className="btn btn-secondary" onClick={onSnapshot} title="Capture annotated snapshot">
            <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <span>SNAPSHOT</span>
          </button>

          <button className="btn btn-toggle" onClick={onToggleEnhance} title="Toggle EP-CLAHE domain adaptation">
            <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2a10 10 0 0 0 0 20z" fill="currentColor" fillOpacity="0.3" />
              <circle cx="12" cy="12" r="4" strokeWidth="1.5" />
            </svg>
            <span>EP-CLAHE</span>
            <span className={`toggle-pill ${isEnhance ? 'active' : ''}`}>
              {isEnhance ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>

        <div className="toolbar-right">
          <div className="laser-arm-control">
            <span className="laser-arm-label">LASER INTERLOCK:</span>
            <button
              className={`btn-laser-toggle ${isFiring ? 'firing' : isArmed ? 'armed' : 'safe'}`}
              onClick={onToggleLaser}
            >
              <span className="laser-indicator"></span>
              <span>{isFiring ? 'EMITTING LASER' : isArmed ? 'ARMED / HOT' : 'SAFE / DISARMED'}</span>
            </button>
          </div>

          <button className="btn btn-icon-only" onClick={toggleFullscreen} title="Toggle Fullscreen View">
            <svg className="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}
