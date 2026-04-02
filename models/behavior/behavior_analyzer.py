"""
Behavior Analyzer (Orchestrator)
Combines typing, mouse, and clipboard analysis into unified behavior anomaly score.
"""

import logging
from typing import Dict, Any, Optional, List

from backend.schemas import TypingProfile, TypingCalibrationData
from models.behavior.typing_analyzer import TypingAnalyzer
from models.behavior.mouse_analyzer import MouseAnalyzer
from models.behavior.clipboard_detector import ClipboardDetector

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """
    Orchestrates behavioral biometrics analysis.
    
    Sub-scores weighted as:
        typing: 0.50
        mouse:  0.25
        clipboard: 0.25
    """

    def __init__(self):
        self.typing_analyzer = TypingAnalyzer()
        self.mouse_analyzer = MouseAnalyzer()
        self.clipboard_detector = ClipboardDetector()
        
        self.weights = {
            "typing": 0.50,
            "mouse": 0.25,
            "clipboard": 0.25
        }

    def analyze_keystrokes(
        self,
        keystrokes: List[TypingCalibrationData],
        baseline_profile: Optional[TypingProfile] = None
    ) -> Dict[str, Any]:
        """Analyze keystroke data for all behavioral anomalies."""
        
        # Typing rhythm analysis
        typing_result = self.typing_analyzer.analyze_keystrokes(keystrokes, baseline_profile)
        
        # Clipboard analysis (from keystroke patterns)
        ks_dicts = [{"key": k.key, "timestamp": k.key_down_time} for k in keystrokes]
        clipboard_result = self.clipboard_detector.analyze_keystrokes(ks_dicts)
        
        # Combined score (mouse not available in keystroke-only mode)
        combined_score = (
            0.65 * typing_result["anomaly_score"] +
            0.35 * clipboard_result["anomaly_score"]
        )
        
        combined_confidence = (
            0.65 * typing_result["confidence"] +
            0.35 * clipboard_result["confidence"]
        )

        details = {
            "typing": {
                "score": typing_result["anomaly_score"],
                "details": typing_result["details"]
            },
            "clipboard": {
                "score": clipboard_result["anomaly_score"],
                "details": clipboard_result["details"]
            }
        }

        return {
            "anomaly_score": round(min(combined_score, 1.0), 4),
            "confidence": round(combined_confidence, 4),
            "details": details
        }

    def analyze_full(
        self,
        keystrokes: List[TypingCalibrationData],
        mouse_movements: List[Dict[str, float]],
        baseline_profile: Optional[TypingProfile] = None
    ) -> Dict[str, Any]:
        """Full behavioral analysis including mouse data."""
        
        typing_result = self.typing_analyzer.analyze_keystrokes(keystrokes, baseline_profile)
        mouse_result = self.mouse_analyzer.analyze_movements(mouse_movements)
        ks_dicts = [{"key": k.key, "timestamp": k.key_down_time} for k in keystrokes]
        clipboard_result = self.clipboard_detector.analyze_keystrokes(ks_dicts)

        combined_score = (
            self.weights["typing"] * typing_result["anomaly_score"] +
            self.weights["mouse"] * mouse_result["anomaly_score"] +
            self.weights["clipboard"] * clipboard_result["anomaly_score"]
        )

        details = {
            "typing": {"score": typing_result["anomaly_score"], "details": typing_result["details"]},
            "mouse": {"score": mouse_result["anomaly_score"], "details": mouse_result["details"]},
            "clipboard": {"score": clipboard_result["anomaly_score"], "details": clipboard_result["details"]}
        }

        return {
            "anomaly_score": round(min(combined_score, 1.0), 4),
            "confidence": round(
                self.weights["typing"] * typing_result["confidence"] +
                self.weights["mouse"] * mouse_result["confidence"] +
                self.weights["clipboard"] * clipboard_result["confidence"],
                4
            ),
            "details": details
        }
