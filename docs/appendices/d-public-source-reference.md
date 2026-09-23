---
status: complete
---

# D. 教材代码资源

本附录是教材使用的代码资源索引。教材正文中的代码入口是主要使用位置；本页用于按用途集中查找同一批资源，不替代正文给出的文件范围、验收方法和安全边界。

所有源码链接固定到提交 `62aacaed782091b06060ace276c64e9aaf84ae6b`。同名目录或后续版本不能自动替代本页所列资源。

## ROS 2 基础与启动

### C++ 发布订阅示例

- 代码目录：[`examples/ros2/pubsub/cpp`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/examples/ros2/pubsub/cpp)
- 正文入口：[C++ 发布订阅示例](../05-ros2-development/24-nodes-topics-services-actions.md#pubsub-code-resource)
- 关键文件：`CMakeLists.txt`、`package.xml`、`src/publisher.cpp`、`src/subscriber.cpp`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅用于通信观察

### Python 发布订阅示例

- 代码目录：[`examples/ros2/pubsub/python`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/examples/ros2/pubsub/python)
- 正文入口：[Python 发布订阅示例](../05-ros2-development/24-nodes-topics-services-actions.md#pubsub-code-resource)
- 关键文件：`package.xml`、`py_pubsub/publisher.py`、`py_pubsub/subscriber.py`、`setup.py`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅用于通信观察

### 追踪底盘启动链

- 代码目录：[`ros2/robot/turn-on-wheeltec-robot`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/robot/turn-on-wheeltec-robot)
- 正文入口：[追踪底盘启动链](../05-ros2-development/25-launch-and-parameters.md#bringup-launch-chain)
- 关键文件：`launch/base_serial.launch.py`、`launch/robot_mode_description.launch.py`、`launch/turn_on_wheeltec_robot.launch.py`、`src/wheeltec_robot.cpp`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅作静态源码追踪；robot_mode_description 仍依赖外部 wheeltec_robot_urdf、mini_mec 和 mini_diff URDF 资源，不能据此启动机器人

## ROS 2 导航

### 多点导航示例

- 代码目录：[`ros2/navigation/nav2-waypoint-cycle/nav2_waypoint_cycle`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/nav2-waypoint-cycle/nav2_waypoint_cycle)
- 正文入口：[多点导航示例](../06-sensors-navigation/33-nav2-navigation.md#nav2-code-resource)
- 关键文件：`nav2_waypoint_cycle/waypoint_cycle.py`、`package.xml`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：运行前核对 Nav2 版本

### 路径跟踪示例

- 代码目录：[`ros2/navigation/path-follow/wheeltec_path_follow`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/path-follow/wheeltec_path_follow)
- 正文入口：[路径跟踪示例](../06-sensors-navigation/34-waypoints-path-exploration.md#path-follow-code-resource)
- 关键文件：`launch/follow_path.launch.py`、`package.xml`、`scripts/follow_path.py`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：不替代实机安全检查

### 视觉建图与导航功能包

- 代码目录：[`ros2/navigation/vision-nav/wheeltec_vision_nav`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros2/navigation/vision-nav/wheeltec_vision_nav)
- 正文入口：[视觉建图与导航功能包](../06-sensors-navigation/38-visual-runtime.md#vision-nav-code-resource)
- 关键文件：`config/ekf_visual.yaml`、`config/rtabmap_visual.yaml`、`launch/vision_mapping.launch.py`、`launch/vision_navigation.launch.py`、`package.xml`、`wheeltec_vision_nav/ekf_inputs_logic.py`、`wheeltec_vision_nav/emitter_pair_logic.py`、`wheeltec_vision_nav/launch_utils.py`、`wheeltec_vision_nav/vo_watchdog_logic.py`
- 核验状态：`runtime_verified`；使用方式：`run`。
- 使用边界：需要本车 R680 底盘、D435C 相机与出厂 wheeltec 功能包；电机使能与急停由现场人员负责

## ROS 1 维护

### 人体消息与跟随节点

- 代码目录：[`ros1/maintenance/bodyreader`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/ros1/maintenance/bodyreader)
- 正文入口：[人体消息与跟随节点](../08-advanced-applications/47-mmwave-human-deep-learning.md#bodyreader-code-resource)
- 关键文件：`launch/bodyfollow.launch`、`msg/body.msg`、`package.xml`、`src/bodydata_process.cpp`、`src/follower.cpp`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：依赖 Astra/OpenNI 运行时和相机，仅静态阅读

## 视觉与应用

### KCF 跟踪示例

- 代码目录：[`applications/kcf-tracker/wheeltec_robot_kcf_model`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/applications/kcf-tracker/wheeltec_robot_kcf_model)
- 正文入口：[KCF 跟踪示例](../06-sensors-navigation/37-vision-applications.md#kcf-code-resource)
- 关键文件：`launch/kcf_tracker.launch.py`、`package.xml`、`wheeltec_robot_kcf_model/kcf_tracker_node.py`、`wheeltec_robot_kcf_model/pid_controller.py`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：依赖相机和初始框条件

## STM32 外设实验

### 编码器实验

- 代码目录：[`stm32/labs/encoder/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/encoder/stm32f103-stdperiph)
- 正文入口：[编码器实验](../07-stm32-firmware/41-hardware-init-model-interfaces.md#stm32-encoder-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/Encoder.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅静态核对

### PWM 实验

- 代码目录：[`stm32/labs/pwm/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/pwm/stm32f103-stdperiph)
- 正文入口：[PWM 实验](../07-stm32-firmware/41-hardware-init-model-interfaces.md#stm32-pwm-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/PWM.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅静态核对

### UART 实验

- 代码目录：[`stm32/labs/uart/stm32f103-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/labs/uart/stm32f103-stdperiph)
- 正文入口：[UART 实验](../07-stm32-firmware/41-hardware-init-model-interfaces.md#stm32-uart-lab)
- 关键文件：`STM32F10x_FWLib/src/stm32f10x_usart.c`、`USER/UART1.uvprojx`、`USER/main.c`、`USER/stm32f10x.h`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：仅静态核对

## STM32 控制

### 电机控制

- 代码目录：[`stm32/control/motor/stm32f4-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/control/motor/stm32f4-stdperiph)
- 正文入口：[电机控制](../07-stm32-firmware/42-motor-control-pid.md#stm32-motor-control)
- 关键文件：`USER/WHEELTEC.uvprojx`、`USER/main.c`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：无编译器与实机证据

### PID 控制

- 代码目录：[`stm32/control/pid/stm32f4-stdperiph`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/stm32/control/pid/stm32f4-stdperiph)
- 正文入口：[PID 控制](../07-stm32-firmware/42-motor-control-pid.md#stm32-pid-control)
- 关键文件：`USER/WHEELTEC.uvprojx`、`USER/main.c`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：无编译器与实机证据

## R680 固件

### 静态诊断串口与 CAN 控制链

- 代码目录：[`r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01`](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01)
- 正文入口：[静态诊断串口与 CAN 控制链](../09-r680-platform/50-r680-debug-source-firmware.md#r680-code-resource)
- 关键文件：`HARDWARE/can.c`、`HARDWARE/usartx.c`、`USER/WHEELTEC.uvprojx`、`USER/main.c`
- 核验状态：`static_reviewed`；使用方式：`static_read`。
- 使用边界：无照片、接线与测量证据，不得烧录或声明硬件验证
