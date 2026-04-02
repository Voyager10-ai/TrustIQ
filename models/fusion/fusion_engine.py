"""
Multi-Modal Fusion Engine
Combines all module anomaly scores into a final risk score with explainability.
"""

import numpy as np
from typing import Dict, Any, Optional, List
from collections import deque
import time
import logging

from backend.config import settings
from backend.schemas import ModuleScore, RiskScore, RiskLevel, ModuleType

logger = logging.getLogger(__name__)


class FusionEngine:
    """
    Combines anomaly scores from all detection modules into a unified risk score.
    
    Formula:
        Final Risk = 0.25*Vision + 0.20*Behavior + 0.20*Audio + 0.20*Stylometry + 0.15*Environmental
    
    Risk Levels:
        0-30:  Safe
        30-60: Suspicious
        60-80: High Risk
        80+:   Likely Cheating
    """

    def __init__(self):
        self.weights = {
            ModuleType.VISION: settings.VISION_WEIGHT,
            ModuleType.BEHAVIOR: settings.BEHAVIOR_WEIGHT,
            ModuleType.AUDIO: settings.AUDIO_WEIGHT,
            ModuleType.STYLOMETRY: settings.STYLOMETRY_WEIGHT,
            ModuleType.ENVIRONMENTAL: settings.ENVIRONMENTAL_WEIGHT,
        }
        
        # Exponential moving average for temporal smoothing
        self.alpha = settings.ANOMALY_SMOOTHING_ALPHA
        self.ema_score = 0.0
        
        # Score history for timeline
        self.score_history = deque(maxlen=1000)
        
        # Latest module scores
        self.latest_scores: Dict[str, ModuleScore] = {}

    def compute_risk(self, module_scores: Dict[str, ModuleScore]) -> RiskScore:
        """
        Compute the fused risk score from individual module scores.
        
        Args:
            module_scores: Dict mapping module type string to ModuleScore
        
        Returns:
            RiskScore with overall score, level, and explanation
        """
        # Update latest scores
        self.latest_scores.update(module_scores)
        
        # Weighted sum
        weighted_sum = 0.0
        total_weight = 0.0
        contributions = []

        for module_type, weight in self.weights.items():
            module_key = module_type.value
            if module_key in self.latest_scores:
                score = self.latest_scores[module_key].score
                weighted_contribution = weight * score * 100  # Scale to 0-100
                weighted_sum += weighted_contribution
                total_weight += weight
                contributions.append({
                    "module": module_key,
                    "raw_score": round(score, 4),
                    "weight": weight,
                    "contribution": round(weighted_contribution, 2)
                })

        # Normalize if not all modules present
        if total_weight > 0 and total_weight < 1.0:
            weighted_sum = weighted_sum / total_weight

        # Apply EMA smoothing
        raw_score = weighted_sum
        self.ema_score = self.alpha * raw_score + (1 - self.alpha) * self.ema_score
        final_score = self.ema_score

        # Determine risk level
        risk_level = self._classify_risk(final_score)

        # Sort contributions by magnitude
        contributions.sort(key=lambda x: x["contribution"], reverse=True)

        # Generate explanation
        explanation = self._generate_explanation(final_score, risk_level, contributions)

        # Record history
        self.score_history.append({
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 2),
            "risk_level": risk_level.value,
            "timestamp": time.time()
        })

        return RiskScore(
            session_id="",  # Set by caller
            overall_score=round(final_score, 2),
            risk_level=risk_level,
            module_scores=self.latest_scores,
            fusion_weights={k.value: v for k, v in self.weights.items()},
            explanation=explanation,
            top_contributors=contributions[:3]
        )

    def _classify_risk(self, score: float) -> RiskLevel:
        """Classify risk level from score."""
        if score >= settings.HIGH_RISK_THRESHOLD:
            return RiskLevel.LIKELY_CHEATING
        elif score >= settings.SUSPICIOUS_THRESHOLD:
            return RiskLevel.HIGH_RISK
        elif score >= settings.SAFE_THRESHOLD:
            return RiskLevel.SUSPICIOUS
        return RiskLevel.SAFE

    def _generate_explanation(
        self,
        score: float,
        level: RiskLevel,
        contributions: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation."""
        if level == RiskLevel.SAFE:
            return f"Risk score {score:.1f}/100 — All behavioral patterns within normal range."
        
        # Find top contributor
        top = contributions[0] if contributions else {"module": "unknown", "contribution": 0}
        module_names = {
            "vision": "Vision Intelligence (gaze/face)",
            "behavior": "Behavioral Biometrics (typing/mouse)",
            "audio": "Acoustic Intelligence (voice/room)",
            "stylometry": "Stylometric Analysis (writing style)",
            "environmental": "Environmental Factors"
        }
        
        top_name = module_names.get(top["module"], top["module"])
        
        if level == RiskLevel.SUSPICIOUS:
            return (
                f"Risk score {score:.1f}/100 — Mild behavioral deviation detected. "
                f"Primary contributor: {top_name} ({top['contribution']:.1f} pts)."
            )
        elif level == RiskLevel.HIGH_RISK:
            return (
                f"Risk score {score:.1f}/100 — Significant behavioral anomaly detected. "
                f"Primary contributor: {top_name} ({top['contribution']:.1f} pts). "
                f"Review recommended."
            )
        else:
            return (
                f"Risk score {score:.1f}/100 — Multiple strong behavioral deviations detected. "
                f"Top contributor: {top_name} ({top['contribution']:.1f} pts). "
                f"Immediate review required."
            )

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get score history for timeline visualization."""
        return list(self.score_history)
