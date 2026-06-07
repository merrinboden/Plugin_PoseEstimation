"""
Gesture Handler Module
======================

Interprets hand positions from pose estimation and maps them to Blender actions.

Gesture Recognition:
- Left hand: Camera navigation, viewport panning, zooming
- Right hand: Tool selection, brush properties, painting operations

Includes gesture filtering to distinguish intentional movements from noise.
"""

import bpy
import math
from typing import Tuple, Optional
from enum import Enum


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


class CameraGestureHandler:
    """
    Manages left-hand gestures for camera and viewport control.

    Maps hand positions to:
    - Horizontal movement: Pan left/right
    - Vertical movement: Pan up/down
    - Forward/backward: Zoom in/out

    Uses motion thresholds to filter noise and distinguish intentional gestures.
    """

    # Movement threshold in pixels to trigger action
    PAN_THRESHOLD = 10
    ZOOM_THRESHOLD = 5

    def __init__(self):
        """Initialize camera gesture handler."""
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

        Interprets hand motion to control viewport:
        - Horizontal movement: Pan camera left/right
        - Vertical movement: Pan camera up/down
        - Forward motion (if tracked): Zoom

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

        # Horizontal pan (camera left/right)
        if abs(dx) > self.PAN_THRESHOLD:
            self._pan_camera_horizontal(dx)
            gesture_processed = True

        # Vertical pan (camera up/down)
        if abs(dy) > self.PAN_THRESHOLD:
            self._pan_camera_vertical(dy)
            gesture_processed = True

        self.last_hand_pos = hand_pos
        self.gesture_active = gesture_processed

        return gesture_processed

    def _pan_camera_horizontal(self, delta_x: float):
        """
        Pan viewport horizontally based on hand movement.

        Args:
            delta_x: Horizontal displacement in pixels (positive=right)
        """
        from . import pose_estimator
        action_type = 'PAN_RIGHT' if delta_x > 0 else 'PAN_LEFT'
        pose_estimator.queue_action(action_type, {"amount": int(abs(delta_x) * 0.5)})

    def _pan_camera_vertical(self, delta_y: float):
        """
        Pan viewport vertically based on hand movement.

        Args:
            delta_y: Vertical displacement in pixels (positive=up)
        """
        from . import pose_estimator
        action_type = 'PAN_UP' if delta_y < 0 else 'PAN_DOWN'
        pose_estimator.queue_action(action_type, {"amount": int(abs(delta_y) * 0.5)})

    def zoom_camera(self, direction: int, amount: float = 0.1):
        """
        Zoom viewport in or out.

        Args:
            direction: 1 for zoom in, -1 for zoom out
            amount: Zoom amount relative to current view
        """
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    with bpy.context.temp_override(area=area):
                        bpy.ops.view3d.zoom(delta=direction * int(amount * 100))
        except Exception as e:
            print(f"Error zooming camera: {e}")

    def reset(self):
        """Reset gesture tracking state."""
        self.last_hand_pos = None
        self.gesture_active = False


class BrushGestureHandler:
    """
    Manages right-hand gestures for tool and brush control.

    Maps hand positions to:
    - Hand height: Select different tools
    - Hand distance from center: Adjust brush size
    - Hand movement: Apply brush strokes

    Supports both sculpting and painting operations.
    """

    # Distance thresholds in pixels
    TOOL_SELECTION_THRESHOLD = 50
    BRUSH_SIZE_THRESHOLD = 20

    def __init__(self):
        """Initialize brush gesture handler."""
        self.last_hand_pos: Optional[Tuple[float, float]] = None
        self.tool_change_pending = False
        self.last_tool_index = 0

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
        - Movement pattern: Apply brush stroke

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

        if self.last_hand_pos is None:
            self.last_hand_pos = hand_pos
            return False

        dx = hand_pos[0] - self.last_hand_pos[0]
        dy = hand_pos[1] - self.last_hand_pos[1]

        gesture_processed = False

        # Tool selection based on vertical position
        if abs(dy) > self.TOOL_SELECTION_THRESHOLD:
            self._select_tool_by_height(hand_pos[1], dy)
            gesture_processed = True

        # Brush size based on horizontal distance
        if abs(dx) > self.BRUSH_SIZE_THRESHOLD:
            self._adjust_brush_size(dx)
            gesture_processed = True

        # Continuous brush stroke
        if abs(dx) > 2 or abs(dy) > 2:
            self._apply_brush_stroke(hand_pos, dx, dy)
            gesture_processed = True

        self.last_hand_pos = hand_pos
        return gesture_processed

    def _select_tool_by_height(self, hand_y: float, delta_y: float):
        """
        Select tools based on hand height position.

        Higher hand position cycles through different tools.

        Args:
            hand_y: Y-coordinate of hand position
            delta_y: Vertical motion delta
        """
        from . import pose_estimator

        direction = 'NEXT' if delta_y < 0 else 'PREV'
        pose_estimator.queue_action('SELECT_TOOL', {"direction": direction})

    def _adjust_brush_size(self, delta_x: float):
        """
        Adjust brush size based on horizontal hand movement.

        Rightward movement increases size, leftward decreases.

        Args:
            delta_x: Horizontal motion delta (positive=right)
        """
        from . import pose_estimator

        size_delta = delta_x * 0.1
        pose_estimator.queue_action('ADJUST_BRUSH', {"size_delta": size_delta})

    def _apply_brush_stroke(self, pos: Tuple[float, float], dx: float, dy: float):
        """
        Apply brush stroke at current hand position.

        Args:
            pos: Current hand position (x, y)
            dx: Horizontal motion delta
            dy: Vertical motion delta
        """
        from . import pose_estimator
        pose_estimator.queue_action('BRUSH_STROKE', {"pos": pos, "delta": (dx, dy)})

    def reset(self):
        """Reset gesture tracking state."""
        self.last_hand_pos = None
        self.tool_change_pending = False


class GestureManager:
    """
    Central manager coordinating left and right hand gesture handling.

    Orchestrates interaction between:
    - Pose estimation (hand positions)
    - Camera gestures (left hand)
    - Brush gestures (right hand)
    - Blender UI state

    Handles gesture filtering and timing to prevent spurious activation.
    """

    def __init__(self):
        """Initialize gesture manager."""
        self.camera_handler = CameraGestureHandler()
        self.brush_handler = BrushGestureHandler()
        self.last_update_frame = 0
        self.frame_skip = 2  # Process every Nth frame to reduce CPU load

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
        self.camera_handler.process_left_hand(
            left_hand_pos,
            left_confidence,
            confidence_threshold
        )

        # Process right hand for brush control
        self.brush_handler.process_right_hand(
            right_hand_pos,
            right_confidence,
            confidence_threshold
        )

    def reset_all(self):
        """Reset all gesture handlers."""
        self.camera_handler.reset()
        self.brush_handler.reset()


# Global gesture manager instance
_gesture_manager: Optional[GestureManager] = None


def initialize_gesture_manager():
    """Initialize global gesture manager."""
    global _gesture_manager
    _gesture_manager = GestureManager()


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
