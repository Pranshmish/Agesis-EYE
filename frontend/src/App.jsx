import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import Viewport from './components/Viewport';
import DigitalTwin from './components/DigitalTwin';
import TelemetryCard from './components/TelemetryCard';
import TurretCard from './components/TurretCard';
import ControlsCard from './components/ControlsCard';
import Toast from './components/Toast';

const API_BASE = '';

const getStreamUrl = () => {
  if (typeof window === 'undefined') return '/api/stream';
  if (window.location.port === '5173') {
    return 'http://127.0.0.1:8000/api/stream';
  }
  return '/api/stream';
};

export default function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [connected, setConnected] = useState(false);
  const [streamSrc, setStreamSrc] = useState(() => getStreamUrl());
  const [confThreshold, setConfThreshold] = useState(0.22);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [toast, setToast] = useState({ message: '', visible: false });
  const [viewMode, setViewMode] = useState('FEED'); // 'FEED' | 'TWIN' | 'SPLIT'

  const wsRef = useRef(null);
  const toastTimeoutRef = useRef(null);

  const showToast = (message) => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToast({ message, visible: true });
    toastTimeoutRef.current = setTimeout(() => {
      setToast({ message: '', visible: false });
    }, 2800);
  };

  // Setup WebSocket Telemetry with Auto-Reconnect & Fallback Polling
  useEffect(() => {
    let isMounted = true;
    let pollInterval = null;
    let reconnectTimer = null;

    const connectWs = () => {
      const loc = window.location;
      const wsProto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
      // Connect directly to backend at 127.0.0.1:8000 when on Vite dev port 5173
      const wsHost = loc.port === '5173' ? '127.0.0.1:8000' : loc.host;
      const wsUrl = `${wsProto}//${wsHost}/ws/telemetry`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isMounted) {
            setConnected(true);
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (isMounted) {
              setTelemetry(data);
              setConnected(!!data.connected);
              if (data.conf_threshold !== undefined) {
                setConfThreshold(data.conf_threshold);
              }
            }
          } catch (e) {}
        };

        ws.onclose = () => {
          if (isMounted) {
            setConnected(false);
            if (!pollInterval) {
              pollInterval = setInterval(fetchTelemetry, 1500);
            }
            reconnectTimer = setTimeout(connectWs, 2500);
          }
        };

        ws.onerror = () => {
          if (!pollInterval && isMounted) {
            pollInterval = setInterval(fetchTelemetry, 1500);
          }
        };
      } catch (err) {
        if (!pollInterval && isMounted) {
          pollInterval = setInterval(fetchTelemetry, 1500);
        }
      }
    };

    const fetchTelemetry = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/telemetry`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setTelemetry(data);
            setConnected(!!data.connected);
          }
        }
      } catch (err) {}
    };

    connectWs();

    return () => {
      isMounted = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        const currentWs = wsRef.current;
        if (currentWs.readyState === WebSocket.OPEN) {
          currentWs.close();
        } else if (currentWs.readyState === WebSocket.CONNECTING) {
          currentWs.onopen = () => currentWs.close();
        }
      }
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  // Snapshot handler
  const handleSnapshot = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/snapshot`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast(`Snapshot saved: ${data.filename}`);
      } else {
        showToast(data.message || 'Snapshot capture failed');
      }
    } catch (e) {
      showToast('Error saving snapshot');
    }
  };

  // EP-CLAHE toggle handler
  const handleToggleEnhance = async () => {
    const nextState = !telemetry?.enhance;
    try {
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enhance: nextState }),
      });
      showToast(`EP-CLAHE Domain Transform: ${nextState ? 'ENABLED' : 'DISABLED'}`);
    } catch (e) {
      showToast('Failed to update EP-CLAHE setting');
    }
  };

  // Laser Arm toggle handler
  const handleToggleLaser = async () => {
    const nextArmed = !telemetry?.laser_armed;
    if (nextArmed) {
      if (!window.confirm('CAUTION: Arm high-power targeting laser emitter?\nConfirm laser safety eyewear is deployed before proceeding.')) {
        return;
      }
    }
    try {
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ laser_armed: nextArmed }),
      });
      showToast(`Laser Interlock: ${nextArmed ? 'ARMED / HOT' : 'SAFE / DISARMED'}`);
    } catch (e) {
      showToast('Failed to toggle laser');
    }
  };

  // Confidence threshold update handler
  const handleConfChange = async (val) => {
    setConfThreshold(val);
    try {
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conf: val }),
      });
    } catch (e) {}
  };

  // Camera Feed Inversion / Flip Handler
  const handleToggleFlipV = async () => {
    const nextFlip = !(telemetry?.flip_v ?? true);
    try {
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flip_v: nextFlip }),
      });
      setTelemetry((prev) => ({ ...prev, flip_v: nextFlip }));
      showToast(`Camera Feed Flip: ${nextFlip ? 'UPSIDE-DOWN (INVERTED)' : 'NORMAL'}`);
    } catch (e) {
      showToast('Failed to toggle camera flip');
    }
  };

  // Connect to new camera stream source
  const handleSaveSource = async (url) => {
    try {
      showToast('Connecting to camera stream...');
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: url }),
      });
      setStreamSrc(`${getStreamUrl()}?t=${Date.now()}`);
    } catch (e) {
      showToast('Failed to connect to stream');
    }
  };

  // Auto-discover ESP32 IP
  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      const res = await fetch(`${API_BASE}/api/discover`);
      const data = await res.json();
      if (data.status === 'found') {
        showToast(`ESP32 camera located: ${data.url}`);
        handleSaveSource(data.url);
      } else {
        showToast('Could not find ESP32 automatically. Enter IP manually.');
      }
    } catch (e) {
      showToast('Discovery scan failed');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Turret manual jog
  const handleNudge = async (dPan, dTilt) => {
    try {
      await fetch(`${API_BASE}/api/turret/nudge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pan: dPan, tilt: dTilt }),
      });
    } catch (e) {}
  };

  // Turret center reset
  const handleCenter = async () => {
    try {
      await fetch(`${API_BASE}/api/turret/center`, { method: 'POST' });
      showToast('Turret neutral calibrated to (90.0, 90.0)');
    } catch (e) {}
  };

  // Turret direct home calibration
  const handleHome = async () => {
    try {
      await fetch(`${API_BASE}/api/turret/home`, { method: 'POST' });
      showToast('Turret calibrated to Home position (90.0°, 90.0°)');
    } catch (e) {}
  };

  // Manual Sighting Laser ON/OFF toggle
  const handleToggleManualLaser = async () => {
    const nextState = !telemetry?.manual_laser;
    try {
      const res = await fetch(`${API_BASE}/api/turret/laser/manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manual_laser: nextState }),
      });
      const data = await res.json();
      if (data) {
        setTelemetry((prev) => ({ ...prev, ...data }));
      }
      showToast(`Manual Sighting Laser: ${nextState ? 'EMITTING (ON)' : 'OFF'}`);
    } catch (e) {
      showToast('Failed to toggle manual sighting laser');
    }
  };

  // Target Tracking Lock / Freeze toggle
  const handleToggleTracking = async () => {
    const isCurrentlyTracking = telemetry?.tracking_enabled !== false;
    const nextTracking = !isCurrentlyTracking;
    try {
      const res = await fetch(`${API_BASE}/api/turret/tracking/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tracking_enabled: nextTracking }),
      });
      const data = await res.json();
      if (data) {
        setTelemetry((prev) => ({ ...prev, ...data }));
      }
      showToast(`Turret Tracking: ${nextTracking ? 'ACTIVE (TRACKING)' : 'LOCKED / FROZEN'}`);
    } catch (e) {
      showToast('Failed to toggle tracking');
    }
  };

  // Direction Inversion quick toggle for Pan
  const handleToggleInvertPan = async () => {
    const currentInvert = telemetry?.invert_pan !== false;
    await handleStructureUpdate({ invert_pan: !currentInvert });
  };

  // Structure and calibration trim updates
  const handleStructureUpdate = async (params) => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/structure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data) {
        setTelemetry((prev) => ({ ...prev, ...data }));
      }
      showToast('Calibration parameters updated & saved');
    } catch (e) {
      showToast('Failed to update calibration');
    }
  };

  // Inter-Servo Distance adjustment
  const handleDistanceChange = async (distanceMm) => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/distance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ distance_mm: distanceMm }),
      });
      const data = await res.json();
      if (data) {
        setTelemetry((prev) => ({ ...prev, ...data }));
        showToast(`Servo separation set to ${distanceMm}mm`);
      }
    } catch (e) {
      showToast('Failed to update servo separation distance');
    }
  };

  // Automated Calibration Movement start
  const handleStartCalibration = async () => {
    try {
      showToast('Initiating autonomous 2-servo calibration movement...');
      const res = await fetch(`${API_BASE}/api/turret/calibrate/start`, { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
      }
    } catch (e) {
      showToast('Failed to start calibration routine');
    }
  };

  // Automated Calibration Movement stop
  const handleStopCalibration = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/calibrate/stop`, { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
      }
      showToast('Calibration sequence aborted');
    } catch (e) {}
  };

  // Zero tilt horizontal level calibration
  const handleZeroTilt = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/calibrate/zero_tilt`, { method: 'POST' });
      const data = await res.json();
      if (data) {
        setTelemetry((prev) => ({ ...prev, ...data }));
        showToast(`Zero Level Calibrated! 90.0° set (Offset: ${data.tilt_offset > 0 ? `+${data.tilt_offset}` : data.tilt_offset}°)`);
      }
    } catch (e) {
      showToast('Failed to calibrate zero tilt');
    }
  };

  // Active Reinforcement Centering Alignment
  const handleStartRLAlignment = async () => {
    try {
      showToast('Initiating RL Target Centering Alignment...');
      const res = await fetch(`${API_BASE}/api/turret/alignment/start`, { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
      }
    } catch (e) {
      showToast('Failed to start RL alignment');
    }
  };

  const handleStopRLAlignment = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/alignment/stop`, { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
      }
      showToast('RL Target Centering halted');
    } catch (e) {}
  };

  const handleApplyRLCalibration = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/turret/alignment/calibrate`, { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
        showToast(`Target Centered Calibration Saved! (Pan Trim: ${data.turret.pan_offset}°, Tilt Trim: ${data.turret.tilt_offset}°)`);
      }
    } catch (e) {
      showToast('Failed to apply calibrated offsets');
    }
  };

  return (
    <>
      <div className="hud-scanline"></div>
      <Header
        telemetry={telemetry}
        connected={connected}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      <main className={`dashboard-grid mode-${viewMode.toLowerCase()}`}>
        {/* VIEW 1: Standard CAMERA HUD */}
        {(viewMode === 'FEED' || viewMode === 'SPLIT') && (
          <Viewport
            telemetry={telemetry}
            streamSrc={streamSrc}
            apiBase={API_BASE}
            onReloadStream={() => {
              const base = window.location.port === '5173' ? 'http://127.0.0.1:8000/api/stream' : '/api/stream';
              setStreamSrc(`${base}?t=${Date.now()}`);
            }}
            onSnapshot={handleSnapshot}
            onToggleEnhance={handleToggleEnhance}
            onToggleLaser={handleToggleLaser}
            onToggleManualLaser={handleToggleManualLaser}
            onToggleTracking={handleToggleTracking}
            onToggleInvertPan={handleToggleInvertPan}
            onToggleFlipV={handleToggleFlipV}
          />
        )}

        {/* VIEW 2: 3D MOTION TRAJECTORY DIGITAL TWIN */}
        {(viewMode === 'TWIN' || viewMode === 'SPLIT') && (
          <DigitalTwin
            telemetry={telemetry}
            onDistanceChange={handleDistanceChange}
            isLaserArmed={!!telemetry?.laser_armed}
            isLaserFiring={!!telemetry?.laser_firing}
          />
        )}

        {/* Tactical Control Sidebar (Always accessible or streamlined) */}
        {viewMode !== 'TWIN' && (
          <aside className="sidebar-section">
            <TelemetryCard telemetry={telemetry} />
            <TurretCard
              telemetry={telemetry}
              onNudge={handleNudge}
              onCenter={handleCenter}
              onHome={handleHome}
              onDistanceChange={handleDistanceChange}
              onStructureUpdate={handleStructureUpdate}
              onZeroTilt={handleZeroTilt}
              onToggleTracking={handleToggleTracking}
              onToggleManualLaser={handleToggleManualLaser}
              onStartCalibration={handleStartCalibration}
              onStopCalibration={handleStopCalibration}
              onStartRLAlignment={handleStartRLAlignment}
              onStopRLAlignment={handleStopRLAlignment}
              onApplyRLCalibration={handleApplyRLCalibration}
              onOpenDigitalTwin={() => setViewMode('TWIN')}
            />
            <ControlsCard
              confThreshold={confThreshold}
              onConfChange={handleConfChange}
              currentSource={telemetry?.source}
              onSaveSource={handleSaveSource}
              onDiscover={handleDiscover}
              isDiscovering={isDiscovering}
            />
          </aside>
        )}
      </main>

      <Toast toast={toast} />
    </>
  );
}
