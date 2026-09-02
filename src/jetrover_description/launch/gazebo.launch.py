import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Launch configurations
    description_share = get_package_share_directory("jetrover_description")

    model = LaunchConfiguration("model")
    machine_type = LaunchConfiguration("machine_type")
    lidar_type = LaunchConfiguration("lidar_type")

    model_arg = DeclareLaunchArgument(
        "model",
        default_value=PathJoinSubstitution(
            [
                FindPackageShare("jetrover_description"),
                "urdf",
                "hiwonder_jetrover.xacro",
            ]
        ),
        description="Path to the JetRover Xacro file",
    )

    machine_type_arg = DeclareLaunchArgument(
        "machine_type",
        default_value="JetRover_Mecanum",
        description="JetRover chassis type",
    )

    lidar_type_arg = DeclareLaunchArgument(
        "lidar_type",
        default_value="A1",
        description="LiDAR type",
    )

    set_machine_type = SetEnvironmentVariable(
        name="MACHINE_TYPE",
        value=machine_type,
    )

    set_lidar_type = SetEnvironmentVariable(
        name="LIDAR_TYPE",
        value=lidar_type,
    )

    # Allow Gazebo to find model://jetrover_description/meshes/...
    set_gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=os.path.dirname(description_share),
    )

    robot_description = ParameterValue(
        Command(
            [
                FindExecutable(name="xacro"),
                " ",
                model,
            ]
        ),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,
            }
        ],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                ]
            )
        ),
        launch_arguments={
            "gz_args": "-r empty.sdf"
        }.items(),
    )

    spawn_robot = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="ros_gz_sim",
                executable="create",
                arguments=[
                    "-topic",
                    "robot_description",
                    "-name",
                    "jetrover",
                    "-x",
                    "0.0",
                    "-y",
                    "0.0",
                    "-z",
                    "0.0",
                ],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            model_arg,
            machine_type_arg,
            lidar_type_arg,
            set_machine_type,
            set_lidar_type,
            set_gz_resource_path,
            gazebo,
            robot_state_publisher,
            spawn_robot,
        ]
    )