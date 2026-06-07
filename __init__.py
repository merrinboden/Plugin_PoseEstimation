"""
Pose Estimation-based Blender Plugin
=====================================

A Blender plugin that uses MediaPipe for real-time pose estimation via webcam.
Enables gesture-based control of Blender interface:
- Left hand: Camera navigation and 3D viewport control
- Right hand: Tool and brush selection

Author: Development Team
Version: 1.0.0
Blender Version: 4.0+
"""

import sys
import site

site.addsitedir(site.getusersitepackages())

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty
from . import pose_estimator
from . import gesture_handler
from . import ui_panel

bl_info = {
    "name": "Pose Estimation Gesture Control",
    "blender": (4, 0, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "author": "Development Team",
    "description": "Control Blender with gesture recognition using MediaPipe pose estimation",
    "location": "View3D > Sidebar > Pose Estimation",
}


class PoseEstimationProperties(bpy.types.PropertyGroup):
    """
    Property group storing configuration for the pose estimation system.

    Attributes:
        is_active: Enable/disable pose estimation monitoring
        smoothing_factor: Parameter for filtering noisy joint positions (0.0-1.0)
        confidence_threshold: Minimum confidence level for joint detection
        webcam_index: Index of webcam device to use
    """

    is_active: BoolProperty(
        name="Active",
        description="Enable pose estimation",
        default=False
    )

    smoothing_factor: FloatProperty(
        name="Smoothing",
        description="Motion smoothing factor (higher = smoother)",
        default=0.7,
        min=0.0,
        max=1.0
    )

    confidence_threshold: FloatProperty(
        name="Confidence Threshold",
        description="Minimum confidence for pose detection",
        default=0.5,
        min=0.0,
        max=1.0
    )

    webcam_index: IntProperty(
        name="Webcam Index",
        description="Webcam device index (0=default)",
        default=0,
        min=0
    )

    debug_visual: BoolProperty(
        name="Show Debug Window",
        description="Show OpenCV debug window with annotated wrists",
        default=False
    )

    gesture_mode: EnumProperty(
        name="Gesture Mode",
        description="Select gesture recognition mode",
        items=[
            ("CAMERA", "Camera Control", "Use gestures for camera navigation"),
            ("BRUSH", "Brush Control", "Use gestures for brush control"),
        ],
        default="CAMERA"
    )


def register():
    """Register all plugin classes and properties."""
    bpy.utils.register_class(PoseEstimationProperties)
    bpy.utils.register_class(ui_panel.PoseEstimationPanel)
    bpy.utils.register_class(ui_panel.PoseEstimationDebugPanel)
    bpy.utils.register_class(ui_panel.StartPoseEstimationOperator)
    bpy.utils.register_class(ui_panel.StopPoseEstimationOperator)

    bpy.types.Scene.pose_est_props = bpy.props.PointerProperty(
        type=PoseEstimationProperties
    )


def unregister():
    """Unregister all plugin classes and properties."""
    bpy.utils.unregister_class(PoseEstimationProperties)
    bpy.utils.unregister_class(ui_panel.PoseEstimationPanel)
    bpy.utils.unregister_class(ui_panel.PoseEstimationDebugPanel)
    bpy.utils.unregister_class(ui_panel.StartPoseEstimationOperator)
    bpy.utils.unregister_class(ui_panel.StopPoseEstimationOperator)

    del bpy.types.Scene.pose_est_props

    pose_estimator.stop_estimation()


if __name__ == "__main__":
    register()
