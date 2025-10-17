#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from my_package.urp_control import UrpControl


class TestUrpControl(Node):
    def __init__(self):
        super().__init__('test_urp_control')
        self.urp = UrpControl(self)
        self.timer = self.create_timer(1.0, self.run_once)
        self.done = False

    def run_once(self):
        if self.done:
            return
        self.done = True
        self.get_logger().info("Restarting ROS control...")
        self.urp.restart_ros_control()
        self.urp.wait_script_end(10.0)
        self.get_logger().info("Test completed.")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = TestUrpControl()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

