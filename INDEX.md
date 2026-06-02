"""
INDEX.md - Project Overview & File Structure
==============================================

Complete Pose Estimation Blender Plugin Implementation
Version 1.0.0

PROJECT STRUCTURE
==================

Plugin_PoseEstimation/
│
├── __init__.py
│   ├─ Main plugin entry point for Blender
│   ├─ Plugin registration and lifecycle management
│   ├─ PoseEstimationProperties class definition
│   └─ ~130 lines of documented code
│
├── pose_estimator.py
│   ├─ MediaPipe integration for real-time pose detection
│   ├─ Webcam capture and frame processing
│   ├─ Hand position extraction and smoothing
│   ├─ Threading for background processing
│   ├─ PoseDetectionState data container
│   ├─ PoseEstimator main class with full documentation
│   └─ ~400 lines of documented code
│
├── gesture_handler.py
│   ├─ Gesture recognition and mapping to Blender actions
│   ├─ CameraGestureHandler for left-hand camera control
│   ├─ BrushGestureHandler for right-hand tool/brush control
│   ├─ GestureManager orchestrating gesture processing
│   ├─ Motion threshold-based gesture detection
│   ├─ Confidence-based filtering
│   └─ ~350 lines of documented code
│
├── ui_panel.py
│   ├─ Blender UI panel components
│   ├─ PoseEstimationPanel - main control interface
│   ├─ StartPoseEstimationOperator - startup button
│   ├─ StopPoseEstimationOperator - shutdown button
│   ├─ PoseEstimationDebugPanel - diagnostics display
│   ├─ Modal event handling for continuous updates
│   └─ ~300 lines of documented code
│
├── README.md
│   ├─ Comprehensive user guide
│   ├─ Installation instructions
│   ├─ Usage walkthrough and tutorials
│   ├─ Troubleshooting guide
│   ├─ Performance optimization tips
│   ├─ Module documentation
│   ├─ Future enhancements roadmap
│   └─ ~350 lines of detailed documentation
│
├── INSTALLATION_GUIDE.md
│   ├─ Step-by-step installation for beginners
│   ├─ System requirements (hardware and software)
│   ├─ Dependency installation for Windows/macOS/Linux
│   ├─ MediaPipe installation
│   ├─ Blender plugin installation
│   ├─ First-time setup walkthrough
│   ├─ Initial troubleshooting
│   ├─ Performance optimization
│   └─ ~300 lines of beginner-friendly guide
│
├── DEVELOPMENT.md
│   ├─ Technical architecture documentation
│   ├─ Data flow diagrams
│   ├─ Threading model explanation
│   ├─ MediaPipe landmark reference
│   ├─ Gesture recognition algorithm details
│   ├─ Configuration parameters documentation
│   ├─ Extension guidelines
│   ├─ Debugging techniques
│   ├─ Testing strategy
│   ├─ Optimization opportunities
│   └─ ~450 lines of developer documentation
│
├── QUICK_REFERENCE.md
│   ├─ One-page gesture reference guide
│   ├─ Left hand gesture summary
│   ├─ Right hand gesture summary
│   ├─ Configuration quick settings
│   ├─ Common issues quick fixes
│   ├─ Usage checklist
│   ├─ Emergency shortcuts
│   ├─ Perfect for printing
│   └─ ~300 lines of quick reference
│
├── requirements.txt
│   ├─ Python package dependencies
│   ├─ opencv-python >= 4.5.0
│   ├─ numpy >= 1.19.0
│   ├─ mediapipe >= 0.10.0
│   └─ Used by: pip install -r requirements.txt
│
└── INDEX.md (this file)
    ├─ Project overview
    ├─ File structure explanation
    ├─ Documentation guide
    └─ Quick navigation


FILE DESCRIPTIONS
==================

CORE PLUGIN FILES (Required)
============================

__init__.py (Main Entry Point)
  Purpose: Register plugin with Blender, manage lifecycle
  Key Classes: PoseEstimationProperties
  Key Functions: register(), unregister()
  Documentation: Full docstrings on all functions and classes
  Lines of Code: ~130
  Imports: bpy (Blender API)

pose_estimator.py (MediaPipe Integration)
  Purpose: Capture webcam, run MediaPipe, extract hand positions
  Key Classes:
    - PoseDetectionState: Data container for pose results
    - PoseEstimator: Main pose estimation engine
  Key Algorithms:
    - Exponential moving average smoothing
    - Hand keypoint extraction
    - Threading-based frame processing
  Documentation: Extensive inline comments, class docstrings
  Lines of Code: ~400
  Imports: cv2 (OpenCV), numpy, threading, mediapipe

gesture_handler.py (Gesture Recognition)
  Purpose: Interpret hand positions as gestures, map to Blender actions
  Key Classes:
    - CameraGestureHandler: Left-hand camera control
    - BrushGestureHandler: Right-hand tool/brush control
    - GestureManager: Coordinator
  Key Algorithms:
    - Motion threshold detection
    - Tool selection by hand height
    - Brush size adjustment based on movement
  Documentation: Full docstrings, usage examples
  Lines of Code: ~350
  Imports: bpy (Blender API)

ui_panel.py (Blender Interface)
  Purpose: Provide user interface in Blender viewport sidebar
  Key Classes:
    - PoseEstimationPanel: Main control panel
    - StartPoseEstimationOperator: Start button operator
    - StopPoseEstimationOperator: Stop button operator
    - PoseEstimationDebugPanel: Debug information display
  Key Features:
    - Modal event handling
    - Real-time status display
    - Configuration controls
    - Debug information
  Documentation: Full docstrings for all operators
  Lines of Code: ~300
  Imports: bpy (Blender API)

DOCUMENTATION FILES (Reference)
================================

README.md (Main Documentation)
  Contents:
    - Installation instructions
    - Feature overview
    - Usage guide for different hand positions
    - Configuration parameter explanation
    - Module overview
    - Class hierarchy
    - Troubleshooting guide with solutions
    - Performance considerations
    - Future enhancements
  Audience: All users
  Read When: First time using plugin or looking for comprehensive guide

INSTALLATION_GUIDE.md (Setup Instructions)
  Contents:
    - System requirements
    - Step-by-step installation for Windows/macOS/Linux
    - First-time setup walkthrough
    - Troubleshooting installation issues
    - Performance optimization
    - Uninstallation instructions
  Audience: Users installing for first time
  Read When: Setting up the plugin or troubleshooting installation

DEVELOPMENT.md (Technical Reference)
  Contents:
    - Architecture overview with diagrams
    - Data flow explanation
    - Threading model
    - MediaPipe landmark reference
    - Gesture recognition algorithm details
    - Configuration parameters
    - Extension guidelines
    - Debugging techniques
    - Testing strategy
    - Optimization opportunities
    - Future roadmap
  Audience: Developers maintaining/extending plugin
  Read When: Extending plugin or understanding technical details

QUICK_REFERENCE.md (Cheat Sheet)
  Contents:
    - One-page gesture guide
    - Hand movement quick reference
    - Configuration quick settings
    - Usage checklist
    - Common issues quick fixes
    - Performance targets
    - Emergency shortcuts
  Audience: Users during active use
  Read When: During sessions or can be printed as reference

INDEX.md (This File)
  Contents:
    - Project structure overview
    - File descriptions
    - Documentation guide
    - Reading recommendations
  Audience: New users understanding project layout
  Read When: First time exploring project

requirements.txt (Dependency List)
  Contents:
    - Python package requirements
    - Version specifications
    - Used by pip package manager
  Audience: Installation scripts
  Read When: Installing dependencies


DOCUMENTATION FLOWCHART
======================

START HERE → INDEX.md (you are here)
     ↓
     ├→ First Time User?
     │  ├→ INSTALLATION_GUIDE.md (setup)
     │  └→ README.md (how to use)
     │
     ├→ During Active Use?
     │  └→ QUICK_REFERENCE.md (gestures)
     │
     ├→ Want to Extend Plugin?
     │  ├→ DEVELOPMENT.md (architecture)
     │  └→ Read source code comments
     │
     └→ Problem Solving?
        ├→ README.md → Troubleshooting section
        ├→ QUICK_REFERENCE.md → Common issues
        └→ DEVELOPMENT.md → Debug techniques


CODE ORGANIZATION
=================

Module Hierarchy:

blender (Blender API)
  └─ pose_estimation_plugin
      ├─ Core Components
      │   ├─ PoseEstimationProperties (scene settings)
      │   ├─ PoseEstimator (MediaPipe wrapper)
      │   └─ GestureManager (gesture processing)
      │
      ├─ UI Components
      │   ├─ PoseEstimationPanel (main UI)
      │   ├─ PoseEstimationDebugPanel (debug UI)
      │   ├─ StartPoseEstimationOperator (button)
      │   └─ StopPoseEstimationOperator (button)
      │
      └─ External Dependencies
          ├─ MediaPipe (pose detection)
          ├─ OpenCV (camera capture)
          └─ NumPy (numerical operations)


DOCUMENTATION STATISTICS
========================

Total Lines of Code: ~1,180
  - Excluding comments and docstrings: ~900
  - Including comments and docstrings: ~1,180

Total Documentation Lines: ~1,700
  - README.md: ~350 lines
  - INSTALLATION_GUIDE.md: ~300 lines
  - DEVELOPMENT.md: ~450 lines
  - QUICK_REFERENCE.md: ~300 lines
  - Code comments: ~400 lines

Documentation Coverage:
  - Every function documented
  - Every class documented
  - Every module documented
  - Algorithm explanations included
  - Usage examples provided

Code Comments Style:
  - Docstrings for modules, classes, and functions
  - Inline comments for complex algorithms
  - No redundant comments (code speaks for itself)
  - Algorithm explanations where non-obvious


KEY FEATURES BY FILE
====================

__init__.py Features:
  ✓ Plugin registration
  ✓ Property management
  ✓ Lifecycle management
  ✓ Configuration storage

pose_estimator.py Features:
  ✓ Webcam capture (OpenCV)
  ✓ MediaPipe inference
  ✓ Hand keypoint extraction
  ✓ Motion smoothing (EMA)
  ✓ Background threading
  ✓ Queue-based communication
  ✓ Confidence filtering

gesture_handler.py Features:
  ✓ Motion threshold detection
  ✓ Left-hand camera gestures
  ✓ Right-hand brush gestures
  ✓ Tool selection cycling
  ✓ Brush size adjustment
  ✓ Gesture filtering

ui_panel.py Features:
  ✓ Control panel UI
  ✓ Start/Stop buttons
  ✓ Configuration sliders
  ✓ Status indicator
  ✓ Debug information
  ✓ Modal event handling
  ✓ Real-time updates


GETTING STARTED PATHS
=====================

Path 1: Just Want to Use It
  1. Read: INSTALLATION_GUIDE.md
  2. Install: Follow step-by-step instructions
  3. Run: Enable plugin in Blender
  4. Use: Reference QUICK_REFERENCE.md during sessions

Path 2: Want to Understand It First
  1. Read: README.md (Features & Usage sections)
  2. Read: DEVELOPMENT.md (Architecture section)
  3. Read: Source code (__init__.py, then pose_estimator.py)
  4. Install: INSTALLATION_GUIDE.md
  5. Use: QUICK_REFERENCE.md

Path 3: Want to Extend/Modify It
  1. Read: DEVELOPMENT.md (entire file)
  2. Study: pose_estimator.py (threading, algorithms)
  3. Study: gesture_handler.py (gesture recognition)
  4. Modify: gesture_handler.py (add new gestures)
  5. Test: Enable debug panel, monitor output

Path 4: Troubleshooting Issues
  1. Check: README.md → Troubleshooting section
  2. Check: QUICK_REFERENCE.md → Common Issues
  3. Enable: Debug Panel in plugin UI
  4. Read: DEVELOPMENT.md → Debugging Techniques section
  5. Monitor: System console for error messages


QUICK LINKS BY TASK
===================

Task: Install plugin
  → INSTALLATION_GUIDE.md

Task: First time using
  → README.md (Usage section)
  → QUICK_REFERENCE.md

Task: Adjust settings
  → README.md (Configuration section)
  → QUICK_REFERENCE.md (Configuration Quick Settings)

Task: Understand code
  → DEVELOPMENT.md (Architecture section)
  → Source code docstrings

Task: Add new gesture
  → DEVELOPMENT.md (Extending the Plugin section)
  → gesture_handler.py comments

Task: Fix performance
  → README.md (Performance Considerations)
  → QUICK_REFERENCE.md (Performance Targets)
  → DEVELOPMENT.md (Optimization section)

Task: Report bug
  → System console output
  → Debug panel information
  → DEVELOPMENT.md (Debugging Techniques)


NEXT STEPS
==========

1. New User?
   → Start with INSTALLATION_GUIDE.md

2. Want to Use Now?
   → Follow installation
   → Reference QUICK_REFERENCE.md while using

3. Want to Learn More?
   → Read README.md thoroughly
   → Review DEVELOPMENT.md for technical details

4. Want to Extend?
   → Study DEVELOPMENT.md extensively
   → Review gesture_handler.py as example
   → Follow "Extending the Plugin" guidelines

5. Having Issues?
   → Check relevant troubleshooting section
   → Enable debug panel
   → Review system console output
"""
