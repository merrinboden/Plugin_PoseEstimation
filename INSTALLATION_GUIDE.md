"""
INSTALLATION_GUIDE.md - Step-by-Step Setup Instructions
========================================================

Follow this guide to install and set up the Pose Estimation Blender Plugin
for the first time.

SYSTEM REQUIREMENTS
===================

Hardware:

- Webcam or camera device connected to your computer
- GPU recommended (NVIDIA with CUDA support for best performance)
- Minimum: 4GB RAM, dual-core CPU
- Recommended: 8GB+ RAM, quad-core CPU with GPU

Software:

- Blender 4.0 or newer
- Python 3.8 or newer (included with Blender 4.0+)
- Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)

INSTALLATION STEPS
==================

Step 1: Install System Dependencies
------------------------------------

Windows:

  1. Download and install Python 3.8+ from python.org
  2. During installation, CHECK "Add Python to PATH"
  3. Open Command Prompt and verify:
     python --version

macOS:

  1. Install Homebrew if not already installed:
     /bin/bash -c "$(curl -fsSL <https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh>)"
  2. Install Python:
     brew install python@3.11

Linux (Ubuntu):

  1. Update package manager:
     sudo apt update
  2. Install Python:
     sudo apt install python3 python3-pip python3-venv

Step 2: Install Python Dependencies
------------------------------------

Open terminal/command prompt and run:

# For Windows (Command Prompt as Administrator)

pip install --upgrade pip
pip install opencv-python numpy

# For macOS/Linux

pip3 install --upgrade pip
pip3 install opencv-python numpy

Step 3: Install MediaPipe
-------------------------

This is the simplest step.

   pip install mediapipe

Verify Installation:
   python -c "import mediapipe as mp; print('MediaPipe installed successfully')"

Step 4: Install Blender Plugin
-------------------------------

Option 1: From Blender UI

  1. Open Blender
  2. Go to Edit → Preferences → Add-ons
  3. Click "Install..." button
  4. Navigate to and select the plugin folder
  5. Check the checkbox next to "Pose Estimation Gesture Control"
  6. Click "Save Preferences"

Option 2: Manual Installation

  1. Locate your Blender addons folder:

     Windows:
     C:\Users\<Username>\AppData\Roaming\Blender Foundation\Blender\<version>\scripts\addons\

     macOS:
     ~/Library/Application Support/Blender/<version>/scripts/addons/

     Linux:
     ~/.config/blender/<version>/scripts/addons/

  2. Copy the entire "Plugin_PoseEstimation" folder to that location

  3. Restart Blender

  4. Enable in Preferences > Add-ons (search for "Pose Estimation")

FIRST TIME SETUP
================

Step 1: Verify Webcam
---------------------

1. Before starting the plugin, ensure your webcam works:
   - Windows: Settings > Devices > Camera > Camera privacy settings
   - macOS: System Preferences > Security & Privacy > Camera
   - Linux: Check with: ls /dev/video*

2. Test with another application (Zoom, Teams, etc.)

Step 2: Launch Blender
----------------------

1. Open Blender
2. If prompted about startup configuration, select default settings
3. Wait for Blender to fully load

Step 3: Access the Plugin
-------------------------

1. On the right sidebar, find the "Pose Estimation" tab
   (If not visible, press 'N' key in 3D viewport)

2. You should see:
   - Status indicator
   - Start/Stop buttons
   - Configuration options
   - Information section

Step 4: Configure Settings
---------------------------

Default settings are reasonable to start:

Webcam Index: 0 (default webcam)
Confidence Threshold: 0.5 (balance between sensitivity and noise)
Smoothing: 0.7 (smooth hand tracking)

If webcam not detected:

- Try changing Webcam Index to 1, 2, etc.
- Check if another application is using the webcam

Step 5: Start Pose Estimation
------------------------------

1. Click "Start Estimation" button
2. Wait 1-2 seconds for MediaPipe to initialize
3. Status will change to "ACTIVE" (green indicator)
4. Position your hands in front of the webcam

Expected Results:

- Both hands should be visible to the camera
- Confidence scores in debug panel should be > 0.5
- Smooth hand movements should update position

FIRST TIME USAGE
================

Basic Workflow:

1. Start Pose Estimation (as above)

2. For Camera Navigation:
   - Move your LEFT hand horizontally to pan
   - Move your LEFT hand vertically to tilt
   - Keep hand in center of camera view

3. For Brush Control:
   - Ensure in SCULPT MODE (Tab → Sculpt Mode)
   - Move RIGHT hand to control brush
   - Upward/downward motion to change tools
   - Horizontal motion to adjust brush size

4. Monitor Debug Panel:
   - Check hand confidence scores
   - Ensure "Valid: Yes" for proper detection
   - Verify hand positions updating smoothly

5. Stop when finished:
   - Click "Stop Estimation" button
   - Status returns to "INACTIVE"

TROUBLESHOOTING INITIAL ISSUES
==============================

Issue: "MediaPipe not installed" error
Solution:
   pip install mediapipe
   If still fails, check Python version (3.9+ required):
  python --version

Issue: Webcam not detected (Index error)
Solution:

  1. Try different webcam_index values (0, 1, 2)
  2. Verify webcam with system settings
  3. Close other applications using webcam
  4. Restart Blender
  5. Check for USB camera: lsusb (Linux)

Issue: No hand detection (Low confidence)
Solution:

  1. Improve lighting - move to brighter area
  2. Lower confidence_threshold to 0.3-0.4
  3. Position hands more centrally in frame
  4. Ensure hands are not partially obscured
  5. Check the webcam is active and visible in Blender console logs

Issue: Jerky/jumpy hand tracking
Solution:

  1. Increase smoothing_factor to 0.8-0.9
  2. Keep hands moving at moderate speed
  3. Improve lighting conditions
  4. Check camera resolution isn't too low
  5. Lower frame rate if CPU overloaded

Issue: Plugin doesn't appear in Preferences
Solution:

  1. Verify installation location is correct
  2. Check __init__.py is in plugin root directory
  3. Ensure bl_info dict is present in __init__.py
  4. Restart Blender completely
  5. Check Blender console (Window > Toggle System Console) for errors

PERFORMANCE OPTIMIZATION
=========================

First Run (Slow):

- MediaPipe ships with lightweight runtime assets
- Initialization takes around 1-2 seconds
- This is normal

Subsequent Runs (Normal):

- Models cached locally
- Initialization takes 2-3 seconds
- Normal operation: 20-60 FPS depending on hardware

If Slow on Your Hardware:

1. Reduce resolution:
   - Check webcam resolution settings
   - Lower to 640x480 if using 1080p

2. Skip frames:
   - Edit gesture_handler.py: frame_skip = 5 (higher = faster)

3. Reduce camera resolution if needed:
   - Lower webcam resolution to reduce CPU load

4. Close other camera-heavy applications:
   - Free up webcam bandwidth and system resources

NEXT STEPS
==========

After successful installation and first run:

1. Read README.md for detailed usage guide
2. Check DEVELOPMENT.md for technical details
3. Experiment with gesture customization
4. Fine-tune confidence threshold and smoothing for your setup
5. Consider extending with custom gestures

GETTING HELP
============

If you encounter problems:

1. Check System Console:
   - Window > Toggle System Console (Windows/Linux)
   - Captures detailed error messages

2. Enable Debug Panel:
   - Expand "Debug Info" section in plugin panel
   - Check hand detection and confidence values

3. Check Documentation:
   - README.md - Usage guide
   - DEVELOPMENT.md - Technical details
   - Inline code comments for specific implementation

4. Review Requirements:
   - requirements.txt - All dependencies
   - Check all packages installed correctly

UNINSTALLATION
==============

If you need to remove the plugin:

1. Open Blender Preferences
2. Go to Add-ons
3. Search for "Pose Estimation"
4. Click the checkbox to disable
5. Click "Remove" button

Or manually:

1. Delete plugin folder from addons directory (see Step 4 above)
2. Restart Blender

NEXT: Begin with README.md for comprehensive usage guide
"""
