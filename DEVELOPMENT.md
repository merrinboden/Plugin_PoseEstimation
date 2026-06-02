"""
DEVELOPMENT.md - Technical Development Guide
==============================================

This document provides technical details for developers extending or maintaining
the Pose Estimation Blender Plugin.

ARCHITECTURE OVERVIEW
=====================

The plugin follows a modular architecture with clear separation of concerns:

┌─────────────────────────────────────────────────────────────────────┐
│                         Blender UI Layer                             │
│  (ui_panel.py: PoseEstimationPanel, Operators, Debug Panel)         │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Gesture Recognition Layer                         │
│  (gesture_handler.py: GestureManager, Handlers)                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Pose Estimation Layer                              │
│  (pose_estimator.py: MediaPipe Integration, Threading)              │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│            Hardware Layer (MediaPipe + OpenCV)                       │
│  (Webcam Capture, CPU Processing)                                    │
└─────────────────────────────────────────────────────────────────────┘

DATA FLOW
=========

1. Webcam Capture (pose_estimator.py):
   Webcam → OpenCV VideoCapture → Frame Buffer

2. Pose Estimation:
   Frame Buffer → MediaPipe Inference → Pose Landmarks (33 joints) → Confidence Scores

3. Hand Extraction:
   Pose Landmarks → Extract Left/Right Wrist (indices 15, 16) → Filter by Confidence

4. Smoothing:
   Raw Positions → Exponential Moving Average → Smoothed Positions

5. Gesture Recognition:
   Smoothed Positions → Motion Deltas → Gesture Classification

6. Blender Action Mapping:
   Gestures → CameraGestureHandler / BrushGestureHandler → Blender Operators

THREADING MODEL
===============

The plugin uses background threading to avoid blocking Blender's UI thread:

Main Thread (Blender UI):
- Handles user interactions
- Updates Blender UI
- Calls pose_estimator.get_latest_pose() (non-blocking)
- Triggers gesture processing
- Time: < 1ms per frame

Background Thread (pose_estimator._capture_thread):
- Runs webcam capture loop
- Calls MediaPipe inference (CPU-friendly)
- Queues results (max 1 frame in queue)
- Time: ~10-40ms per frame (depends on hardware)

Queue-based Communication:
- Thread-safe queue for pose results
- Latest frame stored, older frames dropped
- Prevents memory buildup
- Prevents stalls if inference slow

MEDIAPIPE LANDMARK INDICES
==========================

MediaPipe Pose provides 33 landmarks.

Body Landmarks:
0  - Nose
11 - Left Shoulder
12 - Right Shoulder
15 - Left Wrist        ← LEFT HAND
16 - Right Wrist       ← RIGHT HAND

Data Format per Landmark:
Each landmark is converted to [x, y, confidence] where:
- x: Horizontal pixel position in frame
- y: Vertical pixel position in frame
- confidence: Visibility/presence score

GESTURE RECOGNITION ALGORITHM
==============================

Left Hand Gestures (Camera Control):

1. Horizontal Pan Detection:
   - Threshold: PAN_THRESHOLD = 10 pixels
   - If |dx| > 10:
     - Pan camera left if dx < 0
     - Pan camera right if dx > 0

2. Vertical Pan Detection:
   - Threshold: PAN_THRESHOLD = 10 pixels
   - If |dy| > 10:
     - Pan camera up if dy > 0
     - Pan camera down if dy < 0

3. Zoom Detection (optional):
   - Forward/backward hand motion
   - Requires depth estimation or fixed hand position
   - Currently implemented as reserved for future enhancement

Right Hand Gestures (Brush Control):

1. Tool Selection:
   - Threshold: TOOL_SELECTION_THRESHOLD = 50 pixels
   - Vertical hand motion cycles through tools
   - Each tool has unique behavior
   - Motion direction determines cycle direction

2. Brush Size Adjustment:
   - Threshold: BRUSH_SIZE_THRESHOLD = 20 pixels
   - Horizontal motion controls size
   - Right motion increases size
   - Left motion decreases size
   - Range: 1.0 to 500.0

3. Brush Stroke Application:
   - Any motion > 2 pixels applied as stroke
   - Position mapped to 3D model surface
   - Depends on Blender sculpt/paint mode
   - Can include pressure simulation

CONFIGURATION PARAMETERS
========================

Scene Properties (pose_est_props):

is_active: bool
  - Enables/disables pose estimation
  - Controls background thread execution
  - Updates UI status display

smoothing_factor: float (0.0 - 1.0)
  - Exponential moving average coefficient
  - Formula: smoothed = alpha * new + (1 - alpha) * previous
  - 0.0 = no smoothing (raw data)
  - 1.0 = maximum smoothing (slow response)
  - Recommended: 0.6 - 0.8

confidence_threshold: float (0.0 - 1.0)
  - Minimum confidence to consider detection valid
  - Filters low-confidence noisy detections
  - 0.0 = accept all detections
  - 1.0 = only accept very confident detections
  - Recommended: 0.5 - 0.7

webcam_index: int (>= 0)
  - Operating system device index
  - 0 = primary/default webcam
  - Higher numbers for multiple cameras
  - Enumerate with: cv2.VideoCapture().list_devices()

gesture_mode: enum
  - CAMERA: Left hand camera control enabled
  - BRUSH: Right hand brush control enabled
  - Future: Mix, custom modes

EXTENDING THE PLUGIN
====================

Adding New Gestures:

1. Define gesture in gesture_handler.py:
   ```python
   class NewGestureHandler:
       def detect_gesture(self, hand_pos, delta_x, delta_y):
           # Implement detection logic
           pass
       
       def apply_gesture(self):
           # Implement Blender interaction
           pass
   ```

2. Add to GestureManager:
   ```python
   def __init__(self):
       self.new_handler = NewGestureHandler()
   ```

3. Call in process_pose():
   ```python
   self.new_handler.detect_gesture(...)
   ```

4. Update UI panel with configuration options if needed

Adding New Pose Models:

1. Modify the landmark mapping in pose_estimator.py if you want to use a different pose backend.

2. Update keypoint indices in PoseEstimator class if the landmark model changes.

3. Adjust gesture detection thresholds as needed

Supporting Multiple People:

1. Extend pose_estimator.py to select a person by score or tracking logic.

2. Update _extract_hand_positions() to handle multiple landmark sets.

3. Extend GestureManager to track multiple hands

DEBUGGING TECHNIQUES
====================

Enable Debug Panel:
- Shows real-time pose detection status
- Displays hand confidence scores
- Shows current hand positions
- Check for Invalid = True if gesture not working

Check System Console:
- Print statements log important events
- Visible in Blender's System Console
- Look for errors during pose detection

Log Files:
- Add logging module for persistent logs:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Pose detected at frame %d", frame_number)
  ```

Performance Profiling:
- Use timeit to measure function duration:
  ```python
  import timeit
  time_ms = timeit.timeit(lambda: estimate_pose(), number=1) * 1000
  ```

Visualize Predictions:
- Draw keypoints on frame in pose_estimator.py
- Use cv2.circle() and cv2.line()
- Display with cv2.imshow() for development

KNOWN ISSUES AND WORKAROUNDS
=============================

Issue: MediaPipe initialization slow
Workaround:
- Reduce model complexity if needed
- Initialization should be near-instant after import
- Subsequent runs are typically stable

Issue: Hand detection fails on fast motion
Workaround:
- Lower frame skip value in GestureManager
- Increase smoothing_factor to predict motion
- Consider temporal filtering (Kalman filter)

Issue: Camera jitter with low confidence
Workaround:
- Increase confidence_threshold
- Improve lighting conditions
- Increase smoothing_factor

TESTING STRATEGY
================

Unit Tests:

PoseDetectionState:
- Test initialization
- Verify data structure

PoseEstimator:
- Test smoothing algorithm
  ```python
  assert smooth((10, 10), (0, 0), 0.5) == (5, 5)
  ```
- Test keypoint extraction

GestureHandlers:
- Test threshold detection
- Verify gesture classification

Integration Tests:

End-to-end flow:
1. Start webcam capture
2. Process frame with MediaPipe
3. Extract wrists
4. Generate gestures
5. Verify Blender state changed

Performance Tests:
- Measure thread timing
- Monitor queue depth
- Track memory usage

UI Tests:
- Verify panel layout
- Test button functionality
- Confirm property updates

OPTIMIZATION OPPORTUNITIES
===========================

Short-term:
- Implement Kalman filtering for hand tracking
- Reduce camera resolution if needed
- Implement motion prediction to reduce latency
- Add frame rate adaptation

Long-term:
- Replace the current pose backend with a hand-specific model if needed
- Implement hand pose (finger positions)
- Add machine learning gesture classifier
- Support multiple simultaneous users
- Implement gesture recording/playback

FUTURE ROADMAP
==============

Phase 2:
- Finger position tracking
- Pressure sensitivity
- Custom gesture recording
- Gesture library/presets

Phase 3:
- Multiple user support
- Network synchronization
- Advanced gesture machine learning
- Integration with other tools

Phase 4:
- Real-time hand mesh rendering
- Full body tracking
- Motion capture export
- Animation keyframing

REFERENCES
==========

MediaPipe Documentation:
https://developers.google.com/mediapipe

MediaPipe Pose:
https://developers.google.com/mediapipe/solutions/vision/pose_landmarker

Blender Python API:
https://docs.blender.org/api/current/

Blender Plugin Development:
https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

OpenCV Documentation:
https://docs.opencv.org/

HCI Best Practices (ISO 9241-110):
- Suitability for task
- Self-descriptiveness
- Controllability
- Error tolerance
- Suitability for learning
"""
