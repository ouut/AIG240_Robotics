#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

import sys
import termios
import tty

class Input(Node):
    def __init__(self):
        super().__init__('proj1_turtlesim')
        
        self.settings = termios.tcgetattr(sys.stdin)
        
        self.declare_parameter('turtle_name', 'turtle1')
        turtle_name = self.get_parameter('turtle_name').get_parameter_value().string_value
        
        self.pub = self.create_publisher(Twist, f'/{turtle_name}/cmd_vel', 10)
        
        self.get_logger().info(f"control: [{turtle_name}]")
        self.get_logger().info("press WASD to control，[Ctrl+C] cancel...")

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def run_loop(self):
        msg = Twist()
        lin_vel = 2.0
        ang_vel = 1.5

        while rclpy.ok():
            key = self.get_key()
            match key:
                case 'w':
                    msg.linear.x = lin_vel;  
                    msg.angular.z = 0.0
                case 's':
                    msg.linear.x = -lin_vel; 
                    msg.angular.z = 0.0
                case 'a':
                    msg.linear.x = 0.0;      
                    msg.angular.z = ang_vel
                case 'd':
                    msg.linear.x = 0.0;      
                    msg.angular.z = -ang_vel
                case ' ':
                    print(">stop", flush=True)
                    msg.linear.x = 0.0;      
                    msg.angular.z = 0.0
                case '\x03': # Ctrl+C
                    break
                case _:
                    msg.linear.x = 0.0;      msg.angular.z = 0.0
            self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = Input()
    try:
        node.run_loop()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, node.settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()