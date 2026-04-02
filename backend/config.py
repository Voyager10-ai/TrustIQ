"""
ABIE Configuration Module
Centralized configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "exam_cheater"

    # Fusion Weights
    VISION_WEIGHT: float = 0.25
    BEHAVIOR_WEIGHT: float = 0.20
    AUDIO_WEIGHT: float = 0.20
    STYLOMETRY_WEIGHT: float = 0.20
    ENVIRONMENTAL_WEIGHT: float = 0.15

    # Risk Thresholds (0-100)
    SAFE_THRESHOLD: float = 30.0
    SUSPICIOUS_THRESHOLD: float = 60.0
    HIGH_RISK_THRESHOLD: float = 80.0

    # Calibration
    CALIBRATION_DURATION_SECONDS: int = 300
    MIN_GAZE_SAMPLES: int = 100
    MIN_TYPING_SAMPLES: int = 50

    # Anomaly Detection
    ANOMALY_SMOOTHING_ALPHA: float = 0.3  # EMA smoothing factor
    TEMPORAL_WINDOW_SECONDS: float = 10.0  # Sliding window for temporal analysis
    DEVIATION_THRESHOLD: float = 2.5  # Standard deviations for anomaly flagging

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
