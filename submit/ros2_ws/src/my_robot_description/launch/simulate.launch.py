import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory('my_robot_description')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'my_robot.urdf.xacro')

    # xacro → URDF
    robot_description_content = Command(['xacro ', xacro_file])
    robot_description = ParameterValue(robot_description_content, value_type=str)

    urdf_path = '/tmp/my_robot.urdf'
    xacro_to_urdf = ExecuteProcess(
        cmd=['xacro', xacro_file, '-o', urdf_path],
        name='xacro_to_urdf',
        output='screen'
    )

    # macOS 上 Gazebo Sim 必须 server / GUI 分开启动
    # https://github.com/gazebosim/gz-sim/issues/44
    is_macos = sys.platform == 'darwin'

    if is_macos:
        # Server（物理引擎 + 传感器）
        gz_server = ExecuteProcess(
            cmd=['gz', 'sim', '-s', '-r', 'empty.sdf'],
            name='gz_server',
            output='screen'
        )
        # GUI（渲染窗口）
        gz_gui = ExecuteProcess(
            cmd=['gz', 'sim', '-g'],
            name='gz_gui',
            output='screen'
        )
        gz_processes = [gz_server, gz_gui]
    else:
        # Linux：server + GUI 合并在一个进程
        gz_server = ExecuteProcess(
            cmd=['gz', 'sim', '-r', 'empty.sdf'],
            name='gz_sim',
            output='screen'
        )
        gz_processes = [gz_server]

    # Robot State Publisher — TF + /robot_description
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # Spawn 机器人（等 Gazebo Server 就绪后再执行）
    spawn_robot = ExecuteProcess(
        cmd=['ros2', 'run', 'ros_gz_sim', 'create',
             '-name', 'my_robot',
             '-file', urdf_path,
             '-x', '0', '-y', '0', '-z', '0.2'],
        output='screen'
    )

    # ros_gz_bridge — cmd_vel (ROS → Gazebo)
    # DiffDrive 插件监听 /model/my_robot/cmd_vel，必须显式映射
    bridge_cmd_vel = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_cmd_vel',
        arguments=['/cmd_vel@geometry_msgs/msg/Twist]/model/my_robot/cmd_vel@gz.msgs.Twist'],
        output='screen'
    )

    # ros_gz_bridge — odometry (Gazebo → ROS)
    bridge_odom = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_odom',
        arguments=['/model/my_robot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
        output='screen'
    )

    # 等 URDF 写完再 spawn
    spawn_after_urdf = RegisterEventHandler(
        OnProcessExit(
            target_action=xacro_to_urdf,
            on_exit=[spawn_robot],
        )
    )

    return LaunchDescription([
        xacro_to_urdf,
        *gz_processes,
        robot_state_pub,
        bridge_cmd_vel,
        bridge_odom,
        spawn_after_urdf,
    ])
