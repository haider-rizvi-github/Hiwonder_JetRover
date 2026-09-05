from launch import LaunchDescription
from launch.actions import TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def generate_launch_description():

    spawn_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        name="spawner_joint_state_broadcaster",
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    spawn_mecanum_controller = Node(
        package="controller_manager",
        executable="spawner",
        name="spawner_mecanum_drive_controller",
        output="screen",
        arguments=[
            "mecanum_drive_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    spawn_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        name="spawner_arm_controller",
        output="screen",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    spawn_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        name="spawner_gripper_controller",
        output="screen",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    return LaunchDescription(
        [
            TimerAction(
                period=5.0,
                actions=[spawn_joint_state_broadcaster],
            ),

            RegisterEventHandler(
                OnProcessExit(
                    target_action=spawn_joint_state_broadcaster,
                    on_exit=[spawn_mecanum_controller],
                )
            ),

            RegisterEventHandler(
                OnProcessExit(
                    target_action=spawn_mecanum_controller,
                    on_exit=[spawn_arm_controller],
                )
            ),

            RegisterEventHandler(
                OnProcessExit(
                    target_action=spawn_arm_controller,
                    on_exit=[spawn_gripper_controller],
                )
            ),
        ]
    )