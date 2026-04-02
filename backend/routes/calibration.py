"""
Calibration API Routes
Endpoints for collecting behavioral baseline data.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
import time
import logging

from backend.schemas import (
    SessionCreate, SessionData, BehavioralProfile,
    GazeCalibrationData, TypingCalibrationData,
    WritingCalibrationData, AudioCalibrationData,
    CalibrationStatus, GazeProfile, TypingProfile,
    WritingProfile, AcousticProfile
)
from backend.database import database
from calibration.calibrator import Calibrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calibration", tags=["calibration"])

# In-memory session store (backed by MongoDB when available)
active_sessions: Dict[str, SessionData] = {}
calibrators: Dict[str, Calibrator] = {}


@router.post("/start")
async def start_calibration(session_create: SessionCreate) -> Dict[str, Any]:
    """Start a new calibration session."""
    session_id = str(uuid.uuid4())
    
    session = SessionData(
        session_id=session_id,
        student_id=session_create.student_id,
        exam_id=session_create.exam_id,
        student_name=session_create.student_name,
        calibration_status=CalibrationStatus.IN_PROGRESS
    )
    
    active_sessions[session_id] = session
    calibrators[session_id] = Calibrator(session_id, session_create.student_id)
    
    # Persist to MongoDB
    await database.create_session(session.model_dump(mode="json"))
    
    logger.info(f"Calibration started for student {session_create.student_id}, session {session_id}")
    
    return {
        "session_id": session_id,
        "status": "calibration_started",
        "message": "Please complete the calibration steps: gaze, typing, writing, and audio.",
        "steps": ["gaze", "typing", "writing", "audio"]
    }


@router.post("/gaze/{session_id}")
async def submit_gaze_data(session_id: str, data: GazeCalibrationData) -> Dict[str, Any]:
    """Submit gaze calibration frame data."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    result = calibrator.process_gaze_sample(data)
    
    return {
        "status": "accepted",
        "samples_collected": result["samples_collected"],
        "progress": result["progress"],
        "message": result.get("message", "Gaze sample recorded")
    }


@router.post("/typing/{session_id}")
async def submit_typing_data(session_id: str, data: TypingCalibrationData) -> Dict[str, Any]:
    """Submit typing calibration keystroke data."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    result = calibrator.process_typing_sample(data)
    
    return {
        "status": "accepted",
        "samples_collected": result["samples_collected"],
        "progress": result["progress"]
    }


@router.post("/writing/{session_id}")
async def submit_writing_data(session_id: str, data: WritingCalibrationData) -> Dict[str, Any]:
    """Submit writing sample for stylometric baseline."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    result = calibrator.process_writing_sample(data)
    
    return {
        "status": "accepted",
        "word_count": result["word_count"],
        "progress": result["progress"]
    }


@router.post("/audio/{session_id}")
async def submit_audio_data(session_id: str, data: AudioCalibrationData) -> Dict[str, Any]:
    """Submit room audio sample for acoustic baseline."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    result = calibrator.process_audio_sample(data)
    
    return {
        "status": "accepted",
        "duration_collected": result["duration_collected"],
        "progress": result["progress"]
    }


@router.post("/finalize/{session_id}")
async def finalize_calibration(session_id: str) -> Dict[str, Any]:
    """Finalize calibration and generate behavioral fingerprint."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    
    try:
        profile = calibrator.generate_profile()
        
        # Update session
        if session_id in active_sessions:
            active_sessions[session_id].behavioral_profile = profile
            active_sessions[session_id].calibration_status = CalibrationStatus.COMPLETED
        
        # Persist profile
        await database.save_profile(profile.model_dump(mode="json"))
        await database.update_session(session_id, {
            "calibration_status": CalibrationStatus.COMPLETED.value
        })
        
        logger.info(f"Calibration finalized for session {session_id}")
        
        return {
            "status": "completed",
            "session_id": session_id,
            "profile": profile.model_dump(mode="json"),
            "message": "Behavioral fingerprint generated successfully."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{session_id}")
async def get_calibration_status(session_id: str) -> Dict[str, Any]:
    """Get calibration progress status."""
    if session_id not in calibrators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    calibrator = calibrators[session_id]
    return calibrator.get_progress()
