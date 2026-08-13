import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory('my_robot_description')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'my_robot.urdf.xacro')

    # xacro → URDF
    robot_description_content = Command(['xacro ', xacro_file])
    robot_description = ParameterValue(robot_description_content, value_type=str)

    # Robot State Publisher — 发布 /robot_description + TF
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # Joint State Publisher — 为非 fixed 关节发布默认 joint states
    joint_state_pub = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # RViz2 — Fixed Frame 直接设为 base_link
    rviz2 = ExecuteProcess(
        cmd=['rviz2', '-f', 'base_link'],
        output='screen'
    )

    return LaunchDescription([
        robot_state_pub,
        joint_state_pub,
        rviz2,
    ])
