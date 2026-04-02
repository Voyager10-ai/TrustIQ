"""
Stylometry Analyzer (Orchestrator)
Combines writing style analysis and AI text detection.
"""

import logging
from typing import Dict, Any, Optional

from backend.schemas import WritingProfile
from models.stylometry.writing_analyzer import WritingAnalyzer
from models.stylometry.ai_text_detector import AITextDetector

logger = logging.getLogger(__name__)


class StylometryAnalyzer:
    """
    Orchestrates stylometric analysis.
    
    Sub-scores weighted as:
        writing_style: 0.55
        ai_detection:  0.45
    """

    def __init__(self):
        self.writing_analyzer = WritingAnalyzer()
        self.ai_detector = AITextDetector()
        
        self.weights = {
            "writing_style": 0.55,
            "ai_detection": 0.45
        }

    def analyze_text(
        self,
        text: str,
        baseline_profile: Optional[WritingProfile] = None
    ) -> Dict[str, Any]:
        """Analyze text through all stylometric modules."""
        
        writing_result = self.writing_analyzer.analyze(text, baseline_profile)
        ai_result = self.ai_detector.analyze(text)

        combined_score = (
            self.weights["writing_style"] * writing_result["anomaly_score"] +
            self.weights["ai_detection"] * ai_result["anomaly_score"]
        )

        combined_confidence = (
            self.weights["writing_style"] * writing_result["confidence"] +
            self.weights["ai_detection"] * ai_result["confidence"]
        )

        details = {
            "writing_style": {
                "score": writing_result["anomaly_score"],
                "details": writing_result["details"]
            },
            "ai_detection": {
                "score": ai_result["anomaly_score"],
                "details": ai_result["details"]
            },
            "weights": self.weights
        }

        return {
            "anomaly_score": round(min(combined_score, 1.0), 4),
            "confidence": round(combined_confidence, 4),
            "details": details
        }
