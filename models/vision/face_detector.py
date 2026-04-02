"""
Face & Object Detector Module
Detects multiple persons, objects (phones, books, laptops), and illumination changes.
"""

import numpy as np
import cv2
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects face-related anomalies and prohibited objects using MediaPipe & YOLO."""

    def __init__(self):
        self._face_detection = None
        self._yolo = None
        self.illumination_history = []
        self.max_history = 50

    def _get_mp_detector(self):
        if self._face_detection is None:
            try:
                import mediapipe as mp
                self._face_detection = mp.solutions.face_detection.FaceDetection(
                    model_selection=1,
                    min_detection_confidence=0.5
                )
            except ImportError:
                return None
        return self._face_detection

    def _get_yolo(self):
        if self._yolo is None:
            try:
                from ultralytics import YOLO
                # Load the lightest YOLO model to run efficiently on CPU
                self._yolo = YOLO('yolov8n.pt') 
            except Exception as e:
                logger.warning(f"Failed to load YOLO: {e}")
                return None
        return self._yolo

    def analyze(self, frame_base64: str) -> Dict[str, Any]:
        """Analyze frame for multiple faces, phones, watches, etc."""
        anomaly_score = 0.0
        details: Dict[str, Any] = {"objects": []}

        try:
            frame_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {"anomaly_score": 0.0, "confidence": 0.3, "details": {"synthetic": True}}

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_h, frame_w = frame.shape[:2]

            detected_objects = []

            # ─── 1. YOLO Object Detection ───
            yolo = self._get_yolo()
            # We care about: 67 (cell phone), 73 (laptop), 74 (mouse), 76 (keyboard), 77 (cell phone maybe? wait coco class for cell phone is 67), 63 (laptop is 73?, notebook is not there), 73 is laptop. 67 is cell phone, 72 is tv, 84 is book (coco 91-class uses 84 for book).
            # But the ultralytics 80-class COCO:
            # 67 is cell phone, 73 is book, 76 is keyboard. Let's just rely on YOLO's class names!
            if yolo:
                results = yolo(frame, verbose=False)
                for r in results:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        class_name = yolo.names[class_id]
                        conf = float(box.conf[0])
                        if conf < 0.3:
                            continue
                        
                        # Convert bounding box to relative coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        rel_box = {
                            "xmin": x1 / frame_w,
                            "ymin": y1 / frame_h,
                            "width": (x2 - x1) / frame_w,
                            "height": (y2 - y1) / frame_h
                        }

                        # Check for prohibited items or extra persons
                        if class_name in ['cell phone', 'remote', 'tv', 'laptop', 'tablet', 'book', 'clock']:
                            # Prohibited objects
                            detected_objects.append({
                                "label": class_name,
                                "box": rel_box,
                                "color": "text-red-400 border-red-500",
                                "bg": "bg-red-500/20"
                            })
                            anomaly_score = max(anomaly_score, 0.95)
                            details["prohibited_object_detected"] = True
                            details[f"detected_{class_name}"] = True

            # ─── 2. MediaPipe Face Detection ───
            detector = self._get_mp_detector()
            num_faces = 0
            if detector:
                mp_results = detector.process(frame_rgb)
                if mp_results.detections:
                    num_faces = len(mp_results.detections)
                    for i, detection in enumerate(mp_results.detections):
                        bboxC = detection.location_data.relative_bounding_box
                        rect = {
                            "xmin": bboxC.xmin, "ymin": bboxC.ymin,
                            "width": bboxC.width, "height": bboxC.height
                        }
                        
                        # First face is green, additional faces are red
                        is_primary = (i == 0)
                        detected_objects.append({
                            "label": "Student Face" if is_primary else "Extra Person",
                            "box": rect,
                            "color": "text-emerald-400 border-emerald-500" if is_primary else "text-amber-400 border-amber-500",
                            "bg": "bg-emerald-500/20" if is_primary else "bg-amber-500/20"
                        })
                        
                        if is_primary:
                            details["face_box"] = rect # Kept for backward compatibility

            details["face_count"] = num_faces

            if num_faces == 0:
                anomaly_score = max(anomaly_score, 0.4)
                details["no_face_detected"] = True
            elif num_faces > 1:
                anomaly_score = max(anomaly_score, 0.9)
                details["multiple_faces"] = True
                details["second_person_detected"] = True

            details["objects"] = detected_objects

            # ─── 3. Illumination change detection ───
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            current_brightness = float(np.mean(gray))
            self.illumination_history.append(current_brightness)
            if len(self.illumination_history) > self.max_history:
                self.illumination_history.pop(0)

            if len(self.illumination_history) > 5:
                avg_brightness = np.mean(self.illumination_history[:-1])
                brightness_change = abs(current_brightness - avg_brightness) / max(avg_brightness, 1)
                if brightness_change > 0.3:
                    illumination_anomaly = min(brightness_change, 1.0)
                    anomaly_score = max(anomaly_score, illumination_anomaly * 0.6)
                    details["illumination_change"] = round(brightness_change, 3)
                    details["brightness_anomaly"] = True

            details["current_brightness"] = round(current_brightness, 1)

        except Exception as e:
            logger.debug(f"Face/Object detection error: {e}")
            return {"anomaly_score": 0.0, "confidence": 0.3, "details": {"error": str(e)}}

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.85,
            "details": details
        }
