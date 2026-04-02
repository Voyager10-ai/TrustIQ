"""
Clipboard Detector
Detects copy-paste patterns and tab-switching behavior.
"""

import time
from typing import Dict, Any, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ClipboardDetector:
    """Detects suspicious clipboard and tab-switch behavior."""

    def __init__(self):
        self.paste_events = deque(maxlen=100)
        self.tab_switches = deque(maxlen=100)
        self.shortcut_history = deque(maxlen=200)

    def analyze_keystrokes(self, keystrokes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze keystrokes for copy-paste and tab-switch patterns.
        
        Looks for:
            - Ctrl+C / Ctrl+V patterns
            - Alt+Tab frequency
            - Rapid paste after tab switch
        """
        anomaly_score = 0.0
        details = {}
        
        paste_count = 0
        copy_count = 0
        tab_switch_count = 0

        for i, ks in enumerate(keystrokes):
            key = ks.get("key", "").lower()
            
            # Detect Ctrl+V (paste)
            if key == "v" and self._is_ctrl_held(keystrokes, i):
                paste_count += 1
                self.paste_events.append(ks.get("timestamp", time.time()))

            # Detect Ctrl+C (copy)
            if key == "c" and self._is_ctrl_held(keystrokes, i):
                copy_count += 1

            # Detect Alt+Tab
            if key == "tab" and self._is_alt_held(keystrokes, i):
                tab_switch_count += 1
                self.tab_switches.append(ks.get("timestamp", time.time()))

        details["paste_count"] = paste_count
        details["copy_count"] = copy_count
        details["tab_switches"] = tab_switch_count

        # 1. Excessive pasting
        if paste_count > 2:
            anomaly_score = min(paste_count / 5.0, 1.0)
            details["excessive_paste"] = True

        # 2. Tab switching frequency
        if tab_switch_count > 3:
            anomaly_score = max(anomaly_score, min(tab_switch_count / 6.0, 1.0))
            details["excessive_tab_switching"] = True

        # 3. Paste shortly after tab switch
        recent_pastes = [t for t in self.paste_events if time.time() - t < 10]
        recent_tabs = [t for t in self.tab_switches if time.time() - t < 10]
        
        for paste_time in recent_pastes:
            for tab_time in recent_tabs:
                if 0 < paste_time - tab_time < 3.0:
                    anomaly_score = max(anomaly_score, 0.85)
                    details["paste_after_tab_switch"] = True
                    break

        return {
            "anomaly_score": round(min(anomaly_score, 1.0), 4),
            "confidence": 0.75,
            "details": details
        }

    def _is_ctrl_held(self, keystrokes, index):
        """Check if Ctrl was held when a key was pressed."""
        if index > 0:
            prev = keystrokes[index - 1].get("key", "").lower()
            return prev in ("control", "ctrl", "meta", "command")
        return False

    def _is_alt_held(self, keystrokes, index):
        """Check if Alt was held when a key was pressed."""
        if index > 0:
            prev = keystrokes[index - 1].get("key", "").lower()
            return prev in ("alt", "option")
        return False
