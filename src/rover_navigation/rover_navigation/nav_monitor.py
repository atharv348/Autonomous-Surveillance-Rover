#!/usr/bin/env python3
"""
Custom ROS 2 Navigation Monitoring Node (nav_monitor)

Author: Atharv Joshi
Platform: ROS 2 Humble
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatusArray, GoalStatus
from nav2_msgs.action import NavigateToPose

class NavMonitor(Node):
    def __init__(self):
        super().__init__('nav_monitor')
        
        self.current_goal = None
        self.distance_remaining = None
        self.prev_distance = None
        self.status_str = "IDLE"
        self.replanning_timer = 0
        
        # Subscriptions
        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )
        
        self.feedback_sub = self.create_subscription(
            NavigateToPose.Impl.FeedbackMessage,
            '/navigate_to_pose/_action/feedback',
            self.feedback_callback,
            10
        )
        
        self.status_sub = self.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self.status_callback,
            10
        )
        
        # 1 Hz Timer to print status block
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        self.get_logger().info("📡 NavMonitor Node initialized and listening...")

    def goal_callback(self, msg: PoseStamped):
        x = msg.pose.position.x
        y = msg.pose.position.y
        self.current_goal = (x, y)
        self.status_str = "NAVIGATING"
        print(f"\nNew goal received: ({x:.2f}, {y:.2f})")

    def feedback_callback(self, msg):
        feedback = msg.feedback
        dist = getattr(feedback, 'distance_remaining', None)
        if dist is not None:
            # Check for replanning heuristic: distance increases suddenly
            if self.prev_distance is not None and self.status_str in ["NAVIGATING", "REPLANNING"]:
                if dist > self.prev_distance + 0.15:
                    self.status_str = "REPLANNING"
                    self.replanning_timer = 2
                elif self.replanning_timer > 0:
                    self.replanning_timer -= 1
                    if self.replanning_timer == 0:
                        self.status_str = "NAVIGATING"
            self.prev_distance = dist
            self.distance_remaining = dist

    def status_callback(self, msg: GoalStatusArray):
        if not msg.status_list:
            return
        
        latest_status = msg.status_list[-1].status
        
        if latest_status in [GoalStatus.STATUS_EXECUTING, GoalStatus.STATUS_ACCEPTED]:
            if self.status_str != "REPLANNING":
                self.status_str = "NAVIGATING"
        elif latest_status == GoalStatus.STATUS_SUCCEEDED:
            self.status_str = "SUCCEEDED"
            self.distance_remaining = 0.00
        elif latest_status in [GoalStatus.STATUS_ABORTED, GoalStatus.STATUS_CANCELED]:
            self.status_str = "FAILED"

    def timer_callback(self):
        goal_str = f"({self.current_goal[0]:.2f}, {self.current_goal[1]:.2f})" if self.current_goal else "(none)"
        dist_str = f"{self.distance_remaining:.2f} m" if self.distance_remaining is not None else "N/A"
        
        print("------------------------------------------------")
        print(f"Current Goal:       {goal_str}")
        print(f"Remaining Distance: {dist_str}")
        print(f"Status:             {self.status_str}")

def main(args=None):
    rclpy.init(args=args)
    node = NavMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
