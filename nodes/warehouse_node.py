import rclpy
from rclpy.node import Node

from warehouse_interfaces.msg import DeliveryStatus
from warehouse_interfaces.srv import LoadPackage


class WarehouseNode(Node):

    def __init__(self):
        super().__init__('warehouse_node')

        # Robot variables
        self.robot_id = "ROBOT_01"
        self.package_count = 0
        self.battery = 100.0

        # Publisher
        self.publisher = self.create_publisher(
            DeliveryStatus,
            '/delivery_status',
            10
        )

        # Service
        self.service = self.create_service(
            LoadPackage,
            '/load_package',
            self.load_package_callback
        )

        # Timer: publish every second
        self.timer = self.create_timer(
            1.0,
            self.publish_status
        )

        self.get_logger().info("Warehouse Node Started!")

    # Publish robot status
    def publish_status(self):

        msg = DeliveryStatus()

        msg.robot_id = self.robot_id
        msg.package_count = self.package_count
        msg.battery = self.battery
        msg.state = DeliveryStatus.STATE_IDLE

        self.publisher.publish(msg)

        self.get_logger().info(
            f"Robot: {msg.robot_id} | "
            f"Packages: {msg.package_count} | "
            f"Battery: {msg.battery}% | "
            f"State: IDLE"
        )

    # Handle package requests
    def load_package_callback(self, request, response):

        if request.weight < 0:

            response.accepted = False
            response.message = "Invalid package weight"

        elif request.weight > 10.0:

            response.accepted = False
            response.message = "Package exceeds 10 kg limit"

        elif self.package_count >= 5:

            response.accepted = False
            response.message = "Robot capacity is full"

        else:

            self.package_count += 1

            response.accepted = True
            response.message = (
                f"Package {request.package_id} loaded successfully"
            )

        response.total_packages = self.package_count

        self.get_logger().info(response.message)

        return response


def main(args=None):

    rclpy.init(args=args)

    node = WarehouseNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
