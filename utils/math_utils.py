"""
Math Utilities
Statistical and mathematical helper functions.
"""

import numpy as np
from typing import List, Union


def z_score(value: float, mean: float, std: float) -> float:
    """Compute Z-score of a value given mean and standard deviation."""
    if std == 0:
        return 0.0
    return (value - mean) / std


def cosine_similarity(a: Union[List[float], np.ndarray], b: Union[List[float], np.ndarray]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_distance(a: Union[List[float], np.ndarray], b: Union[List[float], np.ndarray]) -> float:
    """Compute cosine distance (1 - similarity) between two vectors."""
    return 1.0 - cosine_similarity(a, b)


def mahalanobis_distance(
    x: np.ndarray,
    mean: np.ndarray,
    cov_inv: np.ndarray
) -> float:
    """Compute Mahalanobis distance."""
    diff = x - mean
    return float(np.sqrt(np.dot(np.dot(diff, cov_inv), diff)))


def exponential_moving_average(
    current: float,
    previous: float,
    alpha: float = 0.3
) -> float:
    """Compute exponential moving average."""
    return alpha * current + (1 - alpha) * previous


def sigmoid(x: float) -> float:
    """Sigmoid function for score normalization."""
    return 1.0 / (1.0 + np.exp(-x))


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def compute_anomaly_score(
    current: float,
    baseline_mean: float,
    baseline_std: float,
    max_deviation: float = 3.0
) -> float:
    """
    Compute anomaly score based on deviation from baseline.
    Returns score in [0, 1] range.
    """
    if baseline_std == 0:
        return 0.0
    
    z = abs(z_score(current, baseline_mean, baseline_std))
    return clamp(z / max_deviation)
