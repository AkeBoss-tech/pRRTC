#!/usr/bin/env python3
"""
Simple PyBullet visualization for pRRTC output paths.
Run this on your Mac after downloading results from Amarel.

Usage: python visualize_path.py path_output.txt

Requires: pip install pybullet numpy
"""

import sys
import time
import numpy as np

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    print("Please install pybullet: pip install pybullet")
    sys.exit(1)


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


def visualize_panda(path: list, speed: float = 0.05):
    """Animate Panda robot following the path."""
    # Setup PyBullet
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
    
    print(f"Animating {len(path)} waypoints...")
    
    # Animate path
    for i, config in enumerate(path):
        for j, joint_idx in enumerate(movable_joints):
            if j < len(config):
                p.resetJointState(robot_id, joint_idx, config[j])
        p.stepSimulation()
        time.sleep(speed)
        
        if i % 10 == 0:
            print(f"  Waypoint {i}/{len(path)}")
    
    print("Animation complete. Press Ctrl+C to exit.")
    
    # Keep window open
    try:
        while True:
            p.stepSimulation()
            time.sleep(0.01)
    except KeyboardInterrupt:
        p.disconnect()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nNo path file provided. Running demo with random path...")
        # Demo mode: generate random path
        path = []
        for _ in range(20):
            config = np.random.uniform(-2, 2, 7).tolist()
            path.append(config)
    else:
        path = load_path_from_console_output(sys.argv[1])
        if not path:
            print(f"No valid configurations found in {sys.argv[1]}")
            sys.exit(1)
        print(f"Loaded {len(path)} waypoints from {sys.argv[1]}")
    
    visualize_panda(path)


if __name__ == "__main__":
    main()
