from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
import xacro

def generate_launch_description():
    # Get package directories
    pkg_share = get_package_share_directory('my_rover_package')
    launch_share = get_package_share_directory('my_rover_launch')
    gazebo_pkg = get_package_share_directory('gazebo_ros')
    
    # Get URDF
    xacro_file = os.path.join(pkg_share, 'urdf', 'my_rover.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_desc = robot_description_config.toxml()
    
    # Get SLAM params
    slam_params_file = os.path.join(launch_share, 'config', 'mapper_params_online_async.yaml')
    
    # Get RViz config
    rviz_config_file = os.path.join(launch_share, 'rviz', 'rover_slam.rviz')
    
    # Gazebo launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_pkg, 'launch', 'gazebo.launch.py')
        )
    )
    
    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}],
    )
    
    # Spawn rover
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'my_rover', '-topic', 'robot_description', '-x', '0', '-y', '0', '-z', '0.1'],
        output='screen',
    )
    
    # SLAM Toolbox
    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params_file],
    )
    
    # RViz2
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
    )
    
    return LaunchDescription([
        gazebo_launch,
        robot_state_publisher,
        spawn_entity,
        slam_toolbox,
        rviz2,
    ])
