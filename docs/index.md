# WHEELTEC ROS 工程教材

这套教材写给已经拿到 WHEELTEC 机器人的使用者。它先用第一篇建立 ROS 2 的系统模型，再沿着实机工作顺序展开：确认硬件和接线，检查底盘与传感器，进入 ROS 2 开发、建图导航、固件维护和故障排查。

!!! note "项目说明"
    本教材是基于用户资料整理的非官方学习项目，不代表 WHEELTEC 官方文档。产品名称和商标归其权利人所有；涉及具体型号、接线和固件操作时，应以设备随附的原始资料为最终依据。

ROS 2 是正文默认环境。使用 ROS 1 旧设备时，请查看[ROS 1 兼容与旧设备维护](appendices/a-ros1-maintenance.md)。R680 的控制板、固件和机械维护集中在第八篇。

!!! warning "先保证安全"
    任何可能让机器人运动的测试，都应先清空周围区域并准备断电。烧录固件前必须确认控制板型号、备份出厂固件，并准备可用的恢复方式。

## 从哪里开始

- 想先理解 ROS 2 的基本工作方式：从[第一篇：ROS 2 理论基础](01-foundations/index.md)开始。
- 第一次使用机器人：从[识别你的机器人配置](02-bringup/06-identify-configuration.md)开始。
- 已经能连接主控，准备做 ROS 2 开发：进入[ROS 2 环境与源码版本选择](04-ros2-development/18-environment-and-source-selection.md)。
- 准备建图和导航：先完成[传感器自检](05-sensors-navigation/25-sensor-checks.md)。
- 维护 R680：先查看[R680 硬件、接线与 OLED 状态](08-r680-platform/42-r680-hardware-wiring-oled.md)。

完整的章节组合见[阅读路径](reading-paths.md)。术语不清楚时可查[术语表](glossary.md)。

## 验证状态

教材正文按学习和实机操作顺序组织，可以独立阅读。无法在当前环境完成的实机操作会明确标注“资料核对通过，实机未验证”。
