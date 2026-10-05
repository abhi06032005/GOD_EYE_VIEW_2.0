# SentinelAI — God's Eye View (GEV) Reuse & Adaptation Map

**Upstream Project:** [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) (MIT License, Bilawal Sidhu)  
**Upstream Commit Base:** `e1cc7af`  
**License:** MIT (Attributions preserved in `README.md`, `LICENSE`, and UI credits).

---

## 1. Upstream Data Ingestion Architecture vs. SentinelAI Architecture

### Upstream (God's Eye View) Ingestion Flow
1. **Frontend / Browser:** Direct calls or Vite development server proxy endpoints:
   - `/api/flights`: Proxied by Vite (`server/providers/aircraft/opensky.js`) to OpenSky Network (`/states/all?extended=1`).
   - `/api/military`: Proxied by Vite (`server/providers/aircraft/adsb-lol.js`) to `https://api.adsb.lol/v2/mil`.
   - `/api/vessels`: Proxied by Vite (`server/providers/vessels/ais-live.js`), which connects via WebSocket to `wss://stream.aisstream.io/v0/stream` and keeps an in-memory sliding window cache.
   - USGS Earthquakes: Queried directly by the client browser in `src/layers/earthquakes/source.js` from `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson`.
   - CCTV / Traffic: Proxied by Vite (`server/providers/cctv.js`) from open-data catalogs (Caltrans, TxDOT, TfL, etc.).
2. **Coupling:** High coupling between the frontend Vite dev server and external API rate limits. Lack of persistent historical storage, real-time message brokering, centralized anomaly detection, or multimodal RAG situational analysis.

### SentinelAI Architecture & Differential Swap
1. **Decoupled Stream-First Pipeline:**
   - **Ingestion (`/ingest`):** Reuses the battle-tested upstream parser algorithms and header logic. Pulls from live providers (OpenSky, adsb.lol, AISStream, USGS) or deterministic replay files (`/data/replay/*.jsonl`). Normalizes data into a unified multimodal schema:
     `{source, entity_id, lat, lon, alt, speed, heading, ts, meta}`
     and publishes directly to **Redpanda (Kafka API)** topics: `flights`, `ships`, `quakes`, `traffic`, `detections`, `events`.
   - **Stream Processor (`/processor`):** Consumes Redpanda topics in real-time, writes normalized records to **PostgreSQL + PostGIS**, executes rule-based and ML-based (Isolation Forest) anomaly detection, and publishes alerts to `events`.
   - **Computer Vision Service (`/cv`):** Runs Ultralytics YOLOv8 on traffic camera streams/frames, detects vehicles/pedestrians/hazards, and streams bounding boxes and counts to `detections`.
   - **RAG & Situational Explanation (`/rag`):** Embeds events into **Qdrant** with `all-MiniLM-L6-v2`. Provides contextual explanations with citations via FastAPI `/api/explain`.
   - **API Gateway (`/api`):** FastAPI providing REST `/api/entities`, `/api/events`, `/api/metrics`, and real-time streaming WebSocket `/ws/live`.
2. **Frontend Adapter (`/frontend`):**
   - Retains 100% of CesiumJS globe visual rendering, 3D glTF aircraft models, sprite rendering, trail animations, and layer toggles.
   - Replaces polling of disconnected endpoints with a unified SentinelAI adapter connecting to `/ws/live`.
   - Adds three UI enhancements:
     1. **Alerts & Anomalies Panel:** Displays real-time anomalies with severity, trigger rule, and "Fly to" camera target.
     2. **Multimodal CV Panel:** Live traffic camera feed preview with YOLO bounding boxes and object counts.
     3. **Mode & Metrics Footer:** Replay / Live toggle, messages/sec, end-to-end latency, and system health.

---

## 2. Granular Module Reuse Matrix

| Upstream File | Original Purpose | SentinelAI Usage & Modifications |
| :--- | :--- | :--- |
| `server/providers/aircraft/opensky.js` | OpenSky token auth, rate limiting, and states fetching | Logic ported/reused in `ingest/fetch_flights.py` for live OpenSky ingestion and replay normalization. |
| `server/providers/aircraft/adsb-lol.js` | adsb.lol military API proxy with cache | Logic ported/reused in `ingest/fetch_flights.py` for adsb.lol fallback and military flight ingest. |
| `server/providers/vessels/ais-live.js` | AISStream WebSocket consumer and vessel ring-buffer | Reused in `ingest/fetch_ships.py` with normalization to SentinelAI message schema. |
| `src/layers/earthquakes/source.js` & `records.js` | USGS GeoJSON fetching and depth parsing | Reused in `ingest/fetch_quakes.py` to ingest seismic events into Kafka & Postgres. |
| `server/providers/cctv/catalog.js` | Registry of open-data traffic cameras | Reused in `cv/service.py` to target live traffic cameras with fallback to `/data/sample/traffic_sample.mp4`. |
| `src/layers/flights/index.js` & `app/layers/flights.js` | CesiumJS flight layer, 3D glTF models, trails | Preserved intact. Fed via `src/data/sentinel_adapter.js`. |
| `src/layers/earthquakes/index.js` | CesiumJS earthquake disc visualization | Preserved intact. Visualizes seismic events from backend. |
| `src/ui.js` & `index.html` | Cesium globe viewport and control buttons | Enhanced with SentinelAI Alerts Drawer, CV Inspector, and Live/Replay switch. |
| `DATA_SOURCES.md` & `LICENSE` | Attribution for OpenSky, OSM, adsb.lol, USGS | Retained and expanded with SentinelAI architecture and data source licenses. |

---

## 3. Normalized Multimodal Schema

All external feeds are normalized before emitting onto Redpanda/Kafka topics:

```json
{
  "source": "opensky" | "adsb.lol" | "aisstream" | "usgs" | "cctv",
  "entity_id": "string (icao24, mmsi, usgs_id, camera_id)",
  "lat": 37.7749,
  "lon": -122.4194,
  "alt": 10500.0,
  "speed": 240.5,
  "heading": 182.0,
  "ts": 1728130800.123,
  "meta": {
    "callsign": "UAL123",
    "squawk": "7700",
    "vertical_rate": -3500.0,
    "ship_type": "Tanker",
    "mag": 5.4,
    "detections": {"car": 12, "truck": 3, "person": 2}
  }
}
```
