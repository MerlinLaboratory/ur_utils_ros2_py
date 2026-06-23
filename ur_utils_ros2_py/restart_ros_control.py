#!/usr/bin/env python3
"""Minimal node that restarts the default ROS control URP program."""

from __future__ import annotations

import rclpy
from rclpy.node import Node

from ur_utils_ros2_py.urp_control import UrpControl


class RestartRosControlNode(Node):
    """Start `ros2.urp` through :class:`UrpControl` and then exit."""

    def __init__(self):
        super().__init__("restart_ros_control")
        self.urp = UrpControl(self)

    def run(self) -> bool:
        self.get_logger().info("Restarting ROS control program")
        self.urp.restart_ros_control()
        return True


def main(args=None):
    rclpy.init(args=args)
    node = RestartRosControlNode()
    try:
        return 0 if node.run() else 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
