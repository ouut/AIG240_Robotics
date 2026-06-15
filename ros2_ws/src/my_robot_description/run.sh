#!/usr/bin/env bash
set -e

# ============================================================
# run.sh — my_robot_description one-click launcher
# Usage: ./run.sh [sim|viz|all|build|check|test|clean]
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

# Activate conda env + source workspace
activate() {
    if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "ros2" ]; then
        info "Activating conda env ros2 ..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ros2
    fi
    . "$WS_DIR/install/setup.sh" 2>/dev/null || true
    ok "ROS_DISTRO=$ROS_DISTRO"
}

# Build
build() {
    activate
    info "Building my_robot_description ..."
    info "(file-only package, no compilation; install dir registers the package)"
    cd "$WS_DIR"
    colcon build --packages-select my_robot_description --symlink-install
    . install/setup.sh
    ok "Build complete (subsequent launch/URDF edits don't need rebuild)"
}

# Check URDF
check() {
    activate
    info "Checking URDF ..."
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "URDF structure OK"
    echo ""
    info "Gazebo plugins:"
    grep -n "plugin\|DiffDrive\|gpu_lidar" "$TMP_URDF" || true
}

# Visualize (RViz only, no simulation)
viz() {
    activate
    info "Launching RViz2 visualization ..."
    ros2 launch my_robot_description visualize.launch.py
}

# Gazebo Sim simulation
sim() {
    activate
    info "Launching Gazebo Sim simulation ..."
    ros2 launch my_robot_description simulate.launch.py
}

# Simulation + RViz together
all() {
    activate
    info "Checking URDF ..."
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "URDF OK"

    info "Launching Gazebo Sim ..."
    ros2 launch my_robot_description simulate.launch.py &
    SIM_PID=$!
    sleep 5

    info "Launching RViz2 ..."
    ros2 launch my_robot_description visualize.launch.py &
    VIZ_PID=$!

    echo ""
    echo "============================================"
    info "Simulation + visualization running"
    info "Keyboard control (new terminal):"
    echo "  conda activate ros2"
    echo "  . $WS_DIR/install/setup.sh"
    echo "  ros2 run teleop_twist_keyboard teleop_twist_keyboard"
    echo ""
    info "Press Ctrl+C to stop all"
    echo "============================================"

    trap "kill $SIM_PID $VIZ_PID 2>/dev/null; exit 0" INT TERM
    wait
}

# Kill leftover processes
clean() {
    warn "Killing all ROS2 / Gazebo processes ..."
    pkill -f "robot_state_publisher" 2>/dev/null || true
    pkill -f "joint_state_publisher" 2>/dev/null || true
    pkill -f "rviz2" 2>/dev/null || true
    pkill -f "gz sim" 2>/dev/null || true
    pkill -f "gzserver" 2>/dev/null || true
    pkill -f "ros_gz" 2>/dev/null || true
    pkill -f "ros2 daemon" 2>/dev/null || true
    ok "Cleanup done"
}

# Full test: URDF → publisher → topics → TF
test() {
    activate
    info "Full test pipeline"

    # 1. Check URDF
    TMP_URDF="/tmp/my_robot.urdf"
    xacro "$WS_DIR/src/my_robot_description/urdf/my_robot.urdf.xacro" -o "$TMP_URDF"
    check_urdf "$TMP_URDF"
    ok "1/4 URDF OK"

    # 2. Start robot_state_publisher
    info "2/4 Starting robot_state_publisher ..."
    ros2 run robot_state_publisher robot_state_publisher "$TMP_URDF" &
    RSP_PID=$!
    sleep 5

    # 3. Check topics
    info "3/4 Checking topics ..."
    ros2 topic info /robot_description 2>/dev/null && ok "  /robot_description OK" || warn "  /robot_description FAIL"
    ros2 topic info /tf 2>/dev/null && ok "  /tf OK" || warn "  /tf FAIL"
    ros2 topic info /tf_static 2>/dev/null && ok "  /tf_static OK" || warn "  /tf_static FAIL"

    # 4. TF tree
    info "4/4 TF tree:"
    ros2 run tf2_tools view_frames --ros-args -r __ns:=/ 2>/dev/null || true
    kill $RSP_PID 2>/dev/null
    echo ""
    ok "Test complete — open frames.pdf for TF tree"
}

# Main
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
        echo "Usage: ./run.sh <command>"
        echo ""
        echo "Commands:"
        echo "  build   Build the workspace"
        echo "  check   Validate URDF structure"
        echo "  viz     Launch RViz2 visualization (no simulation)"
        echo "  sim     Launch Gazebo Sim simulation"
        echo "  all     Launch sim + RViz together"
        echo "  test    Full pipeline: URDF → publisher → topics → TF"
        echo "  clean   Kill all leftover ROS2/Gazebo processes"
        echo ""
        ;;
esac
