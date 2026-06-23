#!/usr/bin/env python3
"""Manual integration test for :class:`ur_utils_ros2_py.urp_control.UrpControl`."""

from __future__ import annotations
import rclpy
from rclpy.node import Node
import time

from ur_utils_ros2_py.urp_control import UrpControl


class TestUrpControl(Node):
    """Drive the dashboard helper through all of its public operations."""

    def __init__(self, test_program: str):
        super().__init__("test_urp_control")
        self.urp = UrpControl(self)
        self.test_program = test_program

    def run(self) -> bool:

        self.get_logger().info("Restoring ROS control program")
        self.urp.restart_ros_control()


        """Exercise the helper and restore ROS control at the end."""
        self.get_logger().info("Stopping any running program")
        stop_result = self.urp.stop_program()
        self.get_logger().info(
            f"stop_program -> success={stop_result.success}, message='{stop_result.message}'"
        )

        self.get_logger().info(f"Loading test program: {self.test_program}")
        load_result = self.urp.load_program(self.test_program)
        self.get_logger().info(
            f"load_program -> success={load_result.success}, answer='{load_result.answer}'"
        )

        self.get_logger().info("Playing loaded program")
        play_result = self.urp.play_program()
        self.get_logger().info(
            f"play_program -> success={play_result.success}, message='{play_result.message}'"
        )

        finished = self.urp.wait_script_end(timeout=30.0)
        self.get_logger().info(f"wait_script_end -> {finished}")

        self.get_logger().info("Testing combined load-and-play")
        self.urp.load_and_play_script(self.test_program)
        finished = self.urp.wait_script_end(timeout=30.0)
        self.get_logger().info(f"wait_script_end -> {finished}")

        self.get_logger().info("Restoring ROS control program")
        self.urp.restart_ros_control()

        return

        self.get_logger().info("Final stop to leave the controller idle")
        self.urp.stop_program()

        return True


def main(args=None):

    rclpy.init()
    node = TestUrpControl("prova_moveL.urp")
    try:
        ok = node.run()
        return 0 if ok else 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
