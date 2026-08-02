# Technical Documentation — Internship Assessment

Author: Atharv Joshi
Platform: ROS 2 Humble (Docker), Gazebo Classic, Nav2, SLAM Toolbox

---

# Task 1 — Autonomous Navigation with Dynamic Obstacle Replanning

## Approach

A custom differential-drive rover was configured with a simulated sensor
suite (LiDAR, camera, IMU, GPS, ultrasonic) defined via URDF/Xacro, spawned
into a Gazebo world containing static obstacles. Autonomous navigation is
handled by the ROS 2 Navigation Stack (Nav2), with live mapping provided by
SLAM Toolbox in asynchronous online mode.

## Pipeline

1. **Simulation** — Gazebo publishes LiDAR scans on `/scan` and wheel
   odometry on `/odom`, with the `map -> odom -> base_link` transform tree
   completed by SLAM Toolbox and the differential-drive plugin.
2. **Mapping** — SLAM Toolbox builds a live occupancy grid from LiDAR as the
   robot explores, publishing the `map` frame and `/map` topic.
3. **Navigation** — Nav2's planner (NavFn/GridBased) computes a global path
   over the global costmap; the DWB controller follows it using the local
   costmap for immediate obstacle avoidance.
4. **Dynamic replanning** — When a new obstacle is introduced into the
   robot's path at runtime (spawned live in Gazebo), the LiDAR detects it,
   the obstacle layer marks it into both costmaps, and Nav2 automatically
   recomputes a valid path around it — with no manual intervention.

## Key implementation decisions

- **SLAM instead of pre-built map + AMCL** — chosen so the system maps and
  navigates unknown terrain simultaneously, matching the "diverse terrain"
  problem statement.
- **Controller frequency tuning** — reduced from 20 Hz to 5 Hz and planner
  from 20 Hz to 2 Hz to run reliably on constrained compute (containerised
  environment), preventing control-loop starvation and goal aborts.
- **LiDAR plugin fix** — the sensor plugin was corrected to publish
  `sensor_msgs/LaserScan` on `/scan` (using the modern
  `libgazebo_ros_ray_sensor` remapping), which the costmaps require.
- **Larger local costmap (5x5 m)** — gives the controller room to plan a
  detour once a new obstacle is detected.

## Result

The rover autonomously plans and follows a path to a commanded goal,
detects obstacles introduced mid-navigation, updates its costmap, replans,
and reaches the goal. Confirmed by Nav2 logs (`Reached the goal! / Goal
succeeded`).

---

# Task 2 — Custom ROS 2 Navigation Monitoring Node (`nav_monitor`)

## Approach

A standalone ROS 2 Python node that observes the Nav2 navigation action and
reports live status, without interfering with navigation itself.

## Implementation

The node subscribes to three sources:

1. **`/goal_pose`** (`PoseStamped`) — captures the target position (x, y)
   the moment a goal is issued.
2. **`/navigate_to_pose/_action/feedback`** — Nav2's action feedback, which
   provides `distance_remaining` live while the robot drives.
3. **`/navigate_to_pose/_action/status`** — the action goal-status array,
   mapped to human-readable states.

A 1 Hz timer prints a clean status block:

```
Current Goal:       (x, y)
Remaining Distance: D m
Status:             NAVIGATING / REPLANNING / SUCCEEDED / FAILED
```

## Status logic

- `STATUS_EXECUTING / ACCEPTED` -> **NAVIGATING**
- `STATUS_SUCCEEDED` -> **SUCCEEDED** (distance forced to 0.00)
- `STATUS_ABORTED / CANCELED` -> **FAILED**
- **REPLANNING** is inferred: when `distance_remaining` suddenly increases
  (the path got longer because Nav2 re-routed around a new obstacle), the
  node reports REPLANNING briefly before returning to NAVIGATING.

## Key decisions

- **Read-only design** — the monitor only subscribes; it never publishes to
  `/cmd_vel` or interferes with Nav2, so it is safe to run alongside live
  navigation.
- **Warm-start goal capture** — starting the monitor before issuing the goal
  ensures the `/goal_pose` message is captured so coordinates display.

## Result

Verified live: the node reports IDLE -> NAVIGATING -> (REPLANNING) ->
SUCCEEDED with the correct goal coordinates and a decreasing distance,
matching Nav2's own success logs. It also reports FAILED correctly when a
goal is unreachable.

---

# Task 3 — 6-Axis Robot Toolpath Generation for a Cone Surface

## Approach

Generate a continuous toolpath that spirals up the surface of a cone,
convert each Cartesian point into 6-axis robot joint coordinates using
inverse kinematics, and export the trajectory to CSV.

## Method

1. **Cone geometry (parametric)** — the cone stands on its base with the
   apex up. At height fraction `f` (0 at base, 1 at apex), the radius is
   `R * (1 - f)` and the height is `H * f`. Sweeping the angle while climbing
   produces a helix that wraps `NUM_TURNS` times up the surface. This gives a
   continuous, evenly-distributed path over the cone.

2. **Path generation** — 300 points are sampled along the helix, each a
   Cartesian `(x, y, z)` tool-tip position on the cone surface, offset to the
   cone's location in the robot's workspace.

3. **Inverse kinematics** — a standard 6-DOF UR5 arm is modelled inline
   (link translations/orientations/axes) using `ikpy`. For each Cartesian
   point, `chain.inverse_kinematics()` solves the six joint angles that place
   the tool tip there. Each solve is warm-started from the previous solution,
   producing a smooth, continuous joint trajectory.

4. **CSV export** — each point is written as a timestamped row:
   `Time, Joint1, Joint2, Joint3, Joint4, Joint5, Joint6`, with time
   incrementing by a fixed step. The cone surface points are also saved
   separately as reference geometry.

## Key decisions

- **UR5 as the 6-axis model** — a well-documented, widely-used 6-DOF arm;
  the task permits any available 6-axis robot.
- **Position-based IK** — the tool tip tracks the surface path; wrist
  orientation is left free (Joint5/6 near zero), which is sufficient for a
  surface-following toolpath. Full surface-normal orientation could be added
  by constraining `target_orientation` if perpendicular tool contact were
  required.
- **Warm-starting** — passing the previous solution as the initial guess
  keeps consecutive joint values continuous (no sudden jumps), giving a
  physically realistic, executable trajectory.

## Deliverables produced

- `cone_toolpath.py` — the generation script
- `cone_toolpath.csv` — Time + 6 joint values (300 rows)
- `cone_geometry.csv` — the cone surface reference points

## Result

A continuous, smooth 300-point 6-axis joint trajectory following a helical
path over the cone surface, exported in the required CSV format.
