#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

// 1. 定义一个普通的全局/静态回调函数（不再属于任何类）
void cb(const std_msgs::msg::String::SharedPtr msg) {
    // 这里的日志器需要通过一个特定的宏来获取，或者直接用 std::cout
    RCLCPP_INFO(rclcpp::get_logger("listener_logger"), "[cpp] I heard: %s", msg->data.c_str());
}

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);

    // 2. 创建纯节点对象
    auto node = rclcpp::Node::make_shared("listener_cpp_lab3");

    // 3. 创建订阅者，直接传入普通函数指针 'cb'
    // 不需要写令人头疼的 std::bind 和 std::placeholders
    auto sub = node->create_subscription<std_msgs::msg::String>("chatter", 10, cb);

    // 4. 进入阻塞循环，等待接收消息
    rclcpp::spin(node);

    rclcpp::shutdown();
    return 0;
}