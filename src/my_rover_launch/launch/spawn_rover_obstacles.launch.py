#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Get package directories
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    my_rover_dir = get_package_share_directory('my_rover')
    
    # Path to URDF
    urdf_file = os.path.join(my_rover_dir, 'urdf', 'rover.urdf')
    
    # Path to world file
    world_file = os.path.join(my_rover_dir, 'worlds', 'obstacles.world')
    
    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_file, 'verbose': 'true'}.items()
    )
    
    # Spawn rover
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'my_rover', '-file', urdf_file, '-x', '0', '-y', '0', '-z', '0.5'],
        output='screen'
    )
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        arguments=[urdf_file]
    )
    
    # Sensor simulator
    sensor_simulator = Node(
        package='my_rover',
        executable='sensor_simulator.py',
        output='screen'
    )
    
    # Obstacle avoidance
    obstacle_avoidance = Node(
        package='my_rover',
        executable='obstacle_avoidance.py',
        output='screen'
    )
    
    return LaunchDescription([
        gazebo,
        spawn_entity,
        robot_state_publisher,
        sensor_simulator,
        obstacle_avoidance
    ])
