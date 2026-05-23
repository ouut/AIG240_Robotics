#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

int main(int argc, char * argv[]){
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("talker_cpp_lab3");
    auto pub = node->create_publisher<std_msgs::msg::String>("chatter", 10);
    rclcpp::WallRate rate(5);
    int count = 0;
    while(rclcpp::ok()){
        auto msg = std_msgs::msg::String();
        msg.data = "[cpp] lab3 hell #" + std::to_string(count++);
        RCLCPP_INFO(node->get_logger(), "%s", msg.data.c_str());
        pub->publish(msg);

        rclcpp::spin_some(node);
        rate.sleep();
    }

    rclcpp::shutdown();
    return 0;
}