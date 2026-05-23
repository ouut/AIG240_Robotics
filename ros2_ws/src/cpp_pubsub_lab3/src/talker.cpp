#include <chrono>
#include <string>
#include <unistd.h>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

// 全局变量
rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub;
int count = 0;
std::string hostname = "unknown";

// 简化回调：让它不带任何参数，内部需要的东西直接在 main 函数里通过 Lambda 喂进去
void timer_callback(rclcpp::Node::SharedPtr node) {
    auto msg = std_msgs::msg::String();

    // 1. 获取当前 ROS 2 时间戳并转换成秒
    rclcpp::Time now = node->get_clock()->now();
    double ros_time_sec = now.seconds();

    // 2. 拼接消息：[Seq: X] [Time: X.X] [Host: X]
    msg.data = "[Seq: " + std::to_string(count++) + "] " +
               "[Time: " + std::to_string(ros_time_sec) + "] " +
               "[Host: " + hostname + "]";

    RCLCPP_INFO(node->get_logger(), "Publishing: %s", msg.data.c_str());
    pub->publish(msg);
}

int main(int argc, char * argv[]){
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("talker_cpp_lab3");

    // 获取主机名
    char host_buffer[256];
    if (gethostname(host_buffer, sizeof(host_buffer)) == 0) {
        hostname = std::string(host_buffer);
    }

    node->declare_parameter<double>("publish_rate_hz", 5.0);
    double hz = node->get_parameter("publish_rate_hz").as_double();

    pub = node->create_publisher<std_msgs::msg::String>("chatter", 10);

    // 将频率转换为时间间隔周期
    std::chrono::duration<double> period(1.0 / hz);
    
    // ==================== 🛠️ 核心修改：使用现代 Lambda 表达式 ====================
    // 用 `[node]` 捕获当前的 node 指针，Jazzy 的模板会一秒识别并通过编译
    auto timer = node->create_wall_timer(
        period, [node]() -> void { timer_callback(node); });
    // =========================================================================

    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}