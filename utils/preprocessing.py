"""
Preprocessing Utilities
Common preprocessing functions for frame, audio, and text data.
"""

import numpy as np
import base64
import cv2
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def decode_frame(frame_base64: str) -> Optional[np.ndarray]:
    """Decode a base64-encoded image frame."""
    try:
        frame_bytes = base64.b64decode(frame_base64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.debug(f"Frame decode error: {e}")
        return None


def encode_frame(frame: np.ndarray) -> str:
    """Encode a frame to base64 JPEG."""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')


def resize_frame(frame: np.ndarray, max_size: int = 640) -> np.ndarray:
    """Resize frame maintaining aspect ratio."""
    h, w = frame.shape[:2]
    if max(h, w) <= max_size:
        return frame
    scale = max_size / max(h, w)
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """Normalize audio to [-1, 1] range."""
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data / max_val
    return audio_data


def decode_audio(audio_base64: str, dtype=np.float32) -> np.ndarray:
    """Decode base64 audio data."""
    try:
        audio_bytes = base64.b64decode(audio_base64)
        return np.frombuffer(audio_bytes, dtype=dtype)
    except Exception as e:
        logger.debug(f"Audio decode error: {e}")
        return np.array([], dtype=dtype)


def clean_text(text: str) -> str:
    """Clean and normalize text for analysis."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


def split_sentences(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
