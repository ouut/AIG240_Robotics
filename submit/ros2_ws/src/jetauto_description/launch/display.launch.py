import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory('jetauto_description')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'jetauto.urdf.xacro')

    # Launch arguments
    odom_frame = LaunchConfiguration('odom_frame', default='odom')
    base_frame = LaunchConfiguration('base_frame', default='base_footprint')
    depth_camera_name = LaunchConfiguration('depth_camera_name', default='camera')

    # xacro → URDF
    robot_description_content = Command([
        'xacro ', xacro_file,
        ' odom_frame:=', odom_frame,
        ' base_frame:=', base_frame,
        ' depth_camera_name:=', depth_camera_name,
        ' lidar_view:=false'
    ])
    robot_description = ParameterValue(robot_description_content, value_type=str)

    # Robot State Publisher
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # Joint State Publisher GUI
    joint_state_pub_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # RViz2
    rviz_config = os.path.join(pkg_dir, 'rviz', 'urdf.rviz')
    rviz2 = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('odom_frame', default_value='odom'),
        DeclareLaunchArgument('base_frame', default_value='base_footprint'),
        DeclareLaunchArgument('depth_camera_name', default_value='camera'),
        robot_state_pub,
        joint_state_pub_gui,
        rviz2,
    ])
