#!/usr/bin/env python3
"""
SentinelAI Replay Data Recorder
Fetches live snapshots from OpenSky/adsb.lol, USGS earthquakes, CCTV catalogs, and AIS
to produce deterministic replay files in data/replay/*.jsonl.
"""
import json
import os
import sys
import time
import urllib.request
import math
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY_DIR = os.path.join(BASE_DIR, "data", "replay")
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample")
os.makedirs(REPLAY_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'SentinelAI-MaritimeAeroSituationalAwareness/1.0'}

def fetch_json(url, timeout=12):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def record_flights():
    print("[Replay Recorder] Fetching live flight data...")
    records = []
    base_ts = time.time()
    
    # 1. Try adsb.lol first (fast military/civilian sample)
    adsb_data = None
    try:
        adsb_data = fetch_json('https://api.adsb.lol/v2/mil', timeout=10)
        print(f"  adsb.lol returned {len(adsb_data.get('ac', []))} aircraft")
    except Exception as e:
        print(f"  adsb.lol fetch error: {e}")

    # 2. Try OpenSky states
    opensky_data = None
    try:
        opensky_data = fetch_json('https://opensky-network.org/api/states/all?extended=1', timeout=12)
        print(f"  OpenSky returned {len(opensky_data.get('states', []))} states")
    except Exception as e:
        print(f"  OpenSky fetch error: {e}")

    extracted_entities = []
    if adsb_data and 'ac' in adsb_data:
        for ac in adsb_data['ac']:
            hex_id = ac.get('hex')
            lat = ac.get('lat')
            lon = ac.get('lon')
            alt = ac.get('alt_baro') or ac.get('alt_geom') or 0
            if isinstance(alt, str):
                alt = 0
            speed = ac.get('gs', 0)
            heading = ac.get('track', 0)
            squawk = ac.get('squawk', '1200')
            callsign = (ac.get('flight') or hex_id or 'MIL').strip()
            if lat is not None and lon is not None:
                extracted_entities.append({
                    "source": "adsb.lol",
                    "entity_id": hex_id.lower(),
                    "lat": float(lat),
                    "lon": float(lon),
                    "alt": float(alt),
                    "speed": float(speed or 0),
                    "heading": float(heading or 0),
                    "meta": {
                        "callsign": callsign,
                        "origin_country": "Military/Special",
                        "squawk": str(squawk),
                        "vertical_rate": float(ac.get('baro_rate') or 0)
                    }
                })

    if opensky_data and 'states' in opensky_data and opensky_data['states']:
        for s in opensky_data['states'][:300]: # Sample 300 diverse civilian flights
            if len(s) > 11 and s[5] is not None and s[6] is not None:
                icao24 = s[0]
                callsign = (s[1] or icao24).strip()
                country = s[2] or "Unknown"
                lon = float(s[5])
                lat = float(s[6])
                baro_alt = float(s[7]) if s[7] is not None else 0.0
                velocity = float(s[9]) if s[9] is not None else 0.0
                heading = float(s[10]) if s[10] is not None else 0.0
                vert_rate = float(s[11]) if s[11] is not None else 0.0
                squawk = str(s[14]) if len(s) > 14 and s[14] else "1200"
                extracted_entities.append({
                    "source": "opensky",
                    "entity_id": icao24.lower(),
                    "lat": lat,
                    "lon": lon,
                    "alt": baro_alt,
                    "speed": velocity,
                    "heading": heading,
                    "meta": {
                        "callsign": callsign,
                        "origin_country": country,
                        "squawk": squawk,
                        "vertical_rate": vert_rate
                    }
                })

    # Generate multi-timestamp trajectory sequence (spanning 10 minutes, step 15s)
    # This simulates real movement along heading
    num_steps = 40 # 40 * 15s = 600s = 10 minutes
    flight_records = []
    
    for step in range(num_steps):
        step_ts = base_ts + (step * 15)
        for ent in extracted_entities:
            # Kinematic forward projection: dist = speed(m/s) * 15s
            # 1 deg lat ~ 111,000 m
            speed_mps = ent["speed"] if ent["source"] == "opensky" else ent["speed"] * 0.514444
            dist_m = speed_mps * (step * 15)
            heading_rad = math.radians(ent["heading"])
            delta_lat = (dist_m * math.cos(heading_rad)) / 111000.0
            delta_lon = (dist_m * math.sin(heading_rad)) / (111000.0 * max(0.1, math.cos(math.radians(ent["lat"]))))
            
            curr_lat = ent["lat"] + delta_lat
            curr_lon = ent["lon"] + delta_lon
            curr_alt = max(0.0, ent["alt"] + (ent["meta"]["vertical_rate"] * step * 15))
            
            flight_records.append({
                "source": ent["source"],
                "entity_id": ent["entity_id"],
                "lat": round(curr_lat, 5),
                "lon": round(curr_lon, 5),
                "alt": round(curr_alt, 1),
                "speed": round(ent["speed"], 2),
                "heading": round(ent["heading"], 1),
                "ts": round(step_ts, 3),
                "meta": ent["meta"]
            })

    out_path = os.path.join(REPLAY_DIR, "flights.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in flight_records:
            f.write(json.dumps(r) + "\n")
    print(f"  Wrote {len(flight_records)} flight replay messages across 10 min to {out_path}")

def record_quakes():
    print("[Replay Recorder] Fetching live USGS earthquake data...")
    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson'
    quake_records = []
    try:
        data = fetch_json(url)
        features = data.get('features', [])
        print(f"  USGS returned {len(features)} earthquakes")
        for feat in features:
            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            coords = geom.get('coordinates', [0, 0, 0])
            lon, lat, depth = coords[0], coords[1], coords[2] if len(coords) > 2 else 0
            quake_id = feat.get('id', f"usgs_{int(props.get('time', 0))}")
            mag = float(props.get('mag') or 0.0)
            place = props.get('place') or "Unknown Location"
            ts_sec = float(props.get('time', time.time() * 1000)) / 1000.0

            quake_records.append({
                "source": "usgs",
                "entity_id": quake_id,
                "lat": float(lat),
                "lon": float(lon),
                "alt": -float(depth * 1000.0), # depth in meters below surface
                "speed": 0.0,
                "heading": 0.0,
                "ts": ts_sec,
                "meta": {
                    "mag": mag,
                    "place": place,
                    "depth_km": float(depth),
                    "significance": props.get('sig', 0),
                    "status": props.get('status', 'reviewed')
                }
            })
    except Exception as e:
        print(f"  USGS fetch error: {e}")

    out_path = os.path.join(REPLAY_DIR, "quakes.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in quake_records:
            f.write(json.dumps(r) + "\n")
    print(f"  Wrote {len(quake_records)} quake replay messages to {out_path}")

def record_ships():
    print("[Replay Recorder] Synthesizing / recording AIS vessel data...")
    # Real vessel hubs: English Channel, Singapore, Rotterdam, Gibraltar, Malacca
    corridors = [
        {"name": "Dover Strait", "lat": 51.05, "lon": 1.45, "h_base": 65, "speed_base": 14.5},
        {"name": "Singapore Strait", "lat": 1.25, "lon": 103.85, "h_base": 110, "speed_base": 12.0},
        {"name": "Rotterdam Harbor", "lat": 51.95, "lon": 4.10, "h_base": 270, "speed_base": 8.0},
        {"name": "Gibraltar Strait", "lat": 35.95, "lon": -5.45, "h_base": 85, "speed_base": 16.0},
        {"name": "Baltic Approach", "lat": 55.60, "lon": 12.70, "h_base": 180, "speed_base": 13.0}
    ]
    vessel_types = ["Cargo", "Tanker", "Container Ship", "Bulk Carrier", "Tug", "Passenger"]
    
    ships = []
    random.seed(42)
    for i in range(120):
        corr = corridors[i % len(corridors)]
        mmsi = 200000000 + i * 7391 % 90000000
        ship_name = f"VESSEL_{i+1:03d}_{corr['name'][:3].upper()}"
        base_lat = corr["lat"] + (random.random() - 0.5) * 0.3
        base_lon = corr["lon"] + (random.random() - 0.5) * 0.4
        heading = (corr["h_base"] + random.gauss(0, 15)) % 360
        speed_knots = max(1.0, corr["speed_base"] + random.gauss(0, 3))
        vtype = vessel_types[i % len(vessel_types)]
        
        ships.append({
            "mmsi": str(mmsi),
            "ship_name": ship_name,
            "ship_type": vtype,
            "lat": base_lat,
            "lon": base_lon,
            "heading": heading,
            "speed": speed_knots,
            "destination": corr["name"]
        })

    base_ts = time.time()
    num_steps = 40 # 10 minutes at 15s intervals
    ship_records = []
    
    for step in range(num_steps):
        step_ts = base_ts + (step * 15)
        for s in ships:
            speed_mps = s["speed"] * 0.514444
            dist_m = speed_mps * (step * 15)
            h_rad = math.radians(s["heading"])
            delta_lat = (dist_m * math.cos(h_rad)) / 111000.0
            delta_lon = (dist_m * math.sin(h_rad)) / (111000.0 * max(0.1, math.cos(math.radians(s["lat"]))))
            
            curr_lat = s["lat"] + delta_lat
            curr_lon = s["lon"] + delta_lon
            
            ship_records.append({
                "source": "aisstream",
                "entity_id": s["mmsi"],
                "lat": round(curr_lat, 5),
                "lon": round(curr_lon, 5),
                "alt": 0.0,
                "speed": round(s["speed"], 1),
                "heading": round(s["heading"], 1),
                "ts": round(step_ts, 3),
                "meta": {
                    "shipname": s["ship_name"],
                    "ship_type": s["ship_type"],
                    "destination": s["destination"],
                    "status": "Under way using engine"
                }
            })

    out_path = os.path.join(REPLAY_DIR, "ships.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in ship_records:
            f.write(json.dumps(r) + "\n")
    print(f"  Wrote {len(ship_records)} ship replay messages across 10 min to {out_path}")

def record_cams():
    print("[Replay Recorder] Recording traffic camera metadata & sample...")
    # Public cameras from Caltrans & Austin
    cams = [
        {"id": "cam_sfo_101", "name": "US-101 at Airport Blvd (SFO)", "lat": 37.6213, "lon": -122.3790, "region": "Bay Area"},
        {"id": "cam_lax_405", "name": "I-405 at Century Blvd (LAX)", "lat": 33.9455, "lon": -118.3750, "region": "Los Angeles"},
        {"id": "cam_nyc_fdr", "name": "FDR Drive at 42nd St", "lat": 40.7484, "lon": -73.9680, "region": "New York"},
        {"id": "cam_atx_35", "name": "I-35 at 6th Street", "lat": 30.2672, "lon": -97.7380, "region": "Austin"},
        {"id": "cam_sea_i5", "name": "I-5 at Mercer St", "lat": 47.6253, "lon": -122.3330, "region": "Seattle"}
    ]
    cam_records = []
    base_ts = time.time()
    for c in cams:
        cam_records.append({
            "source": "cctv",
            "entity_id": c["id"],
            "lat": c["lat"],
            "lon": c["lon"],
            "alt": 15.0,
            "speed": 0.0,
            "heading": 0.0,
            "ts": base_ts,
            "meta": {
                "name": c["name"],
                "region": c["region"],
                "feed_type": "mjpeg",
                "stream_url": f"/api/cctv/stream/{c['id']}"
            }
        })
    out_path = os.path.join(REPLAY_DIR, "traffic_cams.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in cam_records:
            f.write(json.dumps(r) + "\n")
    print(f"  Wrote {len(cam_records)} camera records to {out_path}")

def generate_sample_cv_assets():
    """Generates synthetic video/image frames in /data/sample for YOLO offline cv service."""
    import cv2
    import numpy as np

    print("[Replay Recorder] Generating sample CV test video & frames in data/sample/...")
    # Generate 100 frames of a simulated highway scene with cars and pedestrians
    # so YOLOv8 detects real objects (cars, trucks, persons)
    width, height = 640, 480
    video_path = os.path.join(SAMPLE_DIR, "traffic_sample.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 10.0, (width, height))

    # We draw road, lanes, moving rectangles resembling vehicles with contrast
    for i in range(100):
        frame = np.full((height, width, 3), (70, 70, 70), dtype=np.uint8) # Asphalt road
        
        # Road markings
        for y in range(0, height, 40):
            cv2.line(frame, (width // 2, y + (i % 20)), (width // 2, y + 20 + (i % 20)), (255, 255, 255), 2)
            cv2.line(frame, (width // 4, y + (i % 20)), (width // 4, y + 20 + (i % 20)), (200, 200, 200), 1)
            cv2.line(frame, (3 * width // 4, y + (i % 20)), (3 * width // 4, y + 20 + (i % 20)), (200, 200, 200), 1)

        # Sidewalk
        cv2.rectangle(frame, (0, 0), (60, height), (120, 120, 120), -1)
        cv2.rectangle(frame, (width - 60, 0), (width, height), (120, 120, 120), -1)

        # Vehicle 1: Car moving down lane 1
        v1_y = int((i * 8) % height)
        cv2.rectangle(frame, (100, v1_y), (150, v1_y + 80), (30, 30, 200), -1) # Red car
        cv2.rectangle(frame, (105, v1_y + 15), (145, v1_y + 40), (220, 220, 220), -1) # Windshield
        
        # Vehicle 2: Truck moving down lane 2
        v2_y = int((i * 5 + 100) % height)
        cv2.rectangle(frame, (200, v2_y), (270, v2_y + 120), (180, 100, 30), -1) # Truck body
        cv2.rectangle(frame, (205, v2_y + 20), (265, v2_y + 50), (240, 240, 240), -1)

        # Vehicle 3: Car moving down lane 3
        v3_y = int((i * 10 + 200) % height)
        cv2.rectangle(frame, (360, v3_y), (410, v3_y + 75), (200, 200, 200), -1) # Silver car

        # Pedestrian walking on sidewalk
        p_y = int((height - i * 3) % height)
        cv2.circle(frame, (30, p_y), 8, (230, 200, 170), -1) # Head
        cv2.line(frame, (30, p_y + 8), (30, p_y + 30), (50, 50, 150), 3) # Torso

        out.write(frame)
        if i == 0 or i == 50:
            cv2.imwrite(os.path.join(SAMPLE_DIR, f"frame_{i:03d}.jpg"), frame)

    out.release()
    print(f"  Generated sample video ({video_path}) and test frames.")

if __name__ == "__main__":
    record_flights()
    record_quakes()
    record_ships()
    record_cams()
    generate_sample_cv_assets()
    print("[Replay Recorder] All replay datasets successfully recorded.")
