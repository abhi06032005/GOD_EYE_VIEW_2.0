"""
SentinelAI End-to-End Integration Test
Simulates an end-to-end telemetry pipeline slice:
Ingest -> Event Bus -> StreamProcessor -> Anomaly Detection -> Persistent Event Store.
Asserts that an injected anomaly produces a high-severity alert within < 5.0 seconds.
"""
import pytest
import asyncio
import time
from processor.db import db
from processor.bus import bus
from processor.main import StreamProcessor

async def _run_end_to_end_injected_anomaly_to_alert():
    # 1. Initialize DB, Event Bus, and StreamProcessor
    await db.initialize()
    await bus.start_producer()
    processor = StreamProcessor()
    await processor.initialize()

    # 2. Warm up pipeline once to ensure all modules are loaded
    warmup_rec = {
        "source": "opensky",
        "entity_id": "warmup_flight",
        "lat": 37.0,
        "lon": -122.0,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": time.time(),
        "meta": {"squawk": "1200"}
    }
    await processor.process_flight(warmup_rec)

    # 3. Craft an injected synthetic critical anomaly (General In-Flight Emergency)
    injected_flight_id = f"test_injected_{int(time.time())}"
    anomaly_payload = {
        "source": "opensky",
        "entity_id": injected_flight_id,
        "lat": 37.6189,
        "lon": -122.3750,
        "alt": 9500.0,
        "speed": 230.0,
        "heading": 180.0,
        "ts": time.time(),
        "meta": {
            "callsign": "MAYDAY01",
            "squawk": "7700",
            "vertical_rate": -30.0
        }
    }

    # 4. Process the injected record and measure detection + storage latency
    t_start = time.time()
    await processor.process_flight(anomaly_payload)
    elapsed_time = time.time() - t_start

    # Assert processing took less than 5.0 seconds (well within sub-second real-time envelope)
    assert elapsed_time < 5.0, f"Detection took {elapsed_time:.3f}s, expected < 5.0s"

    # 5. Assert that an alert event was generated in the database
    recent_events = await db.get_recent_events(limit=20)
    matching_events = [e for e in recent_events if e["entity_id"] == injected_flight_id]

    assert len(matching_events) > 0, "No alert event was generated for the injected emergency flight"
    alert = matching_events[0]
    assert alert["severity"] in ["CRITICAL", "HIGH"]
    assert "7700" in alert["summary"] or "emergency" in alert["event_type"].lower()

def test_end_to_end_injected_anomaly_to_alert():
    asyncio.run(_run_end_to_end_injected_anomaly_to_alert())

async def _run_end_to_end_spoofing_detection():
    # Test consecutive telemetry updates triggering cyber spoofing alert
    await db.initialize()
    processor = StreamProcessor()
    await processor.initialize()

    spoof_id = f"cyber_spoof_{int(time.time())}"
    t0 = time.time()

    # Step 1: Normal initial position at SFO
    msg1 = {
        "source": "opensky",
        "entity_id": spoof_id,
        "lat": 37.6189,
        "lon": -122.3750,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": t0,
        "meta": {"callsign": "GHOST01", "squawk": "1200"}
    }
    await processor.process_flight(msg1)

    # Step 2: Instantaneous jump to Sacramento (120 km in 2 seconds)
    msg2 = {
        "source": "opensky",
        "entity_id": spoof_id,
        "lat": 38.5816,
        "lon": -121.4944,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": t0 + 2.0,
        "meta": {"callsign": "GHOST01", "squawk": "1200"}
    }
    t_start = time.time()
    await processor.process_flight(msg2)
    elapsed = time.time() - t_start

    assert elapsed < 5.0, f"Detection took {elapsed:.3f}s, expected < 5.0s"

    recent_events = await db.get_recent_events(limit=20)
    spoof_events = [e for e in recent_events if e["entity_id"] == spoof_id and "spoofing" in e.get("event_type", "")]
    assert len(spoof_events) >= 1
    assert spoof_events[0]["severity"] == "CRITICAL"

def test_end_to_end_spoofing_detection():
    asyncio.run(_run_end_to_end_spoofing_detection())
