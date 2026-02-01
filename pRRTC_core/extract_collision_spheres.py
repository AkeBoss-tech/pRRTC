#!/usr/bin/env python3
"""
Extract collision geometry from a robot URDF and generate sphere approximations.
Useful for adding new robots to pRRTC.

This script:
1. Loads a robot URDF in PyBullet
2. Extracts collision shapes for each link
3. Generates sphere approximations suitable for pRRTC collision checking
4. Outputs the data in a format ready for a .cuh file

Usage:
    python extract_collision_spheres.py                    # Default: Panda
    python extract_collision_spheres.py --urdf path/to/robot.urdf
    python extract_collision_spheres.py --robot kuka
"""

import argparse
import json
import pybullet as p
import pybullet_data
import numpy as np


# Built-in robot URDFs
BUILTIN_ROBOTS = {
    "panda": "franka_panda/panda.urdf",
    "kuka": "kuka_iiwa/model.urdf",
}


def get_collision_shapes(robot_id):
    """Extract collision shape data for each link."""
    num_joints = p.getNumJoints(robot_id)
    collision_data = []
    
    # Base link (index -1)
    base_collision = p.getCollisionShapeData(robot_id, -1)
    if base_collision:
        collision_data.append({
            'link_index': -1,
            'link_name': 'base_link',
            'shapes': parse_collision_shapes(base_collision)
        })
    
    # All other links
    for i in range(num_joints):
        joint_info = p.getJointInfo(robot_id, i)
        link_name = joint_info[12].decode('utf-8')
        
        shapes = p.getCollisionShapeData(robot_id, i)
        if shapes:
            collision_data.append({
                'link_index': i,
                'link_name': link_name,
                'shapes': parse_collision_shapes(shapes)
            })
    
    return collision_data


def parse_collision_shapes(shapes):
    """Parse PyBullet collision shape data."""
    parsed = []
    for shape in shapes:
        shape_type = shape[2]
        dimensions = shape[3]
        local_pos = shape[5]
        local_orn = shape[6]
        
        type_names = {
            p.GEOM_SPHERE: 'sphere',
            p.GEOM_BOX: 'box',
            p.GEOM_CYLINDER: 'cylinder',
            p.GEOM_MESH: 'mesh',
            p.GEOM_CAPSULE: 'capsule',
        }
        
        parsed.append({
            'type': type_names.get(shape_type, 'unknown'),
            'type_id': shape_type,
            'dimensions': list(dimensions),
            'local_position': list(local_pos),
            'local_orientation': list(local_orn),
        })
    return parsed


def approximate_with_spheres(collision_data, spheres_per_link=3):
    """
    Generate sphere approximations for collision geometry.
    This is a simplified approximation - for accurate results,
    you'll want to manually tune sphere placements.
    """
    spheres = []
    
    for link_data in collision_data:
        link_idx = link_data['link_index']
        link_name = link_data['link_name']
        
        for shape in link_data['shapes']:
            shape_type = shape['type']
            dims = shape['dimensions']
            pos = shape['local_position']
            
            if shape_type == 'sphere':
                # Direct sphere - just use it
                spheres.append({
                    'x': pos[0],
                    'y': pos[1],
                    'z': pos[2],
                    'radius': dims[0],
                    'link_index': link_idx,
                    'link_name': link_name
                })
                
            elif shape_type == 'box':
                # Approximate box with spheres at center and corners
                half_extents = [d/2 for d in dims[:3]] if len(dims) >= 3 else [0.05, 0.05, 0.05]
                max_dim = max(half_extents)
                
                # Center sphere
                spheres.append({
                    'x': pos[0],
                    'y': pos[1],
                    'z': pos[2],
                    'radius': max_dim * 0.8,
                    'link_index': link_idx,
                    'link_name': link_name
                })
                
            elif shape_type == 'cylinder':
                # Approximate cylinder with spheres along axis
                radius = dims[1] if len(dims) > 1 else 0.05
                length = dims[0] if dims else 0.1
                
                for z_offset in [-length/3, 0, length/3]:
                    spheres.append({
                        'x': pos[0],
                        'y': pos[1],
                        'z': pos[2] + z_offset,
                        'radius': radius,
                        'link_index': link_idx,
                        'link_name': link_name
                    })
                    
            elif shape_type == 'capsule':
                radius = dims[1] if len(dims) > 1 else 0.05
                length = dims[0] if dims else 0.1
                
                # Spheres at capsule ends and middle
                for z_offset in [-length/2, 0, length/2]:
                    spheres.append({
                        'x': pos[0],
                        'y': pos[1],
                        'z': pos[2] + z_offset,
                        'radius': radius,
                        'link_index': link_idx,
                        'link_name': link_name
                    })
                    
            elif shape_type == 'mesh':
                # For meshes, create a bounding sphere (very approximate)
                spheres.append({
                    'x': pos[0],
                    'y': pos[1],
                    'z': pos[2],
                    'radius': 0.05,  # Default - should be manually tuned
                    'link_index': link_idx,
                    'link_name': link_name,
                    'note': 'mesh - radius needs manual tuning'
                })
    
    return spheres


def generate_cuh_output(spheres, robot_name):
    """Generate C++ code snippet for pRRTC .cuh file."""
    
    output = []
    output.append(f"// Auto-generated sphere data for {robot_name}")
    output.append(f"// Total spheres: {len(spheres)}")
    output.append("")
    output.append(f"#define {robot_name.upper()}_SPHERE_COUNT {len(spheres)}")
    output.append("")
    output.append(f"__device__ __constant__ float4 {robot_name}_spheres_array[{len(spheres)}] = {{")
    
    for i, s in enumerate(spheres):
        comma = "," if i < len(spheres) - 1 else ""
        comment = f"  // link {s['link_index']}: {s['link_name']}"
        if 'note' in s:
            comment += f" ({s['note']})"
        output.append(f"    {{ {s['x']:.4f}f, {s['y']:.4f}f, {s['z']:.4f}f, {s['radius']:.4f}f }}{comma}{comment}")
    
    output.append("};")
    output.append("")
    
    # Generate sphere_to_joint mapping
    output.append(f"__device__ __constant__ int {robot_name}_sphere_to_joint[] = {{")
    joint_indices = [str(max(0, s['link_index'])) for s in spheres]
    # Format in rows of 10
    for i in range(0, len(joint_indices), 10):
        row = ", ".join(joint_indices[i:i+10])
        comma = "," if i + 10 < len(joint_indices) else ""
        output.append(f"    {row}{comma}")
    output.append("};")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Extract collision spheres from URDF")
    parser.add_argument("--urdf", type=str, help="Path to URDF file")
    parser.add_argument("--robot", type=str, choices=list(BUILTIN_ROBOTS.keys()),
                        help="Use built-in robot URDF")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--json", action="store_true", help="Also output JSON")
    args = parser.parse_args()
    
    # Connect to PyBullet (no GUI needed)
    p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    
    # Determine URDF to load
    if args.urdf:
        urdf_path = args.urdf
        robot_name = urdf_path.split('/')[-1].replace('.urdf', '')
    elif args.robot:
        urdf_path = BUILTIN_ROBOTS[args.robot]
        robot_name = args.robot
    else:
        urdf_path = BUILTIN_ROBOTS["panda"]
        robot_name = "panda"
    
    print(f"Loading URDF: {urdf_path}")
    
    # Load robot
    robot_id = p.loadURDF(urdf_path, useFixedBase=True)
    
    # Extract collision data
    print("Extracting collision shapes...")
    collision_data = get_collision_shapes(robot_id)
    
    print(f"Found {len(collision_data)} links with collision geometry")
    for link in collision_data:
        print(f"  Link {link['link_index']} ({link['link_name']}): {len(link['shapes'])} shapes")
    
    # Generate sphere approximations
    print("\nGenerating sphere approximations...")
    spheres = approximate_with_spheres(collision_data)
    print(f"Generated {len(spheres)} spheres")
    
    # Generate output
    cuh_output = generate_cuh_output(spheres, robot_name)
    
    print("\n" + "=" * 60)
    print("GENERATED CODE FOR .cuh FILE")
    print("=" * 60)
    print(cuh_output)
    print("=" * 60)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(cuh_output)
        print(f"\nSaved to: {args.output}")
    
    # Save JSON if requested
    if args.json:
        json_path = args.output.replace('.cuh', '.json') if args.output else f"{robot_name}_spheres.json"
        with open(json_path, 'w') as f:
            json.dump({
                'robot_name': robot_name,
                'collision_data': collision_data,
                'spheres': spheres
            }, f, indent=2)
        print(f"JSON saved to: {json_path}")
    
    p.disconnect()


if __name__ == "__main__":
    main()
