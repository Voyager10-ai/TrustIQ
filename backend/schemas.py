"""
ABIE Pydantic Schemas
Data models for the entire system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ─── Enums ────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    LIKELY_CHEATING = "likely_cheating"


class ModuleType(str, Enum):
    VISION = "vision"
    BEHAVIOR = "behavior"
    AUDIO = "audio"
    STYLOMETRY = "stylometry"
    ENVIRONMENTAL = "environmental"


class CalibrationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Calibration Schemas ─────────────────────────────────────────────────────

class GazeCalibrationData(BaseModel):
    """Raw gaze calibration frame data."""
    frame_base64: str = Field(..., description="Base64 encoded video frame")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class TypingCalibrationData(BaseModel):
    """Keystroke timing data for calibration."""
    key: str
    key_down_time: float
    key_up_time: float
    timestamp: float


class WritingCalibrationData(BaseModel):
    """Writing sample for stylometric baseline."""
    text: str = Field(..., min_length=50)
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class AudioCalibrationData(BaseModel):
    """Audio sample for acoustic baseline."""
    audio_base64: str = Field(..., description="Base64 encoded audio chunk")
    sample_rate: int = 16000
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


# ─── Behavioral Profile ──────────────────────────────────────────────────────

class GazeProfile(BaseModel):
    """Gaze pattern baseline profile."""
    mean_direction: List[float] = Field(default_factory=list)
    variance: List[float] = Field(default_factory=list)
    downward_glance_frequency: float = 0.0
    head_pose_baseline: Dict[str, float] = Field(default_factory=dict)
    sample_count: int = 0


class TypingProfile(BaseModel):
    """Typing rhythm baseline profile."""
    avg_speed_wpm: float = 0.0
    avg_inter_key_interval: float = 0.0
    inter_key_variance: float = 0.0
    avg_hold_time: float = 0.0
    hold_time_variance: float = 0.0
    bigram_timings: Dict[str, float] = Field(default_factory=dict)
    typing_rhythm_vector: List[float] = Field(default_factory=list)


class WritingProfile(BaseModel):
    """Writing style baseline profile."""
    style_embedding: List[float] = Field(default_factory=list)
    avg_sentence_length: float = 0.0
    vocabulary_richness: float = 0.0
    avg_word_length: float = 0.0
    complexity_score: float = 0.0
    pos_distribution: Dict[str, float] = Field(default_factory=dict)


class AcousticProfile(BaseModel):
    """Room acoustic baseline profile."""
    mfcc_baseline: List[float] = Field(default_factory=list)
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    ambient_noise_level: float = 0.0
    room_signature_vector: List[float] = Field(default_factory=list)


class BehavioralProfile(BaseModel):
    """Complete student behavioral fingerprint."""
    student_id: str
    session_id: str
    gaze_profile: GazeProfile = Field(default_factory=GazeProfile)
    typing_profile: TypingProfile = Field(default_factory=TypingProfile)
    writing_profile: WritingProfile = Field(default_factory=WritingProfile)
    acoustic_profile: AcousticProfile = Field(default_factory=AcousticProfile)
    calibration_status: CalibrationStatus = CalibrationStatus.NOT_STARTED
    created_at: datetime = Field(default_factory=datetime.now)
    calibration_duration_seconds: float = 0.0


# ─── Monitoring Schemas ──────────────────────────────────────────────────────

class FrameData(BaseModel):
    """Video frame for live monitoring."""
    session_id: str
    frame_base64: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class KeystrokeData(BaseModel):
    """Real-time keystroke data."""
    session_id: str
    keystrokes: List[TypingCalibrationData]
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class AudioChunkData(BaseModel):
    """Real-time audio chunk."""
    session_id: str
    audio_base64: str
    sample_rate: int = 16000
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class TextSubmission(BaseModel):
    """Text for stylometric analysis."""
    session_id: str
    text: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


# ─── Anomaly & Risk Schemas ──────────────────────────────────────────────────

class ModuleScore(BaseModel):
    """Score from a single detection module."""
    module: ModuleType
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class AnomalyEvent(BaseModel):
    """A flagged anomaly event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    module: ModuleType
    severity: float = Field(ge=0.0, le=1.0)
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class RiskScore(BaseModel):
    """Complete risk assessment."""
    session_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    module_scores: Dict[str, ModuleScore] = Field(default_factory=dict)
    fusion_weights: Dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
    top_contributors: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class RiskTimeline(BaseModel):
    """Risk score over time with events."""
    session_id: str
    scores: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[AnomalyEvent] = Field(default_factory=list)


# ─── Session Schemas ─────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """Create a new exam session."""
    student_id: str
    exam_id: Optional[str] = None
    student_name: Optional[str] = None


class SessionData(BaseModel):
    """Complete session information."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    exam_id: Optional[str] = None
    student_name: Optional[str] = None
    behavioral_profile: Optional[BehavioralProfile] = None
    current_risk: Optional[RiskScore] = None
    calibration_status: CalibrationStatus = CalibrationStatus.NOT_STARTED
    is_active: bool = True
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None


# ─── WebSocket Schemas ───────────────────────────────────────────────────────

class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "risk_update", "anomaly_event", "calibration_progress"
    data: Dict[str, Any]
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
