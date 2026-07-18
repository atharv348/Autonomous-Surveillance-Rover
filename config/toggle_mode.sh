#!/bin/bash

echo "=================================================="
echo "🤖 ROVER MODE CONTROL"
echo "=================================================="
echo ""
echo "Select mode:"
echo "  1) Autonomous (Auto-avoid obstacles)"
echo "  2) Manual (Arrow key control)"
echo ""
read -p "Enter choice (1 or 2): " choice

source ~/ros2_ws/install/setup.bash

if [ "$choice" = "1" ]; then
    echo "🤖 Switching to AUTONOMOUS mode..."
    ros2 topic pub -1 /rover_mode std_msgs/msg/String "{data: 'autonomous'}"
    echo "✅ Rover will now avoid obstacles automatically!"
elif [ "$choice" = "2" ]; then
    echo "🎮 Switching to MANUAL mode..."
    ros2 topic pub -1 /rover_mode std_msgs/msg/String "{data: 'manual'}"
    echo "✅ Use arrow keys to control rover!"
else
    echo "❌ Invalid choice"
fi
