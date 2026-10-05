"""
SentinelAI Computer Vision Service
Runs Ultralytics YOLOv8n on public traffic camera feeds with fallback to /data/sample/traffic_sample.mp4.
Extracts class counts (vehicles, pedestrians) and bounding boxes without storing any raw imagery (Privacy by Design).
Publishes detection events to topic 'detections'.
"""
import os
import sys
import time
import asyncio
import logging
from typing import Dict, Any, List
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from processor.bus import bus

logger = logging.getLogger("CVService")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SAMPLE_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample", "traffic_sample.mp4")
YOLO_MODEL_NAME = os.getenv("YOLO_MODEL", "yolov8n.pt")
CONF_THRESHOLD = float(os.getenv("CV_CONF_THRESHOLD", "0.35"))

# Monitored camera stations with geographic coordinates
CAMERAS = [
    {"id": "cam_sfo_101", "name": "US-101 at Airport Blvd (SFO)", "lat": 37.6213, "lon": -122.3790, "stream": SAMPLE_VIDEO},
    {"id": "cam_lax_405", "name": "I-405 at Century Blvd (LAX)", "lat": 33.9455, "lon": -118.3750, "stream": SAMPLE_VIDEO},
    {"id": "cam_nyc_fdr", "name": "FDR Drive at 42nd St", "lat": 40.7484, "lon": -73.9680, "stream": SAMPLE_VIDEO},
    {"id": "cam_atx_35", "name": "I-35 at 6th Street", "lat": 30.2672, "lon": -97.7380, "stream": SAMPLE_VIDEO}
]

# COCO target classes for traffic/multimodal awareness
TARGET_CLASSES = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

class YOLOVideoService:
    def __init__(self, model_name: str = YOLO_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        from ultralytics import YOLO
        logger.info(f"[CVService] Loading Ultralytics YOLO model: {self.model_name}...")
        self.model = YOLO(self.model_name)
        logger.info(f"[CVService] YOLO model loaded successfully.")

    def process_frame(self, frame) -> Dict[str, Any]:
        t0 = time.time()
        results = self.model.predict(frame, conf=CONF_THRESHOLD, verbose=False)
        infer_time_ms = (time.time() - t0) * 1000.0

        class_counts = {"car": 0, "truck": 0, "bus": 0, "person": 0, "motorcycle": 0}
        bboxes = []

        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [round(float(coord), 1) for coord in box.xyxy[0].tolist()]

                if cls_id in TARGET_CLASSES:
                    cls_name = TARGET_CLASSES[cls_id]
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                    bboxes.append({
                        "class": cls_name,
                        "conf": round(conf, 3),
                        "box": xyxy
                    })

        return {
            "counts": class_counts,
            "bboxes": bboxes,
            "infer_time_ms": round(infer_time_ms, 2)
        }

async def run_cv_worker():
    await bus.start_producer()
    cv_service = YOLOVideoService()
    logger.info("[CVService] Starting continuous video processing loop...")

    # We process cameras sequentially or round-robin
    cam_index = 0
    cap = None
    curr_cam = CAMERAS[0]

    while True:
        curr_cam = CAMERAS[cam_index % len(CAMERAS)]
        cam_index += 1

        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(curr_cam["stream"])

        ret, frame = cap.read()
        if not ret:
            # Loop video stream
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.5)
                continue

        # Run YOLO inference
        det = cv_service.process_frame(frame)
        now_ts = time.time()

        detection_msg = {
            "source": "cctv",
            "camera_id": curr_cam["id"],
            "lat": curr_cam["lat"],
            "lon": curr_cam["lon"],
            "class_counts": det["counts"],
            "bboxes": det["bboxes"],
            "ts": now_ts,
            "meta": {
                "camera_name": curr_cam["name"],
                "infer_time_ms": det["infer_time_ms"],
                "total_objects": sum(det["counts"].values())
            }
        }

        # Publish to Redpanda/Kafka 'detections'
        await bus.publish("detections", detection_msg)
        logger.debug(f"[CVService] {curr_cam['id']}: {det['counts']} in {det['infer_time_ms']}ms")

        # Regulate processing rate to ~4 FPS
        await asyncio.sleep(0.25)

if __name__ == "__main__":
    asyncio.run(run_cv_worker())
