"""
SentinelAI Maritime AIS Telemetry Ingestion Worker
Supports live AISStream.io WebSocket (if key configured) and deterministic replay.
Publishes normalized messages to Redpanda/Kafka topic 'ships'.
"""
import os
import sys
import json
import time
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingest.bus import bus

logger = logging.getLogger("IngestShips")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"
AISSTREAM_KEY = os.getenv("AISSTREAM_API_KEY", "")
REPLAY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "replay", "ships.jsonl")

async def run_live_ais():
    import websockets
    if not AISSTREAM_KEY:
        logger.warning("[IngestShips] AISSTREAM_API_KEY not configured. Falling back to replay stream.")
        await run_replay_ships()
        return

    subscribe_msg = {
        "APIKey": AISSTREAM_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]],
        "FilterMessageTypes": ["PositionReport", "StandardClassBPositionReport"]
    }

    while True:
        try:
            logger.info(f"[IngestShips] Connecting to AISStream.io live WebSocket...")
            async with websockets.connect(AISSTREAM_URL, timeout=10) as ws:
                await ws.send(json.dumps(subscribe_msg))
                async for raw in ws:
                    envelope = json.loads(raw)
                    msg_type = envelope.get("MessageType")
                    meta_data = envelope.get("MetaData", {})
                    msg = envelope.get("Message", {}).get(msg_type, {})
                    
                    mmsi = str(meta_data.get("MMSI", ""))
                    lat = meta_data.get("latitude")
                    lon = meta_data.get("longitude")
                    
                    if mmsi and lat is not None and lon is not None:
                        normalized = {
                            "source": "aisstream",
                            "entity_id": mmsi,
                            "lat": float(lat),
                            "lon": float(lon),
                            "alt": 0.0,
                            "speed": float(msg.get("Sog", 0.0)),
                            "heading": float(msg.get("Cog", 0.0)),
                            "ts": time.time(),
                            "meta": {
                                "shipname": meta_data.get("ShipName", mmsi).strip(),
                                "ship_type": "Vessel",
                                "time_utc": meta_data.get("time_utc")
                            }
                        }
                        await bus.publish("ships", normalized)
        except Exception as e:
            logger.warning(f"[IngestShips] Live AISStream connection interrupted: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

async def run_replay_ships(interval: float = 5.0):
    if not os.path.exists(REPLAY_PATH):
        raise FileNotFoundError(f"Vessel replay file not found: {REPLAY_PATH}")

    logger.info(f"[IngestShips] Streaming maritime vessel replay from {REPLAY_PATH}...")
    while True:
        with open(REPLAY_PATH, "r", encoding="utf-8") as f:
            batch = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rec["ts"] = time.time()
                batch.append(rec)
                if len(batch) >= 40:
                    for item in batch:
                        await bus.publish("ships", item)
                    batch = []
                    await asyncio.sleep(0.05)
            for item in batch:
                await bus.publish("ships", item)
        await asyncio.sleep(interval)

async def run_ship_ingestion(mode: str = "replay"):
    await bus.start_producer()
    logger.info(f"Starting Ship Ingestion Worker in mode '{mode}'")
    if mode == "live" and AISSTREAM_KEY:
        await run_live_ais()
    else:
        await run_replay_ships()

if __name__ == "__main__":
    mode = os.getenv("INGEST_MODE", "replay")
    asyncio.run(run_ship_ingestion(mode=mode))
