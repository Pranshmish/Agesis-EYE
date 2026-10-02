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

  let lockClass = 'searching';
  let lockText = 'SEARCHING TARGET...';
  if (isLocked) {
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
        </div>

        {/* Dynamic Lock Banner */}
        <div className={`lock-banner ${lockClass}`}>
          <span className="lock-icon">◎</span>
          <span>{lockText}</span>
        </div>

        {/* FOV Peripheral Sector Edge Labels */}
        <div
          className="fov-edge-label left"
          style={{ color: targetPos === 'EXTREME LEFT' ? 'var(--cyan-primary)' : 'var(--text-dim)' }}
        >
          EXTREME LEFT
        </div>
        <div
          className="fov-edge-label right"
          style={{ color: targetPos === 'EXTREME RIGHT' ? 'var(--cyan-primary)' : 'var(--text-dim)' }}
        >
          EXTREME RIGHT
        </div>
      </div>

      {/* Quick Action Toolbar */}
      <div className="viewport-toolbar">
        <div className="toolbar-left">
          <button className="btn btn-secondary" onClick={onSnapshot} title="Save annotated snapshot">
            <span className="btn-icon">📷</span> SNAPSHOT
          </button>
          <button className="btn btn-toggle" onClick={onToggleEnhance} title="Toggle EP-CLAHE domain adaptation">
            <span className="btn-icon">✨</span> EP-CLAHE{' '}
            <span className={`toggle-pill ${isEnhance ? 'active' : ''}`}>
              {isEnhance ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>

        <div className="toolbar-right">
          <div className="laser-arm-control">
            <span className="laser-arm-label">LASER EMITTER:</span>
            <button
              className={`btn-laser-toggle ${isArmed || isFiring ? 'armed' : 'safe'}`}
              onClick={onToggleLaser}
            >
              <span className="laser-indicator"></span>
              <span>{isFiring ? 'FIRING!' : isArmed ? 'ARMED (READY)' : 'SAFE / DISARMED'}</span>
            </button>
          </div>
          <button className="btn btn-icon-only" onClick={toggleFullscreen} title="Toggle Fullscreen">
            ⛶
          </button>
        </div>
      </div>
    </section>
  );
}
