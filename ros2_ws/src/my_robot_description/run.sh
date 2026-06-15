#!/usr/bin/env bash
set -e

# ============================================================
# run.sh — my_robot_description 一键启动脚本
# 用法: ./run.sh [sim|viz|all|build|check|clean]
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

# 激活环境
activate() {
    if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "ros2" ]; then
        info "激活 conda 环境 ros2 ..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ros2
    fi
    . "$WS_DIR/install/setup.sh" 2>/dev/null || true
    ok "ROS_DISTRO=$ROS_DISTRO"
}

# 构建
build() {
    activate
    info "构建 my_robot_description ..."
    info "（纯文件包，无编译，只需 install 目录注册包位置）"
    cd "$WS_DIR"
    colcon build --packages-select my_robot_description --symlink-install
    . install/setup.sh
    ok "构建完成（之后改 launch/URDF 无需重编译）"
}

# 检查 URDF
check() {
    activate
    info "验证 URDF ..."
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "URDF 结构正确"
    echo ""
    info "Gazebo 插件:"
    grep -n "plugin\|DiffDrive\|gpu_lidar" "$TMP_URDF" || true
}

# 可视化 (RViz)
viz() {
    activate
    info "启动 RViz 可视化 ..."
    ros2 launch my_robot_description visualize.launch.py
}

# Gazebo 仿真
sim() {
    activate
    info "启动 Gazebo Sim 仿真 ..."
    ros2 launch my_robot_description simulate.launch.py
}

# 全部（先检查，再启动仿真 + 键盘控制）
all() {
    activate
    info "检查 URDF ..."
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "URDF OK"

    info "启动 Gazebo Sim + 可视化 ..."
    ros2 launch my_robot_description simulate.launch.py &
    SIM_PID=$!
    sleep 5

    info "启动 RViz2 ..."
    ros2 launch my_robot_description visualize.launch.py &
    VIZ_PID=$!

    echo ""
    echo "============================================"
    info "仿真和可视化已启动"
    info "新终端运行键盘控制:"
    echo "  conda activate ros2"
    echo "  . $WS_DIR/install/setup.sh"
    echo "  ros2 run teleop_twist_keyboard teleop_twist_keyboard"
    echo ""
    info "按 Ctrl+C 停止所有进程"
    echo "============================================"

    trap "kill $SIM_PID $VIZ_PID 2>/dev/null; exit 0" INT TERM
    wait
}

# 清理残留进程
clean() {
    warn "清理所有 ROS2 相关进程 ..."
    pkill -f "robot_state_publisher" 2>/dev/null || true
    pkill -f "joint_state_publisher" 2>/dev/null || true
    pkill -f "rviz2" 2>/dev/null || true
    pkill -f "gz sim" 2>/dev/null || true
    pkill -f "gzserver" 2>/dev/null || true
    pkill -f "ros_gz" 2>/dev/null || true
    pkill -f "ros2 daemon" 2>/dev/null || true
    ok "清理完成"
}

# 测试：生成 URDF → 检查 → 发布 → 验证 topic
test() {
    activate
    info "完整测试流程"

    # 1. 检查 URDF
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "1/4 URDF 结构 OK"

    # 2. 启动 robot_state_publisher
    info "2/4 启动 robot_state_publisher ..."
    ros2 run robot_state_publisher robot_state_publisher "$TMP_URDF" &
    RSP_PID=$!
    sleep 5

    # 3. 检查 topic
    info "3/4 检查 topic ..."
    ros2 topic info /robot_description 2>/dev/null && ok "  /robot_description OK" || warn "  /robot_description 失败"
    ros2 topic info /tf 2>/dev/null && ok "  /tf OK" || warn "  /tf 失败"
    ros2 topic info /tf_static 2>/dev/null && ok "  /tf_static OK" || warn "  /tf_static 失败"

    # 4. 检查 TF 树
    info "4/4 TF 树:"
    ros2 run tf2_tools view_frames --ros-args -r __ns:=/ 2>/dev/null || true
    kill $RSP_PID 2>/dev/null
    echo ""
    ok "测试完成！查看 frames.pdf 获取 TF 树"
}

# 主入口
CMD="${1:-help}"
case "$CMD" in
    build)  build ;;
    check)  check ;;
    viz)    viz ;;
    sim)    sim ;;
    all)    all ;;
    clean)  clean ;;
    test)   test ;;
    help|*)
        echo ""
        echo "用法: ./run.sh <命令>"
        echo ""
        echo "命令:"
        echo "  build   构建工作空间"
        echo "  check   验证 URDF 结构"
        echo "  viz     启动 RViz2 可视化（无仿真）"
        echo "  sim     启动 Gazebo Sim 仿真"
        echo "  all     同时启动仿真 + RViz"
        echo "  test    完整测试：URDF → publisher → topic → TF"
        echo "  clean   清理所有残留 ROS2 进程"
        echo ""
        ;;
esac
