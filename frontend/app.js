/**
 * Agesis EYE - Frontend Ground Station Controller
 * Connects to WebSocket/REST telemetry, updates tactical HUD, and handles interactive controls.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const badgeFps = document.getElementById("badge-fps");
  const badgeLatency = document.getElementById("badge-latency");
  const badgeConnection = document.getElementById("badge-connection");
  const badgeConnectionText = document.getElementById("badge-connection-text");

  const lockBanner = document.getElementById("lock-banner");
  const lockBannerText = document.getElementById("lock-banner-text");
  const fovLeftLabel = document.getElementById("fov-left-label");
  const fovRightLabel = document.getElementById("fov-right-label");

  const statLockState = document.getElementById("stat-lock-state");
  const statStreak = document.getElementById("stat-streak");
  const valDx = document.getElementById("val-dx");
  const valDy = document.getElementById("val-dy");
  const barDx = document.getElementById("bar-dx");
  const barDy = document.getElementById("bar-dy");
  const valConf = document.getElementById("val-conf");
  const confProgressBar = document.getElementById("conf-progress-bar");
  const sectorBadge = document.getElementById("telemetry-sector-badge");

  const valPan = document.getElementById("val-pan");
  const valTilt = document.getElementById("val-tilt");
  const turretModeBadge = document.getElementById("turret-mode-badge");

  const btnSnapshot = document.getElementById("btn-snapshot");
  const btnEnhance = document.getElementById("btn-enhance");
  const pillEnhance = document.getElementById("pill-enhance");
  const btnLaserArm = document.getElementById("btn-laser-arm");
  const laserBtnText = document.getElementById("laser-btn-text");
  const btnFullscreen = document.getElementById("btn-fullscreen");
  const videoFrameBox = document.getElementById("video-frame-box");

  const sliderConf = document.getElementById("slider-conf");
  const valSliderConf = document.getElementById("val-slider-conf");
  const inputStreamUrl = document.getElementById("input-stream-url");
  const btnSaveSource = document.getElementById("btn-save-source");
  const btnDiscover = document.getElementById("btn-discover");
  const toast = document.getElementById("toast");
  const toastMessage = document.getElementById("toast-message");

  // D-Pad Buttons
  const dpadUp = document.getElementById("dpad-up");
  const dpadDown = document.getElementById("dpad-down");
  const dpadLeft = document.getElementById("dpad-left");
  const dpadRight = document.getElementById("dpad-right");
  const dpadCenter = document.getElementById("dpad-center");

  // State
  let currentEnhance = false;
  let currentArmed = false;
  let ws = null;

  // Show Toast
  function showToast(msg) {
    toastMessage.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2800);
  }

  // Update UI with Telemetry
  function updateTelemetry(data) {
    if (!data) return;

    // Badges
    badgeFps.textContent = `${data.cam_fps || 0} FPS`;
    badgeLatency.textContent = `${data.latency_ms || 0} ms`;

    if (data.connected) {
      badgeConnection.className = "badge-item status-pill";
      badgeConnectionText.textContent = "CONNECTED";
    } else {
      badgeConnection.className = "badge-item status-pill searching";
      badgeConnectionText.textContent = "DISCONNECTED";
    }

    // Lock Status
    if (data.locked) {
      lockBanner.className = "lock-banner locked";
      lockBannerText.textContent = `TARGET LOCKED (STREAK: ${data.streak})`;
      statLockState.className = "stat-val status-badge-inline locked";
      statLockState.textContent = "LOCKED";
    } else if (data.streak > 0) {
      lockBanner.className = "lock-banner acquiring";
      lockBannerText.textContent = `ACQUIRING TARGET (${data.streak}/${data.lock_threshold || 3})`;
      statLockState.className = "stat-val status-badge-inline acquiring";
      statLockState.textContent = "ACQUIRING";
    } else {
      lockBanner.className = "lock-banner searching";
      lockBannerText.textContent = "SEARCHING TARGET...";
      statLockState.className = "stat-val status-badge-inline searching";
      statLockState.textContent = "SEARCHING";
    }

    // Streak
    statStreak.textContent = data.streak || 0;

    // Displacements
    const dx = data.dx || 0;
    const dy = data.dy || 0;
    valDx.textContent = `${dx >= 0 ? "+" : ""}${dx} px`;
    valDy.textContent = `${dy >= 0 ? "+" : ""}${dy} px`;

    // Displacements Visual Bars (Center = 50%)
    const pctX = Math.max(0, Math.min(100, (dx / 160) * 50));
    if (dx >= 0) {
      barDx.style.left = "50%";
      barDx.style.width = `${pctX}%`;
    } else {
      barDx.style.left = `${50 - Math.abs(pctX)}%`;
      barDx.style.width = `${Math.abs(pctX)}%`;
    }

    const pctY = Math.max(0, Math.min(100, (dy / 120) * 50));
    if (dy >= 0) {
      barDy.style.left = "50%";
      barDy.style.width = `${pctY}%`;
    } else {
      barDy.style.left = `${50 - Math.abs(pctY)}%`;
      barDy.style.width = `${Math.abs(pctY)}%`;
    }

    // Confidence
    const confPct = Math.round((data.conf || 0) * 100);
    valConf.textContent = `${confPct}%`;
    confProgressBar.style.width = `${confPct}%`;

    // Peripheral FOV Sector
    const pos = data.target_pos || "CENTER";
    sectorBadge.textContent = `SECTOR: ${pos}`;
    fovLeftLabel.style.color = pos === "EXTREME LEFT" ? "var(--cyan-primary)" : "var(--text-dim)";
    fovRightLabel.style.color = pos === "EXTREME RIGHT" ? "var(--cyan-primary)" : "var(--text-dim)";

    // Turret Angles
    valPan.textContent = `${(data.pan || 90).toFixed(1)}°`;
    valTilt.textContent = `${(data.tilt || 90).toFixed(1)}°`;
    turretModeBadge.textContent = data.is_simulated ? "SIMULATED" : "HARDWARE SERIAL";

    // Laser Emitter State
    currentArmed = !!data.laser_armed;
    if (data.laser_firing) {
      btnLaserArm.className = "btn-laser-toggle armed";
      laserBtnText.textContent = "FIRING!";
    } else if (currentArmed) {
      btnLaserArm.className = "btn-laser-toggle armed";
      laserBtnText.textContent = "ARMED (READY)";
    } else {
      btnLaserArm.className = "btn-laser-toggle safe";
      laserBtnText.textContent = "SAFE / DISARMED";
    }

    // EP-CLAHE
    currentEnhance = !!data.enhance;
    pillEnhance.textContent = currentEnhance ? "ON" : "OFF";
    pillEnhance.className = `toggle-pill ${currentEnhance ? "active" : ""}`;
  }

  // WebSocket Connection with Auto-reconnect
  function initWebSocket() {
    const loc = window.location;
    const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//${loc.host}/ws/telemetry`;

    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        updateTelemetry(data);
      } catch (err) {}
    };

    ws.onclose = () => {
      setTimeout(initWebSocket, 2000);
    };

    ws.onerror = () => {
      // Fallback to polling if WebSocket fails
      startPolling();
    };
  }

  // Fallback Polling
  let pollInterval = null;
  function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(() => {
      fetch("/api/telemetry")
        .then((res) => res.json())
        .then(updateTelemetry)
        .catch(() => {});
    }, 100);
  }

  // Snapshot Action
  btnSnapshot.addEventListener("click", () => {
    fetch("/api/snapshot", { method: "POST" })
      .then((res) => res.json())
      .then((res) => {
        if (res.status === "ok") {
          showToast(`Snapshot saved: ${res.filename}`);
        } else {
          showToast(res.message || "Failed to capture snapshot");
        }
      })
      .catch(() => showToast("Error saving snapshot"));
  });

  // EP-CLAHE Toggle
  btnEnhance.addEventListener("click", () => {
    const nextState = !currentEnhance;
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enhance: nextState }),
    }).then(() => {
      currentEnhance = nextState;
      pillEnhance.textContent = currentEnhance ? "ON" : "OFF";
      pillEnhance.className = `toggle-pill ${currentEnhance ? "active" : ""}`;
      showToast(`EP-CLAHE Domain Transform: ${nextState ? "ENABLED" : "DISABLED"}`);
    });
  });

  // Laser Arm Toggle
  btnLaserArm.addEventListener("click", () => {
    const nextArmed = !currentArmed;
    if (nextArmed) {
      if (!confirm("⚠️ CAUTION: Arm laser emitter?\nMake sure laser safety eyewear is worn!")) {
        return;
      }
    }
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ laser_armed: nextArmed }),
    }).then(() => {
      currentArmed = nextArmed;
      showToast(`Laser Emitter: ${nextArmed ? "ARMED" : "SAFE / DISARMED"}`);
    });
  });

  // Confidence Slider
  sliderConf.addEventListener("input", (e) => {
    valSliderConf.textContent = e.target.value;
  });

  sliderConf.addEventListener("change", (e) => {
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conf: parseFloat(e.target.value) }),
    }).then(() => showToast(`Confidence threshold set to ${e.target.value}`));
  });

  // Stream Source Connect
  btnSaveSource.addEventListener("click", () => {
    const url = inputStreamUrl.value.trim();
    if (!url) return;
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: url }),
    }).then(() => {
      showToast("Connecting to new stream source...");
      const img = document.getElementById("video-stream");
      img.src = `/api/stream?t=${Date.now()}`;
    });
  });

  // Auto-Discover ESP32
  btnDiscover.addEventListener("click", () => {
    btnDiscover.textContent = "SCANNING NETWORK...";
    fetch("/api/discover")
      .then((res) => res.json())
      .then((res) => {
        btnDiscover.textContent = "🔍 AUTO-DISCOVER ESP32";
        if (res.status === "found") {
          inputStreamUrl.value = res.url;
          btnSaveSource.click();
          showToast(`ESP32 camera found at ${res.url}`);
        } else {
          showToast("Could not auto-detect camera. Enter IP manually.");
        }
      })
      .catch(() => {
        btnDiscover.textContent = "🔍 AUTO-DISCOVER ESP32";
        showToast("Discovery failed");
      });
  });

  // D-Pad Manual Jog
  function nudgeTurret(dPan, dTilt) {
    fetch("/api/turret/nudge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pan: dPan, tilt: dTilt }),
    });
  }

  dpadUp.addEventListener("click", () => nudgeTurret(0, 5));
  dpadDown.addEventListener("click", () => nudgeTurret(0, -5));
  dpadLeft.addEventListener("click", () => nudgeTurret(-5, 0));
  dpadRight.addEventListener("click", () => nudgeTurret(5, 0));
  dpadCenter.addEventListener("click", () => {
    fetch("/api/turret/center", { method: "POST" });
  });

  // Fullscreen
  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      videoFrameBox.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });

  // Initialize
  initWebSocket();
});
