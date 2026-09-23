# 阅读路径

根据当前目标选择一条路径。箭头表示知识或操作的先后关系。

## 第一次学习 ROS 2

适合第一次接触机器人、Linux、ROS 2 和嵌入式硬件的读者。第 1～9 章依次建立软件、硬件、通信、传感器和控制基础，第 10 章开始接入实机。

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

1. [第 1 章：认识 ROS 与 ROS 2](01-foundations/01-understanding-ros.md)
2. [第 2 章：一台 ROS 机器人如何工作](01-foundations/02-robot-system-overview.md)
3. [第 3 章：Ubuntu、终端与程序](01-foundations/03-ubuntu-terminal-programs.md)
4. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
5. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
6. [第 6 章：主控、控制板与固件](02-hardware-basics/06-controller-and-firmware.md)
7. [第 7 章：电气接口与通信](02-hardware-basics/07-electrical-interfaces-communication.md)
8. [第 8 章：传感器与状态反馈](02-hardware-basics/08-sensors-and-feedback.md)
9. [第 9 章：底盘运动与闭环控制](02-hardware-basics/09-chassis-motion-control.md)
10. [第 10 章：识别机器人配置](03-bringup/10-identify-configuration.md)

## 已熟悉 Linux，刚开始学 ROS 2

前置能力：会打开终端、执行命令并阅读文字输出。

```text
1 → 4 → 5 → 22
```

1. [第 1 章：认识 ROS 与 ROS 2](01-foundations/01-understanding-ros.md)
2. [第 4 章：第一次观察 ROS 2](01-foundations/04-first-ros2-observation.md)
3. [第 5 章：ROS 2 程序怎样协作](01-foundations/05-ros2-communication.md)
4. [第 22 章：环境与源码选择](05-ros2-development/22-environment-and-source-selection.md)

## 已熟悉 ROS 2，第一次接入机器人

前置能力：能够解释节点、话题和消息，理解第 6～9 章的硬件、通信、传感器和控制链，并会使用基本观察命令。

```text
10 → 11 → 12 → 13 → 14
```

1. [第 10 章：识别机器人配置](03-bringup/10-identify-configuration.md)
2. [第 11 章：电源与接线安全](03-bringup/11-power-and-wiring.md)
3. [第 12 章：首次上电](03-bringup/12-first-power-on.md)
4. [第 13 章：连接主控](03-bringup/13-connect-controller.md)
5. [第 14 章：基线诊断](03-bringup/14-baseline-diagnosis.md)

## 建图与导航

前置能力：能够解释节点、话题和消息，并已按第 10～14 章完成安全接入检查。

```text
29 → 30 → 31 → 32 → 33
```

1. [第 29 章：传感器、驱动与话题自检](06-sensors-navigation/29-sensor-checks.md)
2. [第 30 章：里程计、TF 与时间](06-sensors-navigation/30-odometry-tf-time.md)
3. [第 31 章：激光雷达与二维建图](06-sensors-navigation/31-lidar-and-mapping.md)
4. [第 32 章：地图保存、定位与坐标验证](06-sensors-navigation/32-map-localization-tf.md)
5. [第 33 章：Nav2 导航](06-sensors-navigation/33-nav2-navigation.md)

R680 用 D435C 红外与深度建图导航时，读完第 29～30 章后阅读第 38 章 [运行过程](06-sensors-navigation/38-visual-runtime.md) 与第 39 章 [操作](06-sensors-navigation/39-visual-operation.md)。

## STM32 固件开发

前置知识：完成第 10～14 章，确认控制板型号和底盘基线；烧录前必须准备恢复方式。

1. [第 40 章：固件架构与 FreeRTOS](07-stm32-firmware/40-firmware-architecture-freertos.md)
2. [第 41 章：硬件初始化、车型与接口](07-stm32-firmware/41-hardware-init-model-interfaces.md)
3. [第 42 章：电机控制与 PID](07-stm32-firmware/42-motor-control-pid.md)
4. [第 43 章：编译、烧录与回滚](07-stm32-firmware/43-build-flash-rollback.md)
5. [第 44 章：ROS 2 与 STM32 联调](07-stm32-firmware/44-ros2-stm32-integration.md)

## R680 维护

前置知识：完成第 10 章的配置识别和第 21 章的底盘标定；涉及固件时，先确认控制板、编码器和车型。

```text
10 → 21 → 49 → 50 → 52
```

1. [第 10 章：识别机器人配置](03-bringup/10-identify-configuration.md)
2. [第 21 章：标定与底盘故障](04-chassis-control/21-calibration-and-faults.md)
3. [第 49 章：R680 硬件、接线与 OLED](09-r680-platform/49-r680-hardware-wiring-oled.md)
4. [第 50 章：R680 调试、源码与固件](09-r680-platform/50-r680-debug-source-firmware.md)
5. [第 52 章：日志、备份、升级与恢复](10-deployment-maintenance/52-logs-backup-upgrade-recovery.md)
