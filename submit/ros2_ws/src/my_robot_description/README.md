# ROS2 Jazzy Simulation Workspace

**Robostack Jazzy** (conda) + **Gazebo Sim (Harmonic 8)** simulation environment.

## Environment

| Component | Version |
|------|------|
| ROS2 | Jazzy |
| Gazebo | Sim 8.10 (Harmonic) |
| Bridge | ros_gz_sim / ros_gz_bridge |
| Platform | macOS ARM64 |

## Setup

```bash
conda env create -f /Users/cc/containers/jupyter_dev/environment.ros2.yml
```

## Quick Start

```bash
cd /Users/cc/containers/jupyter_dev/data/AIG240_Robotics/ros2_ws/src/my_robot_description

# First-time build
./run.sh build

# Validate URDF
./run.sh check

# Full test (URDF → publisher → topics → TF)
./run.sh test
```

## run.sh Commands

```bash
./run.sh build     # Build workspace (--symlink-install, no rebuild needed for edits)
./run.sh check     # Validate URDF structure
./run.sh viz       # Launch RViz2 (no simulation)
./run.sh sim       # Launch Gazebo Sim (physics + control)
./run.sh all       # Launch sim + RViz together
./run.sh test      # Full test pipeline
./run.sh clean     # Kill all leftover ROS2/Gazebo processes
```

## Simulation Workflow

### 1. Start Simulation

```bash
./run.sh sim
```

Key log lines:
```
✅ robot_state_publisher  → Robot initialized
✅ Entity creation successful  → Robot spawned
✅ Creating ROS->GZ Bridge /cmd_vel
✅ Creating GZ->ROS Bridge /model/my_robot/odometry
```

### 2. Control the Robot

#### Keyboard Teleop (recommended)

```bash
conda activate ros2
. install/setup.sh
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Controls:

```
        i      Forward
   j    k    l
  Left  Stop  Right

   u  i  o    Fwd-Left + Forward + Fwd-Right
   j  k  l    Left    + Stop    + Right
   m  ,  .    Back-Left + Back + Back-Right

Key map:
  i  Forward       u  Fwd-Left       o  Fwd-Right
  j  Left          k  Stop           l  Right
  ,  Back          m  Back-Left      .  Back-Right
  q/z  Increase/Decrease linear speed  (±10%)
  w/x  Increase/Decrease angular speed
  Ctrl+C  Quit
```

> **Important**: Gazebo Sim has a ~1s timeout. You must continuously send commands (hold keys down). Do NOT use single-shot `-1`.

#### Manual Commands

```bash
# ❌ Single shot — robot stops after ~1s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}" -1

# ✅ Continuous — robot keeps moving
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}" -r 10
```

### 3. Verify Motion

```bash
# Check odometry data (position should be changing)
ros2 topic echo /model/my_robot/odometry --once

# Check model pose in Gazebo
gz model -m my_robot -p

# Monitor joint states
ros2 topic echo /joint_states
```

### 4. RViz Monitoring (optional)

Gazebo GUI may have rendering issues on macOS. Use RViz2 as alternative:

```bash
conda activate ros2
. install/setup.sh

# Launch RViz2
ros2 launch my_robot_description visualize.launch.py

# Or directly
rviz2 -f base_link
```

In RViz2, add:
- **Odometry** → topic: `/model/my_robot/odometry`
- **TF** → view coordinate tree
- **RobotModel** → topic: `/robot_description`

## Robot Model

```
base_link ──┬── left_wheel_joint  → left_wheel   (differential drive)
            ├── right_wheel_joint → right_wheel  (differential drive)
            └── laser_joint       → laser_link   (fixed)

Gazebo plugins:
  - gz::sim::systems::DiffDrive  (gz-sim-diff-drive-system)
  - gpu_lidar sensor
```

## Topic Map (ROS ↔ Gazebo)

| ROS Topic | Gazebo Topic | Dir | Description |
|------|------|:---:|------|
| `/cmd_vel` | `/cmd_vel` (model scoped) | → | Velocity command |
| `/model/my_robot/odometry` | `/model/my_robot/odometry` | ← | Odometry feedback |
| `/robot_description` | — | — | URDF string |
| `/tf` / `/tf_static` | `/model/my_robot/tf` | — | TF transforms |

## Known Issues

- **DDS thread affinity errors** — macOS harmless warnings, ignore
- **Gazebo GUI black screen** — macOS ARM64 OGRE-Next rendering issue; physics unaffected, use RViz2 instead
- **Server + GUI must run separately** — macOS known bug, launch file handles this automatically

## Directory Structure

```
ros2_ws/
├── README.md
├── src/
│   └── my_robot_description/       # Robot description package
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── run.sh                  # One-click launcher
│       ├── urdf/
│       │   └── my_robot.urdf.xacro
│       └── launch/
│           ├── simulate.launch.py   # Gazebo simulation
│           └── visualize.launch.py  # RViz visualization
├── build/
├── install/
└── log/
```
