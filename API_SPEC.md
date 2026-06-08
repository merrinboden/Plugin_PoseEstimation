# Pose Estimation Service - WebSocket API Specification

## Protocol

**WebSocket Protocol**: RFC 6455
**Encoding**: JSON
**Broadcast Rate**: ~16ms (30fps)
**Update Frequency**: Every pose detection frame

## Connection

```
URL: ws://host:port/ws/pose
Default: ws://127.0.0.1:8000/ws/pose
```

## Message Types

### 1. Pose Update (Service → Client, Continuous)

Broadcasted every frame (~16ms) when client is connected.

```json
{
  "type": "pose_update",
  "timestamp": 42,
  "left_hand_pos": [120.5, 200.3],
  "left_hand_confidence": 0.92,
  "left_hand_landmarks": [
    [115.2, 195.1, -0.05],
    [120.5, 190.2, 0.12],
    ...  // 21 total landmarks
  ],
  "right_hand_pos": [500.1, 180.2],
  "right_hand_confidence": 0.95,
  "right_hand_landmarks": [
    [495.2, 175.1, -0.03],
    [500.1, 170.2, 0.15],
    ...  // 21 total landmarks
  ],
  "gestures": [
    "PAN_LEFT",
    "ADJUST_BRUSH"
  ],
  "gesture_data": {
    "PAN_LEFT": {"amount": 15},
    "ADJUST_BRUSH": {"size_delta": 2.5}
  },
  "service_timestamp": 1717861234.567
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "pose_update" |
| timestamp | integer | Frame number (incremental) |
| left_hand_pos | [float, float] | Hand position in screen coordinates [x, y] |
| left_hand_confidence | float | Confidence score 0.0-1.0 |
| left_hand_landmarks | [[float, float, float], ...] | 21 hand landmarks [x, y, z] in pixels |
| right_hand_pos | [float, float] | Hand position [x, y] |
| right_hand_confidence | float | Confidence score 0.0-1.0 |
| right_hand_landmarks | [[float, float, float], ...] | 21 hand landmarks [x, y, z] |
| gestures | [string] | Array of detected gestures this frame |
| gesture_data | object | Metadata for each gesture |
| service_timestamp | float | Unix timestamp for latency measurement |

## Gesture Reference

### Camera Control (Left Hand)

**PAN_LEFT**
```json
{
  "type": "PAN_LEFT",
  "data": {"amount": integer}  // Pixels moved left
}
```
Move left hand left to trigger. Amount scales with speed.

**PAN_RIGHT**
```json
{
  "type": "PAN_RIGHT",
  "data": {"amount": integer}  // Pixels moved right
}
```

**PAN_UP**
```json
{
  "type": "PAN_UP",
  "data": {"amount": integer}  // Pixels moved up
}
```

**PAN_DOWN**
```json
{
  "type": "PAN_DOWN",
  "data": {"amount": integer}  // Pixels moved down
}
```

### Brush Control (Right Hand)

**ADJUST_BRUSH**
```json
{
  "type": "ADJUST_BRUSH",
  "data": {"size_delta": float}  // Change in brush size (-50 to +50)
}
```
Move right hand left/right to trigger. Negative = smaller, positive = larger.

**ADJUST_STRENGTH**
```json
{
  "type": "ADJUST_STRENGTH",
  "data": {"strength_delta": float}  // Change in strength (-1.0 to +1.0)
}
```
Move right hand diagonally to trigger. Scales strength property.

**SELECT_TOOL**
```json
{
  "type": "SELECT_TOOL",
  "data": {"direction": string}  // "NEXT" or "PREV"
}
```
Move right hand vertically to cycle through tools.

**BRUSH_STROKE**
```json
{
  "type": "BRUSH_STROKE",
  "data": {
    "pos": [float, float],      // Absolute position [x, y]
    "delta": [float, float]     // Change since last frame [dx, dy]
  }
}
```
Detected when brush cursor is active and hand is moving.

## Dynamic Gestures

Detected based on motion patterns and timing:

**SWIPE_LEFT**
- Trigger: Fast horizontal movement (>100px in <500ms)
- Action: Undo
- Enabled: true

**SWIPE_RIGHT**
- Trigger: Fast horizontal movement (>100px in <500ms)
- Action: Redo
- Enabled: true

**CIRCULAR_MOTION**
- Trigger: Circular hand motion (>80px radius, 0.5+ rotations)
- Action: Mode toggle
- Enabled: true

## Connection Lifecycle

### Connect
1. Client sends WebSocket handshake
2. Server accepts (HTTP 101)
3. Server starts broadcasting pose updates

### Receive Updates
```python
while connected:
    message = await ws.recv()
    pose = json.loads(message)
    # Process pose/gestures
```

### Disconnect
- Client closes connection: graceful shutdown
- Server detects: stops broadcasting to this client
- Reconnect: new connection starts fresh

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Broadcast Rate | 30fps (16ms) | Limited by pose detection speed |
| Latency | 50-100ms | Hand movement → service detection → client receive |
| Message Size | ~1-3 KB | Includes 42 hand landmarks (21 per hand) |
| Bandwidth | 30-90 KB/s | Per client (30fps × ~3KB) |
| Max Clients | 10+ | Tested; depends on server CPU |
| Frame Drop | 0% | Drop frames instead of buffering |

## Error Handling

### No Hands Detected
```json
{
  "type": "pose_update",
  "timestamp": 15,
  "left_hand_pos": [0, 0],
  "left_hand_confidence": 0.0,
  "left_hand_landmarks": [],
  "right_hand_pos": [0, 0],
  "right_hand_confidence": 0.0,
  "right_hand_landmarks": [],
  "gestures": [],
  "gesture_data": {}
}
```

### Connection Loss
- Client: Reconnect automatically (exponential backoff)
- Server: Gracefully drop client from broadcast list
- No error messages sent; connection simply closes

### Invalid Frames
- Dropped silently; next frame broadcasted normally
- Timestamp advances continuously even with dropped frames

## Configuration API (Future)

Reserved for future extensions:

```json
{
  "type": "get_config",
  "key": "camera_control.left_hand.horizontal_pan.threshold"
}
```

```json
{
  "type": "update_config",
  "updates": {
    "camera_control.left_hand.horizontal_pan.threshold": 30
  }
}
```

## Example Client Implementation

### Python (Async)
```python
import asyncio
import websockets
import json

async def main():
    uri = "ws://127.0.0.1:8000/ws/pose"
    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            pose = json.loads(msg)
            
            if pose['left_hand_confidence'] > 0.5:
                print(f"Left hand at {pose['left_hand_pos']}")
            
            for gesture in pose['gestures']:
                print(f"Gesture: {gesture}")

asyncio.run(main())
```

### JavaScript
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws/pose');

ws.onmessage = (event) => {
    const pose = JSON.parse(event.data);
    
    if (pose.left_hand_confidence > 0.5) {
        console.log(`Left hand at [${pose.left_hand_pos}]`);
    }
    
    pose.gestures.forEach(gesture => {
        console.log(`Gesture: ${gesture}`);
    });
};
```

## Testing

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

### WebSocket Test
```bash
python test_server_manual.py
```

### Manual Connection
```bash
wscat -c ws://127.0.0.1:8000/ws/pose
```

## Rate Limiting

None currently; all connected clients receive all broadcasts.

Future: Per-client rate limiting via client_id parameter.

## Versioning

Current: API v1.0 (no versioning required for MVP)

Future: URL parameter `?api_version=2` for backward compatibility.

---

**API Version**: 1.0
**Last Updated**: 2026-06-08
**Status**: Stable (MVP)
