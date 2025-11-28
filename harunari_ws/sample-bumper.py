import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
#from harunari_interfaces.msg import HarunariStatus

class Bumper(Node):
    def __init__(self):
        super().__init__('bumper_node')
        self.stop_sub =self.create_subscription(Bool,'/stop', self.stop_callback(), 10)

    def stop_callback(self, msg: Bool):
        relpy.init(args=args)
        rclpy.spin(Node)
        node.destroy_node()
        relpy.shutdown()


if __name__ == "__main__":
    main()