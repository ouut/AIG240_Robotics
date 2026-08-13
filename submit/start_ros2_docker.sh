#!/bin/bash
docker run -d \
  --name ros2 \
  -p 6080:80 \
  --shm-size=512mb \
  -e TZ=America/Toronto \
  -v "$(pwd)/ros2_ws:/home/ubuntu/ros2_ws" \
  --security-opt seccomp=unconfined \
  --restart always \
  tiryoh/ros2-desktop-vnc:jazzy