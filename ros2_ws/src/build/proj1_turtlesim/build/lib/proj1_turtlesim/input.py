#!/usr/bin/env python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import sys
import termios
import tty
import select 


class Input(Node):
    def __init__(self):
        super().__init__('proj1_turtlesim')
        # ros2 run <package_name> <runable name> --ros-args -p turtle_name:=turtle2
        turtle_name = self.get_parameter('turtle_name').get_parameter_value().string_value
        self.pub = self.create_publisher(Twist, f'/{turtle_name}/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info(f"send Twist msg to [{turtle_name}]")

    def get_key_non_blocking(self):
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            if rlist:
                key = sys.stdin.read(1) 
            else:
                key = None 
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            return key

    def timer_callback(self):
        select_key = self.get_key_non_blocking()
        msg = Twist()
        match key:
            case 'w':
                self.get_logger().info("w")
                msg.linear.x = 2.0
            case 's':
                self.get_logger().info("s")
                msg.linear.x = -2.0
            case 'a':
                self.get_logger().info("a")
                msg.angular.z = 1.5
            case 'd':
                self.get_logger().info("d")
                msg.angular.z = -1.5
            case None:
                msg.linear.x = 0.0
                msg.angular.z = 0.0
                
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args = args)
    node = Input()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()   

if __name__ == "__main__":
    main()
