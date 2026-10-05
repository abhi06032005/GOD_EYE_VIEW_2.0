"""
SentinelAI Multimodal Stream Processor
Consumes topics from Redpanda/Kafka (flights, ships, quakes, detections),
writes normalized records to Postgres/SQLite, evaluates rules + ML anomaly detection,
and publishes alerts & correlated events to the 'events' topic + DB.
"""
import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from processor.db import db
from processor.bus import bus
from processor.rules import AnomalyRuleEngine
from processor.ml import MLAnomalyDetector

logger = logging.getLogger("StreamProcessor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class StreamProcessor:
    def __init__(self):
        self.rule_engine = AnomalyRuleEngine()
        self.ml_detector = MLAnomalyDetector()
        self.active_entities = {} # entity_id -> {lat, lon, ts, type}
        self.msg_count = 0
        self.anomaly_count = 0
        self.start_time = time.time()

    async def initialize(self):
        await db.initialize()
        await bus.start_producer()
        logger.info("[StreamProcessor] Initialized DB and Event Bus.")

    async def handle_flight(self, topic: str, rec: Dict[str, Any]):
        self.msg_count += 1
        # 1. Persist to DB
        await db.insert_telemetry("flights", rec)
        self.active_entities[rec["entity_id"]] = {
            "entity_id": rec["entity_id"],
            "lat": rec["lat"],
            "lon": rec["lon"],
            "alt": rec.get("alt", 0.0),
            "ts": rec.get("ts", time.time()),
            "type": "flight"
        }

        # 2. Rule-based anomaly evaluation
        anomalies = self.rule_engine.evaluate_flight(rec)
        
        # 3. ML anomaly evaluation
        ml_anom = self.ml_detector.predict(rec, "flight")
        if ml_anom:
            anomalies.append(ml_anom)

        # 4. Dispatch detected anomalies
        for anom in anomalies:
            await self._process_anomaly(anom)

    async def handle_ship(self, topic: str, rec: Dict[str, Any]):
        self.msg_count += 1
        await db.insert_telemetry("ships", rec)
        self.active_entities[rec["entity_id"]] = {
            "entity_id": rec["entity_id"],
            "lat": rec["lat"],
            "lon": rec["lon"],
            "alt": 0.0,
            "ts": rec.get("ts", time.time()),
            "type": "ship"
        }

        anomalies = self.rule_engine.evaluate_ship(rec)
        ml_anom = self.ml_detector.predict(rec, "ship")
        if ml_anom:
            anomalies.append(ml_anom)

        for anom in anomalies:
            await self._process_anomaly(anom)

    async def handle_quake(self, topic: str, rec: Dict[str, Any]):
        self.msg_count += 1
        await db.insert_telemetry("quakes", rec)

        # Correlate quake with nearby tracked assets
        tracked_list = list(self.active_entities.values())
        anomalies = self.rule_engine.evaluate_quake_proximity(rec, tracked_list)
        for anom in anomalies:
            await self._process_anomaly(anom)

    async def handle_detection(self, topic: str, rec: Dict[str, Any]):
        self.msg_count += 1
        await db.insert_detection(rec)

        # High density traffic alert (> 20 vehicles at intersection)
        counts = rec.get("class_counts", {})
        total_vehicles = counts.get("car", 0) + counts.get("truck", 0) + counts.get("bus", 0)
        if total_vehicles >= 18:
            anom = {
                "id": f"anom_traf_{rec['camera_id']}_{int(rec.get('ts', time.time()))}",
                "entity_id": rec["camera_id"],
                "entity_type": "traffic_camera",
                "rule_name": "heavy_traffic_congestion",
                "severity": "MEDIUM",
                "description": f"Urban Congestion Alert: {total_vehicles} vehicles detected by camera {rec['camera_id']}",
                "lat": rec["lat"],
                "lon": rec["lon"],
                "alt": 0.0,
                "ts": rec.get("ts", time.time()),
                "meta": {"vehicle_count": total_vehicles, "counts": counts}
            }
            await self._process_anomaly(anom)

    async def _process_anomaly(self, anom: Dict[str, Any]):
        self.anomaly_count += 1
        logger.info(f"[ANOMALY DETECTED] [{anom['severity']}] {anom['rule_name']} on {anom['entity_id']}: {anom['description']}")
        # Write to anomalies table
        await db.insert_anomaly(anom)

        # Construct synthesized situational event for Globe alert & RAG
        event = {
            "id": f"EV-{anom['id']}",
            "event_type": anom["rule_name"],
            "entity_id": anom["entity_id"],
            "severity": anom["severity"],
            "title": f"{anom['severity']} Alert: {anom['rule_name'].replace('_', ' ').title()}",
            "summary": anom["description"],
            "lat": anom["lat"],
            "lon": anom["lon"],
            "ts": anom["ts"],
            "meta": anom.get("meta", {})
        }
        await db.insert_event(event)
        # Publish to 'events' topic for real-time WebSocket distribution
        await bus.publish("events", event)

    async def run(self):
        await self.initialize()
        logger.info("[StreamProcessor] Registering topic subscriptions...")
        
        await bus.subscribe(["flights"], self.handle_flight)
        await bus.subscribe(["ships"], self.handle_ship)
        await bus.subscribe(["quakes"], self.handle_quake)
        await bus.subscribe(["detections"], self.handle_detection)

        logger.info("[StreamProcessor] Processing streaming telemetry...")
        while True:
            await asyncio.sleep(10)
            elapsed = time.time() - self.start_time
            rate = self.msg_count / max(1.0, elapsed)
            logger.info(f"[StreamProcessor Heartbeat] Processed: {self.msg_count} msgs ({rate:.1f} msg/s), Anomalies: {self.anomaly_count}")

processor = StreamProcessor()

if __name__ == "__main__":
    asyncio.run(processor.run())
