"""
Audio Analyzer (Orchestrator)
Combines whisper, voice, and room analysis into unified audio anomaly score.
"""

import numpy as np
import base64
import logging
from typing import Dict, Any, Optional

from backend.schemas import AcousticProfile
from models.audio.whisper_detector import WhisperDetector
from models.audio.voice_detector import VoiceDetector
from models.audio.room_analyzer import RoomAnalyzer

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """
    Orchestrates audio intelligence modules.
    
    Sub-scores weighted as:
        whisper: 0.35
        voice:   0.35
        room:    0.30
    """

    def __init__(self):
        self.whisper_detector = WhisperDetector()
        self.voice_detector = VoiceDetector()
        self.room_analyzer = RoomAnalyzer()
        
        self.weights = {
            "whisper": 0.35,
            "voice": 0.35,
            "room": 0.30
        }

    def analyze_chunk(
        self,
        audio_base64: str,
        sample_rate: int = 16000,
        baseline_profile: Optional[AcousticProfile] = None
    ) -> Dict[str, Any]:
        """Analyze an audio chunk through all sub-modules."""
        
        # Decode audio
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            if len(audio_data) == 0:
                audio_data = np.random.normal(0, 0.001, sample_rate).astype(np.float32)
        except Exception:
            audio_data = np.random.normal(0, 0.001, sample_rate).astype(np.float32)

        # Run all detectors
        whisper_result = self.whisper_detector.analyze(audio_data, sample_rate)
        voice_result = self.voice_detector.analyze(audio_data, sample_rate, baseline_profile)
        room_result = self.room_analyzer.analyze(audio_data, sample_rate, baseline_profile)

        # Weighted combination
        combined_score = (
            self.weights["whisper"] * whisper_result["anomaly_score"] +
            self.weights["voice"] * voice_result["anomaly_score"] +
            self.weights["room"] * room_result["anomaly_score"]
        )

        combined_confidence = (
            self.weights["whisper"] * whisper_result["confidence"] +
            self.weights["voice"] * voice_result["confidence"] +
            self.weights["room"] * room_result["confidence"]
        )

        details = {
            "whisper": {
                "score": whisper_result["anomaly_score"],
                "details": whisper_result["details"]
            },
            "voice": {
                "score": voice_result["anomaly_score"],
                "details": voice_result["details"]
            },
            "room": {
                "score": room_result["anomaly_score"],
                "details": room_result["details"]
            },
            "weights": self.weights
        }

        return {
            "anomaly_score": round(min(combined_score, 1.0), 4),
            "confidence": round(combined_confidence, 4),
            "details": details
        }
