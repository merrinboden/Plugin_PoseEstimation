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

# Import matplotlib before mediapipe to avoid circular import
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
except:
    pass

import cv2
import numpy as np
import threading
import queue
from typing import Dict, Tuple, Optional, List

# Now safely import mediapipe - use tasks API (available in 0.10.x)
mp = None
mp_pose = None
mp_hands = None

try:
    import mediapipe
    from mediapipe import tasks
    from mediapipe.tasks.python import vision
    print("[Init] MediaPipe tasks API loaded successfully")
except Exception as e:
    print(f"MediaPipe import error: {e}")
    mp = None
    tasks = None


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

    def __init__(self, webcam_index: int = 0, confidence_threshold: float = 0.5, debug_window: bool = False, broadcaster=None):
        """
        Initialize pose estimator using MediaPipe tasks API.

        Args:
            webcam_index: Index of webcam device (0=default)
            confidence_threshold: Minimum confidence for valid keypoint
            broadcaster: Optional async callback to broadcast pose data
        """
        if not (mp or tasks):
            raise ImportError("MediaPipe not installed. Install with: pip install mediapipe")

        self.webcam_index = webcam_index
        self.confidence_threshold = confidence_threshold
        self.smoothing_factor = 0.9
        self.broadcaster = broadcaster

        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.result_queue: queue.Queue = queue.Queue(maxsize=1)

        self.current_state = PoseDetectionState()
        self._prev_left_hand = (0.0, 0.0)
        self._prev_right_hand = (0.0, 0.0)
        self._image_width = 0
        self._image_height = 0
        self.debug = debug_window

        self.pose = None
        self.hands = None

        try:
            import pathlib
            from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

            model_dir = pathlib.Path(__file__).parent.parent / "models"
            model_dir.mkdir(exist_ok=True)

            pose_model = model_dir / "pose_landmarker_full.task"
            hand_model = model_dir / "hand_landmarker.task"

            if pose_model.exists() and hand_model.exists():
                try:
                    base_options_pose = tasks.BaseOptions(model_asset_path=str(pose_model))
                    options_pose = vision.PoseLandmarkerOptions(
                        base_options=base_options_pose,
                        running_mode=VisionTaskRunningMode.IMAGE
                    )
                    self.pose = vision.PoseLandmarker.create_from_options(options_pose)

                    base_options_hand = tasks.BaseOptions(model_asset_path=str(hand_model))
                    options_hand = vision.HandLandmarkerOptions(
                        base_options=base_options_hand,
                        running_mode=VisionTaskRunningMode.IMAGE,
                        num_hands=2
                    )
                    self.hands = vision.HandLandmarker.create_from_options(options_hand)
                    print("[Init] MediaPipe tasks models loaded successfully")
                except Exception as e:
                    print(f"Error loading models: {e}")
            else:
                print(f"[Init] Model files not found in {model_dir}")
                if not pose_model.exists():
                    print(f"  Missing: {pose_model.name}")
                if not hand_model.exists():
                    print(f"  Missing: {hand_model.name}")
        except Exception as e:
            print(f"Error initializing MediaPipe models: {e}")
            import traceback
            traceback.print_exc()

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
        """Extract hand landmarks from MediaPipe tasks API results."""
        left_landmarks = None
        right_landmarks = None
        left_conf = 0.0
        right_conf = 0.0
        misc = {}

        if hands_results is None or not hands_results.hand_landmarks:
            return None, 0.0, None, 0.0, misc

        try:
            num_hands = len(hands_results.hand_landmarks)
            print(f"[Hand Extraction] Found {num_hands} hands, handedness: {len(hands_results.handedness)}")

            for idx, hand_lm_list in enumerate(hands_results.hand_landmarks):
                label = None
                score = 0.0

                print(f"  [Hand {idx}] Type: {type(hand_lm_list)}, Landmarks: {len(hand_lm_list)}")

                if idx < len(hands_results.handedness) and hands_results.handedness[idx]:
                    category = hands_results.handedness[idx][0]
                    label = category.category_name
                    score = float(category.score)
                    print(f"  Hand {idx}: {label} (confidence: {score:.2f})")

                try:
                    # hand_landmarks is a list of NormalizedLandmark objects
                    lm_arr = np.array([
                        [float(lm.x * width), float(lm.y * height), float(lm.z)]
                        for lm in hand_lm_list
                    ], dtype=np.float32)

                    print(f"  [Hand {idx}] Extracted {lm_arr.shape[0]} landmarks")

                    # Determine hand side
                    if label == 'Left':
                        left_landmarks = lm_arr
                        left_conf = score
                        print(f"  -> Assigned to LEFT")
                    elif label == 'Right':
                        right_landmarks = lm_arr
                        right_conf = score
                        print(f"  -> Assigned to RIGHT")
                    else:
                        # Fallback: check wrist position
                        wrist_x = float(hand_lm_list[0].x)
                        if wrist_x < 0.5:
                            left_landmarks = lm_arr
                            left_conf = score
                            print(f"  -> Assigned to LEFT (fallback)")
                        else:
                            right_landmarks = lm_arr
                            right_conf = score
                            print(f"  -> Assigned to RIGHT (fallback)")
                except (AttributeError, TypeError) as e:
                    print(f"  Hand {idx}: Error processing - {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        except Exception as e:
            print(f"Hand extraction error: {e}")
            import traceback
            traceback.print_exc()

        print(f"[Hand Extraction] Result: Left={left_landmarks is not None}, Right={right_landmarks is not None}")
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
        Process single video frame through MediaPipe legacy API.

        Args:
            frame: Input video frame (BGR format)
            frame_number: Frame counter for timestamping

        Returns:
            Updated PoseDetectionState with detected positions
        """
        self._image_height, self._image_width = frame.shape[:2]
        state = PoseDetectionState()
        state.timestamp = frame_number

        if self.pose is None or self.hands is None:
            print("[Warning] MediaPipe models not loaded. Using fallback hand detection.")
            return self._process_frame_fallback(frame, frame_number)

        try:
            from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = Image(image_format=ImageFormat.SRGB, data=frame_rgb)

            # Use tasks API detect() method
            pose_results = self.pose.detect(mp_image)

            if pose_results and pose_results.pose_landmarks:
                landmarks_list = pose_results.pose_landmarks[0]

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
                    if hands_results and hands_results.hand_landmarks:
                        print(f"[Hand Detection] Found {len(hands_results.hand_landmarks)} hands")
                except Exception as e:
                    print(f"[Hand Detection] Error: {e}")
                    hands_results = None

                l_hands, l_conf_h, r_hands, r_conf_h, misc = self._extract_hands_from_results(
                    hands_results, self._image_width, self._image_height
                )

                if l_hands is not None and l_hands.shape[0] >= 1:
                    lw = (float(l_hands[0, 0]), float(l_hands[0, 1]))
                    left_pos = lw
                    left_conf = l_conf_h
                if r_hands is not None and r_hands.shape[0] >= 1:
                    rw = (float(r_hands[0, 0]), float(r_hands[0, 1]))
                    right_pos = rw
                    right_conf = r_conf_h

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
            disp = cv2.flip(frame.copy(), 1)
            cv2.putText(disp, f"L: {state.left_hand_confidence:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(disp, f"R: {state.right_hand_confidence:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Debug: show hand detection status
            left_status = "[OK]" if state.left_hand_landmarks is not None else "[NO]"
            right_status = "[OK]" if state.right_hand_landmarks is not None else "[NO]"
            cv2.putText(disp, f"Left Hand {left_status}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(disp, f"Right Hand {right_status}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Print to console for debugging
            if frame_number % 10 == 0:
                print(f"[Frame {frame_number}] L:{left_status} R:{right_status} L_lm:{state.left_hand_landmarks is not None} R_lm:{state.right_hand_landmarks is not None}")

            if state.body_keypoints is not None and state.body_keypoints.shape[0] > 16:
                kp = state.body_keypoints

                def flip_x(x):
                    return int(self._image_width - x)

                def draw_limb(p1_idx, p2_idx, color):
                    if p1_idx < len(kp) and p2_idx < len(kp):
                        p1, p2 = kp[p1_idx][:2], kp[p2_idx][:2]
                        cv2.line(disp, (flip_x(p1[0]), int(p1[1])), (flip_x(p2[0]), int(p2[1])), color, 2)

                def draw_joint(idx, color):
                    if idx < len(kp):
                        p = kp[idx][:2]
                        cv2.circle(disp, (flip_x(p[0]), int(p[1])), 5, color, -1)

                draw_limb(11, 13, (100, 150, 100))
                draw_limb(13, 15, (100, 150, 100))
                draw_limb(12, 14, (100, 150, 150))
                draw_limb(14, 16, (100, 150, 150))

                draw_joint(11, (50, 200, 50))
                draw_joint(13, (100, 200, 100))
                draw_joint(15, (150, 200, 150))
                draw_joint(12, (50, 50, 200))
                draw_joint(14, (100, 100, 200))
                draw_joint(16, (150, 150, 200))

            if state.left_hand_confidence > 0:
                lx = int(self._image_width - state.left_hand_pos[0])
                ly = int(state.left_hand_pos[1])
                cv2.circle(disp, (lx, ly), 8, (0, 255, 0), -1)
                cv2.putText(disp, f"L{state.left_hand_confidence:.1f}", (lx-20, ly-15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            if state.right_hand_confidence > 0:
                rx = int(self._image_width - state.right_hand_pos[0])
                ry = int(state.right_hand_pos[1])
                cv2.circle(disp, (rx, ry), 8, (0, 0, 255), -1)
                cv2.putText(disp, f"R{state.right_hand_confidence:.1f}", (rx-20, ry-15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

            finger_connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (0, 9), (9, 10), (10, 11), (11, 12),
                (0, 13), (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20)
            ]

            if state.left_hand_landmarks is not None:
                # Draw all 21 left hand landmarks
                for i, lm in enumerate(state.left_hand_landmarks):
                    x = int(self._image_width - lm[0])
                    y = int(lm[1])
                    # Color based on landmark group
                    if i == 0:
                        color = (0, 255, 100)  # wrist - bright
                    elif i <= 4:
                        color = (0, 200, 0)  # thumb
                    elif i <= 8:
                        color = (50, 200, 0)  # index
                    elif i <= 12:
                        color = (100, 200, 0)  # middle
                    elif i <= 16:
                        color = (150, 200, 0)  # ring
                    else:
                        color = (200, 200, 0)  # pinky
                    cv2.circle(disp, (x, y), 4, color, -1)
                    cv2.putText(disp, str(i), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

                # Draw finger skeleton
                for a, b in finger_connections:
                    if a < len(state.left_hand_landmarks) and b < len(state.left_hand_landmarks):
                        p1 = (int(self._image_width - state.left_hand_landmarks[a][0]), int(state.left_hand_landmarks[a][1]))
                        p2 = (int(self._image_width - state.left_hand_landmarks[b][0]), int(state.left_hand_landmarks[b][1]))
                        cv2.line(disp, p1, p2, (0, 150, 0), 2)

            if state.right_hand_landmarks is not None:
                # Draw all 21 right hand landmarks
                for i, lm in enumerate(state.right_hand_landmarks):
                    x = int(self._image_width - lm[0])
                    y = int(lm[1])
                    # Color based on landmark group
                    if i == 0:
                        color = (100, 100, 255)  # wrist - bright
                    elif i <= 4:
                        color = (0, 0, 200)  # thumb
                    elif i <= 8:
                        color = (50, 0, 200)  # index
                    elif i <= 12:
                        color = (100, 0, 200)  # middle
                    elif i <= 16:
                        color = (150, 0, 200)  # ring
                    else:
                        color = (200, 0, 200)  # pinky
                    cv2.circle(disp, (x, y), 4, color, -1)
                    cv2.putText(disp, str(i), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

                # Draw finger skeleton
                for a, b in finger_connections:
                    if a < len(state.right_hand_landmarks) and b < len(state.right_hand_landmarks):
                        p1 = (int(self._image_width - state.right_hand_landmarks[a][0]), int(state.right_hand_landmarks[a][1]))
                        p2 = (int(self._image_width - state.right_hand_landmarks[b][0]), int(state.right_hand_landmarks[b][1]))
                        cv2.line(disp, p1, p2, (0, 0, 150), 2)

            try:
                cv2.imshow('Pose Debug', disp)
                cv2.waitKey(1)
            except Exception as e:
                # Display not available, landmarks still tracked
                pass

        self.current_state = state
        return state

    def _process_frame_fallback(self, frame: np.ndarray, frame_number: int) -> PoseDetectionState:
        """Fallback hand detection using skin color detection."""
        state = PoseDetectionState()
        state.timestamp = frame_number

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        mask = cv2.bitwise_or(mask, mask2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) >= 2:
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:2]
            hands = []
            for contour in contours:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    hands.append((cx, cy))

            if len(hands) >= 2:
                state.left_hand_pos = tuple(hands[0]) if hands[0][0] < hands[1][0] else tuple(hands[1])
                state.right_hand_pos = tuple(hands[1]) if hands[0][0] < hands[1][0] else tuple(hands[0])
                state.left_hand_confidence = 0.5
                state.right_hand_confidence = 0.5
                state.is_valid = True

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

    def _gesture_processing_thread(self):
        """Background thread for gesture processing."""
        from . import gesture_handler

        print("[Gesture Thread] Started")
        while self.is_running:
            try:
                pose = self.get_latest_pose()
                if pose and pose.is_valid:
                    gesture_handler.process_gesture(
                        pose.left_hand_pos,
                        pose.left_hand_confidence,
                        pose.right_hand_pos,
                        pose.right_hand_confidence,
                        self.confidence_threshold,
                        pose.timestamp
                    )
            except Exception as e:
                print(f"[Gesture Thread] Error: {e}")
                import traceback
                traceback.print_exc()

            threading.Event().wait(0.016)

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



# Service version - PoseEstimator class is used directly
# No global Blender-specific functions

