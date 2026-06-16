# JetAuto Description — ROS2 机器人描述包

> **从 ROS1 (catkin) 迁移至 ROS2 (ament_cmake + Robostack)，适配 Gazebo Sim 8.x (Harmonic)**

本包包含 JetAuto 移动机器人的 URDF 模型、3D 网格文件、Gazebo 仿真插件、RViz2 配置及启动文件。

---

## 目录

- [快速开始](#快速开始)
- [包结构](#包结构)
- [机器人配置](#机器人配置)
- [启动文件](#启动文件)
- [URDF 模型架构](#urdf-模型架构)
- [传感器清单](#传感器清单)
- [Gazebo 插件迁移对照](#gazebo-插件迁移对照)
- [3D 网格文件](#3d-网格文件)
- [依赖](#依赖)
- [构建](#构建)
- [环境变量](#环境变量)
- [已知限制](#已知限制)
- [测试](#测试)

---

## 快速开始

### 前置条件

1. 已通过 conda 安装 ROS2 Jazzy (Robostack)
2. 已完成工作空间构建（见[构建](#构建)章节）

### 启动步骤

```bash
# 1. 激活 ROS2 环境
conda activate ros2

# 2. 进入工作空间并加载
cd ros2_ws
source install/setup.bash   # 或 source install/setup.zsh  (macOS 用 zsh)

# 3. 设置机器人配置变量 (必需！不设置会导致 xacro 编译报错)
export MACHINE_TYPE=default        # 机器人型号: default | JetAutoPro
export LIDAR_TYPE=A1               # 激光雷达型号: A1 | A2 | G4
export DEPTH_CAMERA_TYPE=camera    # 深度相机: camera | None

# 4. 在 RViz2 中可视化机器人模型
ros2 launch jetauto_description display.launch.py

# 5. 启动 Gazebo Sim 完整仿真
ros2 launch jetauto_description gazebo.launch.py

# 6. 启动 RViz2 控制视图 (含导航/控制面板)
ros2 launch jetauto_description control_view.launch.py
```

### 启动后：RViz2 中 RobotModel 的必要配置

启动 `display.launch.py` 后，RViz2 窗口会打开。如果左侧 Displays 面板中 **RobotModel** 显示正常，则无需额外操作。如果看不到机器人模型（只看到 TF 坐标轴），需要手动配置 **Description Topic**：

#### 配置方法

1. 在左侧 **Displays** 面板中，展开 **RobotModel** 条目
2. 找到 **Description Topic** 字段
3. 填入：`/robot_description`
4. 确认 **Enabled** 勾选框已勾选

#### 为什么需要填写这个字段

`robot_state_publisher` 节点读取 URDF 模型文件，将完整的机器人几何信息（包括所有连杆、关节和 3D 网格文件路径）发布到 **`/robot_description`** 这个 ROS Topic 上。RViz2 的 RobotModel 显示插件需要订阅这个 Topic 才能知道机器人长什么样、该怎么渲染。

> **背景说明**：TF 坐标轴（红绿蓝三色柱子）显示说明 `robot_state_publisher` 工作正常，正在发布坐标系变换。但 **TF 只包含位置和方向信息，不包含 3D 几何数据**。要看到完整的 3D 模型，RViz2 必须通过 `/robot_description` 获取每个连杆的网格文件路径并用 OGRE 渲染引擎绘制出来。

#### 确认配置正确

配置完成后，你应该能看到：

| 应该看到的 | 说明 |
|-----------|------|
| 🟢 完整的 3D 机器人模型 | 底盘 + 4轮 + 雷达 + IMU + 相机等 |
| 🟢 轮子和相机关节可通过 GUI 滑块控制 | `joint_state_publisher_gui` 窗口 |
| 🟢 左侧 Displays 面板正常工作 | 可添加/删除/配置各种显示 |

> **关于机器人位置**：如果模型显示正常但离视野很远，可以在 RViz2 左侧 **Views** 面板 → **Current View** 中点右键选 **Zero** 重置视角，RViz2 会自动对准机器人。

---

## 包结构

```
jetauto_description/
├── CMakeLists.txt                  # ament_cmake 构建脚本
├── package.xml                     # ROS2 包元数据 (format 3)
├── README.md                       # 本文件
│
├── config/                         # 配置文件
│   └── joint_names_jetauto_description.yaml   # 控制器关节名称 (Pro 用)
│
├── launch/                         # ROS2 Python 启动文件
│   ├── display.launch.py           # RViz2 可视化
│   ├── gazebo.launch.py            # Gazebo Sim 仿真
│   └── control_view.launch.py      # RViz2 控制视图
│
├── meshes/                         # 3D STL 网格 (共 28 个)
│   ├── base_link.stl               # 底盘 (非 Pro)
│   ├── back_shell_link.stl         # 后壳
│   ├── lidar_link.stl              # 激光雷达外壳
│   ├── screen_link.stl             # 屏幕 (非 Pro)
│   ├── speaker_link.stl            # 扬声器
│   ├── mic_link.stl                # 麦克风
│   ├── depth_camera_link.stl       # 深度相机外壳 (非 Pro)
│   ├── wheel_*_front_link.stl      # 前轮 ×2 (左/右)
│   ├── wheel_*_back_link.stl       # 后轮 ×2 (左/右)
│   └── pro/                        # JetAuto Pro 专用网格 (17 个)
│       ├── base_link.stl           # Pro 底盘
│       ├── screen_link.stl         # Pro 屏幕
│       ├── usb_cam_link.stl        # USB 摄像头
│       ├── depth_camera_link.stl   # Pro 深度相机
│       ├── connect_link.stl        # 连接件
│       ├── arm/                    # 机械臂 (6 个 STL)
│       │   ├── link1.stl ~ link4.stl
│       │   ├── servo_link.stl
│       │   └── gripper_servo_link.stl
│       └── gripper/                # 夹爪 (6 个 STL)
│           ├── r_link.stl / l_link.stl
│           ├── r_in_link.stl / l_in_link.stl
│           └── r_out_link.stl / l_out_link.stl
│
├── rviz/                           # RViz2 配置文件
│   ├── urdf.rviz                   # 模型可视化配置
│   └── control_view.rviz           # 控制视图配置
│
└── urdf/                           # URDF/Xacro 模型文件
    ├── jetauto.urdf.xacro          # ★ 主入口 (被 launch 文件引用)
    ├── jetauto.xacro               # 机器人本体 (不含 Gazebo 插件)
    ├── jetauto.gazebo.xacro        # Gazebo 插件汇总 (包含 Pro/非Pro 条件)
    │
    ├── materials.xacro             # 材质定义 (颜色)
    ├── inertial_matrix.xacro       # 惯性矩阵宏 (球体/圆柱/长方体)
    │
    ├── jetauto_car.urdf.xacro      # 移动底盘 + 4 轮 (非 Pro)
    ├── jetauto_car.gazebo.xacro    # 底盘 Gazebo 插件 (DiffDrive + JointStatePublisher)
    │
    ├── imu.urdf.xacro              # IMU 传感器连杆定义
    ├── imu.gazebo.xacro            # IMU Gazebo 传感器
    │
    ├── lidar.urdf.xacro            # 激光雷达连杆 + 关节
    ├── lidar.gazebo.xacro          # 激光雷达 Gazebo 传感器 (gpu_lidar)
    ├── lidar_a1.urdf.xacro         # A1/A2 型号雷达 frame 偏移
    ├── lidar_g4.urdf.xacro         # G4 型号雷达 frame 偏移
    │
    ├── screen.urdf.xacro           # 屏幕 (非 Pro)
    ├── screen.gazebo.xacro         # 屏幕 Gazebo 材质
    │
    ├── depth_camera.urdf.xacro     # 深度相机 + 旋转关节 (非 Pro)
    ├── depth_camera.gazebo.xacro   # 深度相机 Gazebo 传感器 (rgbd_camera)
    │
    └── pro/                        # JetAuto Pro 扩展 (机械臂 + 夹爪)
        ├── jetauto_car.urdf.xacro         # Pro 底盘 (与标准版共享部分结构)
        ├── jetauto_arm.urdf.xacro         # 4-DOF 机械臂
        ├── jetauto_arm.gazebo.xacro       # 机械臂 Gazebo 控制器
        ├── jetauto_arm.transmission.xacro # 机械臂传动定义 (ros2_control)
        ├── gripper.urdf.xacro             # 夹爪机构 (mimic 关节)
        ├── gripper.gazebo.xacro           # 夹爪 Gazebo 材质
        ├── gripper.transmission.xacro     # 夹爪传动定义
        ├── usb_camera.urdf.xacro          # USB 摄像头
        ├── usb_camera.gazebo.xacro        # USB 摄像头 Gazebo 传感器
        ├── screen.urdf.xacro              # Pro 屏幕
        ├── screen.gazebo.xacro            # Pro 屏幕 Gazebo 材质
        ├── depth_camera.urdf.xacro        # Pro 深度相机
        ├── depth_camera.gazebo.xacro      # Pro 深度相机 Gazebo 传感器
        ├── depth_camera_connect.urdf.xacro   # 深度相机连接件
        ├── depth_camera_connect.gazebo.xacro # 连接件 Gazebo 材质
        └── aerial.urdf.xacro              # 天线
```

---

## 机器人配置

本包通过 **环境变量** 控制系统运行模式，不同变量组合对应不同的硬件配置：

### 配置变量

| 环境变量 | 可选值 | 说明 |
|----------|--------|------|
| `MACHINE_TYPE` | `default` / `JetAutoPro` | 机器人型号。`default` 为标准版，`JetAutoPro` 为带 4-DOF 机械臂和夹爪的 Pro 版 |
| `LIDAR_TYPE` | `A1` / `A2` / `G4` | 激光雷达型号。`A1`/`A2` 使用通用 frame，`G4` 使用专用偏移 |
| `DEPTH_CAMERA_TYPE` | `None` / `camera` / 任意非 None 值 | 是否加载深度相机。`None` 停用，其他值启用 |

### 配置组合示例

```bash
# 标准版 + A1 激光 + 无深度相机
export MACHINE_TYPE=default LIDAR_TYPE=A1 DEPTH_CAMERA_TYPE=None

# 标准版 + G4 激光 + 深度相机
export MACHINE_TYPE=default LIDAR_TYPE=G4 DEPTH_CAMERA_TYPE=camera

# Pro 版 + A1 激光 + 深度相机
export MACHINE_TYPE=JetAutoPro LIDAR_TYPE=A1 DEPTH_CAMERA_TYPE=camera
```

### 各配置下的模型规模 (URDF 展开后)

| 配置 | Links | Joints | 说明 |
|------|-------|--------|------|
| 默认 + A1/G4 + 无相机 | 13 | 12 | 最小配置：底盘 + 4轮 + IMU + 雷达 |
| 默认 + A1/G4 + 相机 | 15 | 14 | + 深度相机 (含 revolute 关节 joint1) |
| Pro + A1 + 无相机 | 33 | 37 | + 机械臂 (4 joints) + 夹爪 (6 joints) + USB 相机 |
| Pro + G4 + 相机 | 35 | 39 | 全功能 Pro 配置 |

---

## 启动文件

### 1. display.launch.py — RViz2 可视化

**用途**：在 RViz2 中查看机器人模型，用于 URDF 调试和可视化。

**启动参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `odom_frame` | `odom` | 里程计坐标系名称 |
| `base_frame` | `base_footprint` | 基座 footprint 坐标系 |
| `depth_camera_name` | `camera` | 深度相机名称前缀，也是深度相机连杆的 frame 前缀 |

**启动的节点及作用**：

| 节点 | 发布的内容 | 作用 |
|------|----------|------|
| `robot_state_publisher` | `/tf`、`/tf_static`、`/robot_description` | ① 发布所有连杆坐标系变换（TF）；② 将完整 URDF 模型发布到 `/robot_description` Topic |
| `joint_state_publisher_gui` | `/joint_states` | 发布所有可动关节的当前角度值，并提供 GUI 滑块手动调节 |
| `rviz2` | — | 3D 渲染窗口，订阅 TF + robot_description + joint_states 进行可视化 |

**数据流**：

```
xacro 文件 → robot_state_publisher → /robot_description (URDF 模型)
                                   → /tf_static (固定关节变换)
                                   → /tf (可动关节变换)
joint_state_publisher_gui          → /joint_states (关节角度)
                                          ↓
RViz2 RobotModel 订阅 /robot_description + /joint_states → 渲染 3D 模型
```

**使用**：
```bash
# 标准启动
ros2 launch jetauto_description display.launch.py

# 自定义深度相机名称
ros2 launch jetauto_description display.launch.py depth_camera_name:=my_camera

# 自定义坐标系
ros2 launch jetauto_description display.launch.py odom_frame:=odom base_frame:=base_footprint
```

**启动后检查清单**：

- [ ] 左侧 Displays 面板正常显示（如无面板，检查[快速开始](#快速开始)中的 RViz2 配置步骤）
- [ ] 3D 视图中能看到完整的机器人模型（底盘 + 4轮 + 雷达 + 传感器等）
- [ ] `joint_state_publisher_gui` 弹窗中出现关节滑块，拖动滑块机器人模型实时运动
- [ ] TF 坐标系（红绿蓝三色轴）指向正确方向

**常见问题**：

| 现象 | 原因 | 解决 |
|------|------|------|
| 看不到模型，只有 TF 轴 | RobotModel 的 Description Topic 未填写 | 填入 `/robot_description` |
| 模型不完整（缺连杆） | 环境变量未正确设置 | 检查 `MACHINE_TYPE`、`LIDAR_TYPE`、`DEPTH_CAMERA_TYPE` |
| 模型全是白色 | 网格文件路径问题 / OGRE 插件问题 | 检查 STL 网格文件是否已安装 |
| 模型离相机很远看不到 | 视角问题 | Views 面板 → Current View → 右键 Zero 重置

---

### 2. gazebo.launch.py — Gazebo Sim 仿真

**用途**：在 Gazebo Sim 8.x (Harmonic) 中启动完整仿真环境。

**启动参数**：同 `display.launch.py`

**启动的节点/进程**：

| 组件 | 说明 |
|------|------|
| `gz sim -s -r empty.sdf` | Gazebo Sim Server (物理引擎 + 传感器) |
| `gz sim -g` | Gazebo Sim GUI 渲染窗口 (仅 macOS 分离启动) |
| `xacro → /tmp/jetauto.urdf` | 将 xacro 编译为 URDF 文件 |
| `ros2 run ros_gz_sim create` | 在 Gazebo 中生成 JetAuto 机器人 |
| `robot_state_publisher` | 发布 TF + robot_description |
| `ros_gz_bridge` (cmd_vel) | ROS `/cmd_vel` ↔ Gazebo `/model/jetauto/cmd_vel` |
| `ros_gz_bridge` (odometry) | Gazebo odometry → ROS `/model/jetauto/odometry` |
| `ros_gz_bridge` (scan) | Gazebo laser → ROS `/scan` |
| `ros_gz_bridge` (imu) | Gazebo IMU → ROS `/imu_data` |

**重要**：macOS 上 Gazebo Sim 要求 Server 和 GUI 作为独立进程启动（见 [gz-sim#44](https://github.com/gazebosim/gz-sim/issues/44)），本 launch 文件已自动处理。

**环境变量**：
- `GZ_SIM_RESOURCE_PATH`：自动设置为 `install/jetauto_description/share/`，使 Gazebo 能解析 `model://jetauto_description/...` 路径（用于 STL 网格文件）。

**使用**：
```bash
ros2 launch jetauto_description gazebo.launch.py
ros2 launch jetauto_description gazebo.launch.py depth_camera_name:=depth_cam
```

---

### 3. control_view.launch.py — RViz2 控制视图

**用途**：启动带有导航/控制面板的 RViz2 视图，配合 Gazebo 仿真使用。

**启动的节点**：
- `rviz2` — 使用 `rviz/control_view.rviz` 配置，包含 SetInitialPose、SetGoal、PublishPoint 等交互工具

**与 display.launch.py 的区别**：

| 特性 | display.launch.py | control_view.launch.py |
|------|-------------------|----------------------|
| robot_state_publisher | ✅ 启动 | ❌ 不启动（依赖 Gazebo） |
| joint_state_publisher_gui | ✅ 启动 | ❌ 不启动（Gazebo 提供 joint_states） |
| 交互工具 | 基础 (Interact, Select, Move) | 增强 (+ SetInitialPose, SetGoal, PublishPoint) |
| 适用场景 | 独立查看模型、URDF 调试 | 配合 Gazebo 仿真进行导航控制 |

**使用**：
```bash
# 终端 1：启动 Gazebo 仿真
export MACHINE_TYPE=default LIDAR_TYPE=A1 DEPTH_CAMERA_TYPE=camera
ros2 launch jetauto_description gazebo.launch.py

# 终端 2：启动控制视图
ros2 launch jetauto_description control_view.launch.py
```

---

## URDF 模型架构

### 加载流程

```
jetauto.urdf.xacro (入口)
  │
  ├─ jetauto.xacro (机器人几何结构)
  │   ├─ materials.xacro        # 颜色材质
  │   ├─ inertial_matrix.xacro   # 惯性宏
  │   ├─ imu.urdf.xacro          # IMU 连杆
  │   ├─ lidar.urdf.xacro        # 雷达连杆
  │   ├─ lidar_{a1,g4}.urdf.xacro # 雷达 frame (条件加载)
  │   ├─ [screen.urdf.xacro]     # 屏幕 (仅非 Pro)
  │   ├─ [depth_camera.urdf.xacro] # 深度相机 (仅非 Pro, 条件加载)
  │   ├─ jetauto_car.urdf.xacro  # 底盘+4轮 (非 Pro) 或
  │   └─ pro/jetauto_car.urdf.xacro # 底盘 (Pro) + 机械臂/夹爪/相机/天线
  │
  └─ jetauto.gazebo.xacro (Gazebo 仿真配置)
      ├─ jetauto_car.gazebo.xacro    # 底盘控制器 (DiffDrive + JointStatePublisher)
      ├─ imu.gazebo.xacro            # IMU 传感器
      ├─ lidar.gazebo.xacro          # 雷达传感器
      ├─ [screen.gazebo.xacro]       # 屏幕材质 (仅非 Pro)
      ├─ [depth_camera.gazebo.xacro] # 深度相机传感器 (仅非 Pro)
      └─ [Pro 专用]                  # 机械臂控制器 + 夹爪 + USB相机 + Pro深度相机
```

### 坐标系树 (TF Tree)

```
odom (里程计坐标系)
└── base_footprint
    └── base_link
        ├── back_shell_link
        ├── wheel_right_front_link
        ├── wheel_left_front_link
        ├── wheel_right_back_link (mimic → wheel_right_front)
        ├── wheel_left_back_link  (mimic → wheel_left_front)
        ├── mic_link
        ├── speaker_link
        ├── imu_link
        ├── lidar_link
        │   └── lidar_frame
        ├── screen_link                    (非 Pro)
        ├── [camera]_link → [camera]_frame (非 Pro, revolute joint1)
        │
        └── Pro 扩展:
            ├── link1 → servo_link → link2 → link3 → link4
            │   ├── usb_cam_link
            │   ├── end_effector_link
            │   └── gripper_servo_link
            │       ├── r_link    ← 主驱动关节
            │       ├── l_link    (mimic r_link, -1)
            │       ├── r_in_link (mimic r_link, -1)
            │       ├── r_out_link(mimic r_link,  1)
            │       ├── l_in_link (mimic r_link, -1)
            │       └── l_out_link(mimic r_link,  1)
            ├── [camera]_link → [camera]_frame (Pro, fixed joint)
            ├── connect_link → depth_camera_connect_*
            └── aerial_left_link / aerial_right_link
```

### 关键 URDF/Xacro 文件说明

#### 主文件

| 文件 | 说明 |
|------|------|
| `jetauto.urdf.xacro` | **唯一入口**。组合 jetauto.xacro + jetauto.gazebo.xacro |
| `jetauto.xacro` | 所有机器人几何结构。根据 `MACHINE_TYPE`/`LIDAR_TYPE`/`DEPTH_CAMERA_TYPE` 条件加载子模块 |
| `jetauto.gazebo.xacro` | 所有 Gazebo 仿真配置。根据 `MACHINE_TYPE` 条件加载 Pro/非Pro 插件 |

#### 底盘

| 文件 | 说明 |
|------|------|
| `jetauto_car.urdf.xacro` | 非 Pro 底盘。4 个 continuous 车轮关节 + mimic 后轮 |
| `pro/jetauto_car.urdf.xacro` | Pro 底盘。结构相似但共享部分 Pro 网格不同 |
| `jetauto_car.gazebo.xacro` | DiffDrive 控制器 + JointStatePublisher (非 Pro) |

#### 传感器

| 文件 | 传感器 | Gazebo Sim 类型 | 发布 Topic |
|------|--------|-----------------|------------|
| `imu.urdf.xacro` + `imu.gazebo.xacro` | IMU (惯性测量单元) | `sensor type="imu"` | `imu_data` |
| `lidar.urdf.xacro` + `lidar.gazebo.xacro` | 360° 激光雷达 | `sensor type="gpu_lidar"` | `scan` |
| `depth_camera.urdf.xacro` + `depth_camera.gazebo.xacro` | 深度相机 (RGB-D) | `sensor type="rgbd_camera"` | 自动发布 RGB + Depth |
| `pro/usb_camera.urdf.xacro` + `.gazebo.xacro` | USB 摄像头 | `sensor type="camera"` | 自动发布 image |

#### Pro 机械臂

| 文件 | 说明 |
|------|------|
| `pro/jetauto_arm.urdf.xacro` | 4-DOF 机械臂 (joint1-4) + end_effector |
| `pro/jetauto_arm.gazebo.xacro` | JointPositionController ×5 (joint1-4, r_joint) + DiffDrive + JointStatePublisher |
| `pro/jetauto_arm.transmission.xacro` | ros2_control 传动接口定义 |
| `pro/gripper.urdf.xacro` | 平行夹爪。使用 URDF `<mimic>` 标签实现关节联动 |
| `pro/gripper.gazebo.xacro` | 夹爪材质。mimic 由 JointStatePublisher 原生支持 |
| `pro/gripper.transmission.xacro` | 夹爪传动接口定义 |

#### 通用宏

| 文件 | 说明 |
|------|------|
| `materials.xacro` | 8 种颜色材质 (black/blue/green/gray/darkgray/red/white/yellow) |
| `inertial_matrix.xacro` | 3 种惯性计算宏: `sphere_inertial`, `cylinder_inertial`, `box_inertial` |

---

## 传感器清单

### 标准版 (JETSON NANO)

| 传感器 | 类型 | 更新率 | Topic (ROS) | Gazebo 插件 |
|--------|------|--------|-------------|-------------|
| LiDAR (RPLIDAR A1/A2/G4) | 360° 激光 | 5 Hz | `/scan` | `<sensor type="gpu_lidar">` |
| IMU (内置) | 6-DOF 惯性 | 自适应 | `/imu_data` | `<sensor type="imu">` |
| 深度相机 (Orbbec Astra) | RGB-D | 20 Hz | 自动发布 | `<sensor type="rgbd_camera">` |

### Pro 版 (追加)

| 传感器 | 类型 | 更新率 | Topic (ROS) | Gazebo 插件 |
|--------|------|--------|-------------|-------------|
| USB 摄像头 | RGB | 30 Hz | 自动发布 | `<sensor type="camera">` |
| 深度相机 (Pro 型号) | RGB-D | 20 Hz | 自动发布 | `<sensor type="rgbd_camera">` |

---

## Gazebo 插件迁移对照

本包已将所有 ROS1 Gazebo Classic 插件替换为 Gazebo Sim 8.x (Harmonic) 等效项：

| 原 ROS1 插件 | 新 Gazebo Sim 插件 | 文件 |
|-------------|-------------------|------|
| `libgazebo_ros_planar_move.so` | `gz-sim-diff-drive-system` (DiffDrive) | `jetauto_car.gazebo.xacro` |
| `libgazebo_ros_control.so` | `gz-sim-joint-state-publisher-system` + `gz-sim-joint-position-controller-system` | `jetauto_car.gazebo.xacro` / `pro/jetauto_arm.gazebo.xacro` |
| `libgazebo_ros_imu.so` | `<sensor type="imu">` (原生) | `imu.gazebo.xacro` |
| `libgazebo_ros_laser.so` | `<sensor type="gpu_lidar">` (原生) | `lidar.gazebo.xacro` |
| `libgazebo_ros_openni_kinect.so` | `<sensor type="rgbd_camera">` (原生) | `depth_camera.gazebo.xacro` |
| `libgazebo_ros_camera.so` | `<sensor type="camera">` (原生) | `pro/usb_camera.gazebo.xacro` |
| `libroboticsgroup_upatras_gazebo_mimic_joint_plugin.so` | **已移除** — URDF `<mimic>` 标签由 JointStatePublisher 原生支持 | `pro/gripper.gazebo.xacro` |

### Gazebo Sim DiffDrive 参数

```xml
<plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
    <left_joint>wheel_left_front_joint</left_joint>
    <right_joint>wheel_right_front_joint</right_joint>
    <wheel_separation>0.17225</wheel_separation>   <!-- 两轮间距 (m) -->
    <wheel_radius>0.049</wheel_radius>              <!-- 轮子半径 (m) -->
    <odom_publish_frequency>20.0</odom_publish_frequency>
    <topic>/cmd_vel</topic>
    <odom_topic>/model/jetauto/odometry</odom_topic>
</plugin>
```

### ros_gz_bridge 桥接映射

| ROS Topic | 方向 | Gazebo Topic | 消息类型 |
|-----------|------|-------------|----------|
| `/cmd_vel` | ROS → Gz | `/model/jetauto/cmd_vel` | `Twist` |
| `/model/jetauto/odometry` | Gz → ROS | (odom published by DiffDrive) | `Odometry` |
| `/scan` | Gz → ROS | (laser scan from sensor) | `LaserScan` |
| `/imu_data` | Gz → ROS | (IMU data from sensor) | `Imu` |

---

## 3D 网格文件

所有网格均为 ASCII STL 格式，来源为 HiWonder 官方 CAD 导出。

### 标准版网格 (11 个)

| 文件 | 对应 Link | 尺寸 (粗略) |
|------|----------|------------|
| `base_link.stl` | base_link | ~297×145×113 mm |
| `back_shell_link.stl` | back_shell_link | 后壳 |
| `lidar_link.stl` | lidar_link | 雷达外壳 |
| `screen_link.stl` | screen_link | 屏幕面板 |
| `speaker_link.stl` | speaker_link | 扬声器 |
| `mic_link.stl` | mic_link | 麦克风 |
| `depth_camera_link.stl` | camera_link | 深度相机外壳 |
| `wheel_right_front_link.stl` | wheel_right_front | 右前轮 |
| `wheel_left_front_link.stl` | wheel_left_front | 左前轮 |
| `wheel_right_back_link.stl` | wheel_right_back | 右后轮 |
| `wheel_left_back_link.stl` | wheel_left_back | 左后轮 |

### Pro 版网格 (17 个)

| 路径 | 对应 Link |
|------|----------|
| `pro/base_link.stl` | Pro 底盘 |
| `pro/screen_link.stl` | Pro 屏幕 |
| `pro/usb_cam_link.stl` | USB 摄像头 |
| `pro/depth_camera_link.stl` | Pro 深度相机 |
| `pro/connect_link.stl` | 相机连接件 |
| `pro/arm/link1.stl` | 机械臂关节1 |
| `pro/arm/link2.stl` | 机械臂关节2 |
| `pro/arm/link3.stl` | 机械臂关节3 |
| `pro/arm/link4.stl` | 机械臂关节4 |
| `pro/arm/servo_link.stl` | 舵机 |
| `pro/arm/gripper_servo_link.stl` | 夹爪舵机 |
| `pro/gripper/r_link.stl` | 右夹爪 |
| `pro/gripper/l_link.stl` | 左夹爪 |
| `pro/gripper/r_in_link.stl` | 右内夹爪 |
| `pro/gripper/r_out_link.stl` | 右外夹爪 |
| `pro/gripper/l_in_link.stl` | 左内夹爪 |
| `pro/gripper/l_out_link.stl` | 左外夹爪 |

---

## 依赖

### 构建依赖

| 包 | 用途 |
|----|------|
| `ament_cmake` | ROS2 构建系统 |

### 运行时依赖

| 包 | 用途 |
|----|------|
| `robot_state_publisher` | 发布 TF + robot_description |
| `joint_state_publisher_gui` | 关节状态 GUI 滑块 (display.launch.py) |
| `rviz2` | 3D 可视化 |
| `xacro` | URDF 宏处理 |
| `ros_gz_sim` | Gazebo Sim 集成 (spawn/create) |
| `ros_gz_bridge` | ROS ↔ Gazebo 消息桥接 |

### 系统依赖

| 软件 | 版本要求 |
|------|---------|
| Gazebo Sim | **8.x** (Harmonic) |
| ROS 2 | **Jazzy** (via Robostack) |
| Python | **3.12+** |
| 操作系统 | macOS 14+ / Ubuntu 24.04+ |

---

## 构建

```bash
# 在 ros2_ws 工作空间中
cd ros2_ws

# 安装依赖 (首次)
conda activate ros2
rosdep install --from-paths src --ignore-src -y

# 构建
colcon build --packages-select jetauto_description

# 加载
source install/setup.bash
```

**重建提示**：如果修改了 URDF/xacro 或 launch 文件，需要重新 build：
```bash
rm -rf build/jetauto_description install/jetauto_description
colcon build --packages-select jetauto_description
```

---

## 环境变量

| 变量 | 说明 | 设置位置 |
|------|------|---------|
| `MACHINE_TYPE` | 机器人型号 (`default` / `JetAutoPro`) | 用户设置 (启动前 export) |
| `LIDAR_TYPE` | 雷达型号 (`A1` / `A2` / `G4`) | 用户设置 |
| `DEPTH_CAMERA_TYPE` | 深度相机 (`None` / `camera`) | 用户设置 |
| `GZ_SIM_RESOURCE_PATH` | Gazebo 资源搜索路径 | 由 `gazebo.launch.py` 自动设置 |

---

## 已知限制

### 1. macOS OGRE 插件配置 (已修复)

macOS 上 Robostack 打包的 `plugins.cfg` 存在两个问题：
- **PluginFolder 路径错误**：指向不存在的 `lib/Release` 目录，实际插件在 `lib/OGRE/`
- **缺少 Codec_Assimp**：没有加载 STL 网格解码器，导致 RViz2 无法渲染 3D 模型

**已内置修复**：本项目已修复上述配置，无需手动操作。如果遇到"模型不显示但 TF 轴正常"的问题，参考[快速开始](#快速开始)中的 RViz2 配置步骤。

### 2. macOS DART 物理引擎不支持 mimic 约束

Gazebo Sim 8.x 在 macOS 上使用 DART 物理引擎，**不支持 URDF `<mimic>` 关节约束**。影响：后轮不会随前轮旋转（仅视觉效果），DiffDrive 驱动不受影响。

### 3. STL 网格文件较大

Pro 版共 28 个 STL 文件，`ros_gz_sim create` 加载时可能看到 mesh 相关的 `[Err]` 日志。这些是非致命错误——只要 `Entity creation successful` 出现，机器人就已正确生成。Gazebo 在无显示 server 模式下可能无法找到 mesh 但机器人结构仍然正确。

### 4. 关节状态发布

`robot_state_publisher` 需要配合 `joint_state_publisher` (或 `joint_state_publisher_gui`) 才能正确发布关节状态 TF。在 Gazebo 仿真中，Gazebo 通过 `JointStatePublisher` 系统发布 `/joint_states`，`robot_state_publisher` 订阅后计算 TF。

### 5. Pro 版 ros2_control

`pro/jetauto_arm.transmission.xacro` 和 `pro/gripper.transmission.xacro` 定义了 ros2_control 传动接口，目前使用 `JointPositionController` 作为 Gazebo Sim 插件。如需通过 ROS 端控制机械臂，需要额外的 `ros2_control` 配置和 controller manager。

---

## 测试

本包已通过以下自动化测试：

### 静态测试 (34 项)
- ✅ `colcon build` 构建成功
- ✅ 5 种配置组合 xacro 展开成功
- ✅ 3 个 launch 文件可被 `ros2 launch` 发现
- ✅ URDF 结构验证 (root, base_link, base_footprint, 传感器)
- ✅ Gazebo 插件验证 (DiffDrive, JointStatePublisher)
- ✅ 无 ROS1 插件残留 (`libgazebo_ros_*`, `libroboticsgroup_*`)
- ✅ 车轮关节类型为 `continuous`
- ✅ Pro 模式 link1, r_link, mimic 关节存在
- ✅ 所有 Python launch 文件语法正确
- ✅ 安装目录/文件完整性

### 仿真端到端测试 (16 项)
- ✅ Gazebo Sim Server 正常启动
- ✅ 机器人 Spawn (`Entity creation successful`)
- ✅ Mesh 资源路径解析 (GZ_SIM_RESOURCE_PATH)
- ✅ DiffDrive / JointStatePublisher / gpu_lidar / imu 插件存在
- ✅ Gazebo topics `/clock`, `/cmd_vel` 正常
- ✅ `robot_state_publisher` 运行正常
- ✅ `ros_gz_bridge` cmd_vel 桥接正常
- ✅ 控制命令 `/cmd_vel` 发送成功

---

## 迁移历史

- **原始版本**: ROS1 (catkin), Gazebo Classic, `ros2_ws_techer/src/jetauto_simulations/jetauto_description/`
- **迁移日期**: 2026-06-16
- **目标环境**: ROS2 Jazzy (Robostack), Gazebo Sim 8.10.0 (Harmonic), macOS
- **迁移内容**:
  - `package.xml`: format 2 → format 3, `catkin` → `ament_cmake`
  - `CMakeLists.txt`: catkin → ament_cmake
  - 3 个 launch 文件: ROS1 XML → ROS2 Python
  - 7 个 Gazebo xacro: ROS1 插件 → Gazebo Sim 原生传感器/系统
  - 底盘 URDF: 车轮关节 `fixed` → `continuous` (DiffDrive 兼容)
  - 添加 `GZ_SIM_RESOURCE_PATH` 环境变量设置

---

## 参考

- [HiWonder JetAuto 官方资料](https://www.hiwonder.com/)
- [Gazebo Sim 文档](https://gazebosim.org/docs)
- [ros_gz 集成文档](https://github.com/gazebosim/ros_gz)
- [Robostack (conda ROS2)](https://robostack.github.io/)
