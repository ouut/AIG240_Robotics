#!/usr/bin/env python3
"""
jetauto_square.py — ROS2 node that drives the JetAuto robot through a
~1 m square pattern in Gazebo, repeating twice.

Pattern (per repetition, assignment steps):
  1. Forward ~1 m
  2. Move left ~1 m *without changing heading*  (diff‑drive: turn‑move‑turn)
  3. Rotate clockwise ~90°
  4. Move right ~1 m *while facing inward*       (diff‑drive: turn‑move‑turn)
  5. Return to start (simple: forward + turn)
  6. Repeat 2×

Coordinate note:
  The robot spawns at yaw = 0 (facing +x / east in ROS REP-103).
  All steps are *relative* to the robot's current pose, so the absolute
  orientation of the square in the world frame depends on the spawn yaw.
  The square is always 1 m × 1 m and the robot returns to its exact
  start position with its original heading.

Control strategy:
  - Odometry‑feedback: subscribes to /model/jetauto/odometry for pose
  - Publishes geometry_msgs/msg/Twist to /cmd_vel
  - Proportional controller on distance / heading error
  - State machine sequences through the pattern steps
"""

import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


# ---------------------------------------------------------------------------
# Quaternion helpers (avoid extra dependency on tf_transformations at runtime)
# ---------------------------------------------------------------------------
def quat_to_yaw(q):
    """Return yaw (rotation about Z) from a quaternion [x, y, z, w]."""
    siny_cosp = 2.0 * (q[3] * q[2] + q[0] * q[1])
    cosy_cosp = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])
    return math.atan2(siny_cosp, cosy_cosp)


def normalize_angle(a):
    """Wrap angle to [-pi, pi)."""
    return math.atan2(math.sin(a), math.cos(a))


# ---------------------------------------------------------------------------
# Controller node
# ---------------------------------------------------------------------------
class JetAutoSquareController(Node):
    def __init__(self, repeats=2):
        super().__init__('jetauto_square_controller')

        # Publisher – drive commands
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscriber – ground-truth pose from Gazebo
        self.odom_sub = self.create_subscription(
            Odometry, '/model/jetauto/odometry', self.odom_cb, 10)

        # Current pose estimate
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.odom_received = False

        # Control parameters
        self.linear_kp = 0.8        # P‑gain for linear speed
        self.angular_kp = 1.2       # P‑gain for angular speed
        self.max_linear = 0.25      # m/s  (keep conservative for sim accuracy)
        self.max_angular = 0.8      # rad/s
        self.dist_tol = 0.03        # metres – "close enough" for each segment
        self.angle_tol = 0.04       # radians (~2.3°) – "close enough"

        # Pattern definition
        self.repeats = repeats
        self.current_repeat = 0

        # Build the step list ONCE (relative moves + heading targets)
        self.steps = self._build_steps()
        self.step_index = 0

        # State machine
        self.state = 'WAIT_ODOM'     # WAIT_ODOM → WAIT_START → EXEC → DONE
        self.state_timer = None

        # Timers
        self.control_timer = self.create_timer(0.05, self.control_loop)  # 20 Hz
        self.get_logger().info('JetAuto Square Controller initialised.')
        self.get_logger().info('Waiting for odometry …')

    # -------------------------------------------------------------------
    # Step builder
    # -------------------------------------------------------------------
    def _build_steps(self):
        """
        Each step is a dict:
          type:  'linear'  – drive forward    dist  metres  (+ve = forward)
                 'rotate'  – turn in place    angle radians  (+ve = CCW / left)
          desc: human label

        The robot spawns at yaw = 0 (faces +x / east in ROS REP-103).
        The sequence below traces a 1 m × 1 m square relative to the
        start pose.  Because every step is relative, the absolute world
        orientation does not matter — the robot always ends back at the
        start position with the start heading.

        Trace (yaw = 0 → facing +x / east):
          #  Action                          yaw      (x,  y)
          ────────────────────────────────────────────────────
           0  (start)                         0°     ( 0,  0)
           1  Forward 1 m                     0°     ( 1,  0)
           2  Turn CCW 90°                   +90°     ( 1,  0)
           3  Forward 1 m (side-left)        +90°     ( 1,  1)
           4  Turn CW 90° (restore)            0°     ( 1,  1)
           5  Turn CW 90° (rotate CW)        -90°     ( 1,  1)
           6  Turn CW 90° (prep right)      ±180°     ( 1,  1)
           7  Forward 1 m (right/inward)    ±180°     ( 0,  1)
           8  Turn CCW 90° (align return)    -90°     ( 0,  1)
           9  Forward 1 m (return!)          -90°     ( 0,  0)  ← back at start
          10  Turn CCW 90° (restore)           0°     ( 0,  0)  ← ready for next rep
        """
        steps = []
        for rep in range(self.repeats):
            label = f'(rep {rep+1}/{self.repeats})'
            # ── Assignment step 1: Forward ~1 m ──────────────────────
            steps.append({'type': 'linear', 'dist': 1.0,
                          'desc': f'Forward 1 m {label}'})
            # ── Assignment step 2: Move left 1 m, same heading ───────
            #    Diff‑drive: turn CCW 90°, forward 1 m, turn CW 90°
            steps.append({'type': 'rotate', 'angle':  math.pi/2,
                          'desc': f'Turn CCW 90° (prep side-left) {label}'})
            steps.append({'type': 'linear', 'dist': 1.0,
                          'desc': f'Forward 1 m (side-left) {label}'})
            steps.append({'type': 'rotate', 'angle': -math.pi/2,
                          'desc': f'Turn CW 90° (restore heading) {label}'})
            # ── Assignment step 3: Rotate clockwise ~90° ─────────────
            steps.append({'type': 'rotate', 'angle': -math.pi/2,
                          'desc': f'Turn CW 90° (rotate clockwise) {label}'})
            # ── Assignment step 4: Move right ~1 m, facing inward ────
            #    Diff‑drive: turn CW 90°, forward 1 m, turn CCW 90°
            steps.append({'type': 'rotate', 'angle': -math.pi/2,
                          'desc': f'Turn CW 90° (prep right/inward) {label}'})
            steps.append({'type': 'linear', 'dist': 1.0,
                          'desc': f'Forward 1 m (right / inward) {label}'})
            steps.append({'type': 'rotate', 'angle':  math.pi/2,
                          'desc': f'Turn CCW 90° (align for return) {label}'})
            # ── Assignment step 5: Return to start ───────────────────
            #    Robot is now one side away from start, pointing toward it.
            steps.append({'type': 'linear', 'dist': 1.0,
                          'desc': f'Forward 1 m (return to start) {label}'})
            steps.append({'type': 'rotate', 'angle':  math.pi/2,
                          'desc': f'Turn CCW 90° (restore original heading) {label}'})
        return steps

    # -------------------------------------------------------------------
    # Odometry callback
    # -------------------------------------------------------------------
    def odom_cb(self, msg: Odometry):
        pose = msg.pose.pose
        self.x = pose.position.x
        self.y = pose.position.y
        q = pose.orientation
        self.yaw = quat_to_yaw([q.x, q.y, q.z, q.w])
        if not self.odom_received:
            self.odom_received = True
            # Record start pose so we can assess drift at the end
            self.start_x = self.x
            self.start_y = self.y
            self.start_yaw = self.yaw
            self.get_logger().info(
                f'Odometry locked. Start pose: '
                f'({self.x:.3f}, {self.y:.3f}), yaw={self.yaw:.3f} rad')

    # -------------------------------------------------------------------
    # Main control loop (20 Hz timer)
    # -------------------------------------------------------------------
    def control_loop(self):
        if self.state == 'WAIT_ODOM':
            if self.odom_received:
                self.get_logger().info(
                    'Press ENTER in the terminal to start the square pattern …')
                self.state = 'WAIT_START'

        elif self.state == 'WAIT_START':
            # Non‑blocking check for user input
            pass   # handled by the blocking input() in main()

        elif self.state == 'EXEC':
            self._execute_step()

        elif self.state == 'DONE':
            self.cmd_pub.publish(Twist())   # ensure stop
            # Shut down cleanly after a short delay so the last log is visible
            self.get_logger().info('Pattern complete! Destroying node.')
            self.destroy_node()

    # -------------------------------------------------------------------
    # Execute current step with proportional control
    # -------------------------------------------------------------------
    def _execute_step(self):
        if self.step_index >= len(self.steps):
            # All repetitions done
            self.state = 'DONE'
            dx = self.x - self.start_x
            dy = self.y - self.start_y
            self.get_logger().info(
                f'Final drift from start: Δx={dx:.3f} m, Δy={dy:.3f} m')
            return

        step = self.steps[self.step_index]

        # Initialise tracking on first call of this step
        if not hasattr(self, '_step_start_x'):
            self._step_start_x = self.x
            self._step_start_y = self.y
            self._step_start_yaw = self.yaw
            self._step_dist_travelled = 0.0
            self.get_logger().info(f'▶ {step["desc"]}')

        twist = Twist()

        if step['type'] == 'linear':
            # Compute remaining distance
            target_dist = step['dist']
            dx_sofar = self.x - self._step_start_x
            dy_sofar = self.y - self._step_start_y
            dist_travelled = math.hypot(dx_sofar, dy_sofar)
            remaining = target_dist - dist_travelled

            if remaining < self.dist_tol:
                # Segment complete
                self.get_logger().info(
                    f'  ✓ {step["desc"]} — travelled {dist_travelled:.3f} m')
                self._advance_step()
                return

            # P control on remaining distance
            speed = self.linear_kp * remaining
            speed = max(-self.max_linear, min(self.max_linear, speed))
            # Clamp to a minimum so we don't stall
            if 0.0 < abs(speed) < 0.03:
                speed = 0.03 * (1.0 if speed > 0 else -1.0)
            twist.linear.x = speed

            # Heading correction while driving forward
            heading_err = normalize_angle(self._step_start_yaw - self.yaw)
            twist.angular.z = self.angular_kp * heading_err

        elif step['type'] == 'rotate':
            target_angle = step['angle']
            turned = normalize_angle(self.yaw - self._step_start_yaw)
            remaining = target_angle - turned
            remaining = normalize_angle(remaining)

            if abs(remaining) < self.angle_tol:
                self.get_logger().info(
                    f'  ✓ {step["desc"]} — turned {math.degrees(turned):.1f}°')
                self._advance_step()
                return

            speed = self.angular_kp * remaining
            speed = max(-self.max_angular, min(self.max_angular, speed))
            if 0.0 < abs(speed) < 0.06:
                speed = 0.06 * (1.0 if speed > 0 else -1.0)
            twist.angular.z = speed

        self.cmd_pub.publish(twist)

    def _advance_step(self):
        """Move to the next step; add a brief stop in between."""
        self.step_index += 1
        # Reset per‑step tracking (safe delete – may not exist on first call)
        for attr in ('_step_start_x', '_step_start_y', '_step_start_yaw'):
            try:
                delattr(self, attr)
            except AttributeError:
                pass
        # Short zero‑velocity pause for stability
        self.cmd_pub.publish(Twist())
        time.sleep(0.3)

    # -------------------------------------------------------------------
    # Public API called from main() after input()
    # -------------------------------------------------------------------
    def start_pattern(self):
        self.get_logger().info('Starting square pattern …')
        self.state = 'EXEC'


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = JetAutoSquareController(repeats=2)

    # Spin in a background thread so we can wait for user input
    import threading
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    # Wait until odometry is received, then prompt for start
    while rclpy.ok() and not node.odom_received:
        time.sleep(0.1)

    input('Press ENTER to start the square pattern …')
    node.start_pattern()

    # Keep alive until the node destroys itself
    try:
        while rclpy.ok() and node.state != 'DONE':
            time.sleep(0.2)
    except KeyboardInterrupt:
        node.get_logger().info('Interrupted by user.')

    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
