# SentinelAI — System Assumptions & Engineering Decisions

This document records architectural assumptions, tradeoffs, and design choices made during the development of SentinelAI.

---

## 1. Data Ingestion & Live vs. Replay Modes
- **OpenSky Network Rate Limits:** The anonymous OpenSky API limits requests to ~10s intervals and restricts rate-limits strictly. Ingestion implements automatic fallback to `adsb.lol` when OpenSky returns HTTP 429 or network errors.
- **AISStream Authentication:** Real-time AIS vessel telemetry from `wss://stream.aisstream.io/v0/stream` requires a free API key (`AISSTREAM_API_KEY`). If the key is absent or upstream is down, the ingestion service automatically falls back to deterministic replay from `/data/replay/ships.jsonl` (synthesized across major shipping straits: Dover, Singapore, Rotterdam, Gibraltar, Baltic).
- **Offline / Deterministic Replay:** Every external feed (OpenSky, adsb.lol, AIS, USGS, CCTV) has a recorded 10-minute snapshot in `/data/replay/*.jsonl`. When `INGEST_MODE=replay`, the ingestion workers stream these files with realistic kinematic time intervals, making unit tests, demos, and admissions evaluations 100% reproducible without internet dependencies.

---

## 2. Infrastructure & Broker Decoupling
- **Docker Compose (`make up`):** In a production/containerized environment, Docker Compose provisions:
  - `redpanda`: Single-node Kafka-compatible event streaming broker (port 9092, console 8080).
  - `postgres` (with PostGIS extensions): Persistent relational & spatial store (port 5432).
  - `qdrant`: Vector database for RAG situational awareness (port 6333).
  - `ingest`, `processor`, `cv`, `api`, `frontend` containers.
- **Host / Standalone Compatibility:** In environments where the Docker daemon is restricted or not elevated, all microservices (`ingest`, `processor`, `cv`, `api`, `eval`) implement an automatic transport fallback (e.g., in-memory or socket-based event bus, SQLite database) sharing identical schemas. This guarantees that evaluation scripts (`/eval/eval_*.py`) and test suites (`pytest`) execute with zero friction.

---

## 3. Computer Vision & Privacy
- **Privacy by Design:** Strict adherence to GDPR and EU AI Act principles for situational awareness. No raw camera frames, video streams, or identifiable personal imagery are permanently stored on disk or in the database.
- **Detections-Only Persistence:** The CV pipeline (Ultralytics YOLOv8n) processes incoming frames in memory, extracts object classes (`car`, `truck`, `bus`, `person`, `motorcycle`), bounding box coordinates, and counts, and publishes only metadata to the `detections` topic.
- **CCTV Fallback:** Because public webcams may drop connection or cycle IP addresses, the CV service gracefully falls back to `/data/sample/traffic_sample.mp4` when camera streams are unreachable.

---

## 4. Anomaly Detection & Cyber Threat Scenarios
- **Rule-Based Baselines:** Deterministic checks for immediate critical events:
  - Aircraft squawking emergency transponder codes (7500: Hijack, 7600: Radio failure, 7700: General emergency).
  - Vertical descent rate exceeding 4,000 ft/min.
  - Ship drifting in designated shipping lanes (speed < 0.8 knots in high-density corridors).
  - High-magnitude seismic event ($M \ge 4.5$) within proximity ($< 150\text{ km}$) of tracked assets.
  - Restricted geofence breach.
- **ML Anomaly Detection (Isolation Forest):** Evaluates multi-dimensional kinematic vectors `[speed, acceleration, vertical_rate, heading_rate]` to identify non-linear operational deviations.
- **Cybersecurity ADS-B Spoofing:** To demonstrate resilience for cybersecurity master's programs (e.g. CYBERSURE), a dedicated synthetic injection suite (`scripts/inject.py`) simulates GPS/ADS-B track spoofing: impossible velocities ($> 1200\text{ km/h}$ for civilian turboprops), discontinuous teleportation jumps ($> 50\text{ km}$ in $< 15\text{ s}$), and duplicate ICAO24 transmitters. Consistency rules detect and flag these as `"possible_spoofing"`.

---

## 5. Multimodal RAG & Pluggable LLM
- **Deterministic Offline Explanations:** When `LLM_PROVIDER=none` or when offline, SentinelAI uses a deterministic template synthesizer that queries Qdrant for similar historical events and cross-references nearby weather and earthquakes.
- **Context Grounding:** The prompt strictly enforces that every claim must cite retrieved event IDs (e.g., `[Event #EV-1042]`) and explicitly state `"insufficient context"` when no relevant background is found, preventing hallucinations.
