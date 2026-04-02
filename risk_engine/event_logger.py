"""
Event Logger
Logs all anomaly events with timestamps and details.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


class EventLogger:
    """Logs anomaly events for audit trail and timeline visualization."""

    def __init__(self, log_dir: Optional[str] = None):
        self.events: deque = deque(maxlen=10000)
        self.log_dir = Path(log_dir) if log_dir else None
        
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        session_id: str,
        module: str,
        severity: float,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log an anomaly event."""
        event = {
            "session_id": session_id,
            "module": module,
            "severity": round(severity, 4),
            "description": description,
            "details": details or {},
            "timestamp": time.time(),
            "time_readable": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.events.append(event)
        
        # Optionally write to file
        if self.log_dir:
            self._write_to_file(session_id, event)
        
        logger.info(f"Event [{module}] severity={severity:.2f}: {description}")
        return event

    def get_events(
        self,
        session_id: Optional[str] = None,
        module: Optional[str] = None,
        min_severity: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get filtered events."""
        filtered = []
        for event in reversed(self.events):
            if session_id and event["session_id"] != session_id:
                continue
            if module and event["module"] != module:
                continue
            if event["severity"] < min_severity:
                continue
            filtered.append(event)
            if len(filtered) >= limit:
                break
        return filtered

    def get_event_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of events for a session."""
        session_events = [e for e in self.events if e["session_id"] == session_id]
        
        if not session_events:
            return {"total_events": 0, "by_module": {}, "avg_severity": 0}
        
        by_module = {}
        severities = []
        for event in session_events:
            module = event["module"]
            if module not in by_module:
                by_module[module] = {"count": 0, "total_severity": 0}
            by_module[module]["count"] += 1
            by_module[module]["total_severity"] += event["severity"]
            severities.append(event["severity"])
        
        for module_data in by_module.values():
            module_data["avg_severity"] = round(
                module_data["total_severity"] / module_data["count"], 4
            )
        
        return {
            "total_events": len(session_events),
            "by_module": by_module,
            "avg_severity": round(sum(severities) / len(severities), 4),
            "max_severity": round(max(severities), 4)
        }

    def _write_to_file(self, session_id: str, event: Dict[str, Any]):
        """Write event to a log file."""
        try:
            log_file = self.log_dir / f"{session_id}.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write event log: {e}")


# Global event logger
event_logger = EventLogger()
