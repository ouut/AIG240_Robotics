from setuptools import find_packages, setup

package_name = 'lab4_jetauto_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@example.com',
    description='ROS2 node to move JetAuto through a square pattern in Gazebo',
    license='BSD',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'jetauto_square = lab4_jetauto_control.jetauto_square:main',
        ],
    },
)
