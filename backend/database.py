"""
ABIE Database Module
MongoDB connection and operations using motor async driver.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Async MongoDB database manager."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Verify connection
            await self.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}. Running in memory-only mode.")
            self.client = None
            self.db = None

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.db is not None

    # ─── Session Operations ───────────────────────────────────────────────

    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new exam session."""
        if not self.is_connected:
            return session_data.get("session_id", "")
        result = await self.db.sessions.insert_one(session_data)
        return str(result.inserted_id)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        if not self.is_connected:
            return None
        return await self.db.sessions.find_one({"session_id": session_id})

    async def update_session(self, session_id: str, update_data: Dict[str, Any]):
        """Update session data."""
        if not self.is_connected:
            return
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )

    # ─── Profile Operations ──────────────────────────────────────────────

    async def save_profile(self, profile_data: Dict[str, Any]):
        """Save behavioral profile."""
        if not self.is_connected:
            return
        await self.db.profiles.update_one(
            {"student_id": profile_data["student_id"], "session_id": profile_data["session_id"]},
            {"$set": profile_data},
            upsert=True
        )

    async def get_profile(self, student_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get behavioral profile."""
        if not self.is_connected:
            return None
        return await self.db.profiles.find_one({
            "student_id": student_id,
            "session_id": session_id
        })

    # ─── Risk Event Operations ───────────────────────────────────────────

    async def log_risk_event(self, event_data: Dict[str, Any]):
        """Log a risk/anomaly event."""
        if not self.is_connected:
            return
        event_data["logged_at"] = datetime.now()
        await self.db.risk_events.insert_one(event_data)

    async def get_risk_events(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get risk events for a session."""
        if not self.is_connected:
            return []
        cursor = self.db.risk_events.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    # ─── Risk Score Operations ───────────────────────────────────────────

    async def save_risk_score(self, score_data: Dict[str, Any]):
        """Save a risk score snapshot."""
        if not self.is_connected:
            return
        await self.db.risk_scores.insert_one(score_data)

    async def get_risk_timeline(self, session_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get risk score timeline."""
        if not self.is_connected:
            return []
        cursor = self.db.risk_scores.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).limit(limit)
        return await cursor.to_list(length=limit)


# Singleton database instance
database = Database()
