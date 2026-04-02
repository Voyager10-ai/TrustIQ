"""
WebSocket Route
Real-time streaming + multiplexed exam data handling.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging
import time

from backend.routes.monitoring import risk_calculators
from models.vision.face_detector import FaceDetector

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = set()
        self.connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.connections:
            self.connections[session_id].discard(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")

    async def broadcast(self, session_id: str, message: dict):
        if session_id not in self.connections:
            return
        dead = set()
        for ws in self.connections[session_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.connections[session_id].discard(ws)

    def get_active_sessions(self):
        """Return list of active session IDs."""
        return list(self.connections.keys())


manager = ConnectionManager()


# ─── Original dashboard stream ────────────────────────────────────────────────

@router.websocket("/ws/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """Stream real-time risk data to the dashboard."""
    await manager.connect(session_id, websocket)

    try:
        while True:
            if session_id in risk_calculators:
                calc = risk_calculators[session_id]
                risk = calc.get_current_risk()

                await websocket.send_json({
                    "type": "risk_update",
                    "data": {
                        "overall_score": risk.overall_score,
                        "risk_level": risk.risk_level.value,
                        "module_scores": {
                            name: {"score": score.score, "confidence": score.confidence}
                            for name, score in risk.module_scores.items()
                        },
                        "explanation": risk.explanation,
                        "top_contributors": risk.top_contributors
                    },
                    "timestamp": risk.timestamp
                })
            else:
                await websocket.send_json({
                    "type": "waiting",
                    "data": {"message": "Waiting for monitoring data..."},
                    "timestamp": 0
                })

            await asyncio.sleep(0.5)

            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id, websocket)


# ─── Exam WebSocket (multiplexed student data) ───────────────────────────────

# Store incoming exam data per session for analysis
exam_sessions: Dict[str, dict] = {}


@router.websocket("/ws/exam/{session_id}")
async def websocket_exam(websocket: WebSocket, session_id: str):
    """
    Multiplexed WebSocket for student exam portal.
    Receives: frames, audio chunks, keystrokes, mouse data, text
    Sends: risk_update messages back to the student
    """
    await manager.connect(session_id, websocket)

    # Initialize session data
    exam_sessions[session_id] = {
        "start_time": time.time(),
        "frame_count": 0,
        "audio_count": 0,
        "keystroke_count": 0,
        "mouse_count": 0,
        "text_submissions": 0,
        "paste_count": 0,
        "tab_switches": 0,
        "risk_score": 0.0,
        "module_scores": {},
        "face_detector": FaceDetector(),
        "latest_vision_risk": 0.0
    }

    logger.info(f"Exam session started: {session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")
            payload = msg.get("data")

            session = exam_sessions[session_id]

            if msg_type == "frame":
                # Video frame received — pass to vision analyzer
                session["frame_count"] += 1
                try:
                    # Strip base64 prefix if present (usually we just get raw base64 from canvas)
                    b64_data = payload.split(",")[-1] if "," in payload else payload
                    analysis = session["face_detector"].analyze(b64_data)
                    session["latest_vision_risk"] = analysis.get("anomaly_score", 0.0)
                    session["latest_vision_details"] = analysis.get("details", {})
                    # Store latest frame for Proctor Dashboard visibility
                    session["latest_frame"] = payload
                except Exception as e:
                    logger.warning(f"Failed to process frame for session {session_id}: {e}")
                
                # We don't log every frame to avoid spam, but we update the risk score based on real vision analysis!
                if session["frame_count"] % 10 == 0:
                    logger.debug(f"[{session_id}] Processed {session['frame_count']} frames. Vision Risk: {session['latest_vision_risk']}")

            elif msg_type == "audio":
                # Audio chunk received — pass to audio analyzer
                session["audio_count"] += 1
                logger.debug(f"[{session_id}] Audio chunk #{session['audio_count']}")

            elif msg_type == "keystrokes":
                # Keystroke batch received — pass to behavior analyzer
                if isinstance(payload, list):
                    session["keystroke_count"] += len(payload)
                    # Count paste events and tab switches
                    for entry in payload:
                        if entry.get("isPaste"):
                            session["paste_count"] += 1
                        if entry.get("isTabSwitch"):
                            session["tab_switches"] += 1
                logger.debug(f"[{session_id}] Keystrokes: {session['keystroke_count']} total")

            elif msg_type == "mouse":
                # Mouse data batch received
                if isinstance(payload, list):
                    session["mouse_count"] += len(payload)
                logger.debug(f"[{session_id}] Mouse events: {session['mouse_count']} total")

            elif msg_type == "text":
                # Text submission for stylometric analysis
                session["text_submissions"] += 1
                logger.debug(f"[{session_id}] Text submission #{session['text_submissions']}")

            # ─── Compute risk score ──
            # Simulate real analysis using data volume as proxy
            elapsed = time.time() - session["start_time"]
            
            # Risk factors
            risk_factors = {}
            
            # Vision: Map FaceDetector's true anomaly_score -> vision risk factor (max 0.6 contribution)
            # If anomaly_score is high (e.g. no face = 0.4, multiple faces = 0.9), it pushes the risk up!
            risk_factors["vision"] = min(1.0, session.get("latest_vision_risk", 0.0))
            
            # Behavior: paste count and tab switches increase risk
            paste_risk = min(1.0, session["paste_count"] * 0.2)
            tab_risk = min(1.0, session["tab_switches"] * 0.15)
            risk_factors["behavior"] = min(1.0, paste_risk + tab_risk)
            
            # Audio: simulated baseline
            risk_factors["audio"] = 0.05 + (0.1 if session["audio_count"] == 0 and elapsed > 5 else 0)
            
            # Stylometry: simulated
            risk_factors["stylometry"] = 0.05
            
            # Environmental: simulated
            risk_factors["environmental"] = 0.03

            # Weighted fusion
            weights = {"vision": 0.25, "behavior": 0.25, "audio": 0.20, "stylometry": 0.20, "environmental": 0.10}
            overall = sum(risk_factors.get(k, 0) * w for k, w in weights.items()) * 100
            
            # EMA smoothing
            session["risk_score"] = 0.3 * overall + 0.7 * session.get("risk_score", 0)
            session["module_scores"] = risk_factors

            # Send risk update back to student periodically
            if session["frame_count"] % 4 == 0 or msg_type in ("keystrokes", "text"):
                risk_level = "safe" if session["risk_score"] < 30 else "suspicious" if session["risk_score"] < 60 else "high_risk" if session["risk_score"] < 80 else "critical"
                
                await websocket.send_json({
                    "type": "risk_update",
                    "overall_score": session["risk_score"],
                    "risk_level": risk_level,
                    "module_scores": risk_factors,
                    "stats": {
                        "frames": session["frame_count"],
                        "keystrokes": session["keystroke_count"],
                        "pastes": session["paste_count"],
                        "tab_switches": session["tab_switches"]
                    },
                    "active_tracking": session.get("latest_vision_details", {}),
                    "timestamp": time.time()
                })

    except WebSocketDisconnect:
        logger.info(f"Exam session ended: {session_id}")
        manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"Exam WebSocket error: {e}")
        manager.disconnect(session_id, websocket)
    finally:
        # Log final session stats
        if session_id in exam_sessions:
            session = exam_sessions[session_id]
            logger.info(
                f"Session {session_id} final stats: "
                f"frames={session['frame_count']}, "
                f"keystrokes={session['keystroke_count']}, "
                f"pastes={session['paste_count']}, "
                f"tab_switches={session['tab_switches']}, "
                f"risk={session['risk_score']:.1f}"
            )


# ─── Proctor API: get active sessions ────────────────────────────────────────

@router.get("/ws/active-sessions")
async def get_active_sessions():
    """Return list of active exam sessions with their current risk data."""
    sessions = []
    for sid, data in exam_sessions.items():
        if sid in manager.connections:
            sessions.append({
                "session_id": sid,
                "risk_score": data.get("risk_score", 0),
                "module_scores": data.get("module_scores", {}),
                "stats": {
                    "frames": data.get("frame_count", 0),
                    "keystrokes": data.get("keystroke_count", 0),
                    "pastes": data.get("paste_count", 0),
                    "tab_switches": data.get("tab_switches", 0),
                },
                "latest_frame": data.get("latest_frame", None),
                "active_tracking": data.get("latest_vision_details", {}),
                "duration": time.time() - data.get("start_time", time.time())
            })
    return {"sessions": sessions}
