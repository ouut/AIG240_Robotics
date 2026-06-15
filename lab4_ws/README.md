# Lab4 Workspace — ROS2 + Gazebo 仿真

基于 **Robostack** (conda) 的 ROS2 Humble + Gazebo 11 仿真工作空间。

## 环境要求

- macOS / Linux
- conda 环境 `ros2`（Robostack 安装）
- ROS2 Humble
- Gazebo 11 (Classic)

## 快速开始

```bash
# 1. 激活 ROS2 环境
conda activate ros2

# 2. Source 工作空间
. install/setup.sh

# 3. 启动仿真
ros2 launch my_robot_description simulate.launch.py
```

## 构建

```bash
conda activate ros2
colcon build --packages-select my_robot_description
. install/setup.sh
```

## 验证 URDF

URDF = **U**nified **R**obot **D**escription **F**ormat，是一个 XML 文件，描述机器人的物理结构（link / joint / 惯性 / 碰撞 / 外观）。

构建前验证模型结构是否正确：

```bash
# xacro 宏展开为纯 URDF，再用 check_urdf 检查 link/joint 连接树
ros2 run xacro xacro src/my_robot_description/urdf/my_robot.urdf.xacro > /tmp/my_robot.urdf
check_urdf /tmp/my_robot.urdf
```

输出示例：
```
robot name is: my_robot
root Link: base_link has 3 child(ren)
    child(1):  laser_link
    child(2):  left_wheel
    child(3):  right_wheel
```

## RViz 可视化（无仿真，调试用）

不启动 Gazebo，仅用 `robot_state_publisher` + RViz2 在 3D 窗口中查看机器人模型，适合快速调试 URDF 结构和坐标系。

### 原理

`robot_state_publisher` 读取 URDF 后发布两类数据：

```
                       robot_state_publisher
                       ┌─────────────────────┐
  URDF 文件 ─────────→ │ 解析 link / joint 树  │
                       └────────┬────────────┘
                                │
                ┌───────────────┼───────────────┐
                ↓                               ↓
     /robot_description               /tf + /tf_static
     (std_msgs/msg/String)            (tf2_msgs/msg/TFMessage)
     发布完整 URDF 原文，                 每个 joint 算出的父子 link
     供 RViz2、spawn_entity 等订阅        坐标变换，RViz 据此绘制 3D 模型
```

### 使用

**方式一：launch 文件一行启动（推荐）**

```bash
conda activate ros2
. install/setup.sh
ros2 launch my_robot_description visualize.launch.py
```

**方式二：手动分步启动**

需要两个终端（或一个后台进程）：

```bash
# ===== 终端 1：启动 robot_state_publisher =====
conda activate ros2

# xacro 转换
ros2 run xacro xacro src/my_robot_description/urdf/my_robot.urdf.xacro > /tmp/my_robot.urdf

# 启动 publisher（前台持续运行，发布 TF）
ros2 run robot_state_publisher robot_state_publisher /tmp/my_robot.urdf

# ===== 终端 2：打开 RViz2 =====
conda activate ros2
rviz2
```

或者单终端，把 publisher 放后台：

```bash
conda activate ros2
ros2 run xacro xacro src/my_robot_description/urdf/my_robot.urdf.xacro > /tmp/my_robot.urdf
ros2 run robot_state_publisher robot_state_publisher /tmp/my_robot.urdf &  # 后台
rviz2                                                                      # 前台
```

在 RViz2 中：
1. 点击 **Add** → 选择 **RobotModel**
2. 将 **Description Topic** 设为 `/robot_description`
3. **Fixed Frame** 设为 `base_link`（默认是 `map`，会报 `Frame map does not exist` 错误）

### 与 Gazebo 仿真的区别

| | `robot_state_publisher` + RViz2 | `ros2 launch ... simulate.launch.py` |
|---|---|---|
| 启动 Gazebo | ❌ 不需要 | ✅ 启动 |
| 物理引擎 | ❌ 无 | ✅ 碰撞、重力、惯性 |
| 传感器插件 | ❌ 不加载 | ✅ 激光雷达等 |
| 控制 (/cmd_vel) | ❌ 不工作 | ✅ diff_drive 驱动轮子 |
| 用途 | 检查 URDF 结构、TF 树 | 完整仿真 |
| 启动速度 | 秒级 | 十秒级 |

## 包说明

### my_robot_description

机器人描述包，包含：

| 文件 | 说明 |
|------|------|
| `urdf/my_robot.urdf.xacro` | 机器人 URDF 模型（xacro 格式） |
| `launch/simulate.launch.py` | 仿真启动文件 |
| `launch/visualize.launch.py` | RViz 可视启动文件（无 Gazebo） |

### 机器人模型

```
base_link ──┬── left_wheel_joint  → left_wheel   (连续旋转)
            ├── right_wheel_joint → right_wheel  (连续旋转)
            └── laser_joint       → laser_link   (固定)
```

- **base_link**: 蓝色长方体 0.5×0.3×0.2m
- **left_wheel / right_wheel**: 黑色圆柱，半径 0.05m，差分驱动
- **laser_link**: 红色圆柱，前置 360° 激光雷达

### Gazebo 插件

- `libgazebo_ros_diff_drive.so` — 差分驱动，接收 `/cmd_vel` 控制
- `libgazebo_ros_ray_sensor.so` — 激光雷达，发布 `/scan`

## 测试控制

```bash
conda activate ros2
. install/setup.sh

# 向前移动
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}" -1

# 左转
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.5}}" -1

# 查看激光数据
ros2 topic echo /scan
```

## 已知问题

- macOS 上 Gazebo 启动时会打印 Qt5/Qt6 类重复警告，不影响功能。
- `robot_state_publisher` 会提示 root link 不应有 inertia（KDL 限制），可忽略。
- 如果 RViz 里出现异常模型（比如别人的机器人）或 mesh 加载错误，说明有其他 workspace 的 ROS2 进程残留，此时 `/robot_description` 会被多个发布者抢占：

  ```bash
  # 检查 /robot_description 发布者数量（正常应为 1）
  ros2 topic info /robot_description
  # 如果 Publisher count > 1，杀掉所有 ROS 进程重来
  pkill -f "ros2\|robot_state\|joint_state\|rviz2\|static_joint\|robot_desc"
  ```

## 目录结构

```
lab4_ws/
├── README.md
├── src/                           # 所有 ROS2 包的源码目录
│   └── my_robot_description/      # 机器人描述包
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── urdf/
│       │   └── my_robot.urdf.xacro    # URDF 模型
│       ├── launch/
│       │   └── simulate.launch.py     # 启动文件
│       ├── include/
│       └── src/
├── build/                         # colcon 构建输出
├── install/                       # colcon 安装输出
└── log/                           # 构建日志
```
