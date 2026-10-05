"""
SentinelAI Unified REST & Streaming WebSocket API Gateway
Provides endpoints for entities, real-time events, RAG situational explanations,
live system telemetry, and a high-performance WebSocket stream for CesiumJS.
"""
import os
import sys
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from processor.db import db
from processor.bus import bus, _internal_bus

logger = logging.getLogger("SentinelAPI")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="SentinelAI Platform API",
    description="Real-time Multimodal Situational-Awareness & Threat Detection Gateway",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory sliding window for measured metrics
class MetricsTracker:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.lags_ms: List[float] = []
        self.msg_timestamps: List[float] = []
        self.total_msgs = 0
        self.total_anomalies = 0
        self.lock = asyncio.Lock()

    async def record_message(self, ts_origin: float, is_anomaly: bool = False):
        async with self.lock:
            now = time.time()
            self.total_msgs += 1
            if is_anomaly:
                self.total_anomalies += 1
            self.msg_timestamps.append(now)
            if ts_origin > 0:
                lag_ms = max(0.0, (now - ts_origin) * 1000.0)
                self.lags_ms.append(lag_ms)

            # Trim sliding window
            if len(self.lags_ms) > self.window_size:
                self.lags_ms = self.lags_ms[-self.window_size:]
            if len(self.msg_timestamps) > self.window_size:
                self.msg_timestamps = self.msg_timestamps[-self.window_size:]

    async def get_metrics(self) -> Dict[str, Any]:
        async with self.lock:
            now = time.time()
            # Calculate throughput in the last 10 seconds
            recent_msgs = [t for t in self.msg_timestamps if now - t <= 10.0]
            msgs_per_sec = len(recent_msgs) / 10.0 if recent_msgs else 0.0

            lags = sorted(self.lags_ms) if self.lags_ms else [0.0]
            p50 = lags[int(len(lags) * 0.50)]
            p95 = lags[min(int(len(lags) * 0.95), len(lags) - 1)]
            p99 = lags[min(int(len(lags) * 0.99), len(lags) - 1)]

            return {
                "msgs_per_sec": round(msgs_per_sec, 2),
                "e2e_lag_p50_ms": round(p50, 2),
                "e2e_lag_p95_ms": round(p95, 2),
                "e2e_lag_p99_ms": round(p99, 2),
                "total_messages": self.total_msgs,
                "total_anomalies": self.total_anomalies,
                "measured_samples": len(self.lags_ms),
                "timestamp": now
            }

metrics_tracker = MetricsTracker()

# Connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

manager = ConnectionManager()

# Background listener feeding WebSocket from Event Bus
async def event_bus_listener():
    async def _handle(topic: str, msg: Dict[str, Any]):
        is_event = (topic == "events")
        ts_origin = float(msg.get("ts", time.time()))
        await metrics_tracker.record_message(ts_origin, is_anomaly=is_event)
        
        # Stream out to all connected WebSocket globe clients
        payload = {
            "topic": topic,
            "type": "event" if is_event else "telemetry",
            "data": msg
        }
        await manager.broadcast(payload)

    await bus.subscribe(["flights", "ships", "quakes", "detections", "events"], _handle)

@app.on_event("startup")
async def startup_event():
    await db.initialize()
    await bus.start_producer()
    asyncio.create_task(event_bus_listener())
    logger.info("[SentinelAPI] Gateway initialized and event bus listener started.")

@app.get("/api/health")
async def health_check():
    stats = await db.get_stats()
    return {"status": "healthy", "service": "sentinel-api", "db_stats": stats}

@app.get("/api/metrics")
async def get_metrics():
    """Returns measured live throughput and p50/p95 latency metrics."""
    return await metrics_tracker.get_metrics()

@app.get("/api/entities")
async def get_entities(entity_type: Optional[str] = Query(None, description="flights, ships, or quakes")):
    """Returns the most recent tracked entities from the persistent store."""
    if entity_type == "flights":
        return {"flights": await db.get_latest_entities("flights", 300)}
    elif entity_type == "ships":
        return {"ships": await db.get_latest_entities("ships", 150)}
    elif entity_type == "quakes":
        return {"quakes": await db.get_latest_entities("quakes", 100)}
    else:
        flights = await db.get_latest_entities("flights", 200)
        ships = await db.get_latest_entities("ships", 100)
        quakes = await db.get_latest_entities("quakes", 50)
        return {"flights": flights, "ships": ships, "quakes": quakes}

@app.get("/api/events")
async def get_events(limit: int = 50, severity: Optional[str] = None):
    """Returns latest situational events and detected anomalies."""
    events = await db.get_recent_events(limit=limit, min_severity=severity)
    return {"events": events, "count": len(events)}

@app.get("/api/flights")
async def get_gods_eye_flights():
    """
    Drop-in compatibility route for upstream God's Eye View flight format.
    Allows God's Eye frontend to point directly to SentinelAI.
    """
    records = await db.get_latest_entities("flights", 350)
    states = []
    now_ts = int(time.time())
    for r in records:
        meta = r.get("meta", {})
        states.append([
            r["entity_id"],
            meta.get("callsign", r["entity_id"]),
            meta.get("origin_country", "Unknown"),
            int(r["ts"]),
            now_ts,
            r["lon"],
            r["lat"],
            r.get("alt", 0.0),
            False, # on_ground
            r.get("speed", 0.0),
            r.get("heading", 0.0),
            meta.get("vertical_rate", 0.0),
            None,
            r.get("alt", 0.0),
            meta.get("squawk", "1200"),
            False,
            0
        ])
    return {"time": now_ts, "states": states}

@app.get("/api/vessels")
async def get_gods_eye_vessels():
    """Drop-in compatibility route for God's Eye View vessel format."""
    records = await db.get_latest_entities("ships", 150)
    vessels = []
    for r in records:
        meta = r.get("meta", {})
        vessels.append({
            "mmsi": r["entity_id"],
            "name": meta.get("shipname", r["entity_id"]),
            "type": meta.get("ship_type", "Cargo"),
            "lat": r["lat"],
            "lon": r["lon"],
            "heading": r.get("heading", 0.0),
            "speed": r.get("speed", 0.0),
            "destination": meta.get("destination", "Open Sea"),
            "status": meta.get("status", "Under way")
        })
    return {"vessels": vessels, "count": len(vessels)}

class ExplainRequest(BaseModel):
    event_id: Optional[str] = None
    question: Optional[str] = None

@app.post("/api/explain")
async def explain_event(req: ExplainRequest):
    """
    Multimodal RAG situational analysis endpoint.
    Retrieves semantic context and generates cited explanations.
    """
    from rag.service import rag_service
    explanation = await rag_service.explain(event_id=req.event_id, query=req.question)
    return explanation

@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """Real-time bi-directional streaming endpoint for CesiumJS frontend."""
    await manager.connect(websocket)
    # Send initial state snapshot upon connection
    try:
        initial_flights = await db.get_latest_entities("flights", 100)
        initial_events = await db.get_recent_events(limit=20)
        metrics = await metrics_tracker.get_metrics()
        
        await websocket.send_text(json.dumps({
            "topic": "bootstrap",
            "type": "snapshot",
            "data": {
                "flights": initial_flights,
                "events": initial_events,
                "metrics": metrics
            }
        }))
        
        while True:
            # Keep socket alive and handle incoming client commands (e.g. filter/toggle)
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                if cmd.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "ts": time.time()}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
