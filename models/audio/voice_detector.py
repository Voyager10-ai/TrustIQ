"""
Voice Detector
Detects secondary voices and speaker verification against baseline.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional

from backend.schemas import AcousticProfile

logger = logging.getLogger(__name__)


class VoiceDetector:
    """Detects secondary voice presence via speaker embedding distance."""

    def __init__(self):
        self.speaker_embeddings = []
        self.baseline_embedding = None

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        baseline: Optional[AcousticProfile] = None
    ) -> Dict[str, Any]:
        """Analyze audio for secondary voice detection."""
        anomaly_score = 0.0
        details = {}

        if len(audio_data) == 0:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {}}

        try:
            import librosa

            # Voice Activity Detection (simple energy + ZCR based)
            frame_length = int(0.025 * sample_rate)
            hop_length = int(0.010 * sample_rate)
            
            frames = librosa.util.frame(audio_data, frame_length=frame_length, hop_length=hop_length)
            frame_energy = np.sum(frames ** 2, axis=0)
            energy_threshold = np.mean(frame_energy) * 2
            voice_frames = frame_energy > energy_threshold
            voice_ratio = float(np.mean(voice_frames))

            details["voice_activity_ratio"] = round(voice_ratio, 3)

            if voice_ratio > 0.2:  # Significant voice activity
                # Extract MFCC as simple speaker embedding
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=20)
                current_embedding = np.mean(mfccs, axis=1)

                # Compare to baseline
                if baseline and baseline.mfcc_baseline:
                    baseline_mfcc = np.array(baseline.mfcc_baseline[:20])
                    if len(baseline_mfcc) == len(current_embedding):
                        # Cosine distance
                        cos_sim = np.dot(baseline_mfcc, current_embedding) / (
                            np.linalg.norm(baseline_mfcc) * np.linalg.norm(current_embedding) + 1e-8
                        )
                        distance = 1.0 - max(cos_sim, 0)
                        details["speaker_distance"] = round(float(distance), 4)

                        if distance > 0.5:
                            anomaly_score = min(distance, 1.0)
                            details["different_speaker_detected"] = True

                # Track embeddings for multi-speaker detection
                self.speaker_embeddings.append(current_embedding)
                if len(self.speaker_embeddings) > 10:
                    # Check variance in embeddings (multiple speakers = high variance)
                    emb_array = np.array(self.speaker_embeddings[-10:])
                    emb_var = float(np.mean(np.var(emb_array, axis=0)))
                    details["embedding_variance"] = round(emb_var, 4)
                    
                    if emb_var > 5.0:
                        anomaly_score = max(anomaly_score, 0.7)
                        details["multiple_speakers_likely"] = True

        except ImportError:
            rms = float(np.sqrt(np.mean(audio_data ** 2)))
            if rms > 0.05:
                anomaly_score = 0.3
                details["voice_activity_detected"] = True

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.65,
            "details": details
        }
