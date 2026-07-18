#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus, Range
from std_msgs.msg import Header
import math
import random

class SensorSimulator(Node):
    def __init__(self):
        super().__init__('sensor_simulator')
        
        # Publishers
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/gps/fix', 10)
        self.ultrasonic_pubs = {
            'front': self.create_publisher(Range, '/ultrasonic_front', 10),
            'back': self.create_publisher(Range, '/ultrasonic_back', 10),
            'left': self.create_publisher(Range, '/ultrasonic_left', 10),
            'right': self.create_publisher(Range, '/ultrasonic_right', 10)
        }
        
        # Timer for publishing sensor data at 10Hz
        self.create_timer(0.1, self.publish_sensors)
        self.get_logger().info('✅ Sensor Simulator Started')
    
    def publish_sensors(self):
        # Publish IMU data
        imu_msg = Imu()
        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'imu_link'
        imu_msg.orientation.w = 1.0
        imu_msg.linear_acceleration.x = random.uniform(-0.1, 0.1)
        imu_msg.linear_acceleration.y = random.uniform(-0.1, 0.1)
        imu_msg.linear_acceleration.z = 9.81 + random.uniform(-0.1, 0.1)
        imu_msg.angular_velocity.x = random.uniform(-0.05, 0.05)
        imu_msg.angular_velocity.y = random.uniform(-0.05, 0.05)
        imu_msg.angular_velocity.z = random.uniform(-0.05, 0.05)
        self.imu_pub.publish(imu_msg)
        
        # Publish GPS data
        gps_msg = NavSatFix()
        gps_msg.header.stamp = self.get_clock().now().to_msg()
        gps_msg.header.frame_id = 'gps_link'
        gps_msg.latitude = 19.0760 + random.uniform(-0.0001, 0.0001)
        gps_msg.longitude = 72.8777 + random.uniform(-0.0001, 0.0001)
        gps_msg.altitude = 10.0 + random.uniform(-0.5, 0.5)
        gps_msg.status.status = NavSatStatus.STATUS_FIX
        gps_msg.status.service = NavSatStatus.SERVICE_GPS
        self.gps_pub.publish(gps_msg)
        
        # Publish Ultrasonic data
        for direction, pub in self.ultrasonic_pubs.items():
            range_msg = Range()
            range_msg.header.stamp = self.get_clock().now().to_msg()
            range_msg.header.frame_id = f'ultrasonic_{direction}'
            range_msg.radiation_type = Range.ULTRASOUND
            range_msg.field_of_view = 0.26  # ~15 degrees
            range_msg.min_range = 0.02  # 2cm
            range_msg.max_range = 4.0   # 4m
            range_msg.range = random.uniform(0.5, 4.0)
            pub.publish(range_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SensorSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
