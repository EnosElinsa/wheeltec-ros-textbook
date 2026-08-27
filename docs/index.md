# WHEELTEC ROS 工程教材

WHEELTEC ROS 工程教材围绕一台轮式机器人的开发流程展开。读者先认识 ROS 2 和机器人的软硬件结构，再完成上电、底盘控制、传感器接入、建图导航和系统维护。

!!! note "项目说明"
    本教材是非官方学习项目，不代表 WHEELTEC 官方文档。产品名称和商标归其权利人所有；涉及具体型号、接线和固件操作时，应以设备标签、随货清单和当前系统状态为准。

ROS 2 是正文默认环境。使用 ROS 1 旧设备时，请查看[ROS 1 兼容与旧设备维护](appendices/a-ros1-maintenance.md)。R680 的控制板、固件和机械维护集中在第八篇。

!!! warning "先保证安全"
    任何可能让机器人运动的测试，都应先清空周围区域并准备断电。烧录固件前必须确认控制板型号、备份出厂固件，并准备可用的恢复方式。

## 第一次学习 ROS 2

对机器人、Linux 或 ROS 2 尚不熟悉的读者，可按顺序阅读第一篇第 1～5 章。每章都提供概念说明、示例输出和练习，便于先建立模型，再连接实机。

1. [第 1 章：认识 ROS 与 ROS 2](01-foundations/01-understanding-ros.md)
2. [第 2 章：一台 ROS 机器人如何工作](01-foundations/02-robot-system-overview.md)
3. [第 3 章：Ubuntu、终端与程序](01-foundations/03-ubuntu-terminal-programs.md)
4. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
5. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)

## 按任务进入

- 想先理解 ROS 2 的基本工作方式：从[第一篇：从零认识 ROS 机器人](01-foundations/index.md)开始。
- 第一次使用机器人：从[识别你的机器人配置](02-bringup/06-identify-configuration.md)开始。
- 已经能连接主控，准备做 ROS 2 开发：进入[ROS 2 环境与源码版本选择](04-ros2-development/18-environment-and-source-selection.md)。
- 准备建图和导航：先完成[传感器自检](05-sensors-navigation/25-sensor-checks.md)。
- 维护 R680：先查看[R680 硬件、接线与 OLED 状态](08-r680-platform/42-r680-hardware-wiring-oled.md)。

完整的章节组合见[阅读路径](reading-paths.md)。术语不清楚时可查[术语表](glossary.md)。

## 验证状态

页面中的“资料核对通过，实机未验证”表示：步骤已根据现有材料整理，但尚缺少当前设备的运行记录。
