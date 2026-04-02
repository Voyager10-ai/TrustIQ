"""
Risk Calculator
Manages session-level risk state with explainable scoring and event timeline.
"""

import time
from typing import Dict, Any, Optional, List
from collections import deque
import logging

from backend.schemas import (
    ModuleScore, RiskScore, RiskLevel, AnomalyEvent,
    ModuleType, BehavioralProfile
)
from models.fusion.fusion_engine import FusionEngine

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Per-session risk calculator that maintains state and provides
    explainable risk assessments.
    """

    def __init__(self, session_id: str, profile: Optional[BehavioralProfile] = None):
        self.session_id = session_id
        self.profile = profile
        self.fusion_engine = FusionEngine()
        
        # Event tracking
        self.events: List[AnomalyEvent] = []
        self.max_events = 500
        
        # Score timeline
        self.timeline: List[Dict[str, Any]] = []

    def update_score(self, module_score: ModuleScore) -> Dict[str, Any]:
        """
        Update risk score with a new module score.
        
        Returns quick summary for API response.
        """
        # Add to fusion engine
        scores = {module_score.module.value: module_score}
        risk = self.fusion_engine.compute_risk(scores)
        risk.session_id = self.session_id
        
        # Track timeline
        self.timeline.append({
            "score": risk.overall_score,
            "risk_level": risk.risk_level.value,
            "module": module_score.module.value,
            "module_score": module_score.score,
            "timestamp": time.time()
        })

        # Generate events for significant anomalies
        if module_score.score > 0.5:
            event = AnomalyEvent(
                session_id=self.session_id,
                module=module_score.module,
                severity=module_score.score,
                description=self._describe_anomaly(module_score),
                details=module_score.details
            )
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events.pop(0)

        return {
            "overall_score": risk.overall_score,
            "risk_level": risk.risk_level.value,
            "explanation": risk.explanation
        }

    def get_current_risk(self) -> RiskScore:
        """Get the current risk assessment."""
        risk = self.fusion_engine.compute_risk({})
        risk.session_id = self.session_id
        return risk

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get the score timeline."""
        return self.timeline

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all anomaly events."""
        return [e.model_dump() for e in self.events]

    def get_explanation(self) -> Dict[str, Any]:
        """Get detailed explainable AI breakdown."""
        risk = self.get_current_risk()
        
        # Module explanations
        module_explanations = {}
        module_names = {
            "vision": "Vision Intelligence",
            "behavior": "Behavioral Biometrics",
            "audio": "Acoustic Intelligence",
            "stylometry": "Stylometric Analysis",
            "environmental": "Environmental Factors"
        }

        for name, score in risk.module_scores.items():
            level = "normal"
            if score.score > 0.7:
                level = "critical"
            elif score.score > 0.4:
                level = "elevated"
            
            module_explanations[name] = {
                "display_name": module_names.get(name, name),
                "score": score.score,
                "confidence": score.confidence,
                "level": level,
                "details": score.details,
                "weight": risk.fusion_weights.get(name, 0)
            }

        # Recent events summary
        recent_events = self.events[-10:] if self.events else []
        event_summary = [
            {
                "time": e.timestamp,
                "module": e.module.value,
                "severity": e.severity,
                "description": e.description
            }
            for e in recent_events
        ]

        return {
            "overall_score": risk.overall_score,
            "risk_level": risk.risk_level.value,
            "explanation": risk.explanation,
            "module_breakdown": module_explanations,
            "recent_events": event_summary,
            "top_contributors": risk.top_contributors,
            "recommendation": self._get_recommendation(risk.risk_level)
        }

    def _describe_anomaly(self, score: ModuleScore) -> str:
        """Generate a human-readable description of an anomaly."""
        module_descriptions = {
            ModuleType.VISION: "Visual anomaly detected (gaze deviation, face issue, or lip movement)",
            ModuleType.BEHAVIOR: "Behavioral anomaly detected (typing rhythm change or suspicious input)",
            ModuleType.AUDIO: "Acoustic anomaly detected (voice activity or room change)",
            ModuleType.STYLOMETRY: "Writing style anomaly detected (style shift or AI-like patterns)",
            ModuleType.ENVIRONMENTAL: "Environmental change detected"
        }
        
        base = module_descriptions.get(score.module, "Unknown anomaly")
        severity = "mild" if score.score < 0.6 else "significant" if score.score < 0.8 else "critical"
        
        return f"{base} — Severity: {severity} ({score.score:.2f})"

    def _get_recommendation(self, level: RiskLevel) -> str:
        """Get a recommendation based on risk level."""
        recommendations = {
            RiskLevel.SAFE: "No action needed. Student behavior is consistent with baseline.",
            RiskLevel.SUSPICIOUS: "Monitor closely. Minor behavioral deviations observed. May be normal variation.",
            RiskLevel.HIGH_RISK: "Review recommended. Significant deviations from baseline detected across multiple indicators.",
            RiskLevel.LIKELY_CHEATING: "Immediate review required. Strong behavioral deviations detected. Consider flagging for manual review."
        }
        return recommendations.get(level, "Unknown status.")
