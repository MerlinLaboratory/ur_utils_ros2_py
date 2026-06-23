from setuptools import setup

package_name = 'ur_utils_ros2_py'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Marco-Faroni',
    maintainer_email='marco.faroni@polimi.it',
    description='UR dashboard control utilities for ROS 2',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'restart_ros_control = ur_utils_ros2_py.restart_ros_control:main',
            'test_node = ur_utils_ros2_py.test_node:main'
        ],
    },
)
