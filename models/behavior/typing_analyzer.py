"""
Typing Analyzer
Detects typing anomalies by comparing real-time patterns to baseline using One-Class SVM.
"""

import numpy as np
from typing import Dict, Any, Optional, List
from collections import defaultdict
import logging

from backend.schemas import TypingProfile, TypingCalibrationData

logger = logging.getLogger(__name__)


class TypingAnalyzer:
    """Detects typing behavior anomalies."""

    def __init__(self):
        self._svm = None
        self._is_fitted = False
        self.recent_ikis = []
        self.recent_holds = []
        self.max_window = 50
        self.burst_threshold = 3.0  # Speed multiplier for burst detection

    def _fit_svm(self, baseline: TypingProfile):
        """Fit One-Class SVM on baseline typing features."""
        if self._is_fitted or not baseline.typing_rhythm_vector:
            return

        try:
            from sklearn.svm import OneClassSVM
            
            # Create training data from baseline stats
            rhythm = baseline.typing_rhythm_vector
            # Generate synthetic samples around the baseline
            np.random.seed(42)
            n_samples = 100
            base_features = np.array(rhythm[:8])
            noise = np.random.normal(0, 0.1, (n_samples, len(base_features)))
            training_data = base_features + noise * base_features * 0.3
            
            self._svm = OneClassSVM(kernel='rbf', gamma='auto', nu=0.1)
            self._svm.fit(training_data)
            self._is_fitted = True
            logger.info("One-Class SVM fitted on typing baseline")
        except ImportError:
            logger.warning("scikit-learn not available for One-Class SVM")

    def analyze_keystrokes(
        self,
        keystrokes: List[TypingCalibrationData],
        baseline_profile: Optional[TypingProfile] = None
    ) -> Dict[str, Any]:
        """Analyze keystrokes for behavioral anomalies."""
        anomaly_score = 0.0
        details = {}
        confidence = 0.5

        if not keystrokes:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {}}

        # Extract timing features
        ikis = []
        hold_times = []
        for i, ks in enumerate(keystrokes):
            hold_times.append(ks.key_up_time - ks.key_down_time)
            if i > 0:
                iki = ks.key_down_time - keystrokes[i - 1].key_up_time
                if 0 < iki < 5.0:
                    ikis.append(iki)

        self.recent_ikis.extend(ikis)
        self.recent_holds.extend(hold_times)
        if len(self.recent_ikis) > self.max_window:
            self.recent_ikis = self.recent_ikis[-self.max_window:]
        if len(self.recent_holds) > self.max_window:
            self.recent_holds = self.recent_holds[-self.max_window:]

        if not ikis:
            return {"anomaly_score": 0.0, "confidence": 0.2, "details": {}}

        current_iki_mean = float(np.mean(ikis))
        current_iki_var = float(np.var(ikis))
        current_hold_mean = float(np.mean(hold_times))

        details["current_iki_mean"] = round(current_iki_mean, 4)
        details["current_speed_wpm"] = round(60.0 / max(current_iki_mean * 5, 0.01), 1)

        if baseline_profile and baseline_profile.avg_inter_key_interval > 0:
            baseline_iki = baseline_profile.avg_inter_key_interval
            baseline_var = baseline_profile.inter_key_variance + 1e-6
            confidence = 0.8

            # 1. Speed deviation
            speed_ratio = baseline_iki / max(current_iki_mean, 0.001)
            if speed_ratio > self.burst_threshold:
                burst_score = min((speed_ratio - 1) / 4.0, 1.0)
                anomaly_score = max(anomaly_score, burst_score)
                details["typing_burst_detected"] = True
                details["speed_ratio"] = round(speed_ratio, 2)

            # 2. Rhythm change (variance comparison)
            var_ratio = current_iki_var / max(baseline_var, 1e-6)
            if var_ratio > 5.0 or var_ratio < 0.1:
                rhythm_anomaly = min(abs(np.log10(max(var_ratio, 0.01))) / 2.0, 1.0)
                anomaly_score = max(anomaly_score, rhythm_anomaly * 0.7)
                details["rhythm_change"] = True
                details["variance_ratio"] = round(var_ratio, 2)

            # 3. Z-score deviation of IKI
            z_score = abs(current_iki_mean - baseline_iki) / max(np.sqrt(baseline_var), 0.001)
            if z_score > 2.5:
                anomaly_score = max(anomaly_score, min(z_score / 5.0, 1.0))
                details["iki_z_score"] = round(z_score, 2)

        # 4. Copy-paste detection (extremely fast input)
        if current_iki_mean < 0.02:  # Faster than human typing
            anomaly_score = max(anomaly_score, 0.9)
            details["copy_paste_suspected"] = True

        # 5. SVM-based anomaly
        if baseline_profile:
            self._fit_svm(baseline_profile)
            if self._is_fitted and self._svm is not None:
                features = np.array([
                    current_iki_mean,
                    np.sqrt(current_iki_var),
                    float(np.median(ikis)),
                    float(np.percentile(ikis, 25)) if len(ikis) > 3 else current_iki_mean,
                    float(np.percentile(ikis, 75)) if len(ikis) > 3 else current_iki_mean,
                    current_hold_mean,
                    float(np.std(hold_times)),
                    float(np.median(hold_times))
                ]).reshape(1, -1)
                
                prediction = self._svm.predict(features)
                if prediction[0] == -1:
                    anomaly_score = max(anomaly_score, 0.6)
                    details["svm_anomaly"] = True

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": confidence,
            "details": details
        }
