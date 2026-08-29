# WHEELTEC ROS 工程教材

WHEELTEC ROS 工程教材围绕一台轮式机器人的开发流程展开。读者先认识 ROS 2 和机器人的软硬件结构，再完成上电、底盘控制、传感器接入、建图导航和系统维护。

!!! note "项目说明"
    本教材是非官方学习项目，不代表 WHEELTEC 官方文档。产品名称和商标归其权利人所有；涉及具体型号、接线和固件操作时，应以设备标签、随货清单和当前系统状态为准。

ROS 2 是正文默认环境。使用 ROS 1 旧设备时，请查看[ROS 1 兼容与旧设备维护](appendices/a-ros1-maintenance.md)。R680 的控制板、固件和机械维护集中在第九篇。

!!! warning "先保证安全"
    任何可能让机器人运动的测试，都应先清空周围区域并准备断电。烧录控制板程序前必须确认控制板型号、备份出厂固件，并准备可用的恢复方式。固件的定义和版本关系见第 6 章。

## 第一次学习 ROS 2

对机器人、Linux、ROS 2 或嵌入式硬件尚不熟悉的读者，可按顺序阅读第 1～9 章。第一篇建立 ROS 与计算机基础，第二篇补齐硬件、接口、传感器和闭环控制，再进入实机操作。

1. [第 1 章：认识 ROS 与 ROS 2](01-foundations/01-understanding-ros.md)
2. [第 2 章：一台 ROS 机器人如何工作](01-foundations/02-robot-system-overview.md)
3. [第 3 章：Ubuntu、终端与程序](01-foundations/03-ubuntu-terminal-programs.md)
4. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
5. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
6. [第 6 章：主控、控制板与固件](02-hardware-basics/06-controller-and-firmware.md)
7. [第 7 章：电气接口与通信](02-hardware-basics/07-electrical-interfaces-communication.md)
8. [第 8 章：传感器与状态反馈](02-hardware-basics/08-sensors-and-feedback.md)
9. [第 9 章：底盘运动与闭环控制](02-hardware-basics/09-chassis-motion-control.md)

## 按任务进入

- 想先理解 ROS 2 的基本工作方式：从[第一篇：从零认识 ROS 机器人](01-foundations/index.md)开始。
- 第一次学习机器人硬件：进入[第二篇：机器人硬件、接口与控制基础](02-hardware-basics/index.md)。
- 第一次使用机器人：完成第二篇后，从[识别你的机器人配置](03-bringup/10-identify-configuration.md)开始。
- 已经能连接主控，准备做 ROS 2 开发：进入[ROS 2 环境与源码版本选择](05-ros2-development/22-environment-and-source-selection.md)。
- 准备建图和导航：先完成[传感器自检](06-sensors-navigation/29-sensor-checks.md)。
- 维护 R680：先查看[R680 硬件、接线与 OLED 状态](09-r680-platform/46-r680-hardware-wiring-oled.md)。

完整的章节组合见[阅读路径](reading-paths.md)。术语不清楚时可查[术语表](glossary.md)。

## 验证状态

页面中的“资料核对通过，实机未验证”表示：步骤已根据现有材料整理，但尚缺少当前设备的运行记录。
