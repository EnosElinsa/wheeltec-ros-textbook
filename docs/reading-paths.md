# 阅读路径

先确定要完成的工作，再从对应路径进入。箭头表示建议的阅读顺序，不是必须完成的实机操作。

## 第一次学习 ROS 2

适合没有机器人、Linux 或 ROS 2 经验的读者。前五章可以使用只读路线；第 6 章开始才进入实机接入。

```text
1 → 2 → 3 → 4 → 5 → 6
```

1. [第 1 章：一台 ROS 机器人由什么组成](01-foundations/01-robot-components.md)
2. [第 2 章：Ubuntu、终端与程序](01-foundations/02-ubuntu-terminal-programs.md)
3. [第 3 章：ROS 2 解决什么问题](01-foundations/03-what-ros2-solves.md)
4. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
5. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
6. [第 6 章：识别机器人配置](02-bringup/06-identify-configuration.md)

## 已熟悉 Linux，刚开始学 ROS 2

前置知识：会打开终端、执行命令并阅读文字输出；不要求已经连接机器人。

```text
3 → 4 → 5 → 18
```

1. [第 3 章：ROS 2 解决什么问题](01-foundations/03-what-ros2-solves.md)
2. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
3. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
4. [第 18 章：环境与源码选择](04-ros2-development/18-environment-and-source-selection.md)

## 已熟悉 ROS 2，第一次接入机器人

前置知识：理解节点、话题和基本观察命令；如果还不了解这些概念，请先读第一篇。

```text
6 → 7 → 8 → 9 → 10
```

1. [第 6 章：识别机器人配置](02-bringup/06-identify-configuration.md)
2. [第 7 章：电源与接线安全](02-bringup/07-power-and-wiring.md)
3. [第 8 章：首次上电](02-bringup/08-first-power-on.md)
4. [第 9 章：连接主控](02-bringup/09-connect-controller.md)
5. [第 10 章：基线诊断](02-bringup/10-baseline-diagnosis.md)

## 建图与导航

前置知识：完成第一篇，能解释节点、话题和消息；开始实机操作前，还要完成第 6～10 章的安全接入检查。

```text
3 → 4 → 5 → 18 → 25 → 26 → 27 → 28
```

1. [第 3 章：ROS 2 解决什么问题](01-foundations/03-what-ros2-solves.md)
2. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
3. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
4. [第 18 章：环境与源码选择](04-ros2-development/18-environment-and-source-selection.md)
5. [第 25 章：传感器自检](05-sensors-navigation/25-sensor-checks.md)
6. [第 26 章：激光雷达与二维建图](05-sensors-navigation/26-lidar-and-mapping.md)
7. [第 27 章：地图保存、定位与坐标验证](05-sensors-navigation/27-map-localization-tf.md)
8. [第 28 章：Nav2 导航](05-sensors-navigation/28-nav2-navigation.md)

## STM32 固件开发

前置知识：完成第 6～10 章，确认控制板型号和底盘基线；烧录前必须准备恢复方式。

1. [第 33 章：固件架构与 FreeRTOS](06-stm32-firmware/33-firmware-architecture-freertos.md)
2. [第 34 章：硬件初始化、车型与接口](06-stm32-firmware/34-hardware-init-model-interfaces.md)
3. [第 35 章：电机控制与 PID](06-stm32-firmware/35-motor-control-pid.md)
4. [第 36 章：编译、烧录与回滚](06-stm32-firmware/36-build-flash-rollback.md)
5. [第 37 章：ROS 2 与 STM32 联调](06-stm32-firmware/37-ros2-stm32-integration.md)

## R680 维护

前置知识：完成第 6 章的配置识别和第 17 章的底盘标定；涉及固件时，先确认控制板、编码器和车型。

```text
6 → 17 → 42 → 43 → 45
```

1. [第 6 章：识别机器人配置](02-bringup/06-identify-configuration.md)
2. [第 17 章：标定与底盘故障](03-chassis-control/17-calibration-and-faults.md)
3. [第 42 章：R680 硬件、接线与 OLED](08-r680-platform/42-r680-hardware-wiring-oled.md)
4. [第 43 章：R680 调试、源码与固件](08-r680-platform/43-r680-debug-source-firmware.md)
5. [第 45 章：日志、备份、升级与恢复](09-deployment-maintenance/45-logs-backup-upgrade-recovery.md)
