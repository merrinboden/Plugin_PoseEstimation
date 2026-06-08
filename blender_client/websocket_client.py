"""WebSocket client for connecting Blender to pose service."""

import threading
import queue
import json
from typing import Optional, Dict, Any
import time

try:
    import websockets
    import asyncio
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class PoseServiceClient:
    """Async WebSocket client for pose service (runs in background thread)."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """Initialize WebSocket client."""
        self.uri = f"ws://{host}:{port}/ws/pose"
        self.connected = False
        self.pose_queue = queue.Queue(maxsize=1)
        self.event_loop = None
        self.thread = None
        self.running = False

    def start(self):
        """Start WebSocket connection in background thread."""
        if not WEBSOCKETS_AVAILABLE:
            print("[Blender Client] websockets library not available")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_client, daemon=True)
        self.thread.start()
        print(f"[Blender Client] Connecting to {self.uri}...")

    def _run_client(self):
        """Run async event loop for WebSocket."""
        try:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(self._connect())
        except Exception as e:
            print(f"[Blender Client] Error in client loop: {e}")
            self.connected = False

    async def _connect(self):
        """Connect to pose service and receive updates."""
        if not WEBSOCKETS_AVAILABLE:
            return

        try:
            async with websockets.connect(self.uri, ping_interval=None) as ws:
                self.connected = True
                print("[Blender Client] Connected to service")

                while self.running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)

                        # Queue latest pose (drop old if queue full)
                        try:
                            self.pose_queue.put_nowait(data)
                        except queue.Full:
                            try:
                                self.pose_queue.get_nowait()
                            except queue.Empty:
                                pass
                            self.pose_queue.put_nowait(data)

                    except asyncio.TimeoutError:
                        continue

        except Exception as e:
            print(f"[Blender Client] Connection error: {e}")
            self.connected = False

    def get_latest_pose(self) -> Optional[Dict[str, Any]]:
        """Get latest pose update (non-blocking)."""
        try:
            return self.pose_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        """Stop WebSocket connection."""
        self.running = False
        self.connected = False
        if self.event_loop:
            try:
                self.event_loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=2.0)
