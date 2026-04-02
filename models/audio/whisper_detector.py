"""
Whisper Detector
Detects whispering in audio using MFCC features and CNN classification.
"""

import numpy as np
import base64
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WhisperDetector:
    """Detects whispering in audio chunks."""

    def __init__(self):
        self._classifier = None
        self.energy_history = []
        self.max_history = 100

    def analyze(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Analyze audio for whisper presence."""
        anomaly_score = 0.0
        details = {}

        if len(audio_data) == 0:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {}}

        try:
            import librosa

            # Energy analysis
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            self.energy_history.append(rms)
            if len(self.energy_history) > self.max_history:
                self.energy_history.pop(0)

            details["rms_energy"] = round(rms, 6)

            # MFCC features
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_var = np.var(mfccs, axis=1)

            # Whisper characteristics:
            # - Higher energy than silence but lower than speech
            # - Specific MFCC pattern (more high-frequency energy relative to low)
            # - Higher spectral centroid than silence

            spectral_centroid = float(np.mean(
                librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            ))
            zero_crossing_rate = float(np.mean(
                librosa.feature.zero_crossing_rate(audio_data)
            ))

            details["spectral_centroid"] = round(spectral_centroid, 2)
            details["zero_crossing_rate"] = round(zero_crossing_rate, 4)

            # Whisper detection heuristic
            # Whispers have: medium RMS, high ZCR, medium-high spectral centroid
            is_not_silence = rms > 0.005
            is_not_loud_speech = rms < 0.1
            has_whisper_zcr = zero_crossing_rate > 0.05
            has_whisper_centroid = 1500 < spectral_centroid < 5000

            if is_not_silence and is_not_loud_speech and has_whisper_zcr and has_whisper_centroid:
                anomaly_score = 0.7
                details["whisper_detected"] = True
                
                # Stronger score if sustained
                if len(self.energy_history) > 5:
                    recent_rms = self.energy_history[-5:]
                    if all(0.005 < r < 0.1 for r in recent_rms):
                        anomaly_score = 0.85
                        details["sustained_whisper"] = True

            # Direct speech detection (louder than whisper)
            elif rms > 0.1:
                anomaly_score = 0.8
                details["speech_detected"] = True

        except ImportError:
            # Fallback without librosa
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            self.energy_history.append(rms)
            if rms > 0.005 and rms < 0.1:
                anomaly_score = 0.3
                details["possible_whisper"] = True
            elif rms > 0.1:
                anomaly_score = 0.5
                details["possible_speech"] = True

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.7,
            "details": details
        }
