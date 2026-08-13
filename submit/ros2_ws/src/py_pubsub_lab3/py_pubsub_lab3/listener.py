#!/usr/bin/env python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class ListenerPyLab3(Node):
    def __init__(self):
        super().__init__('listener_py_lab3')

        self.subscription = self.create_subscription(
            String,
            "chatter",
            self.cb,
            10
        )

    def cb(self,msg):
        self.get_logger().info(f'f[py] I  heard:{msg.data}')

def main(args = None):
    rclpy.init(args=args)
    node = ListenerPyLab3()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()