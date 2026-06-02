"""
README: Pose Estimation Blender Plugin
========================================

A real-time gesture-based control system for Blender using MediaPipe pose estimation
and live webcam input. Control the 3D viewport and painting tools through hand gestures.

INSTALLATION
============

1. Prerequisites:
   - Blender 4.0 or newer
   - Python 3.9+ (for MediaPipe)
   - OpenCV (cv2)
   - MediaPipe library

2. Install Dependencies:

   Open your system terminal and install required Python packages:

   pip install opencv-python
   pip install mediapipe

3. Install Plugin:

   a. In Blender, go to Edit > Preferences > Add-ons
   b. Click "Install..." and select the plugin folder
   c. Enable the "Pose Estimation Gesture Control" addon

   Alternatively, copy the plugin folder to Blender's addon directory:
   - Windows: %APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\
   - Linux: ~/.config/blender/<version>/scripts/addons/
   - macOS: ~/Library/Application Support/Blender/<version>/scripts/addons/

USAGE
=====

1. Initial Setup:

   - Go to View3D > Sidebar > Pose Estimation tab
   - Ensure your webcam is properly connected
   - Verify lighting conditions (good lighting recommended)

2. Starting Pose Estimation:

   - Click "Start Estimation" button
   - Allow the system 1-2 seconds to initialize MediaPipe
   - Status will change to "ACTIVE"

3. Hand Gesture Control:

   LEFT HAND (Camera Navigation):
   - Move left hand horizontally: Pan camera left/right
   - Move left hand vertically: Pan camera up/down
   - Move left hand forward: Zoom in (if depth available)
   - Move left hand backward: Zoom out (if depth available)

   RIGHT HAND (Tool/Brush Control):
   - Vertical position: Cycle through sculpting/painting tools
   - Horizontal movement: Adjust brush size
   - Hand movement: Apply brush strokes to model
   - Distance from body: Modulate brush pressure (optional)

4. Configuration:

   Webcam Index:
   - 0 = Default/primary webcam
   - 1, 2, etc. = Secondary webcams (if multiple connected)

   Confidence Threshold:
   - Range: 0.0 to 1.0
   - Higher = more strict detection (fewer false positives)
   - Recommended: 0.5 to 0.7
   - If hands not detected, lower this value

   Smoothing Factor:
   - Range: 0.0 to 1.0
   - Higher = smoother hand tracking (less jittery)
   - Recommended: 0.6 to 0.8
   - If tracking feels slow, lower this value

REQUIREMENTS
============

File Structure:
```
Plugin_PoseEstimation/
├── __init__.py                 # Main plugin entry point
├── pose_estimator.py          # MediaPipe integration and webcam capture
├── gesture_handler.py         # Gesture recognition and mapping
├── ui_panel.py               # Blender UI components
└── (no external model folder required)
```

Dependencies:
- Blender 4.0+
- Python 3.8+
- opencv-python
- mediapipe
- numpy

DOCUMENTATION
==============

Module Overview:

__init__.py:
- Plugin registration and Blender integration
- Property definitions for configuration
- Plugin lifecycle management

pose_estimator.py:
- PoseDetectionState: Container for detection results
- PoseEstimator: Main MediaPipe engine with threading
- Functions for starting/stopping estimation

gesture_handler.py:
- CameraGestureHandler: Left-hand camera control gestures
- BrushGestureHandler: Right-hand tool/brush control gestures
- GestureManager: Coordinator between gesture handlers

ui_panel.py:
- PoseEstimationPanel: Main control panel UI
- StartPoseEstimationOperator: Start functionality
- StopPoseEstimationOperator: Stop functionality
- PoseEstimationDebugPanel: Debug information display

CLASS HIERARCHY
===============

PoseEstimationProperties (bpy.types.PropertyGroup)
├── is_active: bool
├── smoothing_factor: float (0-1)
├── confidence_threshold: float (0-1)
├── webcam_index: int
└── gesture_mode: enum

PoseDetectionState
├── left_hand_pos: (x, y)
├── left_hand_confidence: float
├── right_hand_pos: (x, y)
├── right_hand_confidence: float
├── body_keypoints: numpy array
├── timestamp: int
└── is_valid: bool

PoseEstimator
├── _setup_mediapipe_params()
├── _extract_hand_positions()
├── _apply_smoothing()
├── _process_frame()
├── _capture_thread()
├── start()
├── stop()
├── get_latest_pose()
└── update_config()

GestureManager
├── CameraGestureHandler
│   ├── process_left_hand()
│   ├── _pan_camera_horizontal()
│   ├── _pan_camera_vertical()
│   └── zoom_camera()
└── BrushGestureHandler
    ├── process_right_hand()
    ├── _select_tool_by_height()
    ├── _adjust_brush_size()
    └── _apply_brush_stroke()

TROUBLESHOOTING
===============

Issue: Webcam not detected
Solution:
- Check that webcam is connected and recognized by OS
- Try different webcam_index values (0, 1, 2...)
- Test webcam with another application first

Issue: Hands not detected / Low confidence scores
Solution:
- Improve lighting conditions
- Lower confidence_threshold in settings
- Ensure hands are clearly visible and not occluded
- Keep hands within frame center

Issue: Tracking feels jittery
Solution:
- Increase smoothing_factor value
- Reduce confidence_threshold slightly
- Ensure good lighting conditions

Issue: Performance is slow / High CPU usage
Solution:
- Lower video frame rate in webcam settings
- Increase frame_skip value in gesture_handler.py
- Disable debug panel if not needed
- Ensure no other heavy processes running

Issue: MediaPipe import error
Solution:
- Verify MediaPipe installation: pip install mediapipe
- Ensure correct Python version (3.9+)
- Check that Blender Python path matches installation

PERFORMANCE CONSIDERATIONS
===========================

Threading:
- Pose estimation runs in separate thread to avoid blocking UI
- Results queued with maximum size to prevent memory buildup

Gesture Recognition:
- Frame skipping reduces processing overhead
- Motion thresholds filter noise
- Exponential moving average smoothing reduces jitter

MediaPipe:
- Lightweight runtime with no separate model download step
- Single-person tracking mode optimized for performance
- Hand detection is built in through the pose landmarks

FUTURE ENHANCEMENTS
===================

Planned Features:
- Two-hand coordination gestures
- Pressure sensitivity based on hand-body distance
- Custom gesture recording and mapping
- Performance metrics and FPS display
- Support for MediaPipe as the default pose backend
- Multiplayer gesture synchronization (network)
- Gesture replay and recording

Known Limitations:
- Single person tracking only
- Occlusion handling limited
- No support for fingers individually (hand detection only)
- Latency depends on hardware (typically 50-100ms)

LICENSE
=======

This plugin is provided as-is for educational and research purposes.
See LICENSE file for details.

SUPPORT
=======

For issues or questions:
1. Check troubleshooting section above
2. Review pose_estimator.py and gesture_handler.py documentation
3. Enable debug panel for diagnostic information
4. Check Blender system console for error messages

Contact:
development.team@example.com

VERSION HISTORY
===============

v1.0.0 (Current):
- Initial release
- MediaPipe integration
- Left hand camera control
- Right hand brush control
- Real-time UI with configuration options
- Debug panel for monitoring
"""

# This file serves as inline documentation
# For development notes, see DEVELOPMENT.md
