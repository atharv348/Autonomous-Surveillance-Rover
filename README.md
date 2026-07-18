# Autonomous Surveillance Rover

Rover system for autonomous waypoint navigation and surveillance in
diverse terrain, targeting resource-constrained edge hardware.

## Problem Statement
Build a rover capable of autonomous waypoint navigation across diverse
terrains, operating under highly constrained compute hardware.

## Packages
- `my_rover` - core rover control
- `my_rover_launch` - launch files
- `my_rover_package` - supporting package
- `rover_gcs` - ground control station
- `rover_navigation` - navigation stack

## Repo Structure
- `src/` - primary implementation (5 ROS 2 packages)
- `archive/rover_ws_early_attempt/` - earlier development iteration, kept for history
- `config/` - URDF, maps, RViz config, bringup scripts
- `docs/` - TF frame diagrams
- `media/` - screenshots, demo videos

## Notes
A recorded rosbag mission (~327MB) exists locally but isn't included here
due to GitHub's file size limits. Available on request or via Git LFS.

## Status
Work in progress.
