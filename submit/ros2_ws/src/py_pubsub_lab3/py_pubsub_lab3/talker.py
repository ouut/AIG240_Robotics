#!/usr/bin/env python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class TalkerPyLab3(Node):
    def __init__(self):
        super().__init__('talker_py_lab3')
        self.declare_parameter('publish_rate_hz', 5.0)
        publish_rate_hz = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        self.pub = self.create_publisher(String, "chatter",10)
        self.count = 0
        timer_period_sec = 1.0/publish_rate_hz
        self.timer = self.create_timer(timer_period_sec, self.timer_callback)

    def timer_callback(self):
        msg = String()
        msg.data = f"[py] lab3 hello #{self.count}"    
        self.get_logger().info(msg.data)
        self.pub.publish(msg)
        self.count += 1


def main(args=None):
    rclpy.init(args = args)
    node = TalkerPyLab3()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()   

if __name__ == "__main__":
    main()
