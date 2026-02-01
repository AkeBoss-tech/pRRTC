#!/usr/bin/env python3
"""
Simple PyBullet visualization for pRRTC output paths.
Run this on your Mac after downloading results from Amarel.

Usage: 
    python visualize_path.py path_output.txt              # Interactive visualization
    python visualize_path.py path_output.txt --video      # Record video to output.mp4
    python visualize_path.py path_output.txt --video output.mp4  # Custom video filename

Requires: pip install pybullet numpy imageio
"""

import sys
import time
import numpy as np
import os

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    print("Please install pybullet: pip install pybullet")
    sys.exit(1)

try:
    import imageio
except ImportError:
    imageio = None


def load_path_from_console_output(filepath: str) -> list:
    """Parse joint configurations from pRRTC console output."""
    path = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('problem', 'idx', 'kernel', 'cost', 'failed')):
                continue
            try:
                values = [float(x) for x in line.split()]
                if len(values) in (7, 8, 14):  # Panda=7, Fetch=8, Baxter=14
                    path.append(values)
            except ValueError:
                continue
    return path


def visualize_panda(path: list, speed: float = 0.05, record_video: bool = False, video_filename: str = "output.mp4"):
    """Animate Panda robot following the path."""
    # Setup PyBullet - use GUI mode for both (needed for rendering)
    if record_video:
        if imageio is None:
            print("Error: imageio is required for video recording. Install with: pip install imageio")
            sys.exit(1)
        # Use GUI mode but we'll capture frames
        physics_client = p.connect(p.GUI)
        # Optionally make window smaller or offscreen
        p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)  # Disable GUI controls
    else:
        physics_client = p.connect(p.GUI)
    
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    
    # Load ground plane and robot
    p.loadURDF("plane.urdf")
    robot_id = p.loadURDF("franka_panda/panda.urdf", [0, 0, 0], useFixedBase=True)
    
    # Get movable joint indices (first 7 joints)
    num_joints = p.getNumJoints(robot_id)
    movable_joints = []
    for i in range(num_joints):
        joint_info = p.getJointInfo(robot_id, i)
        if joint_info[2] != p.JOINT_FIXED:
            movable_joints.append(i)
    movable_joints = movable_joints[:7]  # First 7 for Panda arm
    
    # Setup camera for video recording
    if record_video:
        # Set camera position to view the robot nicely
        camera_distance = 1.5
        camera_yaw = 50
        camera_pitch = -35
        camera_target = [0, 0, 0.5]
        width, height = 1280, 720
        frames = []
        print(f"Recording video to {video_filename}...")
    
    print(f"Animating {len(path)} waypoints...")
    
    # Animate path
    for i, config in enumerate(path):
        for j, joint_idx in enumerate(movable_joints):
            if j < len(config):
                p.resetJointState(robot_id, joint_idx, config[j])
        p.stepSimulation()
        
        # Capture frame for video
        if record_video:
            view_matrix = p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=camera_target,
                distance=camera_distance,
                yaw=camera_yaw,
                pitch=camera_pitch,
                roll=0,
                upAxisIndex=2
            )
            projection_matrix = p.computeProjectionMatrixFOV(
                fov=60,
                aspect=width/height,
                nearVal=0.1,
                farVal=100.0
            )
            _, _, rgb, _, _ = p.getCameraImage(
                width=width,
                height=height,
                viewMatrix=view_matrix,
                projectionMatrix=projection_matrix,
                renderer=p.ER_BULLET_HARDWARE_OPENGL
            )
            frames.append(rgb)
        else:
            time.sleep(speed)
        
        if i % 10 == 0:
            print(f"  Waypoint {i}/{len(path)}")
    
    if record_video:
        print(f"Saving {len(frames)} frames to {video_filename}...")
        # Convert frames to uint8 and save as video
        video_frames = [frame.astype(np.uint8) for frame in frames]
        imageio.mimsave(video_filename, video_frames, fps=1.0/speed if speed > 0 else 10)
        print(f"Video saved to {video_filename}")
        p.disconnect()
    else:
        print("Animation complete. Press Ctrl+C to exit.")
        
        # Keep window open
        try:
            while True:
                p.stepSimulation()
                time.sleep(0.01)
        except KeyboardInterrupt:
            p.disconnect()


def main():
    record_video = False
    video_filename = "output.mp4"
    
    # Parse command line arguments
    args = sys.argv[1:]
    if len(args) == 0:
        print(__doc__)
        print("\nNo path file provided. Running demo with random path...")
        # Demo mode: generate random path
        path = []
        for _ in range(20):
            config = np.random.uniform(-2, 2, 7).tolist()
            path.append(config)
    else:
        path_file = args[0]
        if "--video" in args:
            record_video = True
            # Check if custom video filename is provided
            video_idx = args.index("--video")
            if video_idx + 1 < len(args) and not args[video_idx + 1].startswith("--"):
                video_filename = args[video_idx + 1]
        
        path = load_path_from_console_output(path_file)
        if not path:
            print(f"No valid configurations found in {path_file}")
            sys.exit(1)
        print(f"Loaded {len(path)} waypoints from {path_file}")
    
    visualize_panda(path, record_video=record_video, video_filename=video_filename)


if __name__ == "__main__":
    main()
