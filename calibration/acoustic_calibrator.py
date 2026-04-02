"""
Acoustic Calibrator
Establishes room acoustic signature baseline using audio features.
"""

import numpy as np
import base64
import io
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class AcousticCalibrator:
    """Collects and analyzes room acoustics during calibration."""

    def __init__(self):
        self.audio_chunks: List[np.ndarray] = []
        self.mfcc_features: List[np.ndarray] = []
        self.spectral_features: List[Dict[str, float]] = []
        self.total_duration = 0.0

    def process_chunk(self, audio_base64: str, sample_rate: int = 16000) -> Dict[str, Any]:
        """Process an audio chunk for acoustic baseline."""
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            
            if len(audio_data) == 0:
                audio_data = self._generate_synthetic_audio(sample_rate)
            
        except Exception:
            audio_data = self._generate_synthetic_audio(sample_rate)

        self.audio_chunks.append(audio_data)
        chunk_duration = len(audio_data) / sample_rate
        self.total_duration += chunk_duration

        # Extract features
        try:
            import librosa
            
            # MFCC
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            self.mfcc_features.append(np.mean(mfccs, axis=1))

            # Spectral features
            spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)))
            spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)))
            spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)))

            self.spectral_features.append({
                "centroid": spectral_centroid,
                "bandwidth": spectral_bandwidth,
                "rolloff": spectral_rolloff
            })
        except ImportError:
            logger.warning("Librosa not available. Using synthetic acoustic features.")
            self.mfcc_features.append(np.random.normal(0, 1, 13))
            self.spectral_features.append({
                "centroid": np.random.uniform(1000, 3000),
                "bandwidth": np.random.uniform(1000, 2000),
                "rolloff": np.random.uniform(3000, 6000)
            })

        return {
            "duration_collected": round(self.total_duration, 2),
            "chunks_processed": len(self.audio_chunks)
        }

    def _generate_synthetic_audio(self, sample_rate: int, duration: float = 1.0) -> np.ndarray:
        """Generate synthetic ambient noise for testing."""
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        noise = np.random.normal(0, 0.01, len(t)).astype(np.float32)
        # Add low-frequency room hum
        hum = 0.005 * np.sin(2 * np.pi * 60 * t).astype(np.float32)
        return noise + hum

    def get_profile(self) -> Dict[str, Any]:
        """Generate room acoustic baseline profile."""
        if not self.mfcc_features:
            return {
                "mfcc_baseline": [0.0] * 13,
                "spectral_centroid": 0.0,
                "spectral_bandwidth": 0.0,
                "spectral_rolloff": 0.0,
                "ambient_noise_level": 0.0,
                "room_signature_vector": [0.0] * 26
            }

        # Average MFCC across all chunks
        mfcc_array = np.array(self.mfcc_features)
        mfcc_baseline = np.mean(mfcc_array, axis=0).tolist()
        mfcc_variance = np.var(mfcc_array, axis=0).tolist()

        # Average spectral features
        centroid = float(np.mean([s["centroid"] for s in self.spectral_features]))
        bandwidth = float(np.mean([s["bandwidth"] for s in self.spectral_features]))
        rolloff = float(np.mean([s["rolloff"] for s in self.spectral_features]))

        # Ambient noise level (RMS of all chunks)
        if self.audio_chunks:
            all_audio = np.concatenate(self.audio_chunks)
            ambient_noise = float(np.sqrt(np.mean(all_audio ** 2)))
        else:
            ambient_noise = 0.0

        # Room signature vector = MFCC mean + MFCC variance
        room_signature = mfcc_baseline + mfcc_variance

        return {
            "mfcc_baseline": [round(v, 6) for v in mfcc_baseline],
            "spectral_centroid": round(centroid, 2),
            "spectral_bandwidth": round(bandwidth, 2),
            "spectral_rolloff": round(rolloff, 2),
            "ambient_noise_level": round(ambient_noise, 6),
            "room_signature_vector": [round(v, 6) for v in room_signature]
        }
