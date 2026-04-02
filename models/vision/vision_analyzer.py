"""
Vision Analyzer (Orchestrator)
Combines gaze, face, and lip detection into a unified vision anomaly score.
"""

import logging
from typing import Dict, Any, Optional

from backend.schemas import GazeProfile
from models.vision.gaze_detector import GazeDetector
from models.vision.face_detector import FaceDetector
from models.vision.lip_movement_detector import LipMovementDetector

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Orchestrates all vision sub-modules and produces a combined anomaly score.
    
    Sub-scores weighted as:
        gaze: 0.40
        face: 0.35
        lip:  0.25
    """

    def __init__(self):
        self.gaze_detector = GazeDetector()
        self.face_detector = FaceDetector()
        self.lip_detector = LipMovementDetector()
        
        # Sub-module weights
        self.weights = {
            "gaze": 0.40,
            "face": 0.35,
            "lip": 0.25
        }

    def analyze_frame(
        self,
        frame_base64: str,
        baseline_profile: Optional[GazeProfile] = None
    ) -> Dict[str, Any]:
        """
        Analyze a video frame through all vision sub-modules.
        
        Returns:
            dict with anomaly_score (0-1), confidence, and per-module details
        """
        # Run all detectors
        gaze_result = self.gaze_detector.analyze(frame_base64, baseline_profile)
        face_result = self.face_detector.analyze(frame_base64)
        lip_result = self.lip_detector.analyze(frame_base64)

        # Weighted combination
        combined_score = (
            self.weights["gaze"] * gaze_result["anomaly_score"] +
            self.weights["face"] * face_result["anomaly_score"] +
            self.weights["lip"] * lip_result["anomaly_score"]
        )

        # Weighted confidence
        combined_confidence = (
            self.weights["gaze"] * gaze_result["confidence"] +
            self.weights["face"] * face_result["confidence"] +
            self.weights["lip"] * lip_result["confidence"]
        )

        # Critical override: multi-face always escalates
        if face_result["details"].get("multiple_faces"):
            combined_score = max(combined_score, 0.85)

        details = {
            "gaze": {
                "score": gaze_result["anomaly_score"],
                "details": gaze_result["details"]
            },
            "face": {
                "score": face_result["anomaly_score"],
                "details": face_result["details"]
            },
            "lip": {
                "score": lip_result["anomaly_score"],
                "details": lip_result["details"]
            },
            "weights": self.weights
        }

        return {
            "anomaly_score": round(min(combined_score, 1.0), 4),
            "confidence": round(combined_confidence, 4),
            "details": details
        }
