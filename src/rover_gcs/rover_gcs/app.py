from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan, Image, Imu, NavSatFix, Range
from std_msgs.msg import String
from ai_vision import AIVision
import threading
import json
from datetime import datetime
import pymysql
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lunar_rover_secret_2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class RoverROSBridge(Node):
    def __init__(self, socketio_instance):
        super().__init__('rover_ros_bridge')
        self.socketio = socketio_instance
        
        try:
            from cv_bridge import CvBridge
            import cv2
            import base64
            self.bridge = CvBridge()
            self.cv2 = cv2
            self.base64 = base64
            self.camera_enabled = True
        except ImportError:
            print("⚠️ cv_bridge not available")
            self.camera_enabled = False
        
        try:
            self.ai_vision = AIVision()
            self.ai_enabled = True
            self.get_logger().info('🤖 AI Vision initialized')
        except Exception as e:
            self.get_logger().warning(f'⚠️ AI Vision disabled: {e}')
            self.ai_vision = None
            self.ai_enabled = False
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_pub = self.create_publisher(String, '/rover_mode', 10)
        
        # Subscribers
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.gps_sub = self.create_subscription(NavSatFix, '/gps/fix', self.gps_callback, 10)
        
        # Ultrasonic sensors
        self.ultra_front_sub = self.create_subscription(Range, '/ultrasonic_front', 
                                                         lambda msg: self.ultrasonic_callback(msg, 'front'), 10)
        self.ultra_back_sub = self.create_subscription(Range, '/ultrasonic_back', 
                                                        lambda msg: self.ultrasonic_callback(msg, 'back'), 10)
        self.ultra_left_sub = self.create_subscription(Range, '/ultrasonic_left', 
                                                        lambda msg: self.ultrasonic_callback(msg, 'left'), 10)
        self.ultra_right_sub = self.create_subscription(Range, '/ultrasonic_right', 
                                                         lambda msg: self.ultrasonic_callback(msg, 'right'), 10)
        
        if self.camera_enabled:
            self.camera_sub = self.create_subscription(Image, '/front_camera/image_raw', 
                                                       self.camera_callback, 10)
        
        # Data storage
        self.current_odom = {'position': {'x': 0, 'y': 0, 'z': 0}, 
                             'velocity': {'linear': 0, 'angular': 0}}
        self.current_imu = {'orientation': {'roll': 0, 'pitch': 0, 'yaw': 0},
                            'angular_velocity': {'x': 0, 'y': 0, 'z': 0},
                            'linear_acceleration': {'x': 0, 'y': 0, 'z': 0}}
        self.gps_data = {'latitude': 0.0, 'longitude': 0.0, 'altitude': 0.0, 'status': -1}
        self.ultrasonic_data = {'front': 0, 'back': 0, 'left': 0, 'right': 0}
        
        # Create timer for periodic data transmission
        self.create_timer(0.1, self.timer_callback)
        
        self.get_logger().info('✅ ROS Bridge initialized with all sensors')
    
    def timer_callback(self):
        """Send cached data periodically"""
        self.socketio.emit('odom_update', self.current_odom)
        self.socketio.emit('imu_update', self.current_imu)
        self.socketio.emit('gps_update', self.gps_data)
        self.socketio.emit('ultrasonic_update', self.ultrasonic_data)
    
    def odom_callback(self, msg):
        self.current_odom = {
            'position': {
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'z': msg.pose.pose.position.z
            },
            'velocity': {
                'linear': msg.twist.twist.linear.x,
                'angular': msg.twist.twist.angular.z
            }
        }
    
    def scan_callback(self, msg):
        scan_data = {
            'range_min': msg.range_min,
            'range_max': msg.range_max,
            'ranges': list(msg.ranges[::10])
        }
        self.socketio.emit('scan_update', scan_data)
    
    def imu_callback(self, msg):
        x, y, z, w = msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w
        
        # Convert quaternion to Euler angles
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        sinp = 2 * (w * y - z * x)
        pitch = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(math.pi / 2, sinp)
        
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.current_imu = {
            'orientation': {
                'roll': math.degrees(roll),
                'pitch': math.degrees(pitch),
                'yaw': math.degrees(yaw)
            },
            'angular_velocity': {
                'x': msg.angular_velocity.x,
                'y': msg.angular_velocity.y,
                'z': msg.angular_velocity.z
            },
            'linear_acceleration': {
                'x': msg.linear_acceleration.x,
                'y': msg.linear_acceleration.y,
                'z': msg.linear_acceleration.z
            }
        }
    
    def gps_callback(self, msg):
        self.gps_data = {
            'latitude': msg.latitude,
            'longitude': msg.longitude,
            'altitude': msg.altitude,
            'status': msg.status.status
        }
    
    def ultrasonic_callback(self, msg, position):
        """Handle ultrasonic sensor data"""
        self.ultrasonic_data[position] = msg.range * 100  # Convert to cm
    
    def camera_callback(self, msg):
        if not self.camera_enabled:
            return
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            cv_image = self.cv2.resize(cv_image, (640, 480))
            
            detections = []
            if self.ai_enabled and self.ai_vision:
                cv_image, detections = self.ai_vision.process_frame(cv_image)
            
            _, buffer = self.cv2.imencode('.jpg', cv_image, [self.cv2.IMWRITE_JPEG_QUALITY, 80])
            jpg_as_text = self.base64.b64encode(buffer).decode('utf-8')
            
            self.socketio.emit('camera_frame', {'image': jpg_as_text, 'detections': detections})
        except Exception as e:
            self.get_logger().error(f'Camera error: {e}')
    
    def send_velocity_command(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_vel_pub.publish(msg)
        self.get_logger().info(f'Command: linear={linear}, angular={angular}')
    
    def publish_mode(self, mode):
        """Publish mode change to ROS2 topic"""
        msg = String()
        msg.data = mode
        self.mode_pub.publish(msg)
        self.get_logger().info(f'Mode changed to: {mode}')
    
    def stop_rover(self):
        self.send_velocity_command(0.0, 0.0)

class RoverDatabase:
    def __init__(self):
        try:
            self.connection = pymysql.connect(
                host='localhost',
                user='rover_user',
                password='rover_password',
                database='rover_db',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ Database connected")
        except Exception as e:
            print(f"⚠️ Database failed: {e}")
            self.connection = None
    
    def close(self):
        if self.connection:
            self.connection.close()

ros_bridge = None
db = None
executor = None

def init_ros():
    global ros_bridge, executor
    try:
        rclpy.init()
        ros_bridge = RoverROSBridge(socketio)
        executor = MultiThreadedExecutor()
        executor.add_node(ros_bridge)
        
        ros_thread = threading.Thread(target=executor.spin, daemon=True)
        ros_thread.start()
        print("✅ ROS Bridge initialized")
    except Exception as e:
        print(f"❌ ROS init failed: {e}")

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'ros_connected': ros_bridge is not None,
        'db_connected': db is not None and db.connection is not None,
        'camera_enabled': ros_bridge.camera_enabled if ros_bridge else False,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')

@socketio.on('control_command')
def handle_control_command(data):
    if not ros_bridge:
        emit('command_error', {'error': 'ROS bridge not initialized'})
        return
    
    command = data.get('command')
    if command == 'forward':
        ros_bridge.send_velocity_command(0.5, 0.0)
    elif command == 'backward':
        ros_bridge.send_velocity_command(-0.5, 0.0)
    elif command == 'left':
        ros_bridge.send_velocity_command(0.0, 0.5)
    elif command == 'right':
        ros_bridge.send_velocity_command(0.0, -0.5)
    elif command == 'stop':
        ros_bridge.stop_rover()
    
    emit('command_ack', {'command': command, 'status': 'executed'})
    print(f"✅ Command: {command}")

@socketio.on('mode_change')
def handle_mode_change(data):
    if not ros_bridge:
        emit('mode_error', {'error': 'ROS bridge not initialized'})
        return
    
    mode = data.get('mode', 'autonomous')
    ros_bridge.publish_mode(mode)
    emit('mode_ack', {'mode': mode, 'status': 'changed'})
    print(f"✅ Mode changed to: {mode}")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 LUNAR ROVER GROUND CONTROL STATION")
    print("="*50)
    
    print("\n📊 Initializing database...")
    db = RoverDatabase()
    
    print("\n🤖 Initializing ROS 2 bridge...")
    init_ros()
    
    print("\n" + "="*50)
    print("✅ Ground Control Station Ready!")
    print("🌐 Access at: http://localhost:5000")
    print("="*50 + "\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
        if ros_bridge:
            rclpy.shutdown()
        if db:
            db.close()
