"""
Pose Estimation Service Client - Blender Plugin
================================================

A Blender plugin that connects to a standalone pose estimation service.
Enables gesture-based control of Blender interface via WebSocket.

Author: Development Team
Version: 2.0.0 (Service Client)
Blender Version: 4.0+
"""

import sys
import site

site.addsitedir(site.getusersitepackages())

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from . import ui_panel

bl_info = {
    "name": "Pose Estimation Gesture Control (Service Client)",
    "blender": (4, 0, 0),
    "category": "3D View",
    "version": (2, 0, 0),
    "author": "Development Team",
    "description": "Control Blender with gesture recognition via pose estimation service",
    "location": "View3D > Sidebar > Pose Estimation",
}


class PoseEstimationProperties(bpy.types.PropertyGroup):
    """Service connection and status properties."""

    is_active: BoolProperty(
        name="Active",
        description="Connected to service",
        default=False
    )

    service_host: StringProperty(
        name="Service Host",
        description="Pose service hostname or IP",
        default="127.0.0.1"
    )

    service_port: IntProperty(
        name="Service Port",
        description="Pose service port",
        default=8000,
        min=1024,
        max=65535
    )

    left_hand_confidence: FloatProperty(
        name="Left Hand Confidence",
        default=0.0,
        min=0.0,
        max=1.0
    )

    right_hand_confidence: FloatProperty(
        name="Right Hand Confidence",
        default=0.0,
        min=0.0,
        max=1.0
    )


def register():
    """Register plugin classes and properties."""
    bpy.utils.register_class(PoseEstimationProperties)
    bpy.utils.register_class(ui_panel.PoseEstimationPanel)
    bpy.utils.register_class(ui_panel.StartPoseEstimationOperator)
    bpy.utils.register_class(ui_panel.StopPoseEstimationOperator)

    bpy.types.Scene.pose_est_props = bpy.props.PointerProperty(
        type=PoseEstimationProperties
    )

    print("[Plugin] Pose Estimation Service Client registered")


def unregister():
    """Unregister plugin classes and properties."""
    bpy.utils.unregister_class(PoseEstimationProperties)
    bpy.utils.unregister_class(ui_panel.PoseEstimationPanel)
    bpy.utils.unregister_class(ui_panel.StartPoseEstimationOperator)
    bpy.utils.unregister_class(ui_panel.StopPoseEstimationOperator)

    del bpy.types.Scene.pose_est_props

    print("[Plugin] Pose Estimation Service Client unregistered")


if __name__ == "__main__":
    register()
