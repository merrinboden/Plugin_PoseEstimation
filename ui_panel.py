"""
UI Panel Module - Refactored for Service Client
================================================

Provides Blender interface for connecting to pose estimation service.

Includes:
- Service connection management (host, port)
- Start/stop buttons for service client
- Real-time connection status
- Gesture monitoring display
"""

import bpy


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
        """Draw panel layout with service connection UI."""
        layout = self.layout
        props = context.scene.pose_est_props

        # Title and status section
        row = layout.row()
        if props.is_active:
            row.label(text="Status: CONNECTED", icon='PLAY')
        else:
            row.label(text="Status: DISCONNECTED", icon='PAUSE')

        # Service connection settings
        box = layout.box()
        box.label(text="Service Connection", icon='NETWORK_DRIVE')
        col = box.column(align=True)
        col.prop(props, "service_host", text="Host")
        col.prop(props, "service_port", text="Port")

        # Connection status
        if props.is_active:
            box.label(text="Connected to service", icon='CHECKMARK')
        else:
            box.label(text="Not connected", icon='ERROR')

        # Start/Stop buttons
        row = layout.row(align=True)
        row.scale_y = 1.5

        if props.is_active:
            row.operator(
                "wm.stop_pose_estimation",
                text="Disconnect",
                icon='PAUSE'
            )
        else:
            row.operator(
                "wm.start_pose_estimation",
                text="Connect to Service",
                icon='PLAY'
            )

        # Separator
        layout.separator()

        # Gesture monitoring section
        box = layout.box()
        box.label(text="Hand Detection", icon='HAND')
        col = box.column(align=True)
        col.label(text=f"Left Hand Confidence: {props.left_hand_confidence:.2f}")
        col.label(text=f"Right Hand Confidence: {props.right_hand_confidence:.2f}")

        # Help section
        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 0.8
        col.label(text="How to Use:")
        col.label(text="1. Start pose service: python -m pose_service.server")
        col.label(text="2. Click 'Connect to Service' button")
        col.label(text="3. Move hands in front of webcam")
        col.label(text="4. Use gestures to control Blender")


class StartPoseEstimationOperator(bpy.types.Operator):
    """Connect to pose estimation service."""

    bl_idname = "wm.start_pose_estimation"
    bl_label = "Connect to Service"

    def execute(self, context):
        """Connect to service and start receiving pose updates."""
        try:
            props = context.scene.pose_est_props

            # Import WebSocket client
            from ..blender_client.websocket_client import PoseServiceClient

            # Create client
            client = PoseServiceClient(
                host=props.service_host,
                port=props.service_port
            )

            # Start connection
            client.start()

            # Store client in window manager for access in timer
            context.window_manager.pose_client = client

            # Register timer to process pose updates
            bpy.app.timers.register(process_pose_updates)

            props.is_active = True

            self.report({'INFO'}, f"Connecting to service at {props.service_host}:{props.service_port}")
            print(f"[Blender] Connecting to service at ws://{props.service_host}:{props.service_port}/ws/pose")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to connect: {str(e)}")
            print(f"[Blender] Error: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class StopPoseEstimationOperator(bpy.types.Operator):
    """Disconnect from pose estimation service."""

    bl_idname = "wm.stop_pose_estimation"
    bl_label = "Disconnect from Service"

    def execute(self, context):
        """Disconnect from service."""
        try:
            props = context.scene.pose_est_props

            # Stop client connection
            client = context.window_manager.pose_client
            if client:
                client.stop()
                print("[Blender] Disconnected from service")

            # Unregister timer
            try:
                bpy.app.timers.unregister(process_pose_updates)
            except:
                pass

            props.is_active = False

            self.report({'INFO'}, "Disconnected from service")
            print("[Blender] Disconnected")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error disconnecting: {str(e)}")
            print(f"[Blender] Error: {e}")
            return {'CANCELLED'}



def process_pose_updates():
    """Timer callback: process pose updates from service and execute gestures."""
    try:
        context = bpy.context
        client = context.window_manager.pose_client

        if not client or not client.connected:
            return 0.016  # Keep polling

        pose = client.get_latest_pose()
        if not pose:
            return 0.016  # No update this frame

        # Update confidence scores in properties for UI display
        props = context.scene.pose_est_props
        props.left_hand_confidence = pose.get('left_hand_confidence', 0.0)
        props.right_hand_confidence = pose.get('right_hand_confidence', 0.0)

        # Execute detected gestures
        for gesture in pose.get('gestures', []):
            data = pose.get('gesture_data', {}).get(gesture, {})

            if gesture == 'PAN_LEFT':
                pan_viewport(context, 'LEFT', data.get('amount', 10))
            elif gesture == 'PAN_RIGHT':
                pan_viewport(context, 'RIGHT', data.get('amount', 10))
            elif gesture == 'PAN_UP':
                pan_viewport(context, 'UP', data.get('amount', 10))
            elif gesture == 'PAN_DOWN':
                pan_viewport(context, 'DOWN', data.get('amount', 10))
            elif gesture == 'ADJUST_BRUSH':
                adjust_brush_size(context, data.get('size_delta', 0))
            elif gesture == 'ADJUST_STRENGTH':
                adjust_brush_strength(context, data.get('strength_delta', 0))
            elif gesture == 'SELECT_TOOL':
                cycle_tool(context, data.get('direction', 'NEXT'))

    except Exception as e:
        print(f"[Pose Update] Error: {e}")

    return 0.016  # Call again in ~16ms


def pan_viewport(context, direction, amount):
    """Pan the 3D viewport camera."""
    try:
        for area in context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for region in area.regions:
                if region.type != 'WINDOW':
                    continue

                rv3d = region.data
                if not rv3d:
                    continue

                scale = amount * 0.01  # Scale to viewport units

                if direction == 'LEFT':
                    rv3d.view_location.x -= scale
                elif direction == 'RIGHT':
                    rv3d.view_location.x += scale
                elif direction == 'UP':
                    rv3d.view_location.y += scale
                elif direction == 'DOWN':
                    rv3d.view_location.y -= scale

    except Exception as e:
        print(f"[Pan] Error: {e}")


def adjust_brush_size(context, delta):
    """Adjust brush size in sculpt mode."""
    try:
        if context.mode == 'SCULPT':
            brush = context.tool_settings.sculpt.brush
            if brush:
                new_size = max(1, min(500, brush.size + delta))
                brush.size = new_size
    except Exception as e:
        print(f"[Brush Size] Error: {e}")


def adjust_brush_strength(context, delta):
    """Adjust brush strength in sculpt mode."""
    try:
        if context.mode == 'SCULPT':
            brush = context.tool_settings.sculpt.brush
            if brush:
                new_strength = max(0.0, min(1.0, brush.strength + delta))
                brush.strength = new_strength
    except Exception as e:
        print(f"[Brush Strength] Error: {e}")


def cycle_tool(context, direction):
    """Cycle through sculpt tools."""
    try:
        if context.mode == 'SCULPT':
            print(f"[Tool] Cycling {direction}")
            # Tool cycling logic would go here
    except Exception as e:
        print(f"[Tool Cycle] Error: {e}")
