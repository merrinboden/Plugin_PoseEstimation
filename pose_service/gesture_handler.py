"""
Gesture Handler Module
======================

Service-side gesture recognition and interpretation from hand positions.

Gesture Recognition:
- Left hand: Camera navigation, viewport panning, zooming
- Right hand: Tool selection, brush properties, painting operations

Includes gesture filtering, dynamic gesture detection (swipes, circles), and configurable thresholds.
"""

import math
import time
from typing import Tuple, Optional, List, Dict
from enum import Enum
import yaml
import pathlib


class HandGestureType(Enum):
    """
    Enumeration of recognized hand gestures.

    Values represent different hand positions/movements that trigger actions.
    """
    NEUTRAL = "neutral"
    POINTING = "pointing"
    OPEN_HAND = "open_hand"
    GRAB = "grab"
    PINCH = "pinch"


class GestureConfig:
    """Load and manage gesture mappings from YAML configuration file."""

    def __init__(self, config_path: Optional[str] = None):
        """Load gesture configuration from YAML file."""
        if config_path is None:
            config_path = pathlib.Path(__file__).parent / "gestures_config.yaml"

        self.config = {}
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            print(f"[Gesture Config] Loaded from {config_path}")
        except FileNotFoundError:
            print(f"[Gesture Config] File not found: {config_path}")
        except Exception as e:
            print(f"[Gesture Config] Error loading: {e}")

    def get(self, key: str, default=None):
        """Get config value by dot-notation key (e.g., 'sculpt_mode.right_hand.brush_size.threshold')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_threshold(self, action: str) -> float:
        """Get pixel threshold for a specific action."""
        threshold = self.get(f"thresholds.{action}")
        if threshold is None:
            threshold = self.get("camera_control.left_hand.horizontal_pan.threshold", 25)
        return threshold

    def get_sensitivity(self, action: str) -> float:
        """Get sensitivity multiplier for an action."""
        sensitivity = self.get(f"{action}.sensitivity", 1.0)
        global_mult = self.get("global.sensitivity_multiplier", 1.0)
        return sensitivity * global_mult


class DynamicGestureDetector:
    """Detect dynamic gestures (swipes, circles, taps) from motion history."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.motion_history: List[Tuple[float, float, float]] = []  # (x, y, timestamp)
        self.max_history = 60  # Keep ~1 second of history at 60fps

    def add_motion(self, x: float, y: float):
        """Add hand position to motion history."""
        self.motion_history.append((x, y, time.time()))
        # Trim old entries
        cutoff_time = time.time() - 1.0
        self.motion_history = [(x, y, t) for x, y, t in self.motion_history if t > cutoff_time]

    def detect_swipe(self) -> Optional[str]:
        """Detect horizontal swipe (left or right)."""
        if len(self.motion_history) < 5:
            return None

        first_x = self.motion_history[0][0]
        last_x = self.motion_history[-1][0]
        total_distance = abs(last_x - first_x)

        config_swipe = self.config.get("dynamic_gestures.swipe_left", {})
        min_distance = config_swipe.get("min_distance", 100)
        max_duration = config_swipe.get("max_duration", 500) / 1000.0

        duration = self.motion_history[-1][2] - self.motion_history[0][2]

        if total_distance > min_distance and duration < max_duration:
            if last_x > first_x:
                return "swipe_right"
            else:
                return "swipe_left"

        return None

    def clear_history(self):
        """Clear motion history."""
        self.motion_history = []


class BrushCursorController:
    """Map hand position to brush cursor location in viewport."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.enabled = config.get("sculpt_mode.right_hand.brush_cursor.enabled", True)

    def get_brush_location_from_hand(self, hand_pos: Tuple[float, float], viewport_width: int, viewport_height: int) -> Tuple[int, int]:
        """Convert hand position to brush cursor coordinates in viewport."""
        if not self.enabled:
            return None

        hand_x, hand_y = hand_pos
        # Hand position is typically 0-640 (webcam resolution)
        # Map to viewport coordinates
        brush_x = int(hand_x * viewport_width / 640)
        brush_y = int(hand_y * viewport_height / 480)

        return (brush_x, brush_y)


class CameraGestureHandler:
    """
    Manages left-hand gestures for camera and viewport control.

    Maps hand positions to:
    - Horizontal movement: Pan left/right
    - Vertical movement: Pan up/down
    - Forward/backward: Zoom in/out

    Uses configurable thresholds from gesture config.
    """

    def __init__(self, config: GestureConfig, gesture_manager=None):
        """Initialize camera gesture handler with config."""
        self.config = config
        self.gesture_manager = gesture_manager
        self.last_hand_pos: Optional[Tuple[float, float]] = None
        self.gesture_active = False

    def process_left_hand(
        self,
        hand_pos: Tuple[float, float],
        confidence: float,
        threshold: float
    ) -> bool:
        """
        Process left hand position for camera control.

        Uses configurable thresholds from gesture config.

        Args:
            hand_pos: (x, y) screen position of left hand
            confidence: Detection confidence score (0-1)
            threshold: Minimum confidence to process gesture

        Returns:
            True if gesture was processed
        """
        if confidence < threshold:
            self.last_hand_pos = None
            self.gesture_active = False
            return False

        if self.last_hand_pos is None:
            self.last_hand_pos = hand_pos
            return False

        # Calculate motion delta
        dx = hand_pos[0] - self.last_hand_pos[0]
        dy = hand_pos[1] - self.last_hand_pos[1]

        gesture_processed = False

        # Get configurable thresholds
        h_threshold = self.config.get_threshold("pan_left")
        v_threshold = self.config.get_threshold("pan_up")

        # Horizontal pan (camera left/right)
        if abs(dx) > h_threshold:
            self._pan_camera_horizontal(dx)
            gesture_processed = True

        # Vertical pan (camera up/down)
        if abs(dy) > v_threshold:
            self._pan_camera_vertical(dy)
            gesture_processed = True

        self.last_hand_pos = hand_pos
        self.gesture_active = gesture_processed

        return gesture_processed

    def _pan_camera_horizontal(self, delta_x: float):
        """Pan viewport horizontally based on hand movement."""
        action_type = 'PAN_RIGHT' if delta_x > 0 else 'PAN_LEFT'
        amount = int(abs(delta_x) * 0.5)
        if self.gesture_manager:
            self.gesture_manager.queue_action(action_type, {"amount": amount})
        print(f"[Gesture] {action_type} (+{amount})")

    def _pan_camera_vertical(self, delta_y: float):
        """Pan viewport vertically based on hand movement."""
        action_type = 'PAN_UP' if delta_y < 0 else 'PAN_DOWN'
        amount = int(abs(delta_y) * 0.5)
        if self.gesture_manager:
            self.gesture_manager.queue_action(action_type, {"amount": amount})
        print(f"[Gesture] {action_type} (+{amount})")

    def zoom_camera(self, direction: int, amount: float = 0.1):
        """Zoom viewport in or out."""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    with bpy.context.temp_override(area=area):
                        bpy.ops.view3d.zoom(delta=direction * int(amount * 100))
        except Exception as e:
            pass

    def reset(self):
        """Reset gesture tracking state."""
        self.last_hand_pos = None
        self.gesture_active = False


class BrushGestureHandler:
    """
    Manages right-hand gestures for tool and brush control.

    Maps hand positions to:
    - Horizontal movement: Adjust brush size
    - Vertical movement: Cycle through tools
    - Diagonal movement: Adjust brush strength
    - Hand position: Direct cursor placement

    Uses configurable thresholds from gesture config.
    """

    def __init__(self, config: GestureConfig, gesture_manager=None):
        """Initialize brush gesture handler with config."""
        self.config = config
        self.gesture_manager = gesture_manager
        self.last_hand_pos: Optional[Tuple[float, float]] = None
        self.tool_change_pending = False
        self.last_tool_index = 0
        self.cursor_controller = BrushCursorController(config)
        self.gesture_detector = DynamicGestureDetector(config)

    def process_right_hand(
        self,
        hand_pos: Tuple[float, float],
        confidence: float,
        threshold: float
    ) -> bool:
        """
        Process right hand position for tool and brush control.

        Interprets hand position and motion:
        - Vertical position: Select tool (up=different tools)
        - Distance from neutral: Brush size adjustment
        - Diagonal movement: Brush strength
        - Position: Direct cursor placement

        Args:
            hand_pos: (x, y) screen position of right hand
            confidence: Detection confidence score (0-1)
            threshold: Minimum confidence to process gesture

        Returns:
            True if gesture was processed
        """
        if confidence < threshold:
            self.last_hand_pos = None
            return False

        # Track motion for dynamic gesture detection
        self.gesture_detector.add_motion(hand_pos[0], hand_pos[1])

        if self.last_hand_pos is None:
            self.last_hand_pos = hand_pos
            return False

        dx = hand_pos[0] - self.last_hand_pos[0]
        dy = hand_pos[1] - self.last_hand_pos[1]

        gesture_processed = False

        # Get configurable thresholds
        h_threshold = self.config.get_threshold("brush_size_horizontal")
        v_threshold = self.config.get_threshold("tool_select_vertical")
        d_threshold = self.config.get_threshold("brush_strength_diagonal")

        # Horizontal: brush size
        if abs(dx) > h_threshold:
            self._adjust_brush_size(dx)
            gesture_processed = True

        # Vertical: tool selection
        if abs(dy) > v_threshold:
            self._select_tool_by_height(hand_pos[1], dy)
            gesture_processed = True

        # Diagonal: brush strength
        diagonal_dist = math.sqrt(dx*dx + dy*dy)
        if diagonal_dist > d_threshold and abs(dx) > h_threshold and abs(dy) > v_threshold:
            self._adjust_brush_strength(dx, dy)
            gesture_processed = True

        # Continuous brush cursor mapping
        if self.config.get("sculpt_mode.right_hand.brush_cursor.enabled", True):
            self._apply_brush_stroke(hand_pos, dx, dy)
            gesture_processed = True

        self.last_hand_pos = hand_pos
        return gesture_processed

    def _select_tool_by_height(self, hand_y: float, delta_y: float):
        """Cycle through sculpt tools based on vertical hand movement."""
        direction = 'NEXT' if delta_y < 0 else 'PREV'
        if self.gesture_manager:
            self.gesture_manager.queue_action('SELECT_TOOL', {"direction": direction})
        print(f"[Gesture] Tool cycle: {direction}")

    def _adjust_brush_size(self, delta_x: float):
        """Adjust brush size based on horizontal hand movement."""
        size_delta = delta_x * 0.1
        if self.gesture_manager:
            self.gesture_manager.queue_action('ADJUST_BRUSH', {"size_delta": size_delta})
        print(f"[Gesture] Brush size adjust: {size_delta:+.1f}")

    def _adjust_brush_strength(self, dx: float, dy: float):
        """Adjust brush strength based on diagonal hand movement."""
        # Calculate diagonal magnitude
        magnitude = math.sqrt(dx*dx + dy*dy) * 0.01
        if self.gesture_manager:
            self.gesture_manager.queue_action('ADJUST_STRENGTH', {"strength_delta": magnitude})
        print(f"[Gesture] Brush strength adjust: {magnitude:+.3f}")

    def _apply_brush_stroke(self, pos: Tuple[float, float], dx: float, dy: float):
        """Apply brush stroke at current hand position."""
        # For now, just queue the position for the action processor to handle
        if self.gesture_manager:
            self.gesture_manager.queue_action('BRUSH_STROKE', {"pos": pos, "delta": (dx, dy)})

    def reset(self):
        """Reset gesture tracking state."""
        self.last_hand_pos = None
        self.tool_change_pending = False
        self.gesture_detector.clear_history()


class GestureManager:
    """
    Central manager coordinating left and right hand gesture handling.

    Orchestrates interaction between:
    - Pose estimation (hand positions)
    - Camera gestures (left hand)
    - Brush gestures (right hand)
    - Blender UI state
    - Gesture configuration

    Handles gesture filtering and timing to prevent spurious activation.
    """

    def __init__(self, config: Optional[GestureConfig] = None):
        """Initialize gesture manager with optional config."""
        if config is None:
            config = GestureConfig()

        self.config = config
        self.camera_handler = CameraGestureHandler(config, self)
        self.brush_handler = BrushGestureHandler(config, self)
        self.last_update_frame = 0
        self.frame_skip = self.config.get("global.frame_skip", 2)
        self.pending_actions = []  # Local action queue

    def process_pose(
        self,
        left_hand_pos: Tuple[float, float],
        left_confidence: float,
        right_hand_pos: Tuple[float, float],
        right_confidence: float,
        confidence_threshold: float,
        frame_number: int
    ):
        """
        Process detected pose and generate corresponding gestures.

        Coordinates left and right hand gestures while ensuring they don't
        interfere with each other.

        Args:
            left_hand_pos: Left hand position (x, y)
            left_confidence: Left hand confidence (0-1)
            right_hand_pos: Right hand position (x, y)
            right_confidence: Right hand confidence (0-1)
            confidence_threshold: Minimum confidence to trigger gesture
            frame_number: Current frame number
        """
        # Skip frames to reduce processing overhead
        if frame_number - self.last_update_frame < self.frame_skip:
            return

        self.last_update_frame = frame_number

        # Process left hand for camera control
        left_processed = self.camera_handler.process_left_hand(
            left_hand_pos,
            left_confidence,
            confidence_threshold
        )

        # Process right hand for brush control
        right_processed = self.brush_handler.process_right_hand(
            right_hand_pos,
            right_confidence,
            confidence_threshold
        )

    def reset_all(self):
        """Reset all gesture handlers."""
        self.camera_handler.reset()
        self.brush_handler.reset()

    def queue_action(self, action_type: str, data: Dict = None):
        """Queue an action locally (service version)."""
        self.pending_actions.append({"type": action_type, "data": data or {}})

    def get_and_clear_actions(self) -> List[Dict]:
        """Retrieve and clear pending actions."""
        actions = self.pending_actions.copy()
        self.pending_actions = []
        return actions


# Global gesture manager instance
_gesture_manager: Optional[GestureManager] = None
_gesture_config: Optional[GestureConfig] = None


def initialize_gesture_manager(config: Optional[GestureConfig] = None):
    """Initialize global gesture manager with optional config."""
    global _gesture_manager, _gesture_config
    if config is None:
        config = GestureConfig()
    _gesture_config = config
    _gesture_manager = GestureManager(config)
    print(f"[Gesture Manager] Initialized with config")


def process_gesture(
    left_hand_pos: Tuple[float, float],
    left_confidence: float,
    right_hand_pos: Tuple[float, float],
    right_confidence: float,
    confidence_threshold: float,
    frame_number: int
):
    """Process pose and generate gestures."""
    if _gesture_manager:
        _gesture_manager.process_pose(
            left_hand_pos,
            left_confidence,
            right_hand_pos,
            right_confidence,
            confidence_threshold,
            frame_number
        )


def reset_gestures():
    """Reset all gesture state."""
    if _gesture_manager:
        _gesture_manager.reset_all()


def get_gesture_config() -> Optional[GestureConfig]:
    """Get the current gesture configuration."""
    return _gesture_config
