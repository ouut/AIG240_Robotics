import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    pkg_dir = get_package_share_directory('jetauto_description')
    rviz_config = os.path.join(pkg_dir, 'rviz', 'control_view.rviz')

    rviz2 = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        rviz2,
    ])
