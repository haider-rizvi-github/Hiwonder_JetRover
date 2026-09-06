import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_share = get_package_share_directory("jetrover_controller")

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joystick",
        output="screen",
        parameters=[
            os.path.join(
                package_share,
                "config",
                "joy_config.yaml",
            )
        ],
    )

    joy_teleop_node = Node(
        package="joy_teleop",
        executable="joy_teleop",
        name="joy_teleop",
        output="screen",
        parameters=[
            os.path.join(
                package_share,
                "config",
                "joy_teleop.yaml",
            )
        ],
    )

    arm_gripper_teleop_node = Node(
        package="jetrover_controller",
        executable="arm_gripper_teleop.py",
        name="arm_gripper_teleop",
        output="screen",
        parameters=[
            os.path.join(
                package_share,
                "config",
                "arm_gripper_teleop.yaml",
            )
        ],
    )


    return LaunchDescription(
        [
            joy_node,
            joy_teleop_node,
            arm_gripper_teleop_node,
        ]
    )