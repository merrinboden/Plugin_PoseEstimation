"""WebSocket message schemas for pose service."""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, asdict, field
import json


@dataclass
class HandLandmark:
    """Single hand landmark (21 per hand)."""

    x: float
    y: float
    z: float


@dataclass
class PoseUpdate:
    """Broadcasted pose update from service (sent every ~16ms at 30fps)."""

    type: str = "pose_update"
    timestamp: int = 0

    # Left hand
    left_hand_pos: Tuple[float, float] = (0, 0)
    left_hand_confidence: float = 0.0
    left_hand_landmarks: List[Tuple[float, float, float]] = field(default_factory=list)

    # Right hand
    right_hand_pos: Tuple[float, float] = (0, 0)
    right_hand_confidence: float = 0.0
    right_hand_landmarks: List[Tuple[float, float, float]] = field(default_factory=list)

    # Detected gestures this frame
    gestures: List[str] = field(default_factory=list)  # ["PAN_LEFT", "ADJUST_BRUSH"]
    gesture_data: Dict = field(default_factory=dict)  # {"PAN_LEFT": {"amount": 10}}

    # Service timestamp for latency measurement
    service_timestamp: float = 0.0

    def to_json(self) -> str:
        """Convert to JSON for WebSocket transmission."""
        data = asdict(self)
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str):
        """Parse from JSON."""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ClientMessage:
    """Client → Server message."""

    type: str  # "get_config", "update_config", "ack_action"
    data: Optional[Dict] = None

    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str):
        """Parse from JSON."""
        data = json.loads(json_str)
        return cls(**data)
