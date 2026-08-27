# 阅读路径

不必从头读完整本教材。先确定眼前要完成的工作，再沿对应路径阅读。

## ROS 2 理论基础

1. [ROS 2 是什么](01-foundations/03-what-ros2-solves.md)
2. [系统图与通信模型](01-foundations/05-ros2-communication.md)
3. [工作空间、功能包与运行时环境](04-ros2-development/19-workspace-packages-build.md)
4. [时间、QoS、TF 与实机诊断](04-ros2-development/index.md)

读完第一篇后，再按自己的硬件和任务进入第二篇或第四篇。第一篇解释“系统为什么这样工作”，后续章节负责“在这台机器上怎样操作”。

## 新机首次使用

1. [识别机器人配置](02-bringup/06-identify-configuration.md)
2. [电源与接线安全](02-bringup/07-power-and-wiring.md)
3. [首次上电](02-bringup/08-first-power-on.md)
4. [连接主控](02-bringup/09-connect-controller.md)
5. [基线诊断](02-bringup/10-baseline-diagnosis.md)

## ROS 2 建图与导航

1. [环境与源码选择](04-ros2-development/18-environment-and-source-selection.md)
2. [传感器自检](05-sensors-navigation/25-sensor-checks.md)
3. [雷达与二维建图](05-sensors-navigation/26-lidar-and-mapping.md)
4. [地图、定位与 TF](05-sensors-navigation/27-map-localization-tf.md)
5. [Nav2 导航](05-sensors-navigation/28-nav2-navigation.md)

## STM32 固件开发

1. [固件架构与 FreeRTOS](06-stm32-firmware/33-firmware-architecture-freertos.md)
2. [硬件初始化、车型与接口](06-stm32-firmware/34-hardware-init-model-interfaces.md)
3. [电机控制与 PID](06-stm32-firmware/35-motor-control-pid.md)
4. [编译、烧录与回滚](06-stm32-firmware/36-build-flash-rollback.md)
5. [ROS 2 与 STM32 联调](06-stm32-firmware/37-ros2-stm32-integration.md)

## R680 维护

1. [识别机器人配置](02-bringup/06-identify-configuration.md)
2. [底盘标定与故障](03-chassis-control/17-calibration-and-faults.md)
3. [R680 硬件、接线与 OLED](08-r680-platform/42-r680-hardware-wiring-oled.md)
4. [R680 调试、源码与固件](08-r680-platform/43-r680-debug-source-firmware.md)
5. [日志、备份、升级与恢复](09-deployment-maintenance/45-logs-backup-upgrade-recovery.md)
