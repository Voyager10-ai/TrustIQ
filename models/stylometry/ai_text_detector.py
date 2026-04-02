"""
AI Text Detector
Detects AI-generated text using perplexity analysis.
"""

import numpy as np
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AITextDetector:
    """
    Detects AI-generated text via perplexity and pattern analysis.
    Uses statistical heuristics and optional GPT-2 perplexity scoring.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._loaded = False

    def _load_model(self):
        """Lazy-load GPT-2 for perplexity scoring."""
        if self._loaded:
            return
        self._loaded = True
        
        try:
            import torch
            from transformers import GPT2LMHeadModel, GPT2Tokenizer
            
            self._tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            self._model = GPT2LMHeadModel.from_pretrained('gpt2')
            self._model.eval()
            logger.info("GPT-2 loaded for perplexity analysis")
        except Exception as e:
            logger.warning(f"GPT-2 not available: {e}. Using heuristic detection only.")

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for AI generation indicators."""
        anomaly_score = 0.0
        details = {}

        if not text or len(text.split()) < 20:
            return {"anomaly_score": 0.0, "confidence": 0.1, "details": {"too_short": True}}

        # 1. Statistical heuristics
        heuristic_score = self._heuristic_analysis(text)
        details["heuristic_score"] = round(heuristic_score, 3)

        # 2. Perplexity analysis (if model available)
        perplexity = self._compute_perplexity(text)
        if perplexity is not None:
            details["perplexity"] = round(perplexity, 2)
            # AI text tends to have lower perplexity (more predictable)
            if perplexity < 30:
                perplexity_score = max(0, (30 - perplexity) / 30)
                anomaly_score = max(anomaly_score, perplexity_score)
                details["low_perplexity_flag"] = True

        # Combine scores
        anomaly_score = max(anomaly_score, heuristic_score)

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.6 if self._model else 0.4,
            "details": details
        }

    def _heuristic_analysis(self, text: str) -> float:
        """Statistical heuristics for AI-generated text detection."""
        score = 0.0
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences or not words:
            return 0.0

        # 1. Sentence length uniformity (AI tends to be more uniform)
        sent_lengths = [len(s.split()) for s in sentences]
        if len(sent_lengths) > 2:
            cv = np.std(sent_lengths) / max(np.mean(sent_lengths), 1)
            if cv < 0.2:  # Very uniform
                score = max(score, 0.4)

        # 2. Transition word density (AI uses more)
        transition_words = [
            'however', 'moreover', 'furthermore', 'additionally',
            'consequently', 'nevertheless', 'therefore', 'thus',
            'in conclusion', 'subsequently', 'specifically'
        ]
        text_lower = text.lower()
        transition_count = sum(1 for tw in transition_words if tw in text_lower)
        transition_density = transition_count / max(len(sentences), 1)
        if transition_density > 0.3:
            score = max(score, 0.5)

        # 3. Vocabulary sophistication consistency (AI is uniformly sophisticated)
        sophistication = [np.mean([len(w) for w in s.split()]) for s in sentences if s.split()]
        if len(sophistication) > 2:
            soph_cv = np.std(sophistication) / max(np.mean(sophistication), 1)
            if soph_cv < 0.15:
                score = max(score, 0.35)

        # 4. Lack of personal markers
        personal_words = ['i', 'me', 'my', 'myself', 'think', 'feel', 'believe', 'hmm', 'um', 'like']
        personal_count = sum(1 for w in words if w.lower() in personal_words)
        if len(words) > 50 and personal_count == 0:
            score = max(score, 0.3)

        # 5. Perfect grammar with no contractions
        contractions = ["n't", "'re", "'ve", "'ll", "'d", "'m"]
        has_contractions = any(c in text for c in contractions)
        if not has_contractions and len(words) > 50:
            score = max(score, 0.2)

        return score

    def _compute_perplexity(self, text: str) -> float:
        """Compute GPT-2 perplexity of text."""
        self._load_model()
        
        if self._model is None or self._tokenizer is None:
            return None

        try:
            import torch
            
            encodings = self._tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
            input_ids = encodings.input_ids

            with torch.no_grad():
                outputs = self._model(input_ids, labels=input_ids)
                loss = outputs.loss
                perplexity = float(torch.exp(loss))

            return perplexity
        except Exception as e:
            logger.debug(f"Perplexity computation failed: {e}")
            return None
