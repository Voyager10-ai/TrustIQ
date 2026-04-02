"""
Writing Calibrator
Establishes writing style baseline using NLP features and embeddings.
"""

import numpy as np
import re
from typing import Dict, List, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class WritingCalibrator:
    """Collects and analyzes writing style during calibration."""

    def __init__(self):
        self.writing_samples: List[str] = []
        self._encoder = None

    def _get_encoder(self):
        """Lazy-load sentence transformer."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformer for writing analysis")
            except Exception as e:
                logger.warning(f"Sentence-transformer not available: {e}. Using statistical features only.")
        return self._encoder

    def process_sample(self, text: str) -> Dict[str, Any]:
        """Process a writing sample for calibration."""
        self.writing_samples.append(text)
        word_count = len(text.split())
        return {
            "word_count": word_count,
            "total_samples": len(self.writing_samples),
            "total_words": sum(len(s.split()) for s in self.writing_samples)
        }

    def _extract_stylometric_features(self, text: str) -> Dict[str, float]:
        """Extract stylometric features from text."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        
        if not words:
            return {
                "avg_sentence_length": 0.0,
                "vocabulary_richness": 0.0,
                "avg_word_length": 0.0,
                "complexity_score": 0.0
            }

        # Sentence length stats
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sentence_length = float(np.mean(sentence_lengths)) if sentence_lengths else 0.0

        # Vocabulary richness (type-token ratio)
        unique_words = set(w.lower() for w in words)
        vocabulary_richness = len(unique_words) / len(words) if words else 0.0

        # Average word length
        avg_word_length = float(np.mean([len(w) for w in words]))

        # Complexity score (based on long words, sentence variety)
        long_words = sum(1 for w in words if len(w) > 6) / max(len(words), 1)
        sentence_variance = float(np.var(sentence_lengths)) if len(sentence_lengths) > 1 else 0.0
        complexity_score = (long_words * 0.5 + min(sentence_variance / 100, 0.5))

        # POS-like distribution (simplified without NLTK dependency)
        punctuation_ratio = sum(1 for c in text if c in '.,;:!?') / max(len(text), 1)
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        return {
            "avg_sentence_length": round(avg_sentence_length, 2),
            "vocabulary_richness": round(vocabulary_richness, 4),
            "avg_word_length": round(avg_word_length, 2),
            "complexity_score": round(complexity_score, 4),
            "punctuation_ratio": round(punctuation_ratio, 4),
            "uppercase_ratio": round(uppercase_ratio, 4),
            "sentence_count": len(sentences),
            "word_count": len(words)
        }

    def get_profile(self) -> Dict[str, Any]:
        """Generate writing style baseline profile."""
        if not self.writing_samples:
            return {
                "style_embedding": [],
                "avg_sentence_length": 0.0,
                "vocabulary_richness": 0.0,
                "avg_word_length": 0.0,
                "complexity_score": 0.0,
                "pos_distribution": {}
            }

        combined_text = " ".join(self.writing_samples)
        features = self._extract_stylometric_features(combined_text)

        # Try to get embedding
        style_embedding = []
        encoder = self._get_encoder()
        if encoder is not None:
            try:
                embedding = encoder.encode(combined_text)
                style_embedding = embedding.tolist()
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
                # Use feature-based pseudo-embedding
                style_embedding = self._generate_pseudo_embedding(features)
        else:
            style_embedding = self._generate_pseudo_embedding(features)

        return {
            "style_embedding": style_embedding,
            "avg_sentence_length": features["avg_sentence_length"],
            "vocabulary_richness": features["vocabulary_richness"],
            "avg_word_length": features["avg_word_length"],
            "complexity_score": features["complexity_score"],
            "pos_distribution": {
                "punctuation_ratio": features.get("punctuation_ratio", 0),
                "uppercase_ratio": features.get("uppercase_ratio", 0)
            }
        }

    def _generate_pseudo_embedding(self, features: Dict[str, float]) -> List[float]:
        """Generate a pseudo-embedding from stylometric features."""
        base = [
            features.get("avg_sentence_length", 0) / 50.0,
            features.get("vocabulary_richness", 0),
            features.get("avg_word_length", 0) / 10.0,
            features.get("complexity_score", 0),
            features.get("punctuation_ratio", 0),
            features.get("uppercase_ratio", 0),
        ]
        # Pad to a consistent size
        np.random.seed(hash(str(base)) % (2**31))
        padding = np.random.normal(0, 0.1, 128 - len(base)).tolist()
        return base + padding
