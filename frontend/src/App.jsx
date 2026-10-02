import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import Viewport from './components/Viewport';
import DigitalTwin from './components/DigitalTwin';
import TelemetryCard from './components/TelemetryCard';
import TurretCard from './components/TurretCard';
import ControlsCard from './components/ControlsCard';
import Toast from './components/Toast';

export default function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [connected, setConnected] = useState(false);
  const [streamSrc, setStreamSrc] = useState('/api/stream');
  const [confThreshold, setConfThreshold] = useState(0.35);
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

    const connectWs = () => {
      const loc = window.location;
      const wsProto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = loc.port === '5173' ? '127.0.0.1:8000' : loc.host;
      const wsUrl = `${wsProto}//${wsHost}/ws/telemetry`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMounted) setConnected(true);
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
          setTimeout(connectWs, 2000);
        }
      };

      ws.onerror = () => {
        if (!pollInterval && isMounted) {
          pollInterval = setInterval(fetchTelemetry, 100);
        }
      };
    };

    const fetchTelemetry = async () => {
      try {
        const res = await fetch('/api/telemetry');
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
      if (wsRef.current) wsRef.current.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  // Snapshot handler
  const handleSnapshot = async () => {
    try {
      const res = await fetch('/api/snapshot', { method: 'POST' });
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
      await fetch('/api/config', {
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
      await fetch('/api/config', {
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
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conf: val }),
      });
    } catch (e) {}
  };

  // Connect to new camera stream source
  const handleSaveSource = async (url) => {
    try {
      showToast('Connecting to camera stream...');
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: url }),
      });
      setStreamSrc(`/api/stream?t=${Date.now()}`);
    } catch (e) {
      showToast('Failed to connect to stream');
    }
  };

  // Auto-discover ESP32 IP
  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      const res = await fetch('/api/discover');
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
      await fetch('/api/turret/nudge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pan: dPan, tilt: dTilt }),
      });
    } catch (e) {}
  };

  // Turret center reset
  const handleCenter = async () => {
    try {
      await fetch('/api/turret/center', { method: 'POST' });
      showToast('Turret neutral calibrated to (90.0, 90.0)');
    } catch (e) {}
  };

  // Inter-Servo Distance adjustment
  const handleDistanceChange = async (distanceMm) => {
    try {
      const res = await fetch('/api/turret/distance', {
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
      const res = await fetch('/api/turret/calibrate/start', { method: 'POST' });
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
      const res = await fetch('/api/turret/calibrate/stop', { method: 'POST' });
      const data = await res.json();
      if (data.turret) {
        setTelemetry((prev) => ({ ...prev, ...data.turret }));
      }
      showToast('Calibration sequence aborted');
    } catch (e) {}
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
            onSnapshot={handleSnapshot}
            onToggleEnhance={handleToggleEnhance}
            onToggleLaser={handleToggleLaser}
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
              onDistanceChange={handleDistanceChange}
              onStartCalibration={handleStartCalibration}
              onStopCalibration={handleStopCalibration}
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
