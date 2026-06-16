import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory('jetauto_description')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'jetauto.urdf.xacro')

    # GZ_SIM_RESOURCE_PATH: Gazebo Sim needs this to resolve
    # model://jetauto_description/... → <install>/share/jetauto_description/...
    gz_resource_path = os.path.dirname(pkg_dir)

    # Launch arguments
    odom_frame = LaunchConfiguration('odom_frame', default='odom')
    base_frame = LaunchConfiguration('base_frame', default='base_footprint')
    depth_camera_name = LaunchConfiguration('depth_camera_name', default='camera')

    # xacro → URDF (in-memory for robot_state_publisher)
    robot_description_content = Command([
        'xacro ', xacro_file,
        ' odom_frame:=', odom_frame,
        ' base_frame:=', base_frame,
        ' depth_camera_name:=', depth_camera_name,
        ' lidar_view:=false'
    ])
    robot_description = ParameterValue(robot_description_content, value_type=str)

    # xacro → URDF (to file for spawn)
    urdf_path = '/tmp/jetauto.urdf'
    xacro_to_urdf = ExecuteProcess(
        cmd=['xacro', xacro_file,
             'odom_frame:=odom',
             'base_frame:=base_footprint',
             'depth_camera_name:=camera',
             'lidar_view:=false',
             '-o', urdf_path],
        name='xacro_to_urdf',
        output='screen'
    )

    # macOS: Gazebo Sim requires server + GUI as separate processes
    is_macos = sys.platform == 'darwin'

    # Set GZ_SIM_RESOURCE_PATH so Gazebo can find model://jetauto_description/... meshes
    gz_env = {'GZ_SIM_RESOURCE_PATH': gz_resource_path}

    if is_macos:
        gz_server = ExecuteProcess(
            cmd=['gz', 'sim', '-s', '-r', 'empty.sdf'],
            name='gz_server',
            output='screen',
            additional_env=gz_env
        )
        gz_gui = ExecuteProcess(
            cmd=['gz', 'sim', '-g'],
            name='gz_gui',
            output='screen',
            additional_env=gz_env
        )
        gz_processes = [gz_server, gz_gui]
    else:
        gz_server = ExecuteProcess(
            cmd=['gz', 'sim', '-r', 'empty.sdf'],
            name='gz_sim',
            output='screen',
            additional_env=gz_env
        )
        gz_processes = [gz_server]

    # Robot State Publisher
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # Spawn robot into Gazebo Sim
    spawn_robot = ExecuteProcess(
        cmd=['ros2', 'run', 'ros_gz_sim', 'create',
             '-name', 'jetauto',
             '-file', urdf_path,
             '-x', '0', '-y', '0', '-z', '0.1'],
        output='screen'
    )

    # ros_gz_bridge: cmd_vel (ROS → Gazebo)
    bridge_cmd_vel = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_cmd_vel',
        arguments=['/cmd_vel@geometry_msgs/msg/Twist]/model/jetauto/cmd_vel@gz.msgs.Twist'],
        output='screen'
    )

    # ros_gz_bridge: odometry (Gazebo → ROS)
    bridge_odom = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_odom',
        arguments=['/model/jetauto/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
        output='screen'
    )

    # ros_gz_bridge: laser scan (Gazebo → ROS)
    bridge_scan = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_scan',
        arguments=['/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'],
        output='screen'
    )

    # ros_gz_bridge: imu (Gazebo → ROS)
    bridge_imu = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_imu',
        arguments=['/imu_data@sensor_msgs/msg/Imu[gz.msgs.IMU'],
        output='screen'
    )

    # Wait for URDF to be written before spawning
    spawn_after_urdf = RegisterEventHandler(
        OnProcessExit(
            target_action=xacro_to_urdf,
            on_exit=[spawn_robot],
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument('odom_frame', default_value='odom'),
        DeclareLaunchArgument('base_frame', default_value='base_footprint'),
        DeclareLaunchArgument('depth_camera_name', default_value='camera'),
        xacro_to_urdf,
        *gz_processes,
        robot_state_pub,
        bridge_cmd_vel,
        bridge_odom,
        bridge_scan,
        bridge_imu,
        spawn_after_urdf,
    ])
