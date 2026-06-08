"""FastAPI WebSocket server for pose estimation service."""

# Import matplotlib before mediapipe to avoid circular imports
try:
    import matplotlib
    matplotlib.use('Agg')
except:
    pass

import asyncio
import json
import time
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .pose_engine import PoseEstimator, PoseDetectionState

app = FastAPI(title="Pose Estimation Service")

# CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manage WebSocket connections for broadcasting pose data."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[Server] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        self.active_connections.remove(websocket)
        print(f"[Server] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[Server] Broadcast error: {e}")


manager = ConnectionManager()

# Global pose estimator instance
pose_estimator: Optional[PoseEstimator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize pose estimator on server startup."""
    global pose_estimator
    try:
        print("[Server] Starting pose estimator...")
        pose_estimator = PoseEstimator(
            webcam_index=0,
            confidence_threshold=0.5,
            debug_window=True,
            broadcaster=None  # Service will pull from queue instead
        )
        pose_estimator.start()
        print("[Server] Pose estimator started")

        # Start background task to broadcast pose updates
        asyncio.create_task(broadcast_pose_updates())
    except Exception as e:
        print(f"[Server] Warning: Could not start pose estimator: {e}")
        print("[Server] Continuing without pose estimation (test mode)")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop pose estimator on server shutdown."""
    global pose_estimator
    if pose_estimator:
        print("[Server] Stopping pose estimator...")
        pose_estimator.stop()


async def broadcast_pose_updates():
    """Background task to broadcast pose updates to all clients."""
    global pose_estimator
    while True:
        if pose_estimator:
            try:
                # Get latest pose from estimator's queue (non-blocking)
                pose_state = pose_estimator.get_latest_pose()
                if pose_state:
                    # Convert state to JSON-serializable format
                    pose_data = {
                        "type": "pose_update",
                        "timestamp": pose_state.timestamp,
                        "left_hand_pos": pose_state.left_hand_pos,
                        "left_hand_confidence": pose_state.left_hand_confidence,
                        "left_hand_landmarks": (
                            pose_state.left_hand_landmarks.tolist()
                            if pose_state.left_hand_landmarks is not None
                            else []
                        ),
                        "right_hand_pos": pose_state.right_hand_pos,
                        "right_hand_confidence": pose_state.right_hand_confidence,
                        "right_hand_landmarks": (
                            pose_state.right_hand_landmarks.tolist()
                            if pose_state.right_hand_landmarks is not None
                            else []
                        ),
                        "service_timestamp": time.time(),
                    }
                    await manager.broadcast(pose_data)

            except Exception as e:
                print(f"[Broadcast] Error: {e}")

        # Sleep briefly to avoid busy-waiting (~16ms for ~60fps)
        await asyncio.sleep(0.016)


@app.websocket("/ws/pose")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for pose updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive any client messages (for future: config updates, commands)
            data = await websocket.receive_text()
            print(f"[Server] Received: {data}")

            # Echo test
            await websocket.send_json({"type": "echo", "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[Server] Error: {e}")
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "clients": len(manager.active_connections)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9001)
