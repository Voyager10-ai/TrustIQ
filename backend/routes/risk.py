"""
Risk API Routes
Endpoints for risk assessment and explainability.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from backend.database import database
from backend.routes.monitoring import risk_calculators

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{session_id}")
async def get_risk_score(session_id: str) -> Dict[str, Any]:
    """Get full risk breakdown for a session."""
    if session_id not in risk_calculators:
        raise HTTPException(status_code=404, detail="No monitoring data for this session")
    
    calc = risk_calculators[session_id]
    risk = calc.get_current_risk()
    
    return {
        "session_id": session_id,
        "overall_score": risk.overall_score,
        "risk_level": risk.risk_level.value,
        "module_scores": {
            name: {
                "score": score.score,
                "confidence": score.confidence,
                "details": score.details
            }
            for name, score in risk.module_scores.items()
        },
        "fusion_weights": risk.fusion_weights,
        "explanation": risk.explanation,
        "top_contributors": risk.top_contributors
    }


@router.get("/{session_id}/timeline")
async def get_risk_timeline(session_id: str) -> Dict[str, Any]:
    """Get risk score timeline with events."""
    if session_id not in risk_calculators:
        raise HTTPException(status_code=404, detail="No monitoring data for this session")
    
    calc = risk_calculators[session_id]
    timeline = calc.get_timeline()
    
    # Also get events from database
    db_events = await database.get_risk_events(session_id)
    
    return {
        "session_id": session_id,
        "timeline": timeline,
        "events": db_events
    }


@router.get("/{session_id}/explain")
async def get_risk_explanation(session_id: str) -> Dict[str, Any]:
    """Get explainable AI breakdown of current risk."""
    if session_id not in risk_calculators:
        raise HTTPException(status_code=404, detail="No monitoring data for this session")
    
    calc = risk_calculators[session_id]
    explanation = calc.get_explanation()
    
    return {
        "session_id": session_id,
        "explanation": explanation
    }
