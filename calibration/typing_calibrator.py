"""
Typing Calibrator
Establishes typing rhythm baseline from keystroke timing data.
"""

import numpy as np
from typing import Dict, List, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TypingCalibrator:
    """Collects and analyzes typing rhythm during calibration."""

    def __init__(self):
        self.keystrokes: List[Dict[str, Any]] = []
        self.inter_key_intervals: List[float] = []
        self.hold_times: List[float] = []
        self.bigram_timings: Dict[str, List[float]] = defaultdict(list)
        self.prev_key: str = ""
        self.prev_key_up_time: float = 0.0
        self.word_timestamps: List[float] = []
        self.char_count = 0

    def process_keystroke(self, key: str, key_down: float, key_up: float) -> Dict[str, Any]:
        """Process a single keystroke for calibration."""
        hold_time = key_up - key_down
        self.hold_times.append(hold_time)
        self.char_count += 1

        # Inter-key interval
        if self.prev_key_up_time > 0:
            iki = key_down - self.prev_key_up_time
            if 0 < iki < 5.0:  # Ignore unreasonable intervals
                self.inter_key_intervals.append(iki)

        # Bigram timing
        if self.prev_key:
            bigram = f"{self.prev_key}-{key}"
            if self.prev_key_up_time > 0:
                bigram_time = key_down - self.prev_key_up_time
                if 0 < bigram_time < 5.0:
                    self.bigram_timings[bigram].append(bigram_time)

        # Track word boundaries for WPM
        if key == " " or key == "Enter":
            self.word_timestamps.append(key_down)

        self.keystrokes.append({
            "key": key,
            "key_down": key_down,
            "key_up": key_up,
            "hold_time": hold_time
        })

        self.prev_key = key
        self.prev_key_up_time = key_up

        return {
            "samples_collected": len(self.keystrokes),
            "current_iki": self.inter_key_intervals[-1] if self.inter_key_intervals else 0
        }

    def get_profile(self) -> Dict[str, Any]:
        """Generate typing rhythm baseline profile."""
        if not self.keystrokes:
            return {
                "avg_speed_wpm": 0.0,
                "avg_inter_key_interval": 0.0,
                "inter_key_variance": 0.0,
                "avg_hold_time": 0.0,
                "hold_time_variance": 0.0,
                "bigram_timings": {},
                "typing_rhythm_vector": []
            }

        # Calculate WPM
        wpm = 0.0
        if len(self.word_timestamps) >= 2:
            duration_minutes = (self.word_timestamps[-1] - self.word_timestamps[0]) / 60.0
            if duration_minutes > 0:
                wpm = len(self.word_timestamps) / duration_minutes

        # Inter-key interval stats
        iki_arr = np.array(self.inter_key_intervals) if self.inter_key_intervals else np.array([0.0])
        
        # Hold time stats
        ht_arr = np.array(self.hold_times) if self.hold_times else np.array([0.0])
        
        # Average bigram timings
        avg_bigrams = {}
        for bigram, times in self.bigram_timings.items():
            if len(times) >= 2:
                avg_bigrams[bigram] = float(np.mean(times))

        # Build rhythm vector (statistical features)
        rhythm_vector = [
            float(np.mean(iki_arr)),
            float(np.std(iki_arr)),
            float(np.median(iki_arr)),
            float(np.percentile(iki_arr, 25)) if len(iki_arr) > 1 else 0.0,
            float(np.percentile(iki_arr, 75)) if len(iki_arr) > 1 else 0.0,
            float(np.mean(ht_arr)),
            float(np.std(ht_arr)),
            float(np.median(ht_arr)),
            wpm,
            float(len(self.keystrokes))
        ]

        return {
            "avg_speed_wpm": round(wpm, 2),
            "avg_inter_key_interval": round(float(np.mean(iki_arr)), 4),
            "inter_key_variance": round(float(np.var(iki_arr)), 6),
            "avg_hold_time": round(float(np.mean(ht_arr)), 4),
            "hold_time_variance": round(float(np.var(ht_arr)), 6),
            "bigram_timings": avg_bigrams,
            "typing_rhythm_vector": [round(v, 6) for v in rhythm_vector]
        }
