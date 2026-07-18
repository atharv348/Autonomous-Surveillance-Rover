import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    # Get package directories
    pkg_my_rover = get_package_share_directory('my_rover_package')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    
    # Process the URDF
    urdf_file = os.path.join(pkg_my_rover, 'urdf', 'my_rover.urdf.xacro')
    robot_description = xacro.process_file(urdf_file).toxml()

    # Gazebo launch (uses the correct ROS 2 method)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # Spawn the robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'my_rover',
            '-x', '0',
            '-y', '0', 
            '-z', '0.5'
        ],
        output='screen'
    )

    # Delay spawn to give Gazebo time to start
    delayed_spawn = TimerAction(
        period=5.0,
        actions=[spawn_entity]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        delayed_spawn
    ])
