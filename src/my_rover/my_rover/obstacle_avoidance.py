#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import numpy as np

class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')
        
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/avoidance_status', 10)
        
        self.safe_distance = 1.2
        self.linear_speed = 0.3
        self.angular_speed = 0.8
        self.autonomous_mode = True
        
        self.create_timer(0.1, self.control_loop)
        self.latest_scan = None
        
        self.get_logger().info('✅ Obstacle Avoidance Active')
    
    def scan_callback(self, msg):
        self.latest_scan = msg
    
    def control_loop(self):
        if not self.autonomous_mode or self.latest_scan is None:
            return
            
        msg = self.latest_scan
        ranges = np.array(msg.ranges)
        ranges = np.where((ranges > msg.range_min) & (ranges < msg.range_max), ranges, np.inf)
        
        third = len(ranges) // 3
        min_front = np.min(ranges[third:2*third])
        min_left = np.min(ranges[:third])
        min_right = np.min(ranges[2*third:])
        
        twist = Twist()
        
        if min_front < self.safe_distance:
            self.get_logger().info(f'🚨 OBSTACLE: {min_front:.2f}m')
            twist.linear.x = 0.0
            
            if min_left > min_right:
                twist.angular.z = self.angular_speed
                self.get_logger().info('⬅️ TURNING LEFT')
            else:
                twist.angular.z = -self.angular_speed
                self.get_logger().info('➡️ TURNING RIGHT')
        else:
            twist.linear.x = self.linear_speed
            twist.angular.z = 0.0
        
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
