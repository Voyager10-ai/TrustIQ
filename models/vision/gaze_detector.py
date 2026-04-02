"""
Gaze Detector Module
Detects gaze direction deviations using MediaPipe Face Mesh landmarks.
"""

import numpy as np
import cv2
import base64
import logging
from typing import Dict, Any, Optional

from backend.schemas import GazeProfile

logger = logging.getLogger(__name__)

LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


class GazeDetector:
    """Detects gaze anomalies by comparing to baseline."""

    def __init__(self):
        self._face_mesh = None
        self.recent_gazes = []
        self.downward_count = 0
        self.frame_count = 0
        self.max_history = 30  # 30-frame sliding window

    def _get_face_mesh(self):
        if self._face_mesh is None:
            try:
                import mediapipe as mp
                self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=2,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except ImportError:
                return None
        return self._face_mesh

    def analyze(self, frame_base64: str, baseline: Optional[GazeProfile] = None) -> Dict[str, Any]:
        """Analyze a frame for gaze anomalies."""
        self.frame_count += 1
        anomaly_score = 0.0
        details = {}

        try:
            frame_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return self._synthetic_analysis(baseline)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            face_mesh = self._get_face_mesh()
            if face_mesh is None:
                return self._synthetic_analysis(baseline)

            results = face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                
                # Get gaze direction
                left_iris = self._landmark_center(landmarks, LEFT_IRIS, w, h)
                right_iris = self._landmark_center(landmarks, RIGHT_IRIS, w, h)
                left_eye = self._landmark_center(landmarks, LEFT_EYE, w, h)
                right_eye = self._landmark_center(landmarks, RIGHT_EYE, w, h)

                gaze = ((left_iris - left_eye) + (right_iris - right_eye)) / (2.0 * max(w, 1))
                self.recent_gazes.append(gaze)
                if len(self.recent_gazes) > self.max_history:
                    self.recent_gazes.pop(0)

                # Check for downward glance (phone)
                if gaze[1] > 0.025:
                    self.downward_count += 1
                    details["downward_glance"] = True

                # Compute deviation from baseline
                if baseline and baseline.mean_direction:
                    baseline_mean = np.array(baseline.mean_direction)
                    baseline_var = np.array(baseline.variance) + 1e-6
                    deviation = np.abs(gaze - baseline_mean) / np.sqrt(baseline_var)
                    max_deviation = float(np.max(deviation))
                    anomaly_score = min(max_deviation / 3.0, 1.0)  # Normalize
                    details["deviation_sigma"] = round(max_deviation, 2)

                # Downward glance frequency anomaly
                glance_freq = self.downward_count / max(self.frame_count, 1)
                if baseline and baseline.downward_glance_frequency > 0:
                    freq_ratio = glance_freq / max(baseline.downward_glance_frequency, 0.01)
                    if freq_ratio > 2.0:
                        anomaly_score = max(anomaly_score, min((freq_ratio - 1) / 3.0, 1.0))
                        details["excessive_downward_glances"] = True

                details["gaze_direction"] = gaze.tolist()
                details["face_detected"] = True
            else:
                details["face_detected"] = False
                anomaly_score = 0.3  # Face not detected is mild anomaly
                details["no_face"] = True

        except Exception as e:
            logger.debug(f"Gaze analysis error: {e}")
            return self._synthetic_analysis(baseline)

        return {
            "anomaly_score": round(anomaly_score, 4),
            "confidence": 0.8 if details.get("face_detected") else 0.3,
            "details": details
        }

    def _synthetic_analysis(self, baseline: Optional[GazeProfile] = None) -> Dict[str, Any]:
        """Generate synthetic analysis result."""
        score = np.random.uniform(0.0, 0.2)
        return {
            "anomaly_score": round(score, 4),
            "confidence": 0.3,
            "details": {"synthetic": True, "face_detected": False}
        }

    def _landmark_center(self, landmarks, indices, w, h) -> np.ndarray:
        points = [[landmarks.landmark[i].x * w, landmarks.landmark[i].y * h] for i in indices]
        return np.mean(points, axis=0)
