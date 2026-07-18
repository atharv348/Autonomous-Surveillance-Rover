from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Front left wheel transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.25', '0.28', '0', '0', '0', '0', 'base_link', 'front_left_wheel']
        ),
        # Front right wheel transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.25', '-0.28', '0', '0', '0', '0', 'base_link', 'front_right_wheel']
        ),
        # Rear left wheel transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['-0.25', '0.28', '0', '0', '0', '0', 'base_link', 'rear_left_wheel']
        ),
        # Rear right wheel transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['-0.25', '-0.28', '0', '0', '0', '0', 'base_link', 'rear_right_wheel']
        )
    ])
