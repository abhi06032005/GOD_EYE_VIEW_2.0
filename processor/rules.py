"""
SentinelAI Deterministic & Heuristic Anomaly Rules Engine
Detects emergency squawks, descent spikes, drifting ships, geofence breaches,
high-magnitude earthquake proximity, and ADS-B cyber spoofing.
"""
import math
import time
from typing import Dict, Any, List, Optional, Tuple

# Configurable Restricted Geofences [min_lat, max_lat, min_lon, max_lon, name]
RESTRICTED_GEOFENCES = [
    {"name": "Restricted Airspace R-2508 (Mojave/Edwards)", "min_lat": 35.0, "max_lat": 36.2, "min_lon": -118.0, "max_lon": -116.5, "type": "aero"},
    {"name": "Gibraltar Naval Exclusion Zone", "min_lat": 35.85, "max_lat": 36.15, "min_lon": -5.6, "max_lon": -5.2, "type": "maritime"},
    {"name": "Dover Strait Traffic Separation Scheme Zone Alpha", "min_lat": 51.0, "max_lat": 51.2, "min_lon": 1.3, "max_lon": 1.6, "type": "maritime"}
]

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class AnomalyRuleEngine:
    def __init__(self):
        # State tracking for kinematic consistency (entity_id -> previous state)
        self.entity_history: Dict[str, Dict[str, Any]] = {}
        # Transponder squawk codes of interest
        self.emergency_squawks = {
            "7500": ("HIJACK", "CRITICAL", "Unlawful Interference / Hijacking transponder squawk 7500 detected"),
            "7600": ("COMM_LOSS", "HIGH", "Radio Communication Failure transponder squawk 7600 detected"),
            "7700": ("GENERAL_EMERGENCY", "CRITICAL", "General In-Flight Emergency transponder squawk 7700 declared")
        }

    def evaluate_flight(self, rec: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []
        entity_id = rec["entity_id"]
        lat = rec["lat"]
        lon = rec["lon"]
        alt = rec.get("alt", 0.0)
        speed = rec.get("speed", 0.0)
        ts = rec.get("ts", time.time())
        meta = rec.get("meta", {})
        squawk = str(meta.get("squawk", "")).strip()
        vert_rate = float(meta.get("vertical_rate", 0.0))

        # Rule 1: Emergency Transponder Squawk
        if squawk in self.emergency_squawks:
            code, severity, desc = self.emergency_squawks[squawk]
            anomalies.append({
                "id": f"anom_sqk_{entity_id}_{int(ts)}",
                "entity_id": entity_id,
                "entity_type": "flight",
                "rule_name": f"transponder_{code.lower()}",
                "severity": severity,
                "description": desc,
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "ts": ts,
                "meta": {"squawk": squawk, "callsign": meta.get("callsign")}
            })

        # Rule 2: Sudden Altitude Descent (> 4000 ft/min ~= 20.3 m/s)
        # Note: OpenSky vertical rate is m/s; adsb.lol baro_rate is ft/min
        is_high_descent = False
        if rec.get("source") == "opensky" and vert_rate < -20.3:
            is_high_descent = True
            descent_fpm = abs(vert_rate) * 196.85
        elif vert_rate < -4000:
            is_high_descent = True
            descent_fpm = abs(vert_rate)

        if is_high_descent:
            anomalies.append({
                "id": f"anom_desc_{entity_id}_{int(ts)}",
                "entity_id": entity_id,
                "entity_type": "flight",
                "rule_name": "rapid_descent",
                "severity": "HIGH",
                "description": f"Rapid descent alert: vertical rate {descent_fpm:.0f} ft/min exceeds safety envelope (>4000 ft/min)",
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "ts": ts,
                "meta": {"vertical_rate_fpm": descent_fpm}
            })

        # Rule 3: Extreme Speed Outlier
        # Typical civilian aircraft rarely exceed 350 m/s (~680 knots) ground speed
        speed_mps = speed if rec.get("source") == "opensky" else speed * 0.514444
        if speed_mps > 450: # > 1620 km/h (Supersonic or sensor error)
            anomalies.append({
                "id": f"anom_spd_{entity_id}_{int(ts)}",
                "entity_id": entity_id,
                "entity_type": "flight",
                "rule_name": "extreme_speed_outlier",
                "severity": "MEDIUM",
                "description": f"Kinematic speed outlier: observed velocity {speed_mps * 3.6:.0f} km/h exceeds civil flight envelope",
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "ts": ts,
                "meta": {"speed_kmh": speed_mps * 3.6}
            })

        # Rule 4: Geofence Breach
        for gf in RESTRICTED_GEOFENCES:
            if gf["type"] == "aero":
                if gf["min_lat"] <= lat <= gf["max_lat"] and gf["min_lon"] <= lon <= gf["max_lon"]:
                    anomalies.append({
                        "id": f"anom_gf_{entity_id}_{int(ts)}",
                        "entity_id": entity_id,
                        "entity_type": "flight",
                        "rule_name": "geofence_breach",
                        "severity": "HIGH",
                        "description": f"Unauthorized entry into restricted geofence: {gf['name']}",
                        "lat": lat,
                        "lon": lon,
                        "alt": alt,
                        "ts": ts,
                        "meta": {"geofence": gf["name"]}
                    })

        # Rule 5: Cybersecurity ADS-B Spoofing & Kinematic Inconsistency
        if entity_id in self.entity_history:
            prev = self.entity_history[entity_id]
            dt = ts - prev["ts"]
            if 0 < dt < 60: # Within 1 minute
                dist_km = haversine_km(prev["lat"], prev["lon"], lat, lon)
                calc_speed_kmh = (dist_km / (dt / 3600.0))
                # If calculated velocity exceeds 2000 km/h or instantaneous teleportation (>50km in <15s)
                if calc_speed_kmh > 2000 or (dist_km > 50 and dt < 15):
                    anomalies.append({
                        "id": f"anom_spk_{entity_id}_{int(ts)}",
                        "entity_id": entity_id,
                        "entity_type": "flight",
                        "rule_name": "possible_spoofing",
                        "severity": "CRITICAL",
                        "description": f"Cyber Threat / ADS-B Spoofing detected: Impossible kinematic jump of {dist_km:.1f} km in {dt:.1f}s (apparent speed {calc_speed_kmh:.0f} km/h)",
                        "lat": lat,
                        "lon": lon,
                        "alt": alt,
                        "ts": ts,
                        "meta": {"jump_km": dist_km, "dt_sec": dt, "apparent_speed_kmh": calc_speed_kmh}
                    })

        # Update entity history state
        self.entity_history[entity_id] = {
            "lat": lat, "lon": lon, "alt": alt, "speed": speed, "ts": ts
        }

        return anomalies

    def evaluate_ship(self, rec: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []
        entity_id = rec["entity_id"]
        lat = rec["lat"]
        lon = rec["lon"]
        speed = rec.get("speed", 0.0)
        ts = rec.get("ts", time.time())
        meta = rec.get("meta", {})

        # Rule 1: Drifting in Maritime Shipping Lane
        # Speed near zero (< 0.8 knots) while in restricted/corridor channel
        if speed < 0.8 and ("Under way" in str(meta.get("status", "")) or "Strait" in str(meta.get("destination", ""))):
            anomalies.append({
                "id": f"anom_drift_{entity_id}_{int(ts)}",
                "entity_id": entity_id,
                "entity_type": "ship",
                "rule_name": "drifting_in_corridor",
                "severity": "MEDIUM",
                "description": f"Maritime Hazard: Vessel {meta.get('shipname', entity_id)} dead in water ({speed:.1f} kts) inside designated navigation corridor",
                "lat": lat,
                "lon": lon,
                "alt": 0.0,
                "ts": ts,
                "meta": {"speed_knots": speed, "shipname": meta.get("shipname")}
            })

        # Rule 2: Maritime Geofence Breach
        for gf in RESTRICTED_GEOFENCES:
            if gf["type"] == "maritime":
                if gf["min_lat"] <= lat <= gf["max_lat"] and gf["min_lon"] <= lon <= gf["max_lon"]:
                    anomalies.append({
                        "id": f"anom_mgf_{entity_id}_{int(ts)}",
                        "entity_id": entity_id,
                        "entity_type": "ship",
                        "rule_name": "maritime_exclusion_breach",
                        "severity": "HIGH",
                        "description": f"Naval geofence breach: vessel entered restricted zone {gf['name']}",
                        "lat": lat,
                        "lon": lon,
                        "alt": 0.0,
                        "ts": ts,
                        "meta": {"geofence": gf["name"]}
                    })

        return anomalies

    def check_ais_dark(self, entity_id: str, last_ts: float, current_ts: float, threshold_sec: float = 600.0) -> Optional[Dict[str, Any]]:
        """Flags vessels whose AIS transponder has gone dark (silent for > threshold_sec)."""
        dt = current_ts - last_ts
        if dt >= threshold_sec:
            return {
                "id": f"anom_dark_{entity_id}_{int(current_ts)}",
                "entity_id": entity_id,
                "entity_type": "ship",
                "rule_name": "ais_transponder_dark",
                "severity": "HIGH",
                "description": f"Maritime Security Alert: AIS signal silent for {dt / 60.0:.1f} minutes (exceeds {threshold_sec / 60.0:.0f} min dark threshold)",
                "lat": 0.0,
                "lon": 0.0,
                "alt": 0.0,
                "ts": current_ts,
                "meta": {"silent_seconds": dt, "dark_threshold_sec": threshold_sec}
            }
        return None

    def evaluate_quake_proximity(self, quake: Dict[str, Any], tracked_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies = []
        mag = float(quake.get("meta", {}).get("mag") or 0.0)
        q_lat = quake["lat"]
        q_lon = quake["lon"]
        ts = quake.get("ts", time.time())
        place = quake.get("meta", {}).get("place", "Seismic Zone")

        # Quake M >= 4.5
        if mag >= 4.5:
            for ent in tracked_entities:
                dist = haversine_km(q_lat, q_lon, ent["lat"], ent["lon"])
                if dist < 150.0: # within 150 km of tracked asset
                    anomalies.append({
                        "id": f"anom_qk_{quake['entity_id']}_{ent['entity_id']}",
                        "entity_id": ent["entity_id"],
                        "entity_type": "multimodal_hazard",
                        "rule_name": "significant_quake_proximity",
                        "severity": "CRITICAL" if mag >= 6.0 else "HIGH",
                        "description": f"Seismic Hazard Alert: M{mag:.1f} earthquake ({place}) occurred within {dist:.1f} km of tracked entity {ent['entity_id']}",
                        "lat": ent["lat"],
                        "lon": ent["lon"],
                        "alt": ent.get("alt", 0.0),
                        "ts": ts,
                        "meta": {"magnitude": mag, "distance_km": dist, "quake_id": quake["entity_id"]}
                    })

        return anomalies
