"""Helpers for controlling UR dashboard programs from ROS 2."""

from __future__ import annotations

import time
from threading import Lock

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from ur_dashboard_msgs.srv import Load


class UrpControl:
    """Control a UR controller program through dashboard services.

    The class wraps the dashboard services exposed by the
    `ur_robot_driver` stack and provides a small, synchronous API for
    loading, stopping, and starting URP programs.

    Parameters
    ----------
    node
        ROS 2 node used to create the service clients and log messages.
    load_program_service
        Fully qualified name of the dashboard `load_program` service.
    play_service
        Fully qualified name of the dashboard `play` service.
    stop_service
        Fully qualified name of the dashboard `stop` service.
    robot_program_running_topic
        Topic carrying `std_msgs/msg/Bool`, used to track whether the robot
        program is currently running.
    default_script_name
        URP file loaded by :meth:`restart_ros_control`.
    service_wait_timeout_sec
        Maximum time spent waiting for each service during construction.

    Notes
    -----
    The service clients are synchronous wrappers around asynchronous ROS
    service calls. Internally the class uses
    :func:`rclpy.spin_until_future_complete`, which is supported on both
    ROS 2 Humble and Jazzy.
    """

    DEFAULT_LOAD_SERVICE = "/dashboard_client/load_program"
    DEFAULT_PLAY_SERVICE = "/dashboard_client/play"
    DEFAULT_STOP_SERVICE = "/dashboard_client/stop"
    DEFAULT_ROBOT_PROGRAM_RUNNING_TOPIC = "/io_and_status_controller/robot_program_running"

    def __init__(
        self,
        node: Node,
        *,
        load_program_service: str = DEFAULT_LOAD_SERVICE,
        play_service: str = DEFAULT_PLAY_SERVICE,
        stop_service: str = DEFAULT_STOP_SERVICE,
        robot_program_running_topic: str = DEFAULT_ROBOT_PROGRAM_RUNNING_TOPIC,
        default_script_name: str = "ros2.urp",
        service_wait_timeout_sec: float = 10.0,
    ):
        self.node = node
        self.logger = node.get_logger()
        self.ros_control_urp_script_name = default_script_name
        self.service_wait_timeout_sec = service_wait_timeout_sec
        self._program_running_lock = Lock()
        self._latest_program_running = None

        self.logger.info("Initializing URP Control...")

        self.cli_load_program = node.create_client(Load, load_program_service)
        self.cli_play_program = node.create_client(Trigger, play_service)
        self.cli_stop_program = node.create_client(Trigger, stop_service)
        self.sub_program_running = node.create_subscription(
            Bool,
            robot_program_running_topic,
            self._program_running_callback,
            10,
        )

        for cli, name in [
            (self.cli_load_program, 'load_program'),
            (self.cli_play_program, 'play'),
            (self.cli_stop_program, 'stop')
        ]:
            self.logger.info(f"Waiting for {name} service...")
            elapsed = 0.0
            while not cli.wait_for_service(timeout_sec=1.0):
                self.logger.warning(f"{name} not available, waiting again...")
                elapsed += 1.0
                if 0.0 < self.service_wait_timeout_sec <= elapsed:
                    raise TimeoutError(f"Timed out waiting for {name} service")

        self.logger.info("All dashboard services available.")

    def _program_running_callback(self, msg: Bool) -> None:
        with self._program_running_lock:
            self._latest_program_running = msg.data

    def _spin_future(self, future, operation: str):
        rclpy.spin_until_future_complete(self.node, future)

        result = future.result()
        if result is None:
            raise RuntimeError(f"{operation} service returned no result")
        return result

    def stop_program(self) -> Trigger.Response:
        """Stop the currently running dashboard program."""
        future = self.cli_stop_program.call_async(Trigger.Request())
        return self._spin_future(future, "stop")

    def play_program(self) -> Trigger.Response:
        """Start the currently loaded dashboard program."""
        future = self.cli_play_program.call_async(Trigger.Request())
        return self._spin_future(future, "play")

    def load_program(self, script_name: str) -> Load.Response:
        """Load a URP program on the controller."""
        load_req = Load.Request()
        load_req.filename = script_name
        future = self.cli_load_program.call_async(load_req)
        return self._spin_future(future, "load_program")

    def load_and_play_script(self, script_name: str) -> None:
        """Stop the current program, load `script_name`, and start it."""
        self.logger.info(f"Loading and playing script: {script_name}")
        self.stop_program()
        time.sleep(0.2)
        self.load_program(script_name)
        time.sleep(0.2)
        self.play_program()
        time.sleep(0.2)

    def restart_ros_control(self) -> None:
        """Restore the default ROS control URP program."""
        self.load_and_play_script(self.ros_control_urp_script_name)

    def is_script_running(self) -> bool:
        """Return whether the robot program is currently running."""
        with self._program_running_lock:
            program_running = self._latest_program_running

        if program_running is None:
            self.logger.warning("No /robot_program_running messages received yet; assuming not running.")
            return False

        return bool(program_running)

    def wait_script_end(self, timeout: float = 10.0) -> bool:
        """Wait until the controller script stops running.

        Returns `True` when the script reports completion before the timeout,
        otherwise `False`.
        """
        start = time.time()
        rate = self.node.create_rate(10)
        time.sleep(1.0)
        while (time.time() - start) < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.0)
            if not self.is_script_running():
                self.logger.info("Script finished.")
                return True
            rate.sleep()
        self.logger.warning("Timeout waiting for script to finish.")
        return False
