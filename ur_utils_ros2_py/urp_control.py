import rclpy
from rclpy.node import Node
from ur_dashboard_msgs.srv import Load
from std_srvs.srv import Trigger
import time


class UrpControl:
    """Library class to control UR dashboard services."""

    def __init__(self, node: Node):
        self.node = node
        self.logger = node.get_logger()
        self.ros_control_urp_script_name = "ros1.urp"

        self.logger.info("Initializing URP Control...")

        # Create service clients
        self.cli_load_program = node.create_client(Load, '/ur_hardware_interface/dashboard/load_program')
        self.cli_play_program = node.create_client(Trigger, '/ur_hardware_interface/dashboard/play')
        self.cli_stop_program = node.create_client(Trigger, '/ur_hardware_interface/dashboard/stop')
        self.cli_is_script_running = node.create_client(Trigger, '/ur_hardware_interface/get_is_script_running')

        # Wait for services
        for cli, name in [
            (self.cli_load_program, 'load_program'),
            (self.cli_play_program, 'play'),
            (self.cli_stop_program, 'stop'),
            (self.cli_is_script_running, 'get_is_script_running')
        ]:
            self.logger.info(f"Waiting for {name} service...")
            while not cli.wait_for_service(timeout_sec=1.0):
                self.logger.warn(f"{name} not available, waiting again...")

        self.logger.info("All dashboard services available.")

    def load_and_play_script(self, script_name: str):
        """Stop, load, and play a URP script."""
        self.logger.info(f"Loading and playing script: {script_name}")

        # Stop current program
        stop_future = self.cli_stop_program.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self.node, stop_future)
        time.sleep(0.1)

        # Load new program
        load_req = Load.Request()
        load_req.filename = script_name
        load_future = self.cli_load_program.call_async(load_req)
        rclpy.spin_until_future_complete(self.node, load_future)
        time.sleep(0.1)

        # Play program
        play_future = self.cli_play_program.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self.node, play_future)
        time.sleep(0.1)

    def restart_ros_control(self):
        """Restart ROS control using the default URP script."""
        self.load_and_play_script(self.ros_control_urp_script_name)

    def wait_script_end(self, timeout: float = 10.0):
        """Block until the script stops running or timeout."""
        start = time.time()
        rate = self.node.create_rate(10)
        while (time.time() - start) < timeout:
            req = Trigger.Request()
            future = self.cli_is_script_running.call_async(req)
            rclpy.spin_until_future_complete(self.node, future)
            result = future.result()
            if not result.success and (time.time() - start) > 0.5:
                self.logger.info("Script finished.")
                return True
            rate.sleep()
        self.logger.warn("Timeout waiting for script to finish.")
        return False
