#!/usr/bin/env python3
"""
SentinelAI ML Training Script: Isolation Forest
Trains Isolation Forest models on real recorded replay trajectories (flights & ships).
Saves models to data/models/iforest_flight.joblib and data/models/iforest_ship.joblib.
"""
import os
import sys
import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY_DIR = os.path.join(BASE_DIR, "data", "replay")
MODELS_DIR = os.path.join(BASE_DIR, "data", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def extract_dataset_features(jsonl_path: str, entity_type: str) -> np.ndarray:
    if not os.path.exists(jsonl_path):
        print(f"Warning: {jsonl_path} not found. Generating baseline distribution.")
        if entity_type == "flight":
            return np.random.normal(loc=[220, 0, 0, 0], scale=[40, 0.5, 3.0, 1.0], size=(2000, 4))
        else:
            return np.random.normal(loc=[12, 0, 0, 0], scale=[3, 0.1, 0.01, 0.5], size=(2000, 4))

    entity_states = {}
    features = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            eid = rec["entity_id"]
            speed = float(rec.get("speed", 0.0))
            heading = float(rec.get("heading", 0.0))
            ts = float(rec.get("ts", 0.0))
            vert_rate = float(rec.get("meta", {}).get("vertical_rate", 0.0))

            accel = 0.0
            heading_rate = 0.0
            if eid in entity_states:
                prev = entity_states[eid]
                dt = ts - prev["ts"]
                if 0 < dt < 120:
                    accel = (speed - prev["speed"]) / dt
                    dh = abs(heading - prev["heading"])
                    if dh > 180:
                        dh = 360 - dh
                    heading_rate = dh / dt

            entity_states[eid] = {"speed": speed, "heading": heading, "ts": ts}
            features.append([speed, accel, vert_rate, heading_rate])

    X = np.array(features, dtype=np.float32)
    # Filter out NaNs or infs
    X = np.nan_to_num(X, nan=0.0, posinf=100.0, neginf=-100.0)
    return X

def train():
    print("[SentinelAI ML] Starting Isolation Forest training from replay data...")
    
    # 1. Flight Model
    flight_data_path = os.path.join(REPLAY_DIR, "flights.jsonl")
    X_flight = extract_dataset_features(flight_data_path, "flight")
    print(f"  Training flight model on {len(X_flight)} feature vectors...")
    clf_flight = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        random_state=42,
        n_jobs=-1
    )
    clf_flight.fit(X_flight)
    out_flight = os.path.join(MODELS_DIR, "iforest_flight.joblib")
    joblib.dump(clf_flight, out_flight)
    print(f"  Saved flight model to {out_flight}")

    # 2. Vessel Model
    ship_data_path = os.path.join(REPLAY_DIR, "ships.jsonl")
    X_ship = extract_dataset_features(ship_data_path, "ship")
    print(f"  Training maritime vessel model on {len(X_ship)} feature vectors...")
    clf_ship = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        random_state=42,
        n_jobs=-1
    )
    clf_ship.fit(X_ship)
    out_ship = os.path.join(MODELS_DIR, "iforest_ship.joblib")
    joblib.dump(clf_ship, out_ship)
    print(f"  Saved vessel model to {out_ship}")
    print("[SentinelAI ML] Training complete.")

if __name__ == "__main__":
    train()
