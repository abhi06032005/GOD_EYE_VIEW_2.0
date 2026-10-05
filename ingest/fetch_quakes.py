"""
SentinelAI USGS Earthquake Telemetry Ingestion Worker
Supports live USGS GeoJSON feed and deterministic replay.
Publishes normalized messages to Redpanda/Kafka topic 'quakes'.
"""
import os
import sys
import json
import time
import asyncio
import logging
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingest.bus import bus

logger = logging.getLogger("IngestQuakes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
REPLAY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "replay", "quakes.jsonl")

HEADERS = {'User-Agent': 'SentinelAI-Seismic/1.0'}

async def fetch_live_quakes() -> list:
    loop = asyncio.get_running_loop()
    def _fetch():
        req = urllib.request.Request(USGS_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))

    try:
        data = await loop.run_in_executor(None, _fetch)
        features = data.get("features", [])
        results = []
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])
            lon, lat, depth = coords[0], coords[1], coords[2] if len(coords) > 2 else 0.0
            qid = feat.get("id", f"usgs_{int(props.get('time', 0))}")
            results.append({
                "source": "usgs",
                "entity_id": qid,
                "lat": float(lat),
                "lon": float(lon),
                "alt": -float(depth * 1000.0),
                "speed": 0.0,
                "heading": 0.0,
                "ts": float(props.get("time", time.time() * 1000)) / 1000.0,
                "meta": {
                    "mag": float(props.get("mag") or 0.0),
                    "place": props.get("place", "Seismic Region"),
                    "depth_km": float(depth),
                    "significance": props.get("sig", 0)
                }
            })
        logger.info(f"[IngestQuakes] Live USGS fetch success: {len(results)} earthquakes")
        return results
    except Exception as e:
        logger.warning(f"[IngestQuakes] Live USGS fetch failed: {e}")
        return []

async def run_quake_ingestion(mode: str = "replay", interval: float = 60.0):
    await bus.start_producer()
    logger.info(f"Starting Earthquake Ingestion Worker in mode '{mode}'")

    if mode == "replay":
        if not os.path.exists(REPLAY_PATH):
            raise FileNotFoundError(f"Quakes replay file not found: {REPLAY_PATH}")
        while True:
            logger.info(f"[IngestQuakes] Streaming earthquake replay from {REPLAY_PATH}...")
            with open(REPLAY_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    await bus.publish("quakes", rec)
            await asyncio.sleep(interval)
    else:
        while True:
            records = await fetch_live_quakes()
            for rec in records:
                await bus.publish("quakes", rec)
            await asyncio.sleep(interval)

if __name__ == "__main__":
    mode = os.getenv("INGEST_MODE", "replay")
    asyncio.run(run_quake_ingestion(mode=mode))
