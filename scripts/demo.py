#!/usr/bin/env python3
"""
SentinelAI Live Demonstration Runner (make demo)
Starts the SentinelAI streaming situational-awareness platform in deterministic replay mode,
spawns the FastAPI REST & WebSocket server, boots background stream processors, and injects
scripted multi-modal anomalies within seconds to showcase live alerts on the CesiumJS globe.
"""
import os
import sys
import time
import json
import asyncio
import logging
import uvicorn
from threading import Thread

# Ensure root directory is on PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from processor.db import db
from processor.bus import bus
from processor.main import StreamProcessor
from api.main import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SentinelDemo")

REPLAY_DIR = os.path.join(BASE_DIR, "data", "replay")
FLIGHTS_REPLAY = os.path.join(REPLAY_DIR, "flights.jsonl")
SHIPS_REPLAY = os.path.join(REPLAY_DIR, "ships.jsonl")
QUAKES_REPLAY = os.path.join(REPLAY_DIR, "quakes.jsonl")

BANNER = r"""
=================================================================================
  ____             _   _            _      _    ___ 
 / ___|  ___ _ __ | |_(_)_ __   ___| |    / \  |_ _|
 \___ \ / _ \ '_ \| __| | '_ \ / _ \ |   / _ \  | | 
  ___) |  __/ | | | |_| | | | |  __/ |  / ___ \ | | 
 |____/ \___|_| |_|\__|_|_| |_|\___|_| /_/   \_\___|
 Real-Time Multimodal Situational Awareness & Anomaly Detection Platform
=================================================================================
 [Status]  Platform Running in REPLAY & SCRIPTED INJECTION Mode
 [Gateway] REST API:       http://localhost:8000
 [Stream]  WebSocket Feed: ws://localhost:8000/ws/live
 [Web UI]  Cesium Globe:   http://localhost:5173
 [Docs]    Swagger Docs:   http://localhost:8000/docs
=================================================================================
"""

async def run_replay_stream(processor: StreamProcessor):
    """Feeds background flights, vessels, and earthquakes into the live pipeline."""
    logger.info("[ReplayStream] Loading historical telemetry replay files...")
    
    flights = []
    if os.path.exists(FLIGHTS_REPLAY):
        with open(FLIGHTS_REPLAY, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    flights.append(json.loads(line.strip()))

    ships = []
    if os.path.exists(SHIPS_REPLAY):
        with open(SHIPS_REPLAY, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ships.append(json.loads(line.strip()))

    quakes = []
    if os.path.exists(QUAKES_REPLAY):
        with open(QUAKES_REPLAY, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    quakes.append(json.loads(line.strip()))

    logger.info(f"[ReplayStream] Loaded {len(flights)} flights, {len(ships)} vessels, {len(quakes)} quakes.")

    idx = 0
    while True:
        # Stream 10 flights per cycle
        for i in range(10):
            if flights:
                f_rec = dict(flights[(idx * 10 + i) % len(flights)])
                f_rec["ts"] = time.time()
                await processor.process_flight(f_rec)
                await bus.publish("flights", f_rec)

        # Stream 3 vessels per cycle
        if ships:
            for i in range(3):
                s_rec = dict(ships[(idx * 3 + i) % len(ships)])
                s_rec["ts"] = time.time()
                await processor.process_ship(s_rec)
                await bus.publish("ships", s_rec)

        # Stream 1 quake every 5 cycles
        if quakes and idx % 5 == 0:
            q_rec = dict(quakes[(idx // 5) % len(quakes)])
            q_rec["ts"] = time.time()
            await processor.process_quake(q_rec)
            await bus.publish("quakes", q_rec)

        idx += 1
        await asyncio.sleep(0.5)

async def inject_scripted_demo_scenarios(processor: StreamProcessor):
    """
    Injects realistic, high-impact situational awareness scenarios:
    1. Aircraft General Emergency (Squawk 7700) over SFO
    2. ADS-B Cyber Spoofing (teleporting ghost track across airspace)
    3. Maritime Corridor Obstruction (container vessel dead-in-water in Dover Strait)
    4. Rapid Descent Hazard (flight dropping > 4800 ft/min)
    5. High-Magnitude Earthquake with asset proximity warnings
    """
    await asyncio.sleep(4.0)
    logger.info(">>> [SCENARIO INJECTOR] INITIATING SCRIPTED ANOMALY SEQUENCE (T+4s) <<<")

    # Scenario 1: Aircraft Squawk 7700
    now = time.time()
    logger.info("[INJECT 1/5] In-flight Emergency: Flight UAL921 squawking 7700 over San Francisco...")
    emer_flight = {
        "source": "opensky",
        "entity_id": "a7b8c9",
        "lat": 37.6213,
        "lon": -122.3790,
        "alt": 7200.0,
        "speed": 215.0,
        "heading": 280.0,
        "ts": now,
        "meta": {"callsign": "UAL921", "squawk": "7700", "vertical_rate": -15.2}
    }
    await processor.process_flight(emer_flight)
    await bus.publish("flights", emer_flight)

    await asyncio.sleep(4.0)

    # Scenario 2: ADS-B Cyber Spoofing Attack
    logger.info("[INJECT 2/5] Cyber Threat: ADS-B Spoofing track GHOST_X teleporting 110km in 3s...")
    spoof_1 = {
        "source": "opensky",
        "entity_id": "ghost_spoof_x",
        "lat": 36.8000,
        "lon": -121.5000,
        "alt": 11000.0,
        "speed": 240.0,
        "heading": 90.0,
        "ts": time.time(),
        "meta": {"callsign": "GHOST_X", "squawk": "1200"}
    }
    await processor.process_flight(spoof_1)
    await bus.publish("flights", spoof_1)

    await asyncio.sleep(2.0)
    spoof_2 = {
        "source": "opensky",
        "entity_id": "ghost_spoof_x",
        "lat": 37.8000,
        "lon": -122.5000,
        "alt": 11000.0,
        "speed": 240.0,
        "heading": 90.0,
        "ts": time.time(),
        "meta": {"callsign": "GHOST_X", "squawk": "1200"}
    }
    await processor.process_flight(spoof_2)
    await bus.publish("flights", spoof_2)

    await asyncio.sleep(4.0)

    # Scenario 3: Vessel Dead in Water in Dover Strait
    logger.info("[INJECT 3/5] Maritime Hazard: Vessel EVER_PACIFIC dead in water (0.1 kts) in Dover Strait...")
    drift_ship = {
        "source": "aisstream",
        "entity_id": "352009876",
        "lat": 51.0800,
        "lon": 1.4200,
        "alt": 0.0,
        "speed": 0.1,
        "heading": 42.0,
        "ts": time.time(),
        "meta": {"shipname": "EVER_PACIFIC", "status": "Under way using engine", "destination": "Dover Strait"}
    }
    await processor.process_ship(drift_ship)
    await bus.publish("ships", drift_ship)

    await asyncio.sleep(4.0)

    # Scenario 4: Rapid Altitude Descent (> 4500 ft/min)
    logger.info("[INJECT 4/5] Rapid Altitude Descent: Flight DLH450 dropping at -24.5 m/s (~4800 ft/min)...")
    dive_flight = {
        "source": "opensky",
        "entity_id": "dlh_450",
        "lat": 37.9500,
        "lon": -122.1000,
        "alt": 5800.0,
        "speed": 260.0,
        "heading": 140.0,
        "ts": time.time(),
        "meta": {"callsign": "DLH450", "squawk": "1200", "vertical_rate": -24.5}
    }
    await processor.process_flight(dive_flight)
    await bus.publish("flights", dive_flight)

    await asyncio.sleep(4.0)

    # Scenario 5: Seismic Hazard Alert (M6.3 earthquake)
    logger.info("[INJECT 5/5] Seismic Proximity Alert: M6.3 earthquake near coast assets...")
    quake_alert = {
        "source": "usgs",
        "entity_id": "usgs_demo_m63",
        "lat": 37.5000,
        "lon": -122.2000,
        "alt": -12000.0,
        "speed": 0.0,
        "heading": 0.0,
        "ts": time.time(),
        "meta": {"mag": 6.3, "place": "15km W of San Mateo, CA", "depth_km": 12.0}
    }
    await processor.process_quake(quake_alert)
    await bus.publish("quakes", quake_alert)

    logger.info(">>> [SCENARIO INJECTOR] ALL SCRIPTED DEMO ANOMALIES INJECTED (T+22s) <<<")
    logger.info(">>> Open http://localhost:5173 to view interactive threat drawer on Cesium globe. <<<")

async def monitor_loop():
    """Prints live pipeline metrics every 3 seconds."""
    while True:
        stats = await db.get_stats()
        events = await db.get_recent_events(limit=5)
        logger.info(
            f"[SentinelMonitor] DB Records: {stats.get('total_telemetry_records', 0):,} | "
            f"Active Anomalies/Events: {stats.get('anomalies', 0):,} | "
            f"Latest Alert: {events[0]['title'] if events else 'None'}"
        )
        await asyncio.sleep(3.0)

async def main():
    print(BANNER)
    # Initialize Storage and Bus
    await db.initialize()
    await bus.start_producer()

    processor = StreamProcessor()

    # Launch background tasks
    asyncio.create_task(run_replay_stream(processor))
    asyncio.create_task(inject_scripted_demo_scenarios(processor))
    asyncio.create_task(monitor_loop())

    # Launch FastAPI Server
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SentinelAI] Demo terminated cleanly.")
