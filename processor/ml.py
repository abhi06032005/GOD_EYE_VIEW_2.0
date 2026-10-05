"""
SentinelAI Machine Learning Anomaly Detection (Isolation Forest)
Features engineered: [speed, acceleration, vertical_rate, heading_change_rate]
"""
import os
import joblib
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("SentinelML")

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

class MLAnomalyDetector:
    def __init__(self, contamination: float = 0.02):
        self.contamination = contamination
        self.models: Dict[str, IsolationForest] = {}
        self.prev_states: Dict[str, Dict[str, Any]] = {}
        self._load_or_init_models()

    def _model_path(self, entity_type: str) -> str:
        return os.path.join(MODELS_DIR, f"iforest_{entity_type}.joblib")

    def _load_or_init_models(self):
        for etype in ["flight", "ship"]:
            path = self._model_path(etype)
            if os.path.exists(path):
                try:
                    loaded_clf = joblib.load(path)
                    loaded_clf.n_jobs = 1
                    self.models[etype] = loaded_clf
                    logger.info(f"[SentinelML] Loaded trained IsolationForest for {etype} from {path}")
                    continue
                except Exception as e:
                    logger.warning(f"[SentinelML] Could not load model from {path}: {e}")

            # Initialize baseline IsolationForest
            clf = IsolationForest(
                n_estimators=100,
                contamination=self.contamination,
                random_state=42,
                n_jobs=1
            )
            # Seed with baseline synthetic standard distributions so it is immediately operational
            if etype == "flight":
                # [speed m/s, accel m/s^2, vert_rate m/s, heading_rate deg/s]
                speeds = np.random.normal(220, 40, (1000, 1))
                accels = np.random.normal(0, 0.5, (1000, 1))
                verts = np.random.normal(0, 3.0, (1000, 1))
                hrates = np.random.normal(0, 1.0, (1000, 1))
            else: # ship
                # [speed kts, accel kts/s, 0.0, heading_rate deg/s]
                speeds = np.random.normal(12, 3, (1000, 1))
                accels = np.random.normal(0, 0.1, (1000, 1))
                verts = np.zeros((1000, 1))
                hrates = np.random.normal(0, 0.5, (1000, 1))

            X_init = np.hstack([speeds, accels, verts, hrates])
            clf.fit(X_init)
            self.models[etype] = clf
            try:
                joblib.dump(clf, path)
            except Exception as e:
                logger.warning(f"Could not save model to {path}: {e}")

    def extract_features(self, rec: Dict[str, Any], entity_type: str) -> Optional[np.ndarray]:
        entity_id = rec["entity_id"]
        curr_speed = float(rec.get("speed", 0.0))
        curr_heading = float(rec.get("heading", 0.0))
        curr_ts = float(rec.get("ts", 0.0))
        meta = rec.get("meta", {})
        vert_rate = float(meta.get("vertical_rate", 0.0))

        if entity_type == "flight" and rec.get("source") != "opensky":
            # Convert adsb.lol units to match OpenSky if needed
            vert_rate = vert_rate / 196.85 # ft/min -> m/s

        accel = 0.0
        heading_rate = 0.0

        if entity_id in self.prev_states:
            prev = self.prev_states[entity_id]
            dt = curr_ts - prev["ts"]
            if 0 < dt < 120:
                accel = (curr_speed - prev["speed"]) / dt
                d_heading = abs(curr_heading - prev["heading"])
                if d_heading > 180:
                    d_heading = 360 - d_heading
                heading_rate = d_heading / dt

        self.prev_states[entity_id] = {
            "speed": curr_speed,
            "heading": curr_heading,
            "ts": curr_ts
        }

        return np.array([[curr_speed, accel, vert_rate, heading_rate]])

    def predict(self, rec: Dict[str, Any], entity_type: str) -> Optional[Dict[str, Any]]:
        if entity_type not in self.models:
            return None

        feats = self.extract_features(rec, entity_type)
        if feats is None:
            return None

        clf = self.models[entity_type]
        pred = clf.predict(feats)[0] # -1 = anomaly, 1 = normal
        score = clf.score_samples(feats)[0] # lower means more abnormal

        if pred == -1:
            speed, accel, vert, h_rate = feats[0]
            severity = "HIGH" if score < -0.65 else "MEDIUM"
            return {
                "id": f"anom_ml_{rec['entity_id']}_{int(rec.get('ts', 0))}",
                "entity_id": rec["entity_id"],
                "entity_type": entity_type,
                "rule_name": "isolation_forest_kinematic_outlier",
                "severity": severity,
                "description": f"ML Anomaly (Isolation Forest, score={score:.3f}): Multi-axis kinematic deviation [spd={speed:.1f}, acc={accel:.2f}, vr={vert:.1f}, hr={h_rate:.2f}]",
                "lat": rec["lat"],
                "lon": rec["lon"],
                "alt": rec.get("alt", 0.0),
                "ts": rec.get("ts", 0.0),
                "meta": {
                    "ml_score": float(score),
                    "features": {"speed": float(speed), "accel": float(accel), "vert_rate": float(vert), "heading_rate": float(h_rate)}
                }
            }
        return None
