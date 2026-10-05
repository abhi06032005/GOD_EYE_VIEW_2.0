#!/usr/bin/env python3
"""
SentinelAI Synthetic Anomaly & Cyber Threat Injector
Injects labeled ground-truth anomalies into baseline replay streams:
  1. aircraft_emergency_descent (rapid vertical drop > 5000 ft/min)
  2. aircraft_emergency_squawk (7700 transponder declaration)
  3. drifting_ship (dead in water < 0.2 kts in shipping lane)
  4. geofence_breach (entry into restricted military airspace/naval zone)
  5. possible_spoofing (cyber track manipulation: impossible kinematic jump 95km in 10s)
Outputs: data/replay/injected_dataset.jsonl with ground-truth verification flags.
"""
import os
import sys
import json
import time
import copy
import random
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY_DIR = os.path.join(BASE_DIR, "data", "replay")
FLIGHTS_REPLAY = os.path.join(REPLAY_DIR, "flights.jsonl")
SHIPS_REPLAY = os.path.join(REPLAY_DIR, "ships.jsonl")
INJECTED_OUTPUT = os.path.join(REPLAY_DIR, "injected_dataset.jsonl")

def load_replay_sample(path: str, max_items: int = 400) -> List[Dict[str, Any]]:
    records = []
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(records) >= max_items:
                break
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def generate_injected_dataset(num_anomalies: int = 50) -> List[Dict[str, Any]]:
    flights = load_replay_sample(FLIGHTS_REPLAY, 300)
    ships = load_replay_sample(SHIPS_REPLAY, 150)
    
    dataset = []
    base_ts = time.time()
    
    # Add normal nominal records (label = "nominal", is_anomaly = False)
    for f in flights:
        rec = copy.deepcopy(f)
        rec["is_anomaly"] = False
        rec["ground_truth_label"] = "nominal"
        dataset.append(rec)

    for s in ships:
        rec = copy.deepcopy(s)
        rec["is_anomaly"] = False
        rec["ground_truth_label"] = "nominal"
        dataset.append(rec)

    # Inject 5 targeted anomaly categories
    random.seed(1337)
    anomaly_types = [
        "rapid_descent",
        "transponder_emergency",
        "drifting_in_corridor",
        "geofence_breach",
        "possible_spoofing"
    ]

    injected_count = 0
    for i in range(num_anomalies):
        atype = anomaly_types[i % len(anomaly_types)]
        injected_count += 1
        anom_ts = base_ts + (i * 2)

        if atype == "rapid_descent":
            rec = {
                "source": "opensky",
                "entity_id": f"anom_flt_desc_{i:02d}",
                "lat": 48.8566 + random.gauss(0, 0.5),
                "lon": 2.3522 + random.gauss(0, 0.5),
                "alt": 28000.0,
                "speed": 230.0,
                "heading": 190.0,
                "ts": anom_ts,
                "meta": {
                    "callsign": f"AFR{900+i}",
                    "squawk": "1200",
                    "vertical_rate": -28.5 # -5600 ft/min descent
                },
                "is_anomaly": True,
                "ground_truth_label": "rapid_descent"
            }
            dataset.append(rec)

        elif atype == "transponder_emergency":
            rec = {
                "source": "opensky",
                "entity_id": f"anom_flt_sqk_{i:02d}",
                "lat": 51.5074 + random.gauss(0, 0.5),
                "lon": -0.1278 + random.gauss(0, 0.5),
                "alt": 33000.0,
                "speed": 245.0,
                "heading": 90.0,
                "ts": anom_ts,
                "meta": {
                    "callsign": f"BAW{400+i}",
                    "squawk": "7700", # General emergency
                    "vertical_rate": -5.0
                },
                "is_anomaly": True,
                "ground_truth_label": "transponder_emergency"
            }
            dataset.append(rec)

        elif atype == "drifting_in_corridor":
            rec = {
                "source": "aisstream",
                "entity_id": f"21100{7000+i}",
                "lat": 51.10, # Dover Strait traffic lane
                "lon": 1.45,
                "alt": 0.0,
                "speed": 0.1, # Dead in water
                "heading": 210.0,
                "ts": anom_ts,
                "meta": {
                    "shipname": f"DRIFTING_CARRIER_{i:02d}",
                    "status": "Under way using engine",
                    "destination": "Dover Strait"
                },
                "is_anomaly": True,
                "ground_truth_label": "drifting_in_corridor"
            }
            dataset.append(rec)

        elif atype == "geofence_breach":
            rec = {
                "source": "adsb.lol",
                "entity_id": f"anom_flt_gf_{i:02d}",
                "lat": 35.5, # Inside R-2508 Mojave restricted box
                "lon": -117.2,
                "alt": 15000.0,
                "speed": 210.0,
                "heading": 45.0,
                "ts": anom_ts,
                "meta": {
                    "callsign": f"CIVIL_{i:02d}",
                    "squawk": "1200",
                    "vertical_rate": 0.0
                },
                "is_anomaly": True,
                "ground_truth_label": "geofence_breach"
            }
            dataset.append(rec)

        elif atype == "possible_spoofing":
            # Emit two sequential messages with impossible kinematic teleportation
            eid = f"spoofed_hex_{i:02d}"
            rec1 = {
                "source": "opensky",
                "entity_id": eid,
                "lat": 40.7128,
                "lon": -74.0060,
                "alt": 25000.0,
                "speed": 250.0,
                "heading": 180.0,
                "ts": anom_ts - 5.0,
                "meta": {"callsign": f"SPOOF{i}", "squawk": "1200", "vertical_rate": 0.0},
                "is_anomaly": False,
                "ground_truth_label": "nominal"
            }
            dataset.append(rec1)
            rec2 = {
                "source": "opensky",
                "entity_id": eid,
                "lat": 41.5000, # ~90 km jump in 5 seconds = 64,800 km/h apparent speed!
                "lon": -73.5000,
                "alt": 25000.0,
                "speed": 250.0,
                "heading": 180.0,
                "ts": anom_ts,
                "meta": {"callsign": f"SPOOF{i}", "squawk": "1200", "vertical_rate": 0.0},
                "is_anomaly": True,
                "ground_truth_label": "possible_spoofing"
            }
            dataset.append(rec2)

    # Write out injected dataset
    with open(INJECTED_OUTPUT, "w", encoding="utf-8") as f:
        for r in dataset:
            f.write(json.dumps(r) + "\n")

    print(f"[Injector] Successfully injected {injected_count} ground-truth labeled anomalies into {len(dataset)} total records.")
    print(f"  Dataset saved to {INJECTED_OUTPUT}")
    return dataset

if __name__ == "__main__":
    generate_injected_dataset(num_anomalies=60)
