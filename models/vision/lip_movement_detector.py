"""
Lip Movement Detector
Detects micro lip movements (whispering) using facial landmarks.
"""

import numpy as np
import cv2
import base64
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# MediaPipe face mesh lip landmark indices
UPPER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]
LOWER_LIP = [146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 61]
INNER_UPPER_LIP = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
INNER_LOWER_LIP = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]


class LipMovementDetector:
    """Detects micro lip movements indicating whispering."""

    def __init__(self):
        self._face_mesh = None
        self.lip_aperture_history = []
        self.max_history = 60  # ~2 seconds at 30fps
        self.whisper_threshold = 0.015  # Lip aperture threshold

    def _get_face_mesh(self):
        if self._face_mesh is None:
            try:
                import mediapipe as mp
                self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
            except ImportError:
                return None
        return self._face_mesh

    def analyze(self, frame_base64: str) -> Dict[str, Any]:
        """Analyze frame for lip movement anomalies."""
        anomaly_score = 0.0
        details = {}

        try:
            frame_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {"anomaly_score": 0.0, "confidence": 0.3, "details": {"synthetic": True}}

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            face_mesh = self._get_face_mesh()
            if face_mesh is None:
                return {"anomaly_score": 0.0, "confidence": 0.2, "details": {"mediapipe_unavailable": True}}

            results = face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]

                # Calculate lip aperture ratio
                inner_upper = self._get_landmark_points(landmarks, INNER_UPPER_LIP, w, h)
                inner_lower = self._get_landmark_points(landmarks, INNER_LOWER_LIP, w, h)

                # Vertical distance between inner lips
                upper_center = np.mean(inner_upper, axis=0)
                lower_center = np.mean(inner_lower, axis=0)
                lip_aperture = np.linalg.norm(upper_center - lower_center) / h

                self.lip_aperture_history.append(lip_aperture)
                if len(self.lip_aperture_history) > self.max_history:
                    self.lip_aperture_history.pop(0)

                details["lip_aperture"] = round(float(lip_aperture), 4)

                # Detect micro movements (whispering pattern)
                if len(self.lip_aperture_history) >= 10:
                    recent = self.lip_aperture_history[-10:]
                    aperture_variance = float(np.var(recent))
                    aperture_mean = float(np.mean(recent))
                    
                    # Whispering: small but rhythmic lip movements
                    if aperture_variance > 0.00001 and aperture_mean < 0.04:
                        # Small opening with variation = potential whisper
                        whisper_score = min(aperture_variance * 10000, 1.0)
                        anomaly_score = whisper_score * 0.8
                        details["whisper_detected"] = True
                        details["movement_variance"] = round(aperture_variance, 6)

                    # Speaking: larger mouth opening
                    if aperture_mean > 0.05:
                        anomaly_score = max(anomaly_score, 0.6)
                        details["speaking_detected"] = True

                details["face_detected"] = True
            else:
                details["face_detected"] = False

        except Exception as e:
            logger.debug(f"Lip detection error: {e}")

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.7 if details.get("face_detected") else 0.2,
            "details": details
        }

    def _get_landmark_points(self, landmarks, indices, w, h) -> np.ndarray:
        return np.array([
            [landmarks.landmark[i].x * w, landmarks.landmark[i].y * h]
            for i in indices
        ])
