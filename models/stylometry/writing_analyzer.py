"""
Writing Analyzer
Analyzes writing style features and compares to baseline "writing DNA".
"""

import numpy as np
import re
from typing import Dict, Any, Optional
import logging

from backend.schemas import WritingProfile

logger = logging.getLogger(__name__)


class WritingAnalyzer:
    """Detects writing style deviations from baseline."""

    def __init__(self):
        self._encoder = None
        self.submission_history = []

    def _get_encoder(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                pass
        return self._encoder

    def analyze(
        self,
        text: str,
        baseline: Optional[WritingProfile] = None
    ) -> Dict[str, Any]:
        """Analyze text for stylometric anomalies."""
        anomaly_score = 0.0
        details = {}

        if not text or len(text.strip()) < 10:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {"too_short": True}}

        # Extract features
        features = self._extract_features(text)
        details["features"] = features
        self.submission_history.append(features)

        if baseline:
            # 1. Sentence length deviation
            if baseline.avg_sentence_length > 0:
                sent_deviation = abs(features["avg_sentence_length"] - baseline.avg_sentence_length) / max(baseline.avg_sentence_length, 1)
                if sent_deviation > 0.5:
                    anomaly_score = max(anomaly_score, min(sent_deviation, 1.0) * 0.6)
                    details["sentence_length_change"] = round(sent_deviation, 3)

            # 2. Vocabulary richness jump
            if baseline.vocabulary_richness > 0:
                vocab_change = abs(features["vocabulary_richness"] - baseline.vocabulary_richness) / max(baseline.vocabulary_richness, 0.01)
                if vocab_change > 0.3:
                    anomaly_score = max(anomaly_score, min(vocab_change, 1.0) * 0.5)
                    details["vocabulary_change"] = round(vocab_change, 3)

            # 3. Complexity score jump
            if baseline.complexity_score > 0:
                complexity_change = abs(features["complexity_score"] - baseline.complexity_score) / max(baseline.complexity_score, 0.01)
                if complexity_change > 0.5:
                    anomaly_score = max(anomaly_score, min(complexity_change, 1.0) * 0.6)
                    details["complexity_jump"] = True

            # 4. Embedding distance (writing DNA)
            if baseline.style_embedding:
                encoder = self._get_encoder()
                if encoder:
                    try:
                        current_embedding = encoder.encode(text)
                        baseline_emb = np.array(baseline.style_embedding)
                        
                        if len(baseline_emb) == len(current_embedding):
                            cos_sim = np.dot(baseline_emb, current_embedding) / (
                                np.linalg.norm(baseline_emb) * np.linalg.norm(current_embedding) + 1e-8
                            )
                            distance = 1.0 - max(float(cos_sim), 0)
                            details["writing_dna_distance"] = round(distance, 4)
                            
                            if distance > 0.3:
                                anomaly_score = max(anomaly_score, min(distance * 1.5, 1.0))
                                details["writing_style_change"] = True
                    except Exception as e:
                        logger.debug(f"Embedding comparison failed: {e}")

        # 5. Self-referencing: sudden change from recent submissions
        if len(self.submission_history) > 2:
            prev = self.submission_history[-2]
            curr = features
            
            changes = []
            for key in ["avg_sentence_length", "vocabulary_richness", "complexity_score"]:
                if prev.get(key, 0) > 0:
                    change = abs(curr.get(key, 0) - prev[key]) / max(prev[key], 0.01)
                    changes.append(change)
            
            if changes and np.mean(changes) > 0.5:
                anomaly_score = max(anomaly_score, min(float(np.mean(changes)), 1.0) * 0.5)
                details["sudden_style_shift"] = True

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.7,
            "details": details
        }

    def _extract_features(self, text: str) -> Dict[str, float]:
        """Extract stylometric features from text."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()

        if not words:
            return {"avg_sentence_length": 0, "vocabulary_richness": 0, "avg_word_length": 0, "complexity_score": 0}

        sentence_lengths = [len(s.split()) for s in sentences]
        unique_words = set(w.lower() for w in words)

        return {
            "avg_sentence_length": float(np.mean(sentence_lengths)) if sentence_lengths else 0,
            "sentence_length_variance": float(np.var(sentence_lengths)) if len(sentence_lengths) > 1 else 0,
            "vocabulary_richness": len(unique_words) / len(words),
            "avg_word_length": float(np.mean([len(w) for w in words])),
            "complexity_score": sum(1 for w in words if len(w) > 6) / len(words),
            "word_count": len(words),
            "sentence_count": len(sentences)
        }
