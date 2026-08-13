
#include <chrono>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

using namespace std::chrono_literals;

class SquareDriver : public rclcpp::Node {
public:
  SquareDriver() : Node("square_driver_cpp") {
    pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10);
    linear_speed_ = 1.0;
    angular_speed_ = 1.57;
    forward_time_s_ = 2.0;
    turn_time_s_ = 1.0;
  }

  void run_square() {
    geometry_msgs::msg::Twist msg;
    std::this_thread::sleep_for(1s);

    for (int i = 0; i < 4 && rclcpp::ok(); i++) {
      msg.linear.x = linear_speed_;
      msg.angular.z = 0.0;
      publish_for_duration(msg, forward_time_s_);

      msg.linear.x = 0.0;
      msg.angular.z = angular_speed_;
      publish_for_duration(msg, turn_time_s_);
    }

    msg.linear.x = 0.0;
    msg.angular.z = 0.0;
    pub_->publish(msg);
  }

private:
  void publish_for_duration(const geometry_msgs::msg::Twist & msg, double seconds) {
    auto t_end = this->now() + rclcpp::Duration::from_seconds(seconds);
    while (this->now() < t_end && rclcpp::ok()) {
      pub_->publish(msg);
      rclcpp::sleep_for(100ms);
    }
  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
  double linear_speed_;
  double angular_speed_;
  double forward_time_s_;
  double turn_time_s_;
};

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SquareDriver>();
  node->run_square();
  rclcpp::shutdown();
  return 0;
}

