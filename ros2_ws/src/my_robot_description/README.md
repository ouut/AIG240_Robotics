# ROS2 Jazzy 仿真工作空间

基于 **Robostack Jazzy** (conda) + **Gazebo Sim (Harmonic 8)** 的仿真环境。

## 环境

| 组件 | 版本 |
|------|------|
| ROS2 | Jazzy |
| Gazebo | Sim 8.10 (Harmonic) |
| 仿真桥接 | ros_gz_sim / ros_gz_bridge |
| 平台 | macOS ARM64 |

## 环境安装

```bash
conda env create -f /Users/cc/containers/jupyter_dev/environment.ros2.yml
```

## 快速开始

```bash
cd /Users/cc/containers/jupyter_dev/data/AIG240_Robotics/ros2_ws/src/my_robot_description

# 第一次构建
./run.sh build

# 验证 URDF 结构
./run.sh check

# 完整测试（URDF → publisher → topic → TF）
./run.sh test
```

## run.sh 命令一览

```bash
./run.sh build     # 构建工作空间（--symlink-install，之后改文件无需重编译）
./run.sh check     # 验证 URDF 结构
./run.sh viz       # 启动 RViz2 可视化（无仿真，看模型用）
./run.sh sim       # 启动 Gazebo Sim 仿真（物理引擎 + 控制）
./run.sh all       # 仿真 + RViz 同时启动
./run.sh test      # 全链路测试
./run.sh clean     # 清理所有残留 ROS2/ Gazebo 进程
```

## 仿真验证流程

### 1. 启动仿真

```bash
./run.sh sim
```

启动后日志关键行：
```
✅ robot_state_publisher  → Robot initialized
✅ Entity creation successful  → 机器人已生成
✅ Creating ROS->GZ Bridge /cmd_vel
✅ Creating GZ->ROS Bridge /model/my_robot/odometry
```

### 2. 控制机器人

#### 键盘遥控（推荐）

```bash
conda activate ros2
. install/setup.sh
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

操控：

```
        i      前进（加速）
   j    k    l
   左转  急停  右转

   u  i  o    左上 + 前进 + 右上
   j  k  l    左转 + 急停 + 右转
   m  ,  .    左下 + 后退 + 右下

按键说明：
  i  前进    u  左前    o  右前
  j  左转    k  停止    l  右转
  ,  后退    m  左后    .  右后
  q/z  加速/减速（每次 ±10%）
  w/x  角速度加减
  Ctrl+C  退出
```

> **注意**：Gazebo Sim 有 ~1 秒的超时机制，必须持续发送指令（按住键不放），不能用 `-1` 单发。

#### 手动发指令

```bash
# ❌ 只发一次，机器人走一秒就停
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}" -1

# ✅ 持续发送，机器人一直走
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}" -r 10
```

### 3. 验证运动

```bash
# 看 odometry 数据（位置应该在变化）
ros2 topic echo /model/my_robot/odometry --once

# 看模型在 Gazebo 里的位姿
gz model -m my_robot -p

# 监听 joint 状态
ros2 topic echo /joint_states
```

### 4. RViz 监视（可选）

Gazebo GUI 在 macOS 上 OGRE 渲染可能有问题，可同时开 RViz2 监视：

```bash
conda activate ros2
. install/setup.sh

# 启动 RViz2
ros2 launch my_robot_description visualize.launch.py

# 或在另一个终端
rviz2 -f base_link
```

RViz2 中添加：
- **Odometry** → topic: `/model/my_robot/odometry`
- **TF** → 查看坐标系树
- **RobotModel** → topic: `/robot_description`

## 机器人模型

```
base_link ──┬── left_wheel_joint  → left_wheel   (差速驱动)
            ├── right_wheel_joint → right_wheel  (差速驱动)
            └── laser_joint       → laser_link   (固定)

Gazebo 插件:
  - gz::sim::systems::DiffDrive  (gz-sim-diff-drive-system)
  - gpu_lidar sensor
```

## Topic 对照（ROS ↔ Gazebo）

| ROS Topic | Gazebo Topic | 方向 | 说明 |
|------|------|:---:|------|
| `/cmd_vel` | `/model/my_robot/cmd_vel` | → | 速度控制 |
| `/model/my_robot/odometry` | `/model/my_robot/odometry` | ← | 里程计 |
| `/robot_description` | — | — | URDF 字符串 |
| `/tf` / `/tf_static` | `/model/my_robot/tf` | — | TF 变换 |

## 已知问题

- **macOS DDS 警告** — `Problem to set affinity of thread` 红字，CycloneDDS 在 macOS 上的无害警告，忽略
- **Gazebo GUI 黑屏** — macOS ARM64 上 OGRE-Next 渲染异常，物理仿真不受影响，可用 RViz2 代替可视化
- **Gazebo Server + GUI 需分开启动** — macOS 已知 bug，launch 文件已自动处理

## 目录结构

```
ros2_ws/
├── README.md
├── src/
│   └── my_robot_description/       # 机器人描述包
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── run.sh                  # 一键脚本
│       ├── urdf/
│       │   └── my_robot.urdf.xacro
│       └── launch/
│           ├── simulate.launch.py   # Gazebo 仿真
│           └── visualize.launch.py  # RViz 可视化
├── build/
├── install/
└── log/
```
