# Internship Assessment — What I Built

**By Atharv Joshi**  
Stack: ROS 2 Humble (in Docker), Gazebo, Nav2, SLAM Toolbox, and plain Python for the last one.

📹 **Video Demonstration (Google Drive):**  
[Watch Video Demonstration](https://drive.google.com/drive/u/0/folders/1duk6e5Rs1KtrupEqTI7CTjME6bO1q5Mo)

A quick note on the setup: I ran everything inside a ROS 2 Humble Docker container on WSL2, since my fresh Ubuntu install was 26.04 and the packages I needed line up with Humble. GUI apps (Gazebo, RViz) forward to Windows through WSLg. Worked, but it's compute-limited, which shaped a few of my decisions below.

---

## Task 1 — Autonomous Navigation with Dynamic Obstacle Replanning

### What I was going for

Get the rover to drive itself to a goal, and if a new obstacle shows up in
its path partway there, notice it, replan, and still reach the goal — no
hand-holding.

### How I built it

I've got a differential-drive rover with a full sensor suite (LiDAR, camera,
IMU, GPS, ultrasonic) defined in URDF/Xacro, spawned into a Gazebo world with
some obstacles. Navigation is Nav2, and instead of feeding it a pre-made map
I run SLAM Toolbox live, so it maps and navigates at the same time. That felt
closer to the "diverse terrain" spirit of the problem — the robot doesn't get
to know the world ahead of time.

The flow is basically: Gazebo publishes the LiDAR scan and odometry, SLAM
Toolbox builds the map and fills in the `map -> odom -> base_link` transforms,
Nav2's planner lays down a global path, and the DWB controller drives it while
watching the local costmap for anything in the way. When I drop a new box in
front of the rover mid-drive, the LiDAR picks it up, it gets stamped into the
costmap, and Nav2 just quietly reroutes around it.

### Stuff I ran into (and fixed)

Honestly this task was mostly debugging, not writing new code:

- **The LiDAR wasn't publishing where Nav2 expected.** The robot's URDF had
  an old-style laser plugin config (`<topicName>`, `<frameName>` tags) that
  the modern `libgazebo_ros_ray_sensor` plugin just ignores — so it was
  silently dumping PointCloud2 on the wrong topic instead of LaserScan on
  `/scan`. Fixed the plugin block to use the `<ros><remapping>` +
  `<output_type>` format and suddenly SLAM and the costmaps could see.

- **A plugin-name typo in the Nav2 params** — behaviors were written as
  `nav2_behaviors::Spin` (C++ style) when pluginlib wanted
  `nav2_behaviors/Spin`. One character, but it aborted the whole
  behavior_server on startup.

- **Everything kept aborting with "failed to make progress."** Turned out the
  container couldn't hit the 20 Hz control loop, so Nav2 gave up. Dropped the
  controller to 5 Hz and the planner to 2 Hz and it ran fine. Not glamorous,
  but that's real embedded-ish constraint work.

- **A leftover reactive-avoidance node kept fighting Nav2** for control of
  `/cmd_vel` — it respawns every time Gazebo launches, so I got very used to
  `pkill`-ing it before every run.

### Where it landed

It works. Nav2's own logs say it plainly: `Reached the goal! / Goal
succeeded`. The rover drives to the target, and when I drop an obstacle in
its way it reroutes and still gets there.

---

## Task 2 — The `nav_monitor` Node

### What it needed to do

Write a ROS 2 node that watches whatever navigation is happening and prints
the current goal, how far's left, and the status — NAVIGATING, REPLANNING,
SUCCEEDED, or FAILED.

### How I did it

It's a small Python node that just listens — it never sends any commands, so
it can run alongside Nav2 without getting in the way. It subscribes to three
things:

- `/goal_pose` to grab the goal coordinates the moment I send one
- the `navigate_to_pose` action **feedback**, which hands me
  `distance_remaining` for free while the robot drives
- the action **status**, which I map to the four readable states

Then a 1-second timer just prints a tidy block.

The one bit I had to think about was REPLANNING — Nav2 doesn't hand you a
"replanning" status directly. So I infer it: if the remaining distance
suddenly jumps *up* (the path got longer because it rerouted around
something), I flag REPLANNING for a moment before it settles back to
NAVIGATING. Worked out nicely.

One small gotcha I found: if you start the monitor *after* sending the goal,
it misses the `/goal_pose` message and shows "(none)" for the coordinates.
Start it first, then send the goal, and everything shows up.

### Actual output from a run

```
New goal received: (2.60, 3.00)
------------------------------------------------
Current Goal:       (2.60, 3.00)
Remaining Distance: 0.20 m
Status:             NAVIGATING
------------------------------------------------
Current Goal:       (2.60, 3.00)
Remaining Distance: 0.00 m
Status:             SUCCEEDED
```

And from a longer run it also caught the full arc — IDLE, then NAVIGATING
with the distance ticking down from 1.77 m, brief REPLANNING flickers when it
rerouted, and finally SUCCEEDED at 0.00 m. All four states, exactly as asked.

---

## Task 3 — Cone Surface Toolpath for a 6-Axis Arm

### The task

Make a toolpath that runs along the surface of a cone, turn it into 6-axis
robot joint values, and export it as a CSV with time plus the six joints.

### My approach

This one's pure Python, no ROS needed, which was a nice change of pace.

I defined the cone parametrically — as you climb from base to apex, the radius
shrinks to zero and the height grows. If you sweep the angle around while
climbing, you trace a **helix** spiraling up the cone's surface. That's my
continuous toolpath: 300 points wrapping several times up the cone.

For the "6-axis" part, I needed a real arm to solve against, so I modeled a
**UR5** (standard 6-DOF arm) inline using `ikpy`. For each point on the
helix, I run inverse kinematics to get the six joint angles that put the tool
tip there. I warm-start each solve from the previous answer, so the joint
values flow smoothly instead of jumping around — makes it an actually
executable trajectory.

Then I write it all to CSV in the required `Time, Joint1...Joint6` format, and
also dump the raw cone points separately as reference geometry.

One honest note: I solved position-only IK, so the tool tip follows the
surface but I didn't constrain wrist orientation (Joint5/6 sit near zero).
For a surface-following path that's fine; if you needed the tool held
perpendicular to the surface you'd add an orientation constraint, but the task
didn't call for it.

### Actual output

Straight from the generated CSV:

```
Time,Joint1,Joint2,Joint3,Joint4,Joint5,Joint6
0.0,-0.199781,-0.435773,1.618336,2.014967,0.0,0.0
0.1,-0.166012,-0.439145,1.62372,2.012359,0.0,0.0
0.2,-0.133237,-0.444225,1.635224,2.00716,0.0,0.0
0.3,-0.101652,-0.450921,1.65269,1.999538,0.0,0.0
```

You can see the joints drifting smoothly point to point, which is exactly
what the warm-starting was for.

**Files it produces:**
- `cone_toolpath.py` — the script
- `cone_toolpath.csv` — 300 rows, time + 6 joints
- `cone_geometry.csv` — the cone surface points

---

## Wrap-up

All three are working. Task 1 and 2 run together in the same live stack — the
rover navigates and replans while `nav_monitor` reports what it's doing — and
Task 3 stands on its own as a Python script that spits out the CSV. Most of my
time honestly went into the Gazebo/Nav2 plumbing for Task 1; the monitor and
the cone toolpath came together pretty cleanly once that foundation worked.
