"""
Blender helper script — paste into Blender's Python Console or run from Text Editor.

Usage:
- Run this script in Blender (Text Editor > Run Script) or paste into the Python Console.
- It initializes the estimator with the current scene properties and starts the background thread.
- To stop, call `stop_pose_estimation()` or use the add-on's Stop button.

Note: Blender must have the add-on registered (enable it in Preferences > Add-ons).
"""

import bpy
try:
    from Plugin_PoseEstimation import pose_estimator
except Exception as e:
    print('Error importing pose_estimator:', e)
    raise

# Ensure the add-on properties exist
if not hasattr(bpy.context.scene, 'pose_est_props'):
    print('Pose Estimation properties not found on scene. Make sure the add-on is enabled.')
else:
    props = bpy.context.scene.pose_est_props

    # Optional: adjust properties here
    props.webcam_index = getattr(props, 'webcam_index', 0)
    props.confidence_threshold = getattr(props, 'confidence_threshold', 0.3)
    props.debug_visual = True

    # Initialize and start
    pose_estimator.initialize_estimator(
        webcam_index=props.webcam_index,
        confidence_threshold=props.confidence_threshold,
        debug_visual=props.debug_visual,
    )
    pose_estimator.start_estimation()
    print('Pose estimation started (background). Use stop_pose_estimation() to stop.')


def stop_pose_estimation():
    """Stop the running estimator and cleanup windows."""
    pose_estimator.stop_estimation()
    print('Pose estimation stopped')
