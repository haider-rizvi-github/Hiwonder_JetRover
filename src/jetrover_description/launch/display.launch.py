from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
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
    model = LaunchConfiguration("model")
    machine_type = LaunchConfiguration("machine_type")
    lidar_type = LaunchConfiguration("lidar_type")

    # Path to the JetRover Xacro file
    model_arg = DeclareLaunchArgument(
        "model",
        default_value=PathJoinSubstitution(
            [
                FindPackageShare("jetrover_description"),
                "urdf",
                "hiwonder_jetrover.xacro",
            ]
        ),
        description="Absolute path to the JetRover Xacro file",
    )

    # Choose the JetRover chassis
    machine_type_arg = DeclareLaunchArgument(
        "machine_type",
        default_value="JetRover_Mecanum",
        description=(
            "JetRover chassis: "
            "JetRover_Mecanum, JetRover_Tank or JetRover_Acker"
        ),
    )

    # Choose the LiDAR
    lidar_type_arg = DeclareLaunchArgument(
        "lidar_type",
        default_value="A1",
        description="LiDAR model: A1, A2, C1, S2L, LD14P or G4",
    )

    # Your Xacro reads these environment variables
    set_machine_type = SetEnvironmentVariable(
        name="MACHINE_TYPE",
        value=machine_type,
    )

    set_lidar_type = SetEnvironmentVariable(
        name="LIDAR_TYPE",
        value=lidar_type,
    )

    # Execute Xacro and store the generated URDF
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

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    rviz_config = PathJoinSubstitution(
        [
            FindPackageShare("jetrover_description"),
            "rviz",
            "display.rviz",
        ]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    # Order matters: environment variables must be set before Xacro runs
    return LaunchDescription(
        [
            model_arg,
            machine_type_arg,
            lidar_type_arg,
            set_machine_type,
            set_lidar_type,
            robot_state_publisher,
            joint_state_publisher_gui,
            rviz_node,
        ]
    )