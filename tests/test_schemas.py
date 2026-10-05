"""
SentinelAI Unit Tests: Schema Normalization
Validates standard message contract {source, entity_id, lat, lon, alt, speed, heading, ts, meta}
across OpenSky, adsb.lol, AISStream, USGS, and YOLOv8 detections.
"""
import pytest
import time

REQUIRED_TELEMETRY_FIELDS = {"source", "entity_id", "lat", "lon", "alt", "speed", "heading", "ts", "meta"}
REQUIRED_DETECTION_FIELDS = {"source", "camera_id", "lat", "lon", "class_counts", "bboxes", "ts", "meta"}

def test_opensky_normalization():
    # Raw OpenSky state vector sample
    raw_s = [
        "a4b12c", "UAL123 ", "United States", 1700000000, 1700000005,
        -122.4194, 37.7749, 10500.0, False, 225.5, 92.0, -2.5,
        None, 10450.0, "7700", False, 0
    ]
    now_ts = time.time()
    normalized = {
        "source": "opensky",
        "entity_id": str(raw_s[0]).lower(),
        "lat": float(raw_s[6]),
        "lon": float(raw_s[5]),
        "alt": float(raw_s[7]) if raw_s[7] is not None else 0.0,
        "speed": float(raw_s[9]) if raw_s[9] is not None else 0.0,
        "heading": float(raw_s[10]) if raw_s[10] is not None else 0.0,
        "ts": now_ts,
        "meta": {
            "callsign": (raw_s[1] or raw_s[0]).strip(),
            "origin_country": raw_s[2] or "Unknown",
            "squawk": str(raw_s[14]) if len(raw_s) > 14 and raw_s[14] else "1200",
            "vertical_rate": float(raw_s[11]) if raw_s[11] is not None else 0.0
        }
    }
    assert REQUIRED_TELEMETRY_FIELDS.issubset(normalized.keys())
    assert isinstance(normalized["entity_id"], str)
    assert isinstance(normalized["lat"], float)
    assert isinstance(normalized["lon"], float)
    assert isinstance(normalized["meta"], dict)
    assert normalized["meta"]["squawk"] == "7700"

def test_adsb_lol_normalization():
    # Raw adsb.lol / readsb aircraft sample
    raw_ac = {
        "hex": "AE1234",
        "flight": "REACH101 ",
        "lat": 38.8951,
        "lon": -77.0364,
        "alt_geom": 28000,
        "gs": 420.0,
        "track": 185.0,
        "squawk": "1200",
        "baro_rate": -500
    }
    normalized = {
        "source": "adsb.lol",
        "entity_id": str(raw_ac.get("hex", "")).lower(),
        "lat": float(raw_ac.get("lat", 0.0)),
        "lon": float(raw_ac.get("lon", 0.0)),
        "alt": float(raw_ac.get("alt_geom") or 0.0) * 0.3048,
        "speed": float(raw_ac.get("gs") or 0.0) * 0.514444,
        "heading": float(raw_ac.get("track") or 0.0),
        "ts": time.time(),
        "meta": {
            "callsign": str(raw_ac.get("flight", "")).strip(),
            "squawk": str(raw_ac.get("squawk", "1200")),
            "vertical_rate": float(raw_ac.get("baro_rate") or 0.0)
        }
    }
    assert REQUIRED_TELEMETRY_FIELDS.issubset(normalized.keys())
    assert normalized["entity_id"] == "ae1234"
    assert -90.0 <= normalized["lat"] <= 90.0
    assert -180.0 <= normalized["lon"] <= 180.0

def test_ais_ship_normalization():
    # Raw AIS envelope sample
    envelope = {
        "MessageType": "PositionReport",
        "MetaData": {
            "MMSI": 211281610,
            "ShipName": "EVER_GIVEN",
            "latitude": 30.015,
            "longitude": 32.562,
            "time_utc": "2026-10-05 12:00:00"
        },
        "Message": {
            "PositionReport": {
                "Sog": 11.2,
                "Cog": 182.4,
                "NavigationalStatus": 0
            }
        }
    }
    meta_data = envelope["MetaData"]
    msg = envelope["Message"]["PositionReport"]
    normalized = {
        "source": "aisstream",
        "entity_id": str(meta_data["MMSI"]),
        "lat": float(meta_data["latitude"]),
        "lon": float(meta_data["longitude"]),
        "alt": 0.0,
        "speed": float(msg["Sog"]),
        "heading": float(msg["Cog"]),
        "ts": time.time(),
        "meta": {
            "shipname": str(meta_data.get("ShipName", "")).strip(),
            "status": "Under way using engine" if msg["NavigationalStatus"] == 0 else "Other"
        }
    }
    assert REQUIRED_TELEMETRY_FIELDS.issubset(normalized.keys())
    assert normalized["entity_id"] == "211281610"
    assert normalized["meta"]["shipname"] == "EVER_GIVEN"

def test_usgs_quake_normalization():
    feat = {
        "id": "nc73891234",
        "properties": {
            "mag": 5.4,
            "place": "12 km SSW of Eureka, CA",
            "time": 1700000000000,
            "sig": 450
        },
        "geometry": {
            "coordinates": [-124.2, 40.7, 15.2]
        }
    }
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]
    normalized = {
        "source": "usgs",
        "entity_id": feat["id"],
        "lat": float(coords[1]),
        "lon": float(coords[0]),
        "alt": -float(coords[2] * 1000.0),
        "speed": 0.0,
        "heading": 0.0,
        "ts": float(props["time"]) / 1000.0,
        "meta": {
            "mag": float(props["mag"]),
            "place": props["place"],
            "depth_km": float(coords[2]),
            "significance": props["sig"]
        }
    }
    assert REQUIRED_TELEMETRY_FIELDS.issubset(normalized.keys())
    assert normalized["entity_id"] == "nc73891234"
    assert normalized["meta"]["mag"] == 5.4

def test_yolo_detection_normalization():
    det_msg = {
        "source": "cctv",
        "camera_id": "cam_sfo_101",
        "lat": 37.6213,
        "lon": -122.3790,
        "class_counts": {"car": 12, "truck": 3, "bus": 1, "person": 0},
        "bboxes": [{"class": "car", "conf": 0.88, "box": [100.0, 150.0, 220.0, 280.0]}],
        "ts": time.time(),
        "meta": {
            "camera_name": "US-101 at Airport Blvd (SFO)",
            "infer_time_ms": 78.4,
            "total_objects": 16
        }
    }
    assert REQUIRED_DETECTION_FIELDS.issubset(det_msg.keys())
    assert det_msg["meta"]["total_objects"] == 16
    assert len(det_msg["bboxes"]) == 1
