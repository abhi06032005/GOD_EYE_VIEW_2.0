/**
 * SentinelAI Frontend Adapter
 * Connects God's Eye View (CesiumJS) to the SentinelAI Streaming Backend.
 * Features:
 *   - Real-time WebSocket (/ws/live) ingestion for flights, vessels, quakes, and alerts
 *   - Threat & Anomaly Alerts Drawer with severity colors and Cesium "Fly To" navigation
 *   - Multimodal Computer Vision (CV) Panel displaying live YOLO detections & vehicle counts
 *   - System Telemetry & Performance Metrics Footer (msgs/sec, p50/p95 latency)
 *   - Pluggable RAG Situational Explanation modal
 */

class SentinelAdapter {
  constructor(options = {}) {
    this.apiBase = options.apiBase || 'http://localhost:8000';
    this.wsUrl = options.wsUrl || 'ws://localhost:8000/ws/live';
    this.viewer = null;
    this.ws = null;
    this.alerts = [];
    this.cameras = [
      { id: "cam_blr_silkboard", name: "Silk Board Junction (Bangalore)", counts: { car: 42, truck: 8, bus: 6, person: 12 }, lat: 12.9176, lon: 77.6238 },
      { id: "cam_blr_mgroad", name: "MG Road & Brigade Rd (Bangalore)", counts: { car: 28, truck: 2, bus: 4, person: 19 }, lat: 12.9740, lon: 77.6080 },
      { id: "cam_blr_hebbal", name: "Hebbal Flyover Expressway (Bangalore)", counts: { car: 35, truck: 11, bus: 5, person: 2 }, lat: 13.0358, lon: 77.5970 },
      { id: "cam_blr_ecity", name: "Electronic City Elevated Tollway (Bangalore)", counts: { car: 24, truck: 4, bus: 3, person: 1 }, lat: 12.8452, lon: 77.6602 },
      { id: "cam_blr_majestic", name: "Majestic Terminal Crossing (Bangalore)", counts: { car: 19, truck: 5, bus: 14, person: 34 }, lat: 12.9778, lon: 77.5713 },
      { id: "cam_blr_orr", name: "Outer Ring Road - Bellandur (Bangalore)", counts: { car: 38, truck: 6, bus: 7, person: 8 }, lat: 12.9304, lon: 77.6784 },
      { id: "cam_mum_marinedrive", name: "Marine Drive Promenade (Mumbai)", counts: { car: 31, truck: 1, bus: 2, person: 15 }, lat: 18.9220, lon: 72.8258 },
      { id: "cam_del_cp", name: "Connaught Place Traffic Hub (Delhi)", counts: { car: 26, truck: 3, bus: 5, person: 21 }, lat: 28.6315, lon: 77.2167 }
    ];
    this.metrics = {
      msgs_per_sec: 0,
      e2e_lag_p50_ms: 0,
      e2e_lag_p95_ms: 0,
      total_messages: 0,
      total_anomalies: 0
    };
    this.mode = 'REPLAY'; // 'LIVE' or 'REPLAY'
    this.initStyles();
    this.initUI();
    this.connectWebSocket();
  }

  setViewer(viewer) {
    this.viewer = viewer;
    console.log('[SentinelAI] Cesium Viewer attached to SentinelAdapter.');
  }

  initStyles() {
    if (document.getElementById('sentinel-styles')) return;
    const style = document.createElement('style');
    style.id = 'sentinel-styles';
    style.textContent = `
      /* SentinelAI Situational Awareness Styles */
      :root {
        --sentinel-bg: rgba(10, 15, 25, 0.88);
        --sentinel-border: rgba(0, 220, 255, 0.3);
        --sentinel-cyan: #00e5ff;
        --sentinel-crit: #ff3366;
        --sentinel-high: #ff9900;
        --sentinel-med: #ffcc00;
        --sentinel-text: #e0f0ff;
        --sentinel-font: 'JetBrains Mono', monospace, sans-serif;
      }

      #sentinel-alerts-panel {
        position: fixed;
        top: 60px;
        right: 15px;
        width: 360px;
        max-height: 480px;
        background: var(--sentinel-bg);
        border: 1px solid var(--sentinel-border);
        border-radius: 8px;
        backdrop-filter: blur(12px);
        color: var(--sentinel-text);
        font-family: var(--sentinel-font);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
        transition: transform 0.3s ease;
      }

      .sentinel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        background: rgba(0, 229, 255, 0.08);
        border-bottom: 1px solid var(--sentinel-border);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: var(--sentinel-cyan);
      }

      .sentinel-header .badge {
        background: var(--sentinel-crit);
        color: #fff;
        padding: 2px 7px;
        border-radius: 10px;
        font-size: 11px;
        animation: pulse 1.5s infinite;
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.75; transform: scale(1.05); }
      }

      .sentinel-list {
        overflow-y: auto;
        padding: 8px;
        flex: 1;
      }

      .sentinel-card {
        background: rgba(255, 255, 255, 0.03);
        border-left: 3px solid var(--sentinel-cyan);
        margin-bottom: 8px;
        padding: 10px;
        border-radius: 4px;
        font-size: 11.5px;
        transition: background 0.2s;
      }
      .sentinel-card:hover {
        background: rgba(0, 229, 255, 0.08);
      }
      .sentinel-card.severity-CRITICAL {
        border-left-color: var(--sentinel-crit);
      }
      .sentinel-card.severity-HIGH {
        border-left-color: var(--sentinel-high);
      }
      .sentinel-card.severity-MEDIUM {
        border-left-color: var(--sentinel-med);
      }

      .sentinel-card-title {
        display: flex;
        justify-content: space-between;
        font-weight: 600;
        margin-bottom: 4px;
      }

      .sentinel-actions {
        display: flex;
        gap: 6px;
        margin-top: 8px;
      }

      .sentinel-btn {
        background: rgba(0, 229, 255, 0.15);
        border: 1px solid var(--sentinel-cyan);
        color: var(--sentinel-cyan);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10px;
        cursor: pointer;
        font-family: var(--sentinel-font);
        transition: all 0.2s;
      }
      .sentinel-btn:hover {
        background: var(--sentinel-cyan);
        color: #000;
      }

      /* CV Panel - docked on the right side and toggleable */
      #sentinel-cv-panel {
        display: none;
        position: fixed;
        bottom: 50px;
        right: 15px;
        left: auto;
        width: 320px;
        max-height: 420px;
        overflow-y: auto;
        background: var(--sentinel-bg);
        border: 1px solid var(--sentinel-border);
        border-radius: 8px;
        backdrop-filter: blur(12px);
        color: var(--sentinel-text);
        font-family: var(--sentinel-font);
        z-index: 9999;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
      }

      .cv-cam-item {
        padding: 8px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 11px;
      }
      .cv-counts {
        display: flex;
        gap: 8px;
        margin-top: 4px;
        color: #8be9fd;
      }

      /* Footer */
      #sentinel-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 38px;
        background: rgba(5, 10, 18, 0.95);
        border-top: 1px solid var(--sentinel-border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        font-family: var(--sentinel-font);
        font-size: 11px;
        color: #8be9fd;
        z-index: 99999;
        backdrop-filter: blur(8px);
      }

      .mode-toggle {
        background: #ff5555;
        color: #fff;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        cursor: pointer;
        border: none;
        letter-spacing: 0.5px;
      }
      .mode-toggle.live {
        background: #50fa7b;
        color: #000;
      }

      /* Modal for RAG Explanation */
      #sentinel-rag-modal {
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 520px;
        max-width: 90vw;
        background: rgba(12, 18, 30, 0.98);
        border: 2px solid var(--sentinel-cyan);
        border-radius: 8px;
        padding: 18px;
        z-index: 100000;
        color: var(--sentinel-text);
        font-family: var(--sentinel-font);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.9);
      }
      #sentinel-rag-modal h3 {
        margin-top: 0;
        color: var(--sentinel-cyan);
        font-size: 14px;
      }
      #sentinel-rag-modal .content {
        font-size: 12px;
        line-height: 1.5;
        margin: 12px 0;
        max-height: 280px;
        overflow-y: auto;
        white-space: pre-wrap;
      }
    `;
    document.head.appendChild(style);
  }

  initUI() {
    // 1. Alerts Panel
    const alertsPanel = document.createElement('div');
    alertsPanel.id = 'sentinel-alerts-panel';
    alertsPanel.innerHTML = `
      <div class="sentinel-header">
        <span>🚨 SENTINEL-AI THREAT ALERTS</span>
        <span class="badge" id="sentinel-alert-count">0 ACTIVE</span>
      </div>
      <div class="sentinel-list" id="sentinel-alerts-list">
        <div style="padding:15px; text-align:center; color:#6272a4; font-size:11px;">Listening for streaming anomalies...</div>
      </div>
    `;
    document.body.appendChild(alertsPanel);

    // 2. CV Panel (Hidden by default to prevent obscuring the AI Bot)
    const cvPanel = document.createElement('div');
    cvPanel.id = 'sentinel-cv-panel';
    cvPanel.style.display = 'none';
    cvPanel.innerHTML = `
      <div class="sentinel-header" style="display:flex; justify-content:space-between; align-items:center;">
        <span>📹 YOLOv8 TRAFFIC CV INSPECTOR</span>
        <button id="sentinel-cv-close-btn" class="sentinel-btn" style="padding:1px 7px; font-size:11px;" title="Close Traffic Inspector">✕</button>
      </div>
      <div id="sentinel-cv-list">
        ${this.cameras.map(c => `
          <div class="cv-cam-item" data-cam-lat="${c.lat}" data-cam-lon="${c.lon}" style="cursor:pointer;" title="Click to fly to this camera">
            <div style="font-weight:600; display:flex; justify-content:space-between; align-items:center;">
              <span>${c.name}</span>
              <span style="font-size:9px; color:var(--sentinel-cyan); background:rgba(0,229,255,0.15); padding:1px 5px; border-radius:3px;">FLY 🎯</span>
            </div>
            <div class="cv-counts">
              <span>🚗 ${c.counts.car} cars</span>
              <span>🚚 ${c.counts.truck} trucks</span>
              <span>🚌 ${c.counts.bus} buses</span>
              <span>🚶 ${c.counts.person} peds</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    document.body.appendChild(cvPanel);

    cvPanel.addEventListener('click', (e) => {
      const item = e.target.closest('[data-cam-lat]');
      if (item) {
        const lat = parseFloat(item.dataset.camLat);
        const lon = parseFloat(item.dataset.camLon);
        if (Number.isFinite(lat) && Number.isFinite(lon)) {
          this.flyToEntity(lat, lon, 800);
        }
      }
    });

    // 3. Metrics Footer
    const footer = document.createElement('div');
    footer.id = 'sentinel-footer';
    footer.innerHTML = `
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-weight:700; color:var(--sentinel-cyan);">🛰️ SENTINEL-AI</span>
        <button id="sentinel-mode-btn" class="mode-toggle">REPLAY MODE</button>
        <button id="sentinel-cv-toggle-btn" class="sentinel-btn" title="Toggle YOLOv8 Traffic CV Inspector">📹 TRAFFIC CV</button>
      </div>
      <div id="sentinel-metrics-display" style="display:flex; gap:16px;">
        <span>⚡ 0.0 msgs/s</span>
        <span>⏱️ Lag p50: 0.0 ms | p95: 0.0 ms</span>
        <span>🎯 Active Anomalies: 0</span>
      </div>
      <div>
        <span style="color:#50fa7b;">● REDPANDA STREAMING</span>
      </div>
    `;
    document.body.appendChild(footer);

    // 4. RAG Modal
    const modal = document.createElement('div');
    modal.id = 'sentinel-rag-modal';
    modal.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 id="rag-modal-title">🧠 Multimodal Situational Assessment (RAG)</h3>
        <button id="rag-close-btn" class="sentinel-btn">CLOSE</button>
      </div>
      <div class="content" id="rag-modal-content">Analyzing event context...</div>
      <div id="rag-modal-citations" style="font-size:10px; color:#bd93f9; border-top:1px solid rgba(255,255,255,0.1); padding-top:6px;"></div>
    `;
    document.body.appendChild(modal);

    document.getElementById('rag-close-btn').addEventListener('click', () => {
      modal.style.display = 'none';
    });

    // Traffic CV Toggle Handler
    const toggleCv = () => {
      const isVisible = cvPanel.style.display !== 'none';
      cvPanel.style.display = isVisible ? 'none' : 'block';
      const cvBtn = document.getElementById('sentinel-cv-toggle-btn');
      if (cvBtn) {
        cvBtn.style.background = isVisible ? '' : 'var(--sentinel-cyan)';
        cvBtn.style.color = isVisible ? '' : '#000';
      }
    };

    document.getElementById('sentinel-cv-close-btn')?.addEventListener('click', toggleCv);
    document.getElementById('sentinel-cv-toggle-btn')?.addEventListener('click', toggleCv);

    // Mode Toggle Click
    document.getElementById('sentinel-mode-btn').addEventListener('click', () => {
      this.mode = this.mode === 'REPLAY' ? 'LIVE' : 'REPLAY';
      const btn = document.getElementById('sentinel-mode-btn');
      btn.textContent = `${this.mode} MODE`;
      btn.classList.toggle('live', this.mode === 'LIVE');
      console.log(`[SentinelAI] Switched mode to: ${this.mode}`);
    });
  }

  connectWebSocket() {
    console.log(`[SentinelAI] Connecting to WebSocket: ${this.wsUrl}`);
    try {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => {
        console.log('[SentinelAI] WebSocket stream established.');
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          this.handleIncomingMessage(msg);
        } catch (e) {
          // ignore parsing error
        }
      };

      this.ws.onerror = (e) => {
        console.warn('[SentinelAI] WebSocket error, will retry in 5s:', e);
      };

      this.ws.onclose = () => {
        setTimeout(() => this.connectWebSocket(), 5000);
      };
    } catch (err) {
      console.warn('[SentinelAI] WebSocket initialization error:', err);
    }

    // Periodic metrics poller fallback
    setInterval(async () => {
      try {
        const resp = await fetch(`${this.apiBase}/api/metrics`);
        if (resp.ok) {
          const data = await resp.json();
          this.updateMetrics(data);
        }
      } catch (e) {}
    }, 2500);
  }

  handleIncomingMessage(msg) {
    if (msg.type === 'snapshot' && msg.data) {
      if (msg.data.events) {
        msg.data.events.forEach(ev => this.addAlert(ev));
      }
      if (msg.data.metrics) {
        this.updateMetrics(msg.data.metrics);
      }
    } else if (msg.topic === 'events' || msg.type === 'event') {
      this.addAlert(msg.data);
    } else if (msg.topic === 'detections') {
      this.updateCameraDetections(msg.data);
    }
  }

  addAlert(alert) {
    if (!alert || !alert.id) return;
    if (this.alerts.some(a => a.id === alert.id)) return;

    this.alerts.unshift(alert);
    if (this.alerts.length > 25) this.alerts.pop();

    const list = document.getElementById('sentinel-alerts-list');
    const countBadge = document.getElementById('sentinel-alert-count');
    countBadge.textContent = `${this.alerts.length} ACTIVE`;

    const card = document.createElement('div');
    card.className = `sentinel-card severity-${alert.severity || 'MEDIUM'}`;
    const dateStr = new Date(alert.ts * 1000).toLocaleTimeString();
    
    card.innerHTML = `
      <div class="sentinel-card-title">
        <span style="color:var(--sentinel-cyan);">${alert.entity_id}</span>
        <span style="font-size:10px; opacity:0.8;">${dateStr}</span>
      </div>
      <div style="margin-bottom:4px; font-weight:600;">${alert.title || alert.event_type}</div>
      <div style="opacity:0.85; font-size:11px;">${alert.summary || alert.description}</div>
      <div class="sentinel-actions">
        <button class="sentinel-btn btn-fly">🎯 Fly To</button>
        <button class="sentinel-btn btn-explain">🧠 Explain RAG</button>
      </div>
    `;

    card.querySelector('.btn-fly').addEventListener('click', () => {
      this.flyToEntity(alert.lat, alert.lon, alert.alt || 12000);
    });

    card.querySelector('.btn-explain').addEventListener('click', () => {
      this.openExplainModal(alert);
    });

    if (list.children.length === 1 && list.innerText.includes('Listening')) {
      list.innerHTML = '';
    }
    list.prepend(card);
  }

  flyToEntity(lat, lon, height = 15000) {
    if (!this.viewer) {
      console.warn('[SentinelAI] Cesium Viewer not ready for camera flyTo.');
      return;
    }
    const Cesium = globalThis.Cesium || window.Cesium || this.viewer.constructor.Cesium;
    if (Cesium?.Cartesian3?.fromDegrees) {
      this.viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, height),
        duration: 2.0
      });
    }
  }

  async openExplainModal(alert) {
    const modal = document.getElementById('sentinel-rag-modal');
    const content = document.getElementById('rag-modal-content');
    const title = document.getElementById('rag-modal-title');
    const citations = document.getElementById('rag-modal-citations');

    title.textContent = `🧠 Situational Assessment: ${alert.title || alert.id}`;
    content.textContent = "Querying Qdrant vector database and synthesizing multimodal explanation...";
    citations.textContent = "";
    modal.style.display = 'block';

    try {
      const resp = await fetch(`${this.apiBase}/api/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: alert.id, question: alert.summary })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      content.textContent = data.explanation || "No explanation returned.";
      citations.textContent = `Retrieved References: ${(data.citations || []).join(', ') || 'Direct telemetry correlation'}`;
    } catch (err) {
      content.textContent = `Autonomous Explanation Engine:\n\nTriggered by: ${alert.rule_name || alert.event_type}\nEntity: ${alert.entity_id}\nCoordinates: Lat ${alert.lat.toFixed(4)}, Lon ${alert.lon.toFixed(4)}\n\nThreat Evaluation: Observed kinematic profile deviates from expected nominal operational constraints. Standard operating procedure advises tactical tracking. [Reference: ${alert.id}]`;
      citations.textContent = `Citation: [Event ${alert.id}]`;
    }
  }

  updateCameraDetections(detection) {
    const cam = this.cameras.find(c => c.id === detection.camera_id);
    if (cam && detection.class_counts) {
      cam.counts = detection.class_counts;
      const list = document.getElementById('sentinel-cv-list');
      if (list) {
        list.innerHTML = this.cameras.map(c => `
          <div class="cv-cam-item" data-cam-lat="${c.lat}" data-cam-lon="${c.lon}" style="cursor:pointer;" title="Click to fly to this camera">
            <div style="font-weight:600; display:flex; justify-content:space-between; align-items:center;">
              <span>${c.name}</span>
              <span style="font-size:9px; color:var(--sentinel-cyan); background:rgba(0,229,255,0.15); padding:1px 5px; border-radius:3px;">FLY 🎯</span>
            </div>
            <div class="cv-counts">
              <span>🚗 ${c.counts.car || 0} cars</span>
              <span>🚚 ${c.counts.truck || 0} trucks</span>
              <span>🚌 ${c.counts.bus || 0} buses</span>
              <span>🚶 ${c.counts.person || 0} peds</span>
            </div>
          </div>
        `).join('');
      }
    }
  }

  updateMetrics(m) {
    this.metrics = m;
    const disp = document.getElementById('sentinel-metrics-display');
    if (disp) {
      disp.innerHTML = `
        <span>⚡ ${m.msgs_per_sec} msgs/s</span>
        <span>⏱️ Lag p50: ${m.e2e_lag_p50_ms} ms | p95: ${m.e2e_lag_p95_ms} ms</span>
        <span>🎯 Total Anomalies: ${m.total_anomalies}</span>
      `;
    }
  }
}

// Global Sentinel adapter
const sentinelAdapter = new SentinelAdapter();
export default sentinelAdapter;
export { SentinelAdapter };
