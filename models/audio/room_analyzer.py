"""
Room Analyzer
Detects room acoustic signature changes by comparing live audio to baseline.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional

from backend.schemas import AcousticProfile

logger = logging.getLogger(__name__)


class RoomAnalyzer:
    """Detects environment changes via acoustic signature comparison."""

    def __init__(self):
        self.spectral_history = []
        self.max_history = 50

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        baseline: Optional[AcousticProfile] = None
    ) -> Dict[str, Any]:
        """Analyze room acoustics for environment changes."""
        anomaly_score = 0.0
        details = {}

        if len(audio_data) == 0:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {}}

        try:
            import librosa

            # Current room features
            spectral_centroid = float(np.mean(
                librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            ))
            spectral_bandwidth = float(np.mean(
                librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)
            ))
            spectral_rolloff = float(np.mean(
                librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)
            ))
            rms = float(np.sqrt(np.mean(audio_data ** 2)))

            current_features = {
                "centroid": spectral_centroid,
                "bandwidth": spectral_bandwidth,
                "rolloff": spectral_rolloff,
                "rms": rms
            }
            self.spectral_history.append(current_features)
            if len(self.spectral_history) > self.max_history:
                self.spectral_history.pop(0)

            details["spectral_centroid"] = round(spectral_centroid, 2)
            details["spectral_bandwidth"] = round(spectral_bandwidth, 2)
            details["ambient_level"] = round(rms, 6)

            # Compare to baseline
            if baseline and baseline.spectral_centroid > 0:
                centroid_change = abs(spectral_centroid - baseline.spectral_centroid) / max(baseline.spectral_centroid, 1)
                bandwidth_change = abs(spectral_bandwidth - baseline.spectral_bandwidth) / max(baseline.spectral_bandwidth, 1)
                noise_change = abs(rms - baseline.ambient_noise_level) / max(baseline.ambient_noise_level, 0.001)

                # Room change detection
                if centroid_change > 0.4 or bandwidth_change > 0.4:
                    anomaly_score = min((centroid_change + bandwidth_change) / 2, 1.0)
                    details["room_change_detected"] = True
                    details["centroid_change"] = round(centroid_change, 3)
                    details["bandwidth_change"] = round(bandwidth_change, 3)

                # Noise level change
                if noise_change > 3.0:
                    noise_anomaly = min(noise_change / 10.0, 1.0)
                    anomaly_score = max(anomaly_score, noise_anomaly)
                    details["noise_level_change"] = True

                # MFCC signature comparison
                if baseline.room_signature_vector:
                    mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
                    current_mfcc = np.mean(mfccs, axis=1)
                    baseline_mfcc = np.array(baseline.room_signature_vector[:13])
                    
                    if len(baseline_mfcc) == len(current_mfcc):
                        mfcc_distance = float(np.linalg.norm(current_mfcc - baseline_mfcc))
                        details["mfcc_distance"] = round(mfcc_distance, 4)
                        
                        if mfcc_distance > 20:
                            anomaly_score = max(anomaly_score, min(mfcc_distance / 50, 1.0))
                            details["acoustic_signature_mismatch"] = True

            # Self-referencing: sudden change from recent history
            elif len(self.spectral_history) > 5:
                recent_centroids = [s["centroid"] for s in self.spectral_history[:-1]]
                avg_centroid = np.mean(recent_centroids)
                if abs(spectral_centroid - avg_centroid) / max(avg_centroid, 1) > 0.3:
                    anomaly_score = max(anomaly_score, 0.4)
                    details["sudden_environment_change"] = True

        except ImportError:
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            details["ambient_level"] = round(rms, 6)

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.6,
            "details": details
        }
