"""
SentinelAI Unit Tests: Deterministic and Heuristic Anomaly Rules
Verifies squawk emergencies, rapid descent, speed outliers, geofence breaches,
maritime drift, AIS-dark transponders, seismic proximity, and ADS-B cyber spoofing.
"""
import pytest
import time
from processor.rules import AnomalyRuleEngine, RESTRICTED_GEOFENCES

@pytest.fixture
def engine():
    return AnomalyRuleEngine()

def test_transponder_squawk_7700_emergency(engine):
    rec = {
        "source": "opensky",
        "entity_id": "a4b12c",
        "lat": 37.7749,
        "lon": -122.4194,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": time.time(),
        "meta": {"squawk": "7700", "callsign": "UAL123"}
    }
    anomalies = engine.evaluate_flight(rec)
    squawk_anoms = [a for a in anomalies if a["rule_name"] == "transponder_general_emergency"]
    assert len(squawk_anoms) == 1
    assert squawk_anoms[0]["severity"] == "CRITICAL"
    assert "General In-Flight Emergency" in squawk_anoms[0]["description"]

def test_transponder_squawk_7500_hijack(engine):
    rec = {
        "source": "opensky",
        "entity_id": "b5c23d",
        "lat": 40.7128,
        "lon": -74.0060,
        "alt": 11000.0,
        "speed": 240.0,
        "heading": 180.0,
        "ts": time.time(),
        "meta": {"squawk": "7500", "callsign": "DAL456"}
    }
    anomalies = engine.evaluate_flight(rec)
    squawk_anoms = [a for a in anomalies if a["rule_name"] == "transponder_hijack"]
    assert len(squawk_anoms) == 1
    assert squawk_anoms[0]["severity"] == "CRITICAL"
    assert "Hijacking" in squawk_anoms[0]["description"]

def test_transponder_squawk_7600_comm_loss(engine):
    rec = {
        "source": "opensky",
        "entity_id": "c6d34e",
        "lat": 51.5074,
        "lon": -0.1278,
        "alt": 9000.0,
        "speed": 210.0,
        "heading": 270.0,
        "ts": time.time(),
        "meta": {"squawk": "7600", "callsign": "BAW789"}
    }
    anomalies = engine.evaluate_flight(rec)
    squawk_anoms = [a for a in anomalies if a["rule_name"] == "transponder_comm_loss"]
    assert len(squawk_anoms) == 1
    assert squawk_anoms[0]["severity"] == "HIGH"

def test_rapid_descent_detection(engine):
    # OpenSky vertical rate in m/s (< -20.3 m/s ~= -4000 fpm)
    rec = {
        "source": "opensky",
        "entity_id": "desc_test_1",
        "lat": 34.0522,
        "lon": -118.2437,
        "alt": 7000.0,
        "speed": 230.0,
        "heading": 120.0,
        "ts": time.time(),
        "meta": {"vertical_rate": -25.0, "squawk": "1200"}
    }
    anomalies = engine.evaluate_flight(rec)
    desc_anoms = [a for a in anomalies if a["rule_name"] == "rapid_descent"]
    assert len(desc_anoms) == 1
    assert desc_anoms[0]["severity"] == "HIGH"
    assert desc_anoms[0]["meta"]["vertical_rate_fpm"] > 4000

def test_speed_outlier_detection(engine):
    # OpenSky speed > 450 m/s (> 1620 km/h)
    rec = {
        "source": "opensky",
        "entity_id": "speed_test_1",
        "lat": 38.0,
        "lon": -120.0,
        "alt": 12000.0,
        "speed": 500.0, # m/s
        "heading": 45.0,
        "ts": time.time(),
        "meta": {"squawk": "1200"}
    }
    anomalies = engine.evaluate_flight(rec)
    spd_anoms = [a for a in anomalies if a["rule_name"] == "extreme_speed_outlier"]
    assert len(spd_anoms) == 1
    assert spd_anoms[0]["severity"] == "MEDIUM"

def test_aero_geofence_breach(engine):
    # Restricted Airspace R-2508: lat [35.0, 36.2], lon [-118.0, -116.5]
    rec = {
        "source": "opensky",
        "entity_id": "breach_aero_1",
        "lat": 35.5,
        "lon": -117.2,
        "alt": 5000.0,
        "speed": 200.0,
        "heading": 90.0,
        "ts": time.time(),
        "meta": {"squawk": "1200"}
    }
    anomalies = engine.evaluate_flight(rec)
    gf_anoms = [a for a in anomalies if a["rule_name"] == "geofence_breach"]
    assert len(gf_anoms) == 1
    assert "R-2508" in gf_anoms[0]["description"]

def test_maritime_geofence_breach(engine):
    # Gibraltar Naval Exclusion Zone: lat [35.85, 36.15], lon [-5.6, -5.2]
    rec = {
        "source": "aisstream",
        "entity_id": "211281610",
        "lat": 36.0,
        "lon": -5.4,
        "speed": 12.5,
        "heading": 80.0,
        "ts": time.time(),
        "meta": {"shipname": "CONTAINER_X", "destination": "VALENCIA"}
    }
    anomalies = engine.evaluate_ship(rec)
    gf_anoms = [a for a in anomalies if a["rule_name"] == "maritime_exclusion_breach"]
    assert len(gf_anoms) == 1
    assert "Gibraltar" in gf_anoms[0]["description"]

def test_ship_drifting_in_corridor(engine):
    rec = {
        "source": "aisstream",
        "entity_id": "352001850",
        "lat": 51.1,
        "lon": 1.45,
        "speed": 0.2, # Near 0
        "heading": 45.0,
        "ts": time.time(),
        "meta": {"status": "Under way using engine", "destination": "Dover Strait"}
    }
    anomalies = engine.evaluate_ship(rec)
    drift_anoms = [a for a in anomalies if a["rule_name"] == "drifting_in_corridor"]
    assert len(drift_anoms) == 1
    assert "dead in water" in drift_anoms[0]["description"]

def test_ais_dark_transponder(engine):
    now = time.time()
    last_seen = now - 900 # 15 minutes ago
    anom = engine.check_ais_dark("mmsi_999888777", last_ts=last_seen, current_ts=now, threshold_sec=600.0)
    assert anom is not None
    assert anom["rule_name"] == "ais_transponder_dark"
    assert anom["severity"] == "HIGH"
    assert anom["meta"]["silent_seconds"] >= 600

def test_cyber_spoofing_teleportation(engine):
    t0 = time.time()
    # Initial legitimate state
    rec1 = {
        "source": "opensky",
        "entity_id": "spoof_target_1",
        "lat": 37.7749,
        "lon": -122.4194,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": t0,
        "meta": {"squawk": "1200"}
    }
    anoms1 = engine.evaluate_flight(rec1)
    assert len(anoms1) == 0

    # Sudden teleportation: 100 km away in 5 seconds (> 72,000 km/h)
    rec2 = {
        "source": "opensky",
        "entity_id": "spoof_target_1",
        "lat": 38.6,
        "lon": -121.5,
        "alt": 10000.0,
        "speed": 220.0,
        "heading": 90.0,
        "ts": t0 + 5.0,
        "meta": {"squawk": "1200"}
    }
    anoms2 = engine.evaluate_flight(rec2)
    spoof_anoms = [a for a in anoms2 if a["rule_name"] == "possible_spoofing"]
    assert len(spoof_anoms) == 1
    assert spoof_anoms[0]["severity"] == "CRITICAL"
    assert "Cyber Threat / ADS-B Spoofing" in spoof_anoms[0]["description"]

def test_quake_proximity_alert(engine):
    quake = {
        "entity_id": "usgs_quake_major_1",
        "lat": 34.0,
        "lon": -118.0,
        "ts": time.time(),
        "meta": {"mag": 6.2, "place": "Southern California"}
    }
    tracked_entities = [
        {"entity_id": "asset_near_1", "lat": 34.2, "lon": -118.2, "alt": 500.0}, # ~28 km away
        {"entity_id": "asset_far_1", "lat": 45.0, "lon": -120.0, "alt": 10000.0} # > 1000 km away
    ]
    anomalies = engine.evaluate_quake_proximity(quake, tracked_entities)
    assert len(anomalies) == 1
    assert anomalies[0]["entity_id"] == "asset_near_1"
    assert anomalies[0]["severity"] == "CRITICAL"
    assert anomalies[0]["meta"]["distance_km"] < 50.0
