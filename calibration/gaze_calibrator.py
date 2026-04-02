"""
Gaze Calibrator
Establishes gaze pattern baseline using MediaPipe Face Mesh.
"""

import numpy as np
import cv2
import base64
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# MediaPipe face mesh iris landmark indices
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Head pose model points
FACE_3D_MODEL = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (-225.0, 170.0, -135.0),  # Left eye corner
    (225.0, 170.0, -135.0),   # Right eye corner
    (-150.0, -150.0, -125.0), # Left mouth corner
    (150.0, -150.0, -125.0),  # Right mouth corner
], dtype=np.float64)


class GazeCalibrator:
    """Collects and analyzes gaze patterns during calibration."""

    def __init__(self):
        self.gaze_vectors: List[np.ndarray] = []
        self.head_poses: List[Dict[str, float]] = []
        self.downward_glances = 0
        self.total_frames = 0
        self._face_mesh = None

    def _get_face_mesh(self):
        """Lazy-load MediaPipe face mesh."""
        if self._face_mesh is None:
            try:
                import mediapipe as mp
                self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except ImportError:
                logger.warning("MediaPipe not installed. Using synthetic gaze data.")
                return None
        return self._face_mesh

    def process_frame(self, frame_base64: str) -> Dict[str, Any]:
        """Process a single calibration frame for gaze data."""
        self.total_frames += 1

        try:
            # Decode frame
            frame_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return self._process_synthetic()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            face_mesh = self._get_face_mesh()
            if face_mesh is None:
                return self._process_synthetic()

            results = face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                
                # Extract iris centers
                left_iris_center = self._get_landmark_center(landmarks, LEFT_IRIS, w, h)
                right_iris_center = self._get_landmark_center(landmarks, RIGHT_IRIS, w, h)
                left_eye_center = self._get_landmark_center(landmarks, LEFT_EYE, w, h)
                right_eye_center = self._get_landmark_center(landmarks, RIGHT_EYE, w, h)

                # Compute gaze direction (iris offset from eye center)
                left_gaze = (left_iris_center - left_eye_center) / max(w, 1)
                right_gaze = (right_iris_center - right_eye_center) / max(w, 1)
                avg_gaze = (left_gaze + right_gaze) / 2.0

                self.gaze_vectors.append(avg_gaze)

                # Detect downward glance
                if avg_gaze[1] > 0.02:  # Looking down
                    self.downward_glances += 1

                # Head pose estimation
                head_pose = self._estimate_head_pose(landmarks, w, h)
                self.head_poses.append(head_pose)

                return {
                    "gaze_direction": avg_gaze.tolist(),
                    "head_pose": head_pose,
                    "face_detected": True
                }
            else:
                return self._process_synthetic()

        except Exception as e:
            logger.debug(f"Frame processing error: {e}")
            return self._process_synthetic()

    def _process_synthetic(self) -> Dict[str, Any]:
        """Generate synthetic gaze data when camera/mediapipe unavailable."""
        gaze = np.random.normal(0, 0.01, 2)
        self.gaze_vectors.append(gaze)
        head_pose = {"pitch": np.random.normal(0, 2), "yaw": np.random.normal(0, 3), "roll": np.random.normal(0, 1)}
        self.head_poses.append(head_pose)
        if gaze[1] > 0.02:
            self.downward_glances += 1
        return {
            "gaze_direction": gaze.tolist(),
            "head_pose": head_pose,
            "face_detected": False
        }

    def _get_landmark_center(self, landmarks, indices, w, h) -> np.ndarray:
        """Get the center point of specified landmarks."""
        points = []
        for idx in indices:
            lm = landmarks.landmark[idx]
            points.append([lm.x * w, lm.y * h])
        return np.mean(points, axis=0)

    def _estimate_head_pose(self, landmarks, w, h) -> Dict[str, float]:
        """Estimate head pose from face landmarks."""
        # Key landmark indices for pose estimation
        indices = [1, 152, 263, 33, 287, 57]
        image_points = np.array([
            [landmarks.landmark[idx].x * w, landmarks.landmark[idx].y * h]
            for idx in indices
        ], dtype=np.float64)

        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        success, rvec, tvec = cv2.solvePnP(
            FACE_3D_MODEL, image_points, camera_matrix, dist_coeffs
        )

        if success:
            rmat, _ = cv2.Rodrigues(rvec)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
            return {"pitch": float(angles[0]), "yaw": float(angles[1]), "roll": float(angles[2])}
        
        return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

    def get_profile(self) -> Dict[str, Any]:
        """Generate gaze baseline profile from collected data."""
        if not self.gaze_vectors:
            return {
                "mean_direction": [0.0, 0.0],
                "variance": [0.01, 0.01],
                "downward_glance_frequency": 0.0,
                "head_pose_baseline": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "sample_count": 0
            }

        gaze_array = np.array(self.gaze_vectors)
        mean_direction = np.mean(gaze_array, axis=0).tolist()
        variance = np.var(gaze_array, axis=0).tolist()
        
        head_pose_baseline = {}
        if self.head_poses:
            for key in ["pitch", "yaw", "roll"]:
                values = [p[key] for p in self.head_poses]
                head_pose_baseline[key] = float(np.mean(values))

        return {
            "mean_direction": mean_direction,
            "variance": variance,
            "downward_glance_frequency": self.downward_glances / max(self.total_frames, 1),
            "head_pose_baseline": head_pose_baseline,
            "sample_count": len(self.gaze_vectors)
        }
