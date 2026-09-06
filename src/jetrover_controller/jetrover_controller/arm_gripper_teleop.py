#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from sensor_msgs.msg import Joy, JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class ArmGripperTeleop(Node):

    def __init__(self):
        super().__init__("arm_gripper_teleop")

        self.arm_joints = list(
            self.declare_parameter(
                "arm_joints",
                ["joint1", "joint2", "joint3", "joint4", "joint5"],
            ).value
        )

        self.gripper_joint = self.declare_parameter(
            "gripper_joint", "r_joint"
        ).value

        self.arm_mode_button = int(
            self.declare_parameter("arm_mode_button", 4).value
        )

        self.arm_axis = int(
            self.declare_parameter("arm_axis", 4).value
        )

        self.gripper_axis = int(
            self.declare_parameter("gripper_axis", 7).value
        )

        self.arm_step = float(
            self.declare_parameter("arm_step", 0.02).value
        )

        self.gripper_step = float(
            self.declare_parameter("gripper_step", 0.05).value
        )

        self.arm_min = list(
            self.declare_parameter(
                "arm_min", [-2.09] * len(self.arm_joints)
            ).value
        )

        self.arm_max = list(
            self.declare_parameter(
                "arm_max", [2.09] * len(self.arm_joints)
            ).value
        )

        self.gripper_min = float(
            self.declare_parameter("gripper_min", -0.6).value
        )

        self.gripper_max = float(
            self.declare_parameter("gripper_max", 0.6).value
        )

        self.arm_positions = [0.0] * len(self.arm_joints)
        self.gripper_position = 0.0
        self.selected_joint = 0

        self.joy_msg = None
        self.joint_state_received = False
        self.arm_goal_active = False
        self.gripper_goal_active = False

        self.previous_buttons = []

        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory",
        )

        self.gripper_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/gripper_controller/follow_joint_trajectory",
        )

        self.create_subscription(
            Joy,
            "/joy",
            self.joy_callback,
            10,
        )

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            10,
        )

        self.create_timer(0.05, self.control_loop)

        self.get_logger().info("Arm/gripper joystick node started")

    def joy_callback(self, msg):
        self.joy_msg = msg

        if not self.previous_buttons:
            self.previous_buttons = [0] * len(msg.buttons)

        for index, button in enumerate(msg.buttons):
            was_pressed = (
                index < len(self.previous_buttons)
                and self.previous_buttons[index] == 1
            )

            if button == 1 and not was_pressed:
                if index == 0:
                    self.selected_joint = 0
                elif index == 1:
                    self.selected_joint = 1
                elif index == 2:
                    self.selected_joint = 2
                elif index == 3:
                    self.selected_joint = 3
                elif index == 6:
                    self.selected_joint = 4

                if index in [0, 1, 2, 3, 6]:
                    self.get_logger().info(
                        f"Selected {self.arm_joints[self.selected_joint]}"
                    )

        self.previous_buttons = list(msg.buttons)

    def joint_state_callback(self, msg):
        for index, name in enumerate(msg.name):
            if index >= len(msg.position):
                continue

            if name in self.arm_joints:
                joint_index = self.arm_joints.index(name)
                self.arm_positions[joint_index] = msg.position[index]
                self.joint_state_received = True

            if name == self.gripper_joint:
                self.gripper_position = msg.position[index]

    def control_loop(self):
        if self.joy_msg is None or not self.joint_state_received:
            return

        if len(self.joy_msg.buttons) <= self.arm_mode_button:
            return

        arm_mode_active = (
            self.joy_msg.buttons[self.arm_mode_button] == 1
        )

        if not arm_mode_active:
            return

        if len(self.joy_msg.axes) > self.arm_axis:
            arm_value = self.joy_msg.axes[self.arm_axis]

            if abs(arm_value) > 0.15 and not self.arm_goal_active:
                self.arm_positions[self.selected_joint] += (
                    -arm_value * self.arm_step
                )

                self.arm_positions[self.selected_joint] = max(
                    self.arm_min[self.selected_joint],
                    min(
                        self.arm_max[self.selected_joint],
                        self.arm_positions[self.selected_joint],
                    ),
                )

                self.send_arm_goal()

        if len(self.joy_msg.axes) > self.gripper_axis:
            gripper_value = self.joy_msg.axes[self.gripper_axis]

            if abs(gripper_value) > 0.5 and not self.gripper_goal_active:
                self.gripper_position += (
                    gripper_value * self.gripper_step
                )

                self.gripper_position = max(
                    self.gripper_min,
                    min(self.gripper_max, self.gripper_position),
                )

                self.send_gripper_goal()

    def send_arm_goal(self):
        if not self.arm_client.server_is_ready():
            self.get_logger().warn(
                "Arm trajectory action server is not ready"
            )
            return

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.arm_joints

        point = JointTrajectoryPoint()
        point.positions = list(self.arm_positions)
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 100_000_000  # Change this value to adjust the speed of the arm movement

        goal.trajectory.points = [point]
        self.arm_goal_active = True

        future = self.arm_client.send_goal_async(goal)
        future.add_done_callback(self.arm_goal_response)

    def arm_goal_response(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.arm_goal_active = False
            self.get_logger().warn("Arm goal rejected")
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.arm_goal_finished)

    def arm_goal_finished(self, future):
        self.arm_goal_active = False

    def send_gripper_goal(self):
        if not self.gripper_client.server_is_ready():
            self.get_logger().warn(
                "Gripper trajectory action server is not ready"
            )
            return

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = [self.gripper_joint]

        point = JointTrajectoryPoint()
        point.positions = [self.gripper_position]
        point.time_from_start.sec = 1

        goal.trajectory.points = [point]
        self.gripper_goal_active = True

        future = self.gripper_client.send_goal_async(goal)
        future.add_done_callback(self.gripper_goal_response)

    def gripper_goal_response(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.gripper_goal_active = False
            self.get_logger().warn("Gripper goal rejected")
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.gripper_goal_finished)

    def gripper_goal_finished(self, future):
        self.gripper_goal_active = False


def main(args=None):
    rclpy.init(args=args)
    node = ArmGripperTeleop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()