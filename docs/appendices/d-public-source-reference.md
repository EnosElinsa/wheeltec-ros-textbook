---
status: complete
---

# D. 教材代码资源

按用途查找示例代码、关键文件和对应章节。

## ROS 2 基础与启动

### C++ 发布订阅示例

- 代码目录：[`examples/ros2/pubsub/cpp`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/examples/ros2/pubsub/cpp)
- 正文入口：[C++ 发布订阅示例](../05-ros2-development/24-nodes-topics-services-actions.md#pubsub-code-resource)
- 关键文件：`CMakeLists.txt`、`package.xml`、`src/publisher.cpp`、`src/subscriber.cpp`

### Python 发布订阅示例

- 代码目录：[`examples/ros2/pubsub/python`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/examples/ros2/pubsub/python)
- 正文入口：[Python 发布订阅示例](../05-ros2-development/24-nodes-topics-services-actions.md#pubsub-code-resource)
- 关键文件：`package.xml`、`py_pubsub/publisher.py`、`py_pubsub/subscriber.py`、`setup.py`

### 追踪底盘启动链

- 代码目录：[`ros2/robot/turn-on-wheeltec-robot`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/robot/turn-on-wheeltec-robot)
- 正文入口：[追踪底盘启动链](../05-ros2-development/25-launch-and-parameters.md#bringup-launch-chain)
- 关键文件：`launch/base_serial.launch.py`、`launch/robot_mode_description.launch.py`、`launch/turn_on_wheeltec_robot.launch.py`、`src/wheeltec_robot.cpp`

## ROS 2 导航

### 多点导航示例

- 代码目录：[`ros2/navigation/nav2-waypoint-cycle/nav2_waypoint_cycle`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/nav2-waypoint-cycle/nav2_waypoint_cycle)
- 正文入口：[多点导航示例](../06-sensors-navigation/34-nav2-navigation.md#nav2-code-resource)
- 关键文件：`nav2_waypoint_cycle/waypoint_cycle.py`、`package.xml`

### 路径跟踪示例

- 代码目录：[`ros2/navigation/path-follow/wheeltec_path_follow`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/path-follow/wheeltec_path_follow)
- 正文入口：[路径跟踪示例](../06-sensors-navigation/35-waypoints-path-exploration.md#path-follow-code-resource)
- 关键文件：`launch/follow_path.launch.py`、`package.xml`、`scripts/follow_path.py`

### 视觉建图与导航功能包

- 代码目录：[`ros2/navigation/vision-nav/wheeltec_vision_nav`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/vision-nav/wheeltec_vision_nav)
- 正文入口：[视觉建图与导航功能包](../06-sensors-navigation/40-visual-runtime.md#vision-nav-code-resource)
- 关键文件：`config/ekf_visual.yaml`、`config/rtabmap_visual.yaml`、`launch/vision_mapping.launch.py`、`launch/vision_navigation.launch.py`、`package.xml`、`wheeltec_vision_nav/ekf_inputs_logic.py`、`wheeltec_vision_nav/emitter_pair_logic.py`、`wheeltec_vision_nav/launch_utils.py`、`wheeltec_vision_nav/vo_watchdog_logic.py`

## ROS 1 维护

### 人体消息与跟随节点

- 代码目录：[`ros1/maintenance/bodyreader`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros1/maintenance/bodyreader)
- 正文入口：[人体消息与跟随节点](../08-advanced-applications/52-mmwave-human-deep-learning.md#bodyreader-code-resource)
- 关键文件：`launch/bodyfollow.launch`、`msg/body.msg`、`package.xml`、`src/bodydata_process.cpp`、`src/follower.cpp`

## 视觉与应用

### KCF 跟踪示例

- 代码目录：[`applications/kcf-tracker/wheeltec_robot_kcf_model`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/applications/kcf-tracker/wheeltec_robot_kcf_model)
- 正文入口：[KCF 跟踪示例](../06-sensors-navigation/38-vision-applications.md#kcf-code-resource)
- 关键文件：`launch/kcf_tracker.launch.py`、`package.xml`、`wheeltec_robot_kcf_model/kcf_tracker_node.py`、`wheeltec_robot_kcf_model/pid_controller.py`

## STM32 外设实验

### 编码器实验

- 代码目录：[`stm32/labs/encoder/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/encoder/stm32f103-stdperiph)
- 正文入口：[编码器实验](../07-stm32-firmware/46-hardware-init-model-interfaces.md#stm32-encoder-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/Encoder.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`

### PWM 实验

- 代码目录：[`stm32/labs/pwm/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/pwm/stm32f103-stdperiph)
- 正文入口：[PWM 实验](../07-stm32-firmware/46-hardware-init-model-interfaces.md#stm32-pwm-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/PWM.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`

### UART 实验

- 代码目录：[`stm32/labs/uart/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/uart/stm32f103-stdperiph)
- 正文入口：[UART 实验](../07-stm32-firmware/46-hardware-init-model-interfaces.md#stm32-uart-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/UART1.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`

## STM32 控制

### 电机控制

- 代码目录：[`stm32/control/motor/stm32f4-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/control/motor/stm32f4-stdperiph)
- 正文入口：[电机控制](../07-stm32-firmware/47-motor-control-pid.md#stm32-motor-control)
- 关键文件：`USER/WHEELTEC.uvprojx`、`USER/main.c`

### PID 控制

- 代码目录：[`stm32/control/pid/stm32f4-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/control/pid/stm32f4-stdperiph)
- 正文入口：[PID 控制](../07-stm32-firmware/47-motor-control-pid.md#stm32-pid-control)
- 关键文件：`USER/WHEELTEC.uvprojx`、`USER/main.c`

## R680 固件

### R680 串口与 CAN 固件

- 代码目录：[`r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01)
- 正文入口：[R680 串口与 CAN 固件](../09-r680-platform/55-r680-debug-source-firmware.md#r680-code-resource)
- 关键文件：`HARDWARE/can.c`、`HARDWARE/usartx.c`、`USER/WHEELTEC.uvprojx`、`USER/main.c`
