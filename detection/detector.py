"""
detection/detector.py

Takes a single video frame in, returns detected parking space states out.
Knows nothing about where the frame came from (webcam, file, RTSP, or a
downloaded demo video) - that's each site's video_source, read by
server/stream_worker.py.

The trained model classifies each detected space directly as
space_empty/space_occupied, so no bay-polygon tracing or overlap-matching
is needed - each detection IS a space, reported as-is. This is what makes
the system source-agnostic: it works on any parking footage, and adding a
new site (server/site_service.py) never requires re-tracing anything.

MOCK MODE:
If no trained weights exist yet at config.MODEL_PATH, this falls back to
generating a handful of random space states so the rest of the team can
build and test the server/map without waiting on the model.
"""

import os
import random

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

SPACE_CLASSES = {"space_empty", "space_occupied"}


class ParkingDetector:
    def __init__(self):
        self.mock_mode = not os.path.exists(config.MODEL_PATH)

        if self.mock_mode:
            print(f"[detector] No model found at {config.MODEL_PATH} - running in MOCK MODE.")
            self.model = None
        else:
            from ultralytics import YOLO
            self.model = YOLO(config.MODEL_PATH)
            print(f"[detector] Loaded YOLOv8 model from {config.MODEL_PATH}")

    def process_frame(self, frame):
        """
        frame: a single video frame (numpy array from OpenCV), or None in mock mode.
        Returns: list of {"bay_id": str, "occupied": bool, "confidence": float}
        bay_id here is just a per-frame positional label (space_1, space_2, ...),
        ordered left-to-right by detection x-position - not a persistent
        identity across frames, since counts are aggregated per site rather
        than tracked per named bay (see server/site_service.py).
        """
        if self.mock_mode or frame is None:
            return [
                {
                    "bay_id": f"space_{i}",
                    "occupied": random.random() > 0.5,
                    "confidence": round(random.uniform(0.6, 0.99), 2),
                }
                for i in range(1, 9)
            ]

        detections = self._run_inference(frame)
        detections.sort(key=lambda d: d["bbox"][0])  # left-to-right, for stable-ish IDs within one run

        return [
            {
                "bay_id": f"space_{i}",
                "occupied": d["class"] == "space_occupied",
                "confidence": round(d["confidence"], 2),
            }
            for i, d in enumerate(detections, start=1)
        ]

    def _run_inference(self, frame):
        """Runs YOLOv8 and returns only space_empty/space_occupied detections."""
        results = self.model.predict(frame, conf=config.CONFIDENCE_THRESHOLD, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                if cls_name not in SPACE_CLASSES:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "class": cls_name,
                    "confidence": confidence,
                })
        return detections