cmake_minimum_required(VERSION 3.10)
project(my_robot_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()