"""
QUICK_REFERENCE.md - Quick Gesture Guide
==========================================

Print this page and keep it nearby for quick reference while using the plugin.

HAND GESTURES QUICK REFERENCE
=============================

LEFT HAND - Camera & Navigation Control
========================================

Horizontal Movement:
  ← Move Left  → Pan camera RIGHT
  → Move Right → Pan camera LEFT
  [Motion Threshold: 10 pixels]

Vertical Movement:
  ↑ Move Up   → Pan camera UP
  ↓ Move Down → Pan camera DOWN
  [Motion Threshold: 10 pixels]

Hold Position Steady:
  Keep hand still → Camera stays fixed
  [Hold time: 100ms]

Neutral Position:
  Hand on left side of body, centered in camera view


RIGHT HAND - Tool & Brush Control
==================================

Vertical Movement:
  ↑ Move Up   → Select NEXT tool in list
  ↓ Move Down → Select PREVIOUS tool in list
  [Motion Threshold: 50 pixels]

Horizontal Movement:
  → Move Right → INCREASE brush size
  ← Move Left  → DECREASE brush size
  [Motion Threshold: 20 pixels]

Brush Stroke:
  Any movement > 2 pixels → Apply brush stroke
  Direction determines stroke direction

Neutral Position:
  Hand on right side of body, center to camera view


CONFIGURATION QUICK SETTINGS
============================

For Better Detection:
  Confidence Threshold: 0.4 (if missing detection)
  Confidence Threshold: 0.6 (for stable tracking)
  Confidence Threshold: 0.8 (if too much noise)

For Smoother Tracking:
  Smoothing Factor: 0.5 (more responsive)
  Smoothing Factor: 0.7 (balanced)
  Smoothing Factor: 0.9 (very smooth/slow)

For Multiple Webcams:
  Webcam Index: 0 (primary)
  Webcam Index: 1 (secondary)
  Webcam Index: 2 (tertiary)


USAGE CHECKLIST
===============

Before Starting:
  ☐ Good lighting in the room
  ☐ Webcam connected and working
  ☐ Hands visible and unobstructed
  ☐ Blender in desired mode (SCULPT, PAINT, etc.)

Starting the Plugin:
  ☐ Click "Start Estimation" button
  ☐ Wait 2-3 seconds for initialization
  ☐ Status shows "ACTIVE"
  ☐ Both hands detected (check debug panel)

Using Gestures:
  ☐ Move hands smoothly and deliberately
  ☐ Keep hands within camera frame
  ☐ Avoid sudden movements
  ☐ Monitor confidence scores in debug panel

Finishing:
  ☐ Click "Stop Estimation" button
  ☐ Status shows "INACTIVE"


COMMON ISSUES QUICK FIX
======================

Hands not detected:
  → Check lighting
  → Lower confidence_threshold to 0.3
  → Move hands more to center
  → Close other camera apps

Tracking is jittery:
  → Increase smoothing_factor to 0.8
  → Improve lighting
  → Slow down hand movements

Camera moves but gestures don't:
  → Check confidence scores > threshold
  → Enable debug panel to verify detection
  → Verify you're in correct Blender mode

Slow performance:
  → Close background applications
  → Reduce webcam resolution
  → Increase frame_skip value
  → Check GPU/CPU usage


HAND CONFIDENCE REFERENCE
==========================

Confidence Score Meaning:
  0.8 - 1.0  → Excellent detection (safe to use)
  0.6 - 0.8  → Good detection (normal operation)
  0.4 - 0.6  → Acceptable (may have occasional errors)
  0.2 - 0.4  → Poor (unreliable)
  0.0 - 0.2  → Not detected

If both hands consistently below 0.5:
  → Lower confidence_threshold
  → Improve lighting
  → Ensure hands visible in frame


BLENDER MODE COMPATIBILITY
===========================

Camera Control (Left Hand):
  ✓ Works in ALL modes
  ✓ Object Mode
  ✓ Sculpt Mode
  ✓ Paint Mode
  ✓ Any viewport

Brush Control (Right Hand):
  ✓ Sculpt Mode (main use)
  ✓ Paint Mode (experimental)
  ✗ Limited in Object Mode
  ✗ Not in Edit Mode (yet)

To Enter Sculpt Mode:
  Tab → Select "Sculpt" from menu


DEBUG INFORMATION DISPLAY
=========================

Open Debug Panel:
  1. Find "Debug Info" section in sidebar
  2. Click to expand (if collapsed)

What Each Value Means:
  Frame: Sequential counter (increases each frame)
  Valid: "Yes" = both hands detected above threshold
  Left Hand Confidence: 0.0-1.0 (higher = more certain)
  Right Hand Confidence: 0.0-1.0 (higher = more certain)
  Left Hand Pos: (x, y) screen coordinates
  Right Hand Pos: (x, y) screen coordinates

Tips:
  - If Valid = No, gestures won't work
  - Confidence should be consistent (not fluctuating)
  - Positions should update smoothly


KEYBOARD SHORTCUTS (Blender)
=============================

While Plugin Active:

In 3D Viewport:
  N → Toggle sidebar (show/hide plugin panel)
  Tab → Toggle sculpt mode
  Middle Mouse → Manual camera control
  Scroll → Manual zoom

While Sculpting:
  F → Brush size menu (alternative to gesture)
  Shift+F → Brush strength menu
  [ → Decrease brush size (traditional)
  ] → Increase brush size (traditional)


GESTURE TIPS FOR BEST RESULTS
=============================

1. Hand Positioning
   - Keep hands within camera frame
   - Avoid partial hand views
   - Keep at least 0.5m distance from camera

2. Movement Speed
   - Move hands smoothly and deliberately
   - Avoid jerky or sudden movements
   - Too fast = detection misses gesture
   - Too slow = may not register

3. Lighting
   - Bright, even lighting is essential
   - Avoid strong backlighting
   - Natural daylight works well
   - Avoid shadows on hands

4. Distance from Webcam
   - Optimal: 0.5 - 1.5 meters away
   - Too close: Hands partially out of frame
   - Too far: Confidence scores drop

5. Gesture Amplitude
   - Horizontal pan needs 10+ pixel movement
   - Vertical pan needs 10+ pixel movement
   - Tool selection needs 50+ pixel vertical movement
   - Brush size needs 20+ pixel horizontal movement


PERFORMANCE TARGETS
====================

Expected Performance:

First Launch:
  - MediaPipe initialization: 1-2 seconds (normal)
  - Model download: 5-30 minutes first time (one-time)

Steady State:
  - Pose detection: 20-60 FPS (depends on hardware)
  - Hand tracking latency: 50-100ms
  - Gesture response: < 200ms from movement start

If you see:
  - Low FPS: Check CPU/GPU usage, close other apps
  - High latency: Increase frame_skip to reduce load
  - Freezes: Model may still loading, wait or restart


GESTURE COORDINATE SYSTEM
==========================

Screen Coordinates:
  (0, 0)         → Top-left corner
  (width, 0)     → Top-right corner
  (0, height)    → Bottom-left corner
  (width/2, height/2) → Center

Hand Position in Camera:
  Left = Negative X direction
  Right = Positive X direction
  Up = Negative Y direction
  Down = Positive Y direction


WHEN TO STOP USING THE PLUGIN
==============================

Click Stop when:
  - Finished with gesture control
  - Taking a break (don't leave running)
  - Switching to manual controls
  - Closing Blender
  - Disconnecting webcam

Benefits of Stopping:
  - Frees up CPU/GPU resources
  - Releases webcam access
  - Allows other apps to use camera
  - Reduces heat generation


EMERGENCY SHORTCUTS
====================

If Something Goes Wrong:

System Locked:
  Ctrl+C (in terminal) → Force quit background thread

Blender Frozen:
  Alt+F4 → Close Blender (force if needed)

Camera Won't Release:
  Restart computer (last resort)

Extreme Jitter:
  1. Stop estimation
  2. Increase smoothing_factor to max (1.0)
  3. Restart estimation


CONTACT & SUPPORT
=================

For Help:
1. Check README.md comprehensive guide
2. Review DEVELOPMENT.md for technical details
3. Check system console for error messages
4. Verify all dependencies installed: requirements.txt

Common Resources:
- MediaPipe GitHub: github.com/google-ai-edge/mediapipe
- Blender Manual: docs.blender.org
- Plugin Folder: See INSTALLATION_GUIDE.md


BEFORE YOUR FIRST SESSION
==========================

1. Read this quick reference
2. Check INSTALLATION_GUIDE.md if not yet installed
3. Ensure good lighting
4. Position webcam appropriately
5. Open Blender in Sculpt Mode
6. Find Pose Estimation panel in sidebar
7. Review gesture diagrams above
8. Start with small hand movements
9. Monitor debug panel for confidence
10. Enjoy gesture-based creation!
"""
