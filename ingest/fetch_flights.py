"""
SentinelAI Flight Telemetry Ingestion Worker
Supports OpenSky (live), adsb.lol (live fallback), and replay JSONL.
Publishes normalized messages to Redpanda/Kafka topic 'flights'.
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

logger = logging.getLogger("IngestFlights")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

OPENSKY_URL = "https://opensky-network.org/api/states/all?extended=1"
ADSB_LOL_URL = "https://api.adsb.lol/v2/mil"
REPLAY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "replay", "flights.jsonl")

HEADERS = {'User-Agent': 'SentinelAI-Aero/1.0'}

async def fetch_live_flights() -> list:
    """Attempts OpenSky first, falls back to adsb.lol upon rate-limit (429) or error."""
    loop = asyncio.get_running_loop()
    
    def _fetch_url(url, timeout=8):
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))

    # 1. Try OpenSky
    try:
        data = await loop.run_in_executor(None, _fetch_url, OPENSKY_URL, 8)
        states = data.get("states", [])
        now_ts = time.time()
        results = []
        for s in states[:400]:
            if len(s) > 11 and s[5] is not None and s[6] is not None:
                results.append({
                    "source": "opensky",
                    "entity_id": str(s[0]).lower(),
                    "lat": float(s[6]),
                    "lon": float(s[5]),
                    "alt": float(s[7]) if s[7] is not None else 0.0,
                    "speed": float(s[9]) if s[9] is not None else 0.0,
                    "heading": float(s[10]) if s[10] is not None else 0.0,
                    "ts": now_ts,
                    "meta": {
                        "callsign": (s[1] or s[0]).strip(),
                        "origin_country": s[2] or "Unknown",
                        "squawk": str(s[14]) if len(s) > 14 and s[14] else "1200",
                        "vertical_rate": float(s[11]) if s[11] is not None else 0.0
                    }
                })
        logger.info(f"OpenSky live fetch success: {len(results)} flights")
        return results
    except Exception as e:
        logger.warning(f"OpenSky live fetch failed ({e}). Falling back to adsb.lol...")

    # 2. Fallback: adsb.lol
    try:
        data = await loop.run_in_executor(None, _fetch_url, ADSB_LOL_URL, 8)
        ac_list = data.get("ac", [])
        now_ts = time.time()
        results = []
        for ac in ac_list:
            lat = ac.get("lat")
            lon = ac.get("lon")
            hex_id = ac.get("hex")
            if lat is not None and lon is not None and hex_id:
                alt = ac.get("alt_baro") or ac.get("alt_geom") or 0.0
                if isinstance(alt, str):
                    alt = 0.0
                results.append({
                    "source": "adsb.lol",
                    "entity_id": str(hex_id).lower(),
                    "lat": float(lat),
                    "lon": float(lon),
                    "alt": float(alt),
                    "speed": float(ac.get("gs") or 0.0),
                    "heading": float(ac.get("track") or 0.0),
                    "ts": now_ts,
                    "meta": {
                        "callsign": (ac.get("flight") or hex_id).strip(),
                        "origin_country": "adsb.lol",
                        "squawk": str(ac.get("squawk") or "1200"),
                        "vertical_rate": float(ac.get("baro_rate") or 0.0)
                    }
                })
        logger.info(f"adsb.lol fallback fetch success: {len(results)} flights")
        return results
    except Exception as e:
        logger.error(f"Both OpenSky and adsb.lol live fetch failed: {e}")
        return []

async def run_flight_ingestion(mode: str = "replay", interval: float = 5.0):
    await bus.start_producer()
    logger.info(f"Starting Flight Ingestion Worker in mode '{mode}'")

    if mode == "replay":
        if not os.path.exists(REPLAY_PATH):
            raise FileNotFoundError(f"Replay file not found: {REPLAY_PATH}")
        
        while True:
            logger.info(f"Streaming flight replay from {REPLAY_PATH}...")
            with open(REPLAY_PATH, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    # Update timestamp to current epoch for real-time streaming
                    rec["ts"] = time.time()
                    batch.append(rec)
                    if len(batch) >= 50:
                        for item in batch:
                            await bus.publish("flights", item)
                        batch = []
                        await asyncio.sleep(0.05)
                # Flush remainder
                for item in batch:
                    await bus.publish("flights", item)
            await asyncio.sleep(interval)
    else:
        # Live polling mode
        while True:
            records = await fetch_live_flights()
            for rec in records:
                await bus.publish("flights", rec)
            await asyncio.sleep(interval)

if __name__ == "__main__":
    mode = os.getenv("INGEST_MODE", "replay")
    asyncio.run(run_flight_ingestion(mode=mode))
