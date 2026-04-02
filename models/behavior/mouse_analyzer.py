"""
Mouse Analyzer
Detects mouse behavior anomalies using autoencoder-based anomaly detection.
"""

import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MouseAnalyzer:
    """Detects mouse movement anomalies."""

    def __init__(self):
        self.movement_history: List[Dict[str, float]] = []
        self.speed_history: List[float] = []
        self.jitter_history: List[float] = []
        self.max_history = 100

    def analyze_movements(
        self,
        movements: List[Dict[str, float]],
        clicks: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze mouse movement patterns.
        
        Args:
            movements: List of {x, y, timestamp} dicts
            clicks: List of {x, y, timestamp, button} dicts
        """
        anomaly_score = 0.0
        details = {}

        if not movements or len(movements) < 2:
            return {"anomaly_score": 0.0, "confidence": 0.2, "details": {}}

        # Calculate movement features
        speeds = []
        angles = []
        
        for i in range(1, len(movements)):
            dx = movements[i]["x"] - movements[i - 1]["x"]
            dy = movements[i]["y"] - movements[i - 1]["y"]
            dt = movements[i]["timestamp"] - movements[i - 1]["timestamp"]
            
            if dt > 0:
                distance = np.sqrt(dx**2 + dy**2)
                speed = distance / dt
                speeds.append(speed)
                angles.append(np.arctan2(dy, dx))

        if not speeds:
            return {"anomaly_score": 0.0, "confidence": 0.2, "details": {}}

        # Feature extraction
        avg_speed = float(np.mean(speeds))
        speed_var = float(np.var(speeds))
        jitter = float(np.mean(np.abs(np.diff(speeds)))) if len(speeds) > 1 else 0
        angle_var = float(np.var(angles)) if angles else 0

        self.speed_history.append(avg_speed)
        self.jitter_history.append(jitter)
        if len(self.speed_history) > self.max_history:
            self.speed_history.pop(0)
            self.jitter_history.pop(0)

        details["avg_speed"] = round(avg_speed, 2)
        details["jitter"] = round(jitter, 4)
        details["angle_variance"] = round(angle_var, 4)

        # 1. Jitter anomaly (bot-like perfectly smooth or extremely jittery)
        if len(self.jitter_history) > 10:
            baseline_jitter = np.mean(self.jitter_history[:-1])
            if baseline_jitter > 0:
                jitter_ratio = jitter / max(baseline_jitter, 0.001)
                if jitter_ratio > 3.0 or jitter_ratio < 0.1:
                    anomaly_score = 0.6
                    details["jitter_anomaly"] = True

        # 2. Speed anomaly
        if len(self.speed_history) > 10:
            baseline_speed = np.mean(self.speed_history[:-1])
            if baseline_speed > 0:
                speed_change = abs(avg_speed - baseline_speed) / baseline_speed
                if speed_change > 2.0:
                    anomaly_score = max(anomaly_score, 0.5)
                    details["speed_anomaly"] = True

        # 3. Scroll-like rapid micro movements
        if angle_var < 0.01 and avg_speed > 500:
            anomaly_score = max(anomaly_score, 0.4)
            details["automated_pattern"] = True

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.6,
            "details": details
        }
