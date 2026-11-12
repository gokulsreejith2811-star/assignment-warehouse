import sys
import asyncio
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.action import GoalResponse, CancelResponse

from warehouse_interfaces.action import Deliver


# ===================================
# ACTION SERVER
# ===================================

class DeliveryServer(Node):

    def __init__(self):

        super().__init__('delivery_server')

        self.server = ActionServer(
            self,
            Deliver,
            '/deliver',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        self.get_logger().info("Delivery Action Server Started!")

    # Validate delivery goal
    def goal_callback(self, goal_request):

        if not goal_request.destination.strip():
            self.get_logger().warning("Rejected: Empty destination")
            return GoalResponse.REJECT

        if goal_request.distance <= 0:
            self.get_logger().warning("Rejected: Invalid distance")
            return GoalResponse.REJECT

        if goal_request.speed <= 0:
            self.get_logger().warning("Rejected: Invalid speed")
            return GoalResponse.REJECT

        self.get_logger().info(
            f"Delivery accepted: {goal_request.destination}"
        )

        return GoalResponse.ACCEPT

    # Handle cancellation
    def cancel_callback(self, goal_handle):

        self.get_logger().info("Cancellation requested!")

        return CancelResponse.ACCEPT

    # Execute delivery
    async def execute_callback(self, goal_handle):

        goal = goal_handle.request

        feedback = Deliver.Feedback()
        result = Deliver.Result()

        remaining = float(goal.distance)
        speed = float(goal.speed)

        start_time = time.monotonic()

        self.get_logger().info(
            f"Delivering to {goal.destination}"
        )

        while remaining > 0:

            if goal_handle.is_cancel_requested:

                goal_handle.canceled()

                result.success = False
                result.time_taken = time.monotonic() - start_time

                self.get_logger().warning("Delivery Cancelled!")

                return result

            await asyncio.sleep(0.5)

            remaining = max(0.0, remaining - speed * 0.5)

            feedback.remaining_distance = remaining

            feedback.percent = (
                (goal.distance - remaining) / goal.distance
            ) * 100.0

            goal_handle.publish_feedback(feedback)

            self.get_logger().info(
                f"Remaining: {remaining:.2f} m | "
                f"Progress: {feedback.percent:.1f}%"
            )

        goal_handle.succeed()

        result.success = True
        result.time_taken = time.monotonic() - start_time

        self.get_logger().info("Delivery Completed!")

        return result


# ===================================
# ACTION CLIENT
# ===================================

class DeliveryClient(Node):

    def __init__(self):

        super().__init__('delivery_client')

        self.client = ActionClient(
            self,
            Deliver,
            '/deliver'
        )

        self.goal_handle = None

    def send_goal(self, destination, distance, speed):

        self.get_logger().info("Waiting for action server...")

        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("Action server not available!")
            return None

        goal = Deliver.Goal()

        goal.destination = destination
        goal.distance = distance
        goal.speed = speed

        self.get_logger().info("Sending delivery request...")

        future = self.client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )

        rclpy.spin_until_future_complete(self, future)

        self.goal_handle = future.result()

        if self.goal_handle is None or not self.goal_handle.accepted:

            self.get_logger().error("Delivery goal rejected!")
            return None

        self.get_logger().info("Delivery goal accepted!")

        return self.goal_handle

    # Display feedback
    def feedback_callback(self, feedback_msg):

        feedback = feedback_msg.feedback

        self.get_logger().info(
            f"Remaining: {feedback.remaining_distance:.2f} m | "
            f"Progress: {feedback.percent:.1f}%"
        )

    # Wait for result
    def get_result(self):

        if self.goal_handle is None:
            return

        future = self.goal_handle.get_result_async()

        rclpy.spin_until_future_complete(self, future)

        result = future.result()

        if result is None:
            self.get_logger().error("Could not get delivery result!")
            return

        self.get_logger().info(
            f"Success: {result.result.success} | "
            f"Time: {result.result.time_taken:.2f} seconds | "
            f"Status: {result.status}"
        )

    # Cancel delivery
    def cancel_delivery(self):

        if self.goal_handle is None:
            self.get_logger().warning("No active delivery to cancel!")
            return

        future = self.goal_handle.cancel_goal_async()

        rclpy.spin_until_future_complete(self, future)

        self.get_logger().info("Cancellation request sent!")


# ===================================
# MAIN FUNCTIONS
# ===================================

def server_main(args=None):

    rclpy.init(args=args)

    node = DeliveryServer()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


def client_main(args=None):

    rclpy.init(args=args)

    node = DeliveryClient()

    try:

        destination = sys.argv[1] if len(sys.argv) > 1 else "Section_A"
        distance = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
        speed = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

        goal_handle = node.send_goal(
            destination,
            distance,
            speed
        )

        if goal_handle is not None:
            node.get_result()

    except KeyboardInterrupt:
        node.cancel_delivery()

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    server_main()
