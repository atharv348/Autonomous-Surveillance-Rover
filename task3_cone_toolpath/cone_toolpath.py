#!/usr/bin/env python3
"""
Task 3 — 6-Axis Robot Toolpath Generation for a Cone Surface

Author: Atharv Joshi
Generates a continuous helical toolpath on a cone surface,
computes 6-DOF joint angles (UR5 arm model), and exports to CSV.
"""

import csv
import math

try:
    import ikpy.chain
    IKPY_AVAILABLE = True
except ImportError:
    IKPY_AVAILABLE = False

def create_ur5_chain():
    """Build a kinematic representation of a standard UR5 6-DOF robot arm."""
    if not IKPY_AVAILABLE:
        return None
    
    chain = ikpy.chain.Chain(name='ur5', links=[
        ikpy.link.OriginLink(),
        ikpy.link.URDFLink(
            name="shoulder_pan_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, 0, 0.089159],
            orientation=[0, 0, 0],
            rotation=[0, 0, 1]
        ),
        ikpy.link.URDFLink(
            name="shoulder_lift_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, 0.13585, 0],
            orientation=[0, math.pi/2, 0],
            rotation=[0, 1, 0]
        ),
        ikpy.link.URDFLink(
            name="elbow_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, -0.1197, 0.425],
            orientation=[0, 0, 0],
            rotation=[0, 1, 0]
        ),
        ikpy.link.URDFLink(
            name="wrist_1_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, 0, 0.39225],
            orientation=[0, math.pi/2, 0],
            rotation=[0, 1, 0]
        ),
        ikpy.link.URDFLink(
            name="wrist_2_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, 0.093, 0],
            orientation=[0, 0, 0],
            rotation=[0, 0, 1]
        ),
        ikpy.link.URDFLink(
            name="wrist_3_joint",
            bounds=(-math.pi, math.pi),
            translation=[0, 0, 0.09465],
            orientation=[0, 0, 0],
            rotation=[0, 1, 0]
        )
    ])
    return chain

def analytical_ik(x, y, z):
    """
    Analytical IK solver for a 6-DOF arm.
    Computes smooth, continuous joint angles tracking target Cartesian trajectory.
    """
    l1, l2 = 0.425, 0.39225
    
    j1 = math.atan2(y, x)
    r = math.sqrt(x**2 + y**2) - 0.1
    z_adj = z - 0.089159
    
    d_sq = r**2 + z_adj**2
    
    cos_j3 = (d_sq - l1**2 - l2**2) / (2 * l1 * l2)
    cos_j3 = max(-1.0, min(1.0, cos_j3))
    j3 = math.acos(cos_j3)
    
    alpha = math.atan2(z_adj, r)
    beta = math.atan2(l2 * math.sin(j3), l1 + l2 * math.cos(j3))
    j2 = alpha - beta
    
    j4 = -j2 - j3
    j5 = 0.0
    j6 = 0.0
    
    return [j1, j2, j3, j4, j5, j6]

def generate_cone_toolpath(num_points=300, num_turns=5, base_radius=0.3, height=0.4, center_x=0.5, center_y=0.0, base_z=0.2):
    """Generate 300 points spiraling up the cone surface."""
    points = []
    times = []
    
    for i in range(num_points):
        t = i * 0.1
        f = i / (num_points - 1)
        
        r = base_radius * (1.0 - f)
        z = base_z + height * f
        theta = f * num_turns * 2.0 * math.pi
        
        x = center_x + r * math.cos(theta)
        y = center_y + r * math.sin(theta)
        
        points.append((x, y, z))
        times.append(t)
        
    return times, points

def solve_trajectory(times, points):
    chain = create_ur5_chain()
    trajectory = []
    prev_joints = [0.0] * 8 if chain else [0.0] * 6
    
    for (x, y, z) in points:
        if chain:
            target_vector = [x, y, z]
            joints = chain.inverse_kinematics(target_vector, initial_position=prev_joints)
            prev_joints = joints
            active_joints = list(joints[1:7])
        else:
            active_joints = analytical_ik(x, y, z)
            
        trajectory.append(active_joints)
        
    return trajectory

def main():
    print("Generating Cone Toolpath for 6-Axis Robot...")
    num_points = 300
    times, points = generate_cone_toolpath(num_points=num_points)
    
    with open('cone_geometry.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'X', 'Y', 'Z'])
        for t, (x, y, z) in zip(times, points):
            writer.writerow([f"{t:.1f}", f"{x:.4f}", f"{y:.4f}", f"{z:.4f}"])
    print("Exported cone_geometry.csv")
    
    trajectory = solve_trajectory(times, points)
    
    with open('cone_toolpath.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Joint1', 'Joint2', 'Joint3', 'Joint4', 'Joint5', 'Joint6'])
        for t, joints in zip(times, trajectory):
            formatted_joints = [f"{j:.6f}" for j in joints]
            writer.writerow([f"{t:.1f}"] + formatted_joints)
    print("Exported cone_toolpath.csv")
    print("Task 3 toolpath generation complete!")

if __name__ == '__main__':
    main()
