"""
Feature Extraction Utilities
Shared feature extraction functions for audio, text, and vision data.
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_mfcc(audio_data: np.ndarray, sample_rate: int = 16000, n_mfcc: int = 13) -> np.ndarray:
    """Extract MFCC features from audio data."""
    try:
        import librosa
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
        return np.mean(mfccs, axis=1)
    except ImportError:
        return np.zeros(n_mfcc)


def extract_spectral_features(audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
    """Extract spectral features from audio data."""
    try:
        import librosa
        return {
            "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate))),
            "spectral_bandwidth": float(np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate))),
            "spectral_rolloff": float(np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate))),
            "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(audio_data))),
            "rms_energy": float(np.sqrt(np.mean(audio_data ** 2)))
        }
    except ImportError:
        return {
            "spectral_centroid": 0.0,
            "spectral_bandwidth": 0.0,
            "spectral_rolloff": 0.0,
            "zero_crossing_rate": 0.0,
            "rms_energy": float(np.sqrt(np.mean(audio_data ** 2))) if len(audio_data) > 0 else 0.0
        }


def extract_text_features(text: str) -> Dict[str, float]:
    """Extract stylometric features from text."""
    import re
    
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not words:
        return {
            "word_count": 0, "sentence_count": 0,
            "avg_word_length": 0, "avg_sentence_length": 0,
            "vocabulary_richness": 0, "complexity": 0
        }
    
    unique = set(w.lower() for w in words)
    sent_lengths = [len(s.split()) for s in sentences]
    
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_word_length": float(np.mean([len(w) for w in words])),
        "avg_sentence_length": float(np.mean(sent_lengths)) if sent_lengths else 0,
        "vocabulary_richness": len(unique) / len(words),
        "complexity": sum(1 for w in words if len(w) > 6) / len(words)
    }


def compute_typing_features(
    inter_key_intervals: List[float],
    hold_times: List[float]
) -> Dict[str, float]:
    """Compute typing rhythm features from timing data."""
    iki = np.array(inter_key_intervals) if inter_key_intervals else np.array([0.0])
    ht = np.array(hold_times) if hold_times else np.array([0.0])
    
    return {
        "iki_mean": float(np.mean(iki)),
        "iki_std": float(np.std(iki)),
        "iki_median": float(np.median(iki)),
        "hold_mean": float(np.mean(ht)),
        "hold_std": float(np.std(ht)),
        "estimated_wpm": round(60.0 / max(float(np.mean(iki)) * 5, 0.01), 1)
    }
