"""Manual WebSocket test client for pose service."""

import asyncio
import websockets
import json
from pose_service.messages import PoseUpdate


async def test_client():
    """Test connecting to pose service."""
    uri = "ws://127.0.0.1:8000/ws/pose"

    try:
        async with websockets.connect(uri) as ws:
            print(f"[OK] Connected to {uri}")

            # Create fake pose update
            pose = PoseUpdate(
                timestamp=1,
                left_hand_pos=(100, 200),
                left_hand_confidence=0.9,
                gestures=["PAN_LEFT"],
                gesture_data={"PAN_LEFT": {"amount": 10}},
            )

            # Send to server (echo test)
            await ws.send(pose.to_json())
            print(f"[SENT] {pose.to_json()[:50]}...")

            # Receive echo from server
            response = await ws.recv()
            print(f"[RECV] {response[:50]}...")
            print("[OK] Echo test successful!")

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("Make sure the service is running: python -m pose_service.server")


if __name__ == "__main__":
    asyncio.run(test_client())
