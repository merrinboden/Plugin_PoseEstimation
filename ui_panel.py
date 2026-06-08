"""
UI Panel Module
===============

Provides Blender interface components for pose estimation control.

Includes:
- Main control panel in 3D viewport sidebar
- Start/stop buttons for pose estimation
- Real-time status display (FPS, detection quality)
- Configuration adjustments (confidence threshold, smoothing)
- Error display and feedback messages
"""

import bpy
from . import pose_estimator, gesture_handler


class PoseEstimationPanel(bpy.types.Panel):
    """
    Main UI panel for pose estimation control in 3D viewport.

    Location: View3D > Sidebar > Pose Estimation tab
    Provides user access to all plugin features and settings.
    """

    bl_label = "Pose Estimation"
    bl_idname = "VIEW3D_PT_pose_estimation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pose Estimation'

    def draw(self, context):
        """
        Draw panel layout with all UI elements.

        Args:
            context: Blender context containing scene properties
        """
        layout = self.layout
        props = context.scene.pose_est_props

        # Title and status section
        row = layout.row()
        if props.is_active:
            row.label(text="Status: ACTIVE", icon='PLAY')
        else:
            row.label(text="Status: INACTIVE", icon='PAUSE')

        # Start/Stop buttons
        row = layout.row(align=True)
        row.scale_y = 1.5

        if props.is_active:
            row.operator(
                "wm.stop_pose_estimation",
                text="Stop Estimation",
                icon='PAUSE'
            )
        else:
            row.operator(
                "wm.start_pose_estimation",
                text="Start Estimation",
                icon='PLAY'
            )

        # Separator
        layout.separator()

        # Configuration section
        box = layout.box()
        box.label(text="Configuration", icon='PREFERENCES')

        col = box.column(align=True)
        col.prop(props, "webcam_index", text="Webcam")
        col.prop(props, "confidence_threshold", text="Confidence", slider=True)
        col.prop(props, "smoothing_factor", text="Smoothing", slider=True)
        col.prop(props, "debug_visual", text="Show Debug Window")

        # Separator
        layout.separator()

        # Gesture mode selection
        box = layout.box()
        box.label(text="Control Mode", icon='HAND')
        box.prop(props, "gesture_mode", expand=True)

        # Info section
        layout.separator()
        box = layout.box()
        box.label(text="Information", icon='INFO')

        col = box.column(align=True)
        col.label(text="Left Hand: Camera Control")
        col.label(text="Right Hand: Tool Control")

        # Help section
        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Move left hand to pan camera")
        col.label(text="• Move right hand to paint/sculpt")
        col.label(text="• Keep hands in view for best results")


class StartPoseEstimationOperator(bpy.types.Operator):
    """
    Operator to start pose estimation.

    Initializes pose estimator and gesture manager, begins webcam capture
    and MediaPipe processing. Updates UI to show active state.

    Properties:
        bl_idname: "wm.start_pose_estimation"
        bl_label: Display name in UI
    """

    bl_idname = "wm.start_pose_estimation"
    bl_label = "Start Pose Estimation"

    def execute(self, context):
        """
        Execute pose estimation startup.

        Performs initialization and reports success/failure to user.

        Args:
            context: Blender context

        Returns:
            {'FINISHED'} on success, {'CANCELLED'} on error
        """
        try:
            props = context.scene.pose_est_props

            # Load gesture configuration
            import pathlib
            config_path = pathlib.Path(__file__).parent / "gestures_config.yaml"
            gesture_config = gesture_handler.GestureConfig(str(config_path))

            # Initialize pose estimator with current settings
            pose_estimator.initialize_estimator(
                webcam_index=props.webcam_index,
                confidence_threshold=props.confidence_threshold,
                debug_visual=props.debug_visual
            )

            # Initialize gesture recognition with config
            gesture_handler.initialize_gesture_manager(gesture_config)

            # Start estimation in background thread
            pose_estimator.start_estimation()
            pose_estimator.start_gesture_processing()

            props.is_active = True

            self.report({'INFO'}, "Pose estimation started")
            print("[Pose Estimation] Started successfully")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to start: {str(e)}")
            print(f"[Pose Estimation] Error: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class StopPoseEstimationOperator(bpy.types.Operator):
    """
    Operator to stop pose estimation.

    Halts webcam capture, stops MediaPipe processing, and resets gesture state.
    Updates UI to show inactive state and releases GPU/CPU resources.

    Properties:
        bl_idname: "wm.stop_pose_estimation"
        bl_label: Display name in UI
    """

    bl_idname = "wm.stop_pose_estimation"
    bl_label = "Stop Pose Estimation"

    def execute(self, context):
        """
        Execute pose estimation shutdown.

        Stops background processing and cleanup resources.

        Args:
            context: Blender context

        Returns:
            {'FINISHED'} on success
        """
        try:
            props = context.scene.pose_est_props

            # Stop pose estimation
            pose_estimator.stop_estimation()

            # Reset gesture state
            gesture_handler.reset_gestures()

            props.is_active = False

            self.report({'INFO'}, "Pose estimation stopped")
            print("[Pose Estimation] Stopped")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error stopping: {str(e)}")
            print(f"[Pose Estimation] Stop error: {e}")
            return {'CANCELLED'}


class PoseEstimationDebugPanel(bpy.types.Panel):
    """
    Debug panel for monitoring pose estimation performance.

    Shows real-time statistics:
    - Current FPS of pose detection
    - Hand confidence scores
    - Frame count
    - Detection validity status

    Only visible when "Debug" option is enabled.
    """

    bl_label = "Debug Info"
    bl_idname = "VIEW3D_PT_pose_estimation_debug"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pose Estimation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """
        Draw debug information panel.

        Args:
            context: Blender context
        """
        layout = self.layout
        props = context.scene.pose_est_props

        if not props.is_active:
            layout.label(text="Estimation not running", icon='INFO')
            return

        # Get current pose
        pose = pose_estimator.get_pose()

        box = layout.box()
        box.label(text="Detection Status", icon='CAMERA_DATA')

        col = box.column(align=True)
        col.label(text=f"Frame: {pose.timestamp}")
        col.label(text=f"Valid: {'Yes' if pose.is_valid else 'No'}")

        # Hand confidence display
        box = layout.box()
        box.label(text="Hand Confidence", icon='HAND')

        col = box.column(align=True)
        col.label(text=f"Left Hand: {pose.left_hand_confidence:.2f}")
        col.label(text=f"Right Hand: {pose.right_hand_confidence:.2f}")

        # Hand positions
        box = layout.box()
        box.label(text="Hand Positions", icon='EMPTY_DATA')

        col = box.column(align=True)
        col.label(text=f"Left: ({pose.left_hand_pos[0]:.1f}, {pose.left_hand_pos[1]:.1f})")
        col.label(text=f"Right: ({pose.right_hand_pos[0]:.1f}, {pose.right_hand_pos[1]:.1f})")
