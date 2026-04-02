"""
Monitoring API Routes
Endpoints for real-time exam monitoring.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from backend.schemas import (
    FrameData, KeystrokeData, AudioChunkData,
    TextSubmission, ModuleScore, ModuleType
)
from backend.database import database
from backend.routes.calibration import active_sessions, calibrators
from models.vision.vision_analyzer import VisionAnalyzer
from models.behavior.behavior_analyzer import BehaviorAnalyzer
from models.audio.audio_analyzer import AudioAnalyzer
from models.stylometry.stylometry_analyzer import StylometryAnalyzer
from models.fusion.fusion_engine import FusionEngine
from risk_engine.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor", tags=["monitoring"])

# Module instances
vision_analyzer = VisionAnalyzer()
behavior_analyzer = BehaviorAnalyzer()
audio_analyzer = AudioAnalyzer()
stylometry_analyzer = StylometryAnalyzer()
fusion_engine = FusionEngine()

# Risk calculators per session
risk_calculators: Dict[str, RiskCalculator] = {}


def _get_risk_calculator(session_id: str) -> RiskCalculator:
    """Get or create a risk calculator for a session."""
    if session_id not in risk_calculators:
        profile = None
        if session_id in active_sessions and active_sessions[session_id].behavioral_profile:
            profile = active_sessions[session_id].behavioral_profile
        risk_calculators[session_id] = RiskCalculator(session_id, profile)
    return risk_calculators[session_id]


@router.post("/frame")
async def analyze_frame(data: FrameData) -> Dict[str, Any]:
    """Analyze a video frame for vision anomalies."""
    session_id = data.session_id
    profile = None
    if session_id in active_sessions and active_sessions[session_id].behavioral_profile:
        profile = active_sessions[session_id].behavioral_profile
    
    # Run vision analysis
    vision_result = vision_analyzer.analyze_frame(
        data.frame_base64,
        baseline_profile=profile.gaze_profile if profile else None
    )
    
    # Update risk calculator
    calc = _get_risk_calculator(session_id)
    module_score = ModuleScore(
        module=ModuleType.VISION,
        score=vision_result["anomaly_score"],
        confidence=vision_result["confidence"],
        details=vision_result["details"]
    )
    risk_update = calc.update_score(module_score)
    
    # Log event if anomaly detected
    if vision_result["anomaly_score"] > 0.5:
        await database.log_risk_event({
            "session_id": session_id,
            "module": "vision",
            "score": vision_result["anomaly_score"],
            "details": vision_result["details"],
            "timestamp": data.timestamp
        })
    
    return {
        "vision_score": vision_result["anomaly_score"],
        "details": vision_result["details"],
        "overall_risk": risk_update["overall_score"],
        "risk_level": risk_update["risk_level"]
    }


@router.post("/keystrokes")
async def analyze_keystrokes(data: KeystrokeData) -> Dict[str, Any]:
    """Analyze keystroke data for behavioral anomalies."""
    session_id = data.session_id
    profile = None
    if session_id in active_sessions and active_sessions[session_id].behavioral_profile:
        profile = active_sessions[session_id].behavioral_profile
    
    behavior_result = behavior_analyzer.analyze_keystrokes(
        data.keystrokes,
        baseline_profile=profile.typing_profile if profile else None
    )
    
    calc = _get_risk_calculator(session_id)
    module_score = ModuleScore(
        module=ModuleType.BEHAVIOR,
        score=behavior_result["anomaly_score"],
        confidence=behavior_result["confidence"],
        details=behavior_result["details"]
    )
    risk_update = calc.update_score(module_score)
    
    if behavior_result["anomaly_score"] > 0.5:
        await database.log_risk_event({
            "session_id": session_id,
            "module": "behavior",
            "score": behavior_result["anomaly_score"],
            "details": behavior_result["details"],
            "timestamp": data.timestamp
        })
    
    return {
        "behavior_score": behavior_result["anomaly_score"],
        "details": behavior_result["details"],
        "overall_risk": risk_update["overall_score"],
        "risk_level": risk_update["risk_level"]
    }


@router.post("/audio")
async def analyze_audio(data: AudioChunkData) -> Dict[str, Any]:
    """Analyze audio chunk for acoustic anomalies."""
    session_id = data.session_id
    profile = None
    if session_id in active_sessions and active_sessions[session_id].behavioral_profile:
        profile = active_sessions[session_id].behavioral_profile
    
    audio_result = audio_analyzer.analyze_chunk(
        data.audio_base64,
        sample_rate=data.sample_rate,
        baseline_profile=profile.acoustic_profile if profile else None
    )
    
    calc = _get_risk_calculator(session_id)
    module_score = ModuleScore(
        module=ModuleType.AUDIO,
        score=audio_result["anomaly_score"],
        confidence=audio_result["confidence"],
        details=audio_result["details"]
    )
    risk_update = calc.update_score(module_score)
    
    if audio_result["anomaly_score"] > 0.5:
        await database.log_risk_event({
            "session_id": session_id,
            "module": "audio",
            "score": audio_result["anomaly_score"],
            "details": audio_result["details"],
            "timestamp": data.timestamp
        })
    
    return {
        "audio_score": audio_result["anomaly_score"],
        "details": audio_result["details"],
        "overall_risk": risk_update["overall_score"],
        "risk_level": risk_update["risk_level"]
    }


@router.post("/text")
async def analyze_text(data: TextSubmission) -> Dict[str, Any]:
    """Analyze submitted text for stylometric anomalies."""
    session_id = data.session_id
    profile = None
    if session_id in active_sessions and active_sessions[session_id].behavioral_profile:
        profile = active_sessions[session_id].behavioral_profile
    
    stylometry_result = stylometry_analyzer.analyze_text(
        data.text,
        baseline_profile=profile.writing_profile if profile else None
    )
    
    calc = _get_risk_calculator(session_id)
    module_score = ModuleScore(
        module=ModuleType.STYLOMETRY,
        score=stylometry_result["anomaly_score"],
        confidence=stylometry_result["confidence"],
        details=stylometry_result["details"]
    )
    risk_update = calc.update_score(module_score)
    
    if stylometry_result["anomaly_score"] > 0.5:
        await database.log_risk_event({
            "session_id": session_id,
            "module": "stylometry",
            "score": stylometry_result["anomaly_score"],
            "details": stylometry_result["details"],
            "timestamp": data.timestamp
        })
    
    return {
        "stylometry_score": stylometry_result["anomaly_score"],
        "details": stylometry_result["details"],
        "overall_risk": risk_update["overall_score"],
        "risk_level": risk_update["risk_level"]
    }


@router.get("/status/{session_id}")
async def get_monitoring_status(session_id: str) -> Dict[str, Any]:
    """Get current monitoring status and risk score."""
    calc = _get_risk_calculator(session_id)
    risk_score = calc.get_current_risk()
    
    return {
        "session_id": session_id,
        "overall_score": risk_score.overall_score,
        "risk_level": risk_score.risk_level.value,
        "module_scores": {k: v.model_dump() for k, v in risk_score.module_scores.items()},
        "explanation": risk_score.explanation,
        "top_contributors": risk_score.top_contributors
    }
