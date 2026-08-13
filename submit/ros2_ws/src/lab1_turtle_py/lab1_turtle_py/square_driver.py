import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SquareDriver(Node):
    def __init__(self):
        super().__init__('square_driver_py')
        # Publish to turtle1 by default (remap-able at runtime)
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Engineering constants (tune if needed)
        self.linear_speed = 1.0     # turtlesim units/s
        self.angular_speed = 1.57   # rad/s (~90 deg/s)
        self.forward_time = 2.0     # seconds
        self.turn_time = 1.0        # seconds

    def run_square(self):
        msg = Twist()
        time.sleep(1.0)  # let discovery settle

        for _ in range(4):
            # Forward
            msg.linear.x = self.linear_speed
            msg.angular.z = 0.0
            t_end = time.time() + self.forward_time
            while time.time() < t_end:
                self.pub.publish(msg)
                time.sleep(0.1)

            # Turn
            msg.linear.x = 0.0
            msg.angular.z = self.angular_speed
            t_end = time.time() + self.turn_time
            while time.time() < t_end:
                self.pub.publish(msg)
                time.sleep(0.1)

        # Stop
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = SquareDriver()
    node.run_square()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
