"""
Pose Estimation Module
======================

Handles MediaPipe integration and real-time pose detection from webcam feed.
Uses MediaPipe Pose for detecting body keypoints and tracking left/right hand
positions with confidence scores.

Key Responsibilities:
- Webcam video stream capture and processing
- MediaPipe pose inference and keypoint detection
- Hand position filtering and smoothing
- Confidence-based filtering of unreliable detections
"""

import sys
import os

user_site = os.path.expanduser("~") + r"\AppData\Roaming\Python\Python313\site-packages"
if user_site not in sys.path:
    sys.path.insert(0, user_site)

import cv2
import numpy as np
import threading
import queue
from typing import Dict, Tuple, Optional, List

try:
    from mediapipe.tasks.python.vision import PoseLandmarker, HandLandmarker
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
    from mediapipe import tasks
    mp = type('mp', (), {'solutions': type('solutions', (), {})})()
except ImportError as e:
    print(f"MediaPipe import error: {e}")
    mp = None


class PoseDetectionState:
    """
    Container for current pose detection results.

    Attributes:
        left_hand_pos: (x, y) position of left hand in screen coordinates
        right_hand_pos: (x, y) position of right hand in screen coordinates
        left_hand_confidence: Confidence score for left hand detection (0-1)
        right_hand_confidence: Confidence score for right hand detection (0-1)
        body_keypoints: All detected body keypoints (pose keypoints)
        timestamp: Frame number when detection occurred
        is_valid: True if both hands were detected with sufficient confidence
    """

    def __init__(self):
        self.left_hand_pos: Tuple[float, float] = (0, 0)
        self.right_hand_pos: Tuple[float, float] = (0, 0)
        self.left_hand_confidence: float = 0.0
        self.right_hand_confidence: float = 0.0
        self.body_keypoints: Optional[np.ndarray] = None
        self.timestamp: int = 0
        self.is_valid: bool = False
        # Extended hand information (MediaPipe Hands)
        # Each is either None or an array of shape (21, 3) with x,y in pixels and z in relative coords
        self.left_hand_landmarks: Optional[np.ndarray] = None
        self.right_hand_landmarks: Optional[np.ndarray] = None
        # Fingertip pixel positions: dict of landmark index -> (x,y)
        self.left_fingertips: Optional[Dict[int, Tuple[float, float]]] = None
        self.right_fingertips: Optional[Dict[int, Tuple[float, float]]] = None
        # Palm orientation vectors (nx, ny, nz) in camera coordinates (approximate)
        self.left_palm_orientation: Optional[Tuple[float, float, float]] = None
        self.right_palm_orientation: Optional[Tuple[float, float, float]] = None


class PoseEstimator:
    """
    Main pose estimation engine using MediaPipe.

    Manages webcam capture, MediaPipe inference, and pose filtering.
    Runs in a separate thread to avoid blocking Blender's UI.

    Attributes:
        webcam_index: Device index of webcam to use
        confidence_threshold: Minimum confidence to consider detection valid
        smoothing_factor: Exponential moving average factor (0-1)
        is_running: Thread control flag
    """

    # MediaPipe pose landmark indices
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16

    def __init__(self, webcam_index: int = 0, confidence_threshold: float = 0.5, debug_window: bool = False):
        """
        Initialize pose estimator.

        Args:
            webcam_index: Index of webcam device (0=default)
            confidence_threshold: Minimum confidence for valid keypoint
        """
        if mp is None:
            raise ImportError("MediaPipe not installed. Install with: pip install mediapipe")

        self.webcam_index = webcam_index
        self.confidence_threshold = confidence_threshold
        self.smoothing_factor = 0.7

        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.result_queue: queue.Queue = queue.Queue(maxsize=1)

        self.current_state = PoseDetectionState()
        self._prev_left_hand = (0.0, 0.0)
        self._prev_right_hand = (0.0, 0.0)
        self._image_width = 0
        self._image_height = 0
        self.debug = debug_window

        try:
            import pathlib
            import urllib.request

            model_dir = pathlib.Path.home() / ".mediapipe_models"
            model_dir.mkdir(exist_ok=True)

            pose_model_path = model_dir / "pose_landmarker.task"
            hand_model_path = model_dir / "hand_landmarker.task"

            pose_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite.task"
            hand_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker.task"

            if not pose_model_path.exists():
                print("[Init] Downloading pose model...")
                urllib.request.urlretrieve(pose_url, pose_model_path)
                print("[Init] Pose model downloaded")

            if not hand_model_path.exists():
                print("[Init] Downloading hand model...")
                urllib.request.urlretrieve(hand_url, hand_model_path)
                print("[Init] Hand model downloaded")

            base_options_pose = tasks.BaseOptions(model_asset_path=str(pose_model_path))
            options = tasks.vision.PoseLandmarkerOptions(
                base_options=base_options_pose,
                running_mode=VisionTaskRunningMode.IMAGE
            )
            self.pose = PoseLandmarker.create_from_options(options)

            base_options_hand = tasks.BaseOptions(model_asset_path=str(hand_model_path))
            hand_options = tasks.vision.HandLandmarkerOptions(
                base_options=base_options_hand,
                running_mode=VisionTaskRunningMode.IMAGE
            )
            self.hands = HandLandmarker.create_from_options(hand_options)
            print("[Init] MediaPipe models loaded successfully")
        except Exception as e:
            print(f"Error initializing MediaPipe models: {e}")
            import traceback
            traceback.print_exc()
            self.pose = None
            self.hands = None

    def _setup_mediapipe_params(self) -> Dict:
        """
        Configure MediaPipe parameters for pose detection.

        Returns:
            Dictionary with MediaPipe configuration
        """
        params = dict()
        params["model_complexity"] = 1
        params["smooth_landmarks"] = True
        params["min_detection_confidence"] = self.confidence_threshold
        params["min_tracking_confidence"] = self.confidence_threshold

        return params

    def _landmark_to_pixel(
        self,
        landmark,
        width: int,
        height: int
    ) -> Tuple[Tuple[float, float], float]:
        """
        Convert a MediaPipe landmark to pixel coordinates.

        Args:
            landmark: MediaPipe landmark with x/y/visibility fields
            width: Frame width in pixels
            height: Frame height in pixels

        Returns:
            Tuple of (position, confidence)
        """
        x = float(np.clip(landmark.x, 0.0, 1.0) * width)
        y = float(np.clip(landmark.y, 0.0, 1.0) * height)
        confidence = float(getattr(landmark, "visibility", 0.0) or getattr(landmark, "presence", 0.0) or 0.0)
        return (x, y), confidence

    def _apply_smoothing(
        self,
        new_pos: Tuple[float, float],
        prev_pos: Tuple[float, float],
        alpha: float
    ) -> Tuple[float, float]:
        """
        Apply exponential moving average to smooth hand position.

        Reduces jitter from noisy detections while preserving motion responsiveness.

        Args:
            new_pos: New detected position (x, y)
            prev_pos: Previous smoothed position (x, y)
            alpha: Smoothing factor (0-1); higher = more smoothing

        Returns:
            Smoothed position coordinate
        """
        smoothed_x = alpha * new_pos[0] + (1 - alpha) * prev_pos[0]
        smoothed_y = alpha * new_pos[1] + (1 - alpha) * prev_pos[1]
        return (smoothed_x, smoothed_y)

    def _extract_hand_positions(
        self,
        landmarks,
        width: int,
        height: int
    ) -> Tuple[Tuple[float, float], float, Tuple[float, float], float]:
        """
        Extract left and right wrist positions from MediaPipe landmarks.

        MediaPipe Pose uses wrist landmarks for hand position tracking.
        Confidence scores indicate detection reliability.

        Args:
            landmarks: MediaPipe pose landmarks
            width: Frame width in pixels
            height: Frame height in pixels

        Returns:
            Tuple of (left_hand_pos, left_confidence, right_hand_pos, right_confidence)
        """
        if landmarks is None:
            return (0, 0), 0.0, (0, 0), 0.0

        left_landmark = landmarks[self.LEFT_WRIST]
        right_landmark = landmarks[self.RIGHT_WRIST]

        left_pos, left_conf = self._landmark_to_pixel(left_landmark, width, height)
        right_pos, right_conf = self._landmark_to_pixel(right_landmark, width, height)

        return left_pos, left_conf, right_pos, right_conf

    def _extract_hands_from_results(self, hands_results, width: int, height: int) -> Tuple[Optional[np.ndarray], float, Optional[np.ndarray], float, dict]:
        """
        Extract hand landmarks and handedness confidences from MediaPipe Hands results.

        Returns left_landmarks_px, left_conf, right_landmarks_px, right_conf, misc
        misc may contain handedness labels and original landmarks.
        """
        left_landmarks = None
        right_landmarks = None
        left_conf = 0.0
        right_conf = 0.0
        misc = {}

        if hands_results is None or hands_results.multi_hand_landmarks is None:
            return None, 0.0, None, 0.0, misc

        # Map each detected hand to left/right using classification
        for idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
            # classification info
            label = None
            score = 0.0
            try:
                classif = hands_results.multi_handedness[idx]
                label = classif.classification[0].label
                score = float(classif.classification[0].score)
            except Exception:
                label = None
                score = 0.0

            # convert landmarks to pixel coords
            lm_arr = []
            for lm in hand_landmarks.landmark:
                x = float(np.clip(lm.x, 0.0, 1.0) * width)
                y = float(np.clip(lm.y, 0.0, 1.0) * height)
                z = float(lm.z)
                lm_arr.append([x, y, z])
            lm_arr = np.array(lm_arr, dtype=np.float32)

            if label == 'Left':
                left_landmarks = lm_arr
                left_conf = score
            elif label == 'Right':
                right_landmarks = lm_arr
                right_conf = score
            else:
                # If no label, attempt heuristic by x position
                if lm_arr.shape[0] > 0:
                    cx = float(np.mean(lm_arr[:, 0]))
                    if cx < width / 2:
                        left_landmarks = lm_arr
                        left_conf = max(left_conf, score)
                    else:
                        right_landmarks = lm_arr
                        right_conf = max(right_conf, score)

        misc['raw'] = hands_results
        return left_landmarks, left_conf, right_landmarks, right_conf, misc

    def _compute_palm_orientation(self, hand_lm: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """
        Approximate palm normal vector using three key landmarks (wrist, index_mcp, pinky_mcp).
        Returns normalized (nx, ny, nz) or None if insufficient data.
        """
        try:
            p0 = hand_lm[0]  # wrist
            p5 = hand_lm[5]  # index_finger_mcp
            p17 = hand_lm[17]  # pinky_mcp

            v1 = np.array([p5[0] - p0[0], p5[1] - p0[1], p5[2] - p0[2]], dtype=np.float32)
            v2 = np.array([p17[0] - p0[0], p17[1] - p0[1], p17[2] - p0[2]], dtype=np.float32)
            # cross product gives normal direction
            normal = np.cross(v1, v2)
            norm = np.linalg.norm(normal)
            if norm == 0:
                return None
            normal = normal / norm
            return float(normal[0]), float(normal[1]), float(normal[2])
        except Exception:
            return None

    def _process_frame(self, frame: np.ndarray, frame_number: int) -> PoseDetectionState:
        """
        Process single video frame through MediaPipe.

        Args:
            frame: Input video frame (BGR format)
            frame_number: Frame counter for timestamping

        Returns:
            Updated PoseDetectionState with detected positions
        """
        from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

        self._image_height, self._image_width = frame.shape[:2]

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=frame_rgb)

        state = PoseDetectionState()
        state.timestamp = frame_number

        try:
            pose_results = self.pose.detect(mp_image)

            if pose_results and pose_results.landmarks:
                landmarks_list = pose_results.landmarks[0]

                pose_keypoints = np.array([
                    [float(lm.x * self._image_width),
                     float(lm.y * self._image_height),
                     float(lm.visibility if hasattr(lm, 'visibility') else 0.0)]
                    for lm in landmarks_list
                ], dtype=np.float32)
                state.body_keypoints = pose_keypoints

                left_wrist = landmarks_list[15]
                right_wrist = landmarks_list[16]

                left_pos = (float(left_wrist.x * self._image_width),
                           float(left_wrist.y * self._image_height))
                left_conf = float(left_wrist.visibility if hasattr(left_wrist, 'visibility') else 0.0)

                right_pos = (float(right_wrist.x * self._image_width),
                            float(right_wrist.y * self._image_height))
                right_conf = float(right_wrist.visibility if hasattr(right_wrist, 'visibility') else 0.0)

                try:
                    hands_results = self.hands.detect(mp_image)
                except Exception:
                    hands_results = None

                l_hands, l_conf_h, r_hands, r_conf_h, misc = self._extract_hands_from_results(
                    hands_results, self._image_width, self._image_height
                )

                if l_hands is not None and l_hands.shape[0] >= 1:
                    lw = (float(l_hands[0, 0]), float(l_hands[0, 1]))
                    left_pos = lw
                    left_conf = max(left_conf, l_conf_h)
                if r_hands is not None and r_hands.shape[0] >= 1:
                    rw = (float(r_hands[0, 0]), float(r_hands[0, 1]))
                    right_pos = rw
                    right_conf = max(right_conf, r_conf_h)

                state.left_hand_landmarks = l_hands
                state.right_hand_landmarks = r_hands

                fingertips_idx = [4, 8, 12, 16, 20]
                if l_hands is not None:
                    state.left_fingertips = {i: (float(l_hands[i, 0]), float(l_hands[i, 1])) for i in fingertips_idx}
                    state.left_palm_orientation = self._compute_palm_orientation(l_hands)
                if r_hands is not None:
                    state.right_fingertips = {i: (float(r_hands[i, 0]), float(r_hands[i, 1])) for i in fingertips_idx}
                    state.right_palm_orientation = self._compute_palm_orientation(r_hands)

                left_pos = self._apply_smoothing(left_pos, self._prev_left_hand, self.smoothing_factor)
                right_pos = self._apply_smoothing(right_pos, self._prev_right_hand, self.smoothing_factor)

                self._prev_left_hand = left_pos
                self._prev_right_hand = right_pos

                state.left_hand_pos = left_pos
                state.left_hand_confidence = left_conf
                state.right_hand_pos = right_pos
                state.right_hand_confidence = right_conf

                state.is_valid = (
                    left_conf >= self.confidence_threshold and
                    right_conf >= self.confidence_threshold
                )
        except Exception as e:
            print(f"Error processing frame: {e}")

        if self.debug:
            disp = frame.copy()
            try:
                if state.left_hand_confidence > 0:
                    lx, ly = int(state.left_hand_pos[0]), int(state.left_hand_pos[1])
                    cv2.circle(disp, (lx, ly), 8, (0, 255, 0), -1)
                    cv2.putText(disp, f"L:{state.left_hand_confidence:.2f}", (lx+10, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
                if state.right_hand_confidence > 0:
                    rx, ry = int(state.right_hand_pos[0]), int(state.right_hand_pos[1])
                    cv2.circle(disp, (rx, ry), 8, (0, 0, 255), -1)
                    cv2.putText(disp, f"R:{state.right_hand_confidence:.2f}", (rx+10, ry), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

                try:
                    from mediapipe.tasks.python.vision import HandLandmarker
                    hand_connections = [
                        (0, 1), (1, 2), (2, 3), (3, 4),
                        (0, 5), (5, 6), (6, 7), (7, 8),
                        (5, 9), (9, 10), (10, 11), (11, 12),
                        (9, 13), (13, 14), (14, 15), (15, 16),
                        (13, 17), (17, 18), (18, 19), (19, 20),
                        (0, 17), (0, 13), (0, 9), (0, 5),
                    ]
                except Exception:
                    hand_connections = []

                def _draw_hand_landmarks(arr, color=(0,255,0)):
                    for i in range(arr.shape[0]):
                        x, y = int(arr[i,0]), int(arr[i,1])
                        cv2.circle(disp, (x, y), 3, color, -1)
                    for a, b in hand_connections:
                        try:
                            xa, ya = int(arr[a,0]), int(arr[a,1])
                            xb, yb = int(arr[b,0]), int(arr[b,1])
                            cv2.line(disp, (xa, ya), (xb, yb), color, 1)
                        except Exception:
                            pass

                if state.left_hand_landmarks is not None:
                    _draw_hand_landmarks(state.left_hand_landmarks, color=(0,200,0))
                    for i, (fx, fy) in (state.left_fingertips or {}).items():
                        cv2.circle(disp, (int(fx), int(fy)), 5, (0,255,0), 1)
                    if state.left_palm_orientation is not None:
                        cx = int(state.left_hand_landmarks[:,0].mean())
                        cy = int(state.left_hand_landmarks[:,1].mean())
                        nx, ny, nz = state.left_palm_orientation
                        ox = int(cx + nx * 40)
                        oy = int(cy + ny * 40)
                        cv2.arrowedLine(disp, (cx, cy), (ox, oy), (0,255,0), 2)

                if state.right_hand_landmarks is not None:
                    _draw_hand_landmarks(state.right_hand_landmarks, color=(0,0,200))
                    for i, (fx, fy) in (state.right_fingertips or {}).items():
                        cv2.circle(disp, (int(fx), int(fy)), 5, (0,0,255), 1)
                    if state.right_palm_orientation is not None:
                        cx = int(state.right_hand_landmarks[:,0].mean())
                        cy = int(state.right_hand_landmarks[:,1].mean())
                        nx, ny, nz = state.right_palm_orientation
                        ox = int(cx + nx * 40)
                        oy = int(cy + ny * 40)
                        cv2.arrowedLine(disp, (cx, cy), (ox, oy), (0,0,255), 2)

                cv2.imshow('Pose Debug', disp)
                cv2.waitKey(1)
            except Exception:
                pass

        self.current_state = state
        return state

    def _capture_thread(self):
        """
        Background thread for continuous webcam capture and pose estimation.

        Reads frames from webcam, processes with MediaPipe, and queues results.
        Designed to run in separate thread without blocking Blender UI.
        """
        print(f"[Thread] Opening webcam {self.webcam_index}...")
        cap = cv2.VideoCapture(self.webcam_index)

        if not cap.isOpened():
            print(f"Error: Could not open webcam at index {self.webcam_index}")
            self.is_running = False
            return

        print(f"[Thread] Webcam opened successfully")
        frame_count = 0

        try:
            while self.is_running:
                ret, frame = cap.read()

                if not ret:
                    print("Error: Failed to read frame from webcam")
                    break

                # Process frame and get pose
                state = self._process_frame(frame, frame_count)

                # Update queue (drop old results if queue full)
                try:
                    self.result_queue.put_nowait(state)
                except queue.Full:
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.put_nowait(state)
                    except queue.Empty:
                        pass

                frame_count += 1

        finally:
            cap.release()

    def start(self):
        """Start pose estimation in background thread."""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_thread, daemon=True)
        self.thread.start()
        print("Pose estimation started")

    def stop(self):
        """Stop pose estimation and cleanup resources."""
        self.is_running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        if self.pose:
            try:
                self.pose.close()
            except Exception:
                pass
        if self.hands:
            try:
                self.hands.close()
            except Exception:
                pass
        if self.debug:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        print("Pose estimation stopped")

    def get_latest_pose(self) -> PoseDetectionState:
        """
        Get most recent pose detection result without blocking.

        Returns:
            Latest PoseDetectionState or current cached state if no new result
        """
        try:
            self.current_state = self.result_queue.get_nowait()
        except queue.Empty:
            pass

        return self.current_state

    def update_config(self, confidence_threshold: float, smoothing_factor: float):
        """
        Update estimation parameters without restarting.

        Args:
            confidence_threshold: New confidence threshold (0-1)
            smoothing_factor: New smoothing factor (0-1)
        """
        self.confidence_threshold = confidence_threshold
        self.smoothing_factor = smoothing_factor


# Global instance
_estimator: Optional[PoseEstimator] = None


def initialize_estimator(webcam_index: int = 0, confidence_threshold: float = 0.5, debug_visual: bool = False):
    """Initialize global pose estimator instance."""
    global _estimator
    try:
        _estimator = PoseEstimator(webcam_index, confidence_threshold, debug_visual)
    except Exception as e:
        print(f"Error initializing pose estimator: {e}")
        _estimator = None


def start_estimation():
    """Start pose estimation if initialized."""
    if _estimator:
        _estimator.start()


def stop_estimation():
    """Stop pose estimation."""
    if _estimator:
        _estimator.stop()


def get_pose():
    """Get current pose detection state."""
    if _estimator:
        return _estimator.get_latest_pose()
    return PoseDetectionState()


def update_config(confidence_threshold: float, smoothing_factor: float):
    """Update pose estimator configuration."""
    if _estimator:
        _estimator.update_config(confidence_threshold, smoothing_factor)
