#!/usr/bin/env python3
"""
Interactive PyBullet simulation for robot arms.
Supports Panda, Fetch, and other robots available in pybullet_data.

Usage:
    python simulate_robot.py              # Default: Panda
    python simulate_robot.py --robot panda
    python simulate_robot.py --robot kuka
    python simulate_robot.py --robot fetch
"""

import argparse
import time
import pybullet as p
import pybullet_data


# Robot configurations
ROBOTS = {
    "panda": {
        "urdf": "franka_panda/panda.urdf",
        "base_position": [0, 0, 0],
        "base_orientation": [0, 0, 0, 1],
    },
    "kuka": {
        "urdf": "kuka_iiwa/model.urdf",
        "base_position": [0, 0, 0],
        "base_orientation": [0, 0, 0, 1],
    },
    "fetch": {
        # Fetch is not in pybullet_data by default, using Panda as fallback
        "urdf": "franka_panda/panda.urdf",
        "base_position": [0, 0, 0],
        "base_orientation": [0, 0, 0, 1],
        "note": "Fetch URDF not in pybullet_data, using Panda as demo"
    },
}


def get_movable_joints(robot_id):
    """Get list of movable (non-fixed) joints."""
    movable_joints = []
    for i in range(p.getNumJoints(robot_id)):
        info = p.getJointInfo(robot_id, i)
        joint_type = info[2]
        if joint_type != p.JOINT_FIXED:
            joint_name = info[1].decode('utf-8')
            lower_limit = info[8]
            upper_limit = info[9]
            movable_joints.append({
                'index': i,
                'name': joint_name,
                'type': joint_type,
                'lower': lower_limit,
                'upper': upper_limit
            })
    return movable_joints


def print_robot_info(robot_id):
    """Print detailed information about the robot."""
    print("\n" + "=" * 50)
    print("ROBOT INFORMATION")
    print("=" * 50)
    
    num_joints = p.getNumJoints(robot_id)
    print(f"Total joints: {num_joints}")
    
    movable = get_movable_joints(robot_id)
    print(f"Movable joints: {len(movable)}")
    
    print("\nJoint Details:")
    print("-" * 50)
    for j in movable:
        print(f"  [{j['index']:2d}] {j['name']:20s} | limits: [{j['lower']:.3f}, {j['upper']:.3f}]")
    print("=" * 50 + "\n")


def create_joint_sliders(robot_id, movable_joints):
    """Create GUI sliders for each movable joint."""
    sliders = []
    for joint in movable_joints:
        # Clamp limits for slider (some URDFs have infinite limits)
        lower = max(joint['lower'], -3.14159)
        upper = min(joint['upper'], 3.14159)
        
        slider_id = p.addUserDebugParameter(
            paramName=joint['name'],
            rangeMin=lower,
            rangeMax=upper,
            startValue=0
        )
        sliders.append((joint['index'], slider_id))
    return sliders


def add_coordinate_axes():
    """Add XYZ coordinate axes at origin for reference."""
    length = 0.3
    p.addUserDebugLine([0, 0, 0], [length, 0, 0], [1, 0, 0], lineWidth=2)  # X - Red
    p.addUserDebugLine([0, 0, 0], [0, length, 0], [0, 1, 0], lineWidth=2)  # Y - Green
    p.addUserDebugLine([0, 0, 0], [0, 0, length], [0, 0, 1], lineWidth=2)  # Z - Blue


def main():
    parser = argparse.ArgumentParser(description="Interactive robot arm simulation")
    parser.add_argument("--robot", type=str, default="panda",
                        choices=list(ROBOTS.keys()),
                        help="Robot to simulate")
    parser.add_argument("--no-gravity", action="store_true",
                        help="Disable gravity")
    args = parser.parse_args()
    
    # Connect to PyBullet with GUI
    physics_client = p.connect(p.GUI)
    
    # Configure visualization - disable built-in GUI panels for cleaner view
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
    p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)
    p.configureDebugVisualizer(p.COV_ENABLE_MOUSE_PICKING, 1)
    
    # Set camera to better view the robot
    # (distance, yaw, pitch, target position)
    p.resetDebugVisualizerCamera(
        cameraDistance=1.5,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0.5]
    )
    
    # Set up paths and physics
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    if not args.no_gravity:
        p.setGravity(0, 0, -9.81)
    
    # Load ground plane
    plane_id = p.loadURDF("plane.urdf")
    
    # Load robot
    robot_config = ROBOTS[args.robot]
    if "note" in robot_config:
        print(f"Note: {robot_config['note']}")
    
    robot_id = p.loadURDF(
        robot_config["urdf"],
        basePosition=robot_config["base_position"],
        baseOrientation=robot_config["base_orientation"],
        useFixedBase=True
    )
    
    # Print robot info
    print_robot_info(robot_id)
    
    # Get movable joints and create sliders
    movable_joints = get_movable_joints(robot_id)
    sliders = create_joint_sliders(robot_id, movable_joints)
    
    # Add coordinate reference
    add_coordinate_axes()
    
    # Add end-effector position display
    ee_text_id = None
    ee_link = len(movable_joints) - 1  # Usually the last link
    
    # Use real-time simulation for smoother performance
    p.setRealTimeSimulation(1)
    
    print("Simulation running. Use the sliders to control joints.")
    print("Camera controls: Scroll to zoom, click+drag to rotate, Ctrl+drag to pan.")
    print("Close the window or press Ctrl+C to exit.\n")
    
    frame_count = 0
    
    try:
        while True:
            # Check if PyBullet is still connected
            if not p.isConnected():
                print("GUI window closed.")
                break
            
            try:
                # Read slider values and apply to joints
                for joint_idx, slider_id in sliders:
                    target_pos = p.readUserDebugParameter(slider_id)
                    p.setJointMotorControl2(
                        robot_id,
                        joint_idx,
                        p.POSITION_CONTROL,
                        targetPosition=target_pos,
                        force=500
                    )
                
                # Only update EE text every 10 frames to reduce overhead
                frame_count += 1
                if frame_count % 10 == 0:
                    # Get and display end-effector position
                    ee_state = p.getLinkState(robot_id, ee_link)
                    ee_pos = ee_state[0]
                    
                    # Update EE position text
                    if ee_text_id is not None:
                        p.removeUserDebugItem(ee_text_id)
                    ee_text_id = p.addUserDebugText(
                        f"EE: ({ee_pos[0]:.3f}, {ee_pos[1]:.3f}, {ee_pos[2]:.3f})",
                        textPosition=[0.5, 0, 0.8],
                        textColorRGB=[0, 0, 0],
                        textSize=1.2
                    )
                
                # Sleep longer to reduce CPU usage (real-time sim handles physics)
                time.sleep(1/60)  # ~60 FPS update rate
                
            except p.error as e:
                # This catches "Failed to read parameter" when GUI is closed
                print(f"GUI closed or error: {e}")
                break
            
    except KeyboardInterrupt:
        print("\nSimulation ended by user.")
    finally:
        if p.isConnected():
            p.disconnect()
        print("Disconnected from PyBullet.")


if __name__ == "__main__":
    main()
