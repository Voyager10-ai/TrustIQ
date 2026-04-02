"""
Main Calibrator
Orchestrates all baseline collection to generate a BehavioralProfile.
"""

import time
import logging
from typing import Dict, Any

from backend.schemas import (
    BehavioralProfile, GazeProfile, TypingProfile,
    WritingProfile, AcousticProfile, CalibrationStatus,
    GazeCalibrationData, TypingCalibrationData,
    WritingCalibrationData, AudioCalibrationData
)
from calibration.gaze_calibrator import GazeCalibrator
from calibration.typing_calibrator import TypingCalibrator
from calibration.writing_calibrator import WritingCalibrator
from calibration.acoustic_calibrator import AcousticCalibrator

logger = logging.getLogger(__name__)


class Calibrator:
    """
    Master calibrator that orchestrates all four baseline collectors.
    
    Usage:
        calibrator = Calibrator(session_id, student_id)
        calibrator.process_gaze_sample(data)
        calibrator.process_typing_sample(data)
        calibrator.process_writing_sample(data)
        calibrator.process_audio_sample(data)
        profile = calibrator.generate_profile()
    """

    def __init__(self, session_id: str, student_id: str):
        self.session_id = session_id
        self.student_id = student_id
        self.start_time = time.time()
        
        # Sub-calibrators
        self.gaze = GazeCalibrator()
        self.typing = TypingCalibrator()
        self.writing = WritingCalibrator()
        self.acoustic = AcousticCalibrator()
        
        # Progress tracking
        self.progress = {
            "gaze": {"samples": 0, "target": 50, "complete": False},
            "typing": {"samples": 0, "target": 30, "complete": False},
            "writing": {"samples": 0, "target": 1, "complete": False},
            "audio": {"samples": 0, "target": 5, "complete": False}
        }

    def process_gaze_sample(self, data: GazeCalibrationData) -> Dict[str, Any]:
        """Process a gaze calibration sample."""
        result = self.gaze.process_frame(data.frame_base64)
        self.progress["gaze"]["samples"] += 1
        
        if self.progress["gaze"]["samples"] >= self.progress["gaze"]["target"]:
            self.progress["gaze"]["complete"] = True
        
        progress = self.progress["gaze"]["samples"] / self.progress["gaze"]["target"]
        return {
            "samples_collected": self.progress["gaze"]["samples"],
            "progress": min(progress, 1.0),
            "message": "Gaze baseline complete!" if self.progress["gaze"]["complete"] else "Keep looking at the screen naturally."
        }

    def process_typing_sample(self, data: TypingCalibrationData) -> Dict[str, Any]:
        """Process a typing calibration sample."""
        self.typing.process_keystroke(data.key, data.key_down_time, data.key_up_time)
        self.progress["typing"]["samples"] += 1
        
        if self.progress["typing"]["samples"] >= self.progress["typing"]["target"]:
            self.progress["typing"]["complete"] = True
        
        progress = self.progress["typing"]["samples"] / self.progress["typing"]["target"]
        return {
            "samples_collected": self.progress["typing"]["samples"],
            "progress": min(progress, 1.0)
        }

    def process_writing_sample(self, data: WritingCalibrationData) -> Dict[str, Any]:
        """Process a writing calibration sample."""
        result = self.writing.process_sample(data.text)
        self.progress["writing"]["samples"] += 1
        self.progress["writing"]["complete"] = True
        
        return {
            "word_count": result["word_count"],
            "progress": 1.0
        }

    def process_audio_sample(self, data: AudioCalibrationData) -> Dict[str, Any]:
        """Process an audio calibration sample."""
        result = self.acoustic.process_chunk(data.audio_base64, data.sample_rate)
        self.progress["audio"]["samples"] += 1
        
        if self.progress["audio"]["samples"] >= self.progress["audio"]["target"]:
            self.progress["audio"]["complete"] = True
        
        progress = self.progress["audio"]["samples"] / self.progress["audio"]["target"]
        return {
            "duration_collected": result["duration_collected"],
            "progress": min(progress, 1.0)
        }

    def get_progress(self) -> Dict[str, Any]:
        """Get overall calibration progress."""
        overall = sum(1 for v in self.progress.values() if v["complete"]) / len(self.progress)
        return {
            "session_id": self.session_id,
            "overall_progress": overall,
            "modules": self.progress,
            "duration_seconds": time.time() - self.start_time,
            "ready_to_finalize": all(v["complete"] for v in self.progress.values())
        }

    def generate_profile(self) -> BehavioralProfile:
        """Generate the complete behavioral fingerprint."""
        duration = time.time() - self.start_time
        
        # Get profiles from each calibrator
        gaze_data = self.gaze.get_profile()
        typing_data = self.typing.get_profile()
        writing_data = self.writing.get_profile()
        acoustic_data = self.acoustic.get_profile()
        
        profile = BehavioralProfile(
            student_id=self.student_id,
            session_id=self.session_id,
            gaze_profile=GazeProfile(**gaze_data),
            typing_profile=TypingProfile(**typing_data),
            writing_profile=WritingProfile(**writing_data),
            acoustic_profile=AcousticProfile(**acoustic_data),
            calibration_status=CalibrationStatus.COMPLETED,
            calibration_duration_seconds=duration
        )
        
        logger.info(
            f"Behavioral profile generated for student {self.student_id} "
            f"(session {self.session_id}) in {duration:.1f}s"
        )
        
        return profile
