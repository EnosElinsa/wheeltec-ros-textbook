# 阅读路径

不必从头读完整本教材。先确定眼前要完成的工作，再沿对应路径阅读。

## ROS 2 理论基础

1. [ROS 2 是什么](00-ros2-theory/t1-what-is-ros2.md)
2. [系统图与通信模型](00-ros2-theory/t2-graph-and-communication.md)
3. [工作空间、功能包与运行时环境](00-ros2-theory/t3-workspace-package-runtime.md)
4. [时间、QoS、TF 与实机诊断](00-ros2-theory/t4-time-qos-tf-diagnosis.md)

读完卷零后，再按自己的硬件和任务进入卷一或卷三。卷零解释“系统为什么这样工作”，后续章节负责“在这台机器上怎样操作”。

## 新机首次使用

1. [识别机器人配置](01-bringup/01-identify-configuration.md)
2. [电源与接线安全](01-bringup/02-power-and-wiring.md)
3. [首次上电](01-bringup/03-first-power-on.md)
4. [连接主控](01-bringup/04-connect-controller.md)
5. [基线诊断](01-bringup/05-baseline-diagnosis.md)

## ROS 2 建图与导航

1. [环境与源码选择](03-ros2-development/13-environment-and-source-selection.md)
2. [传感器自检](04-sensors-navigation/20-sensor-checks.md)
3. [雷达与二维建图](04-sensors-navigation/21-lidar-and-mapping.md)
4. [地图、定位与 TF](04-sensors-navigation/22-map-localization-tf.md)
5. [Nav2 导航](04-sensors-navigation/23-nav2-navigation.md)

## STM32 固件开发

1. [固件架构与 FreeRTOS](05-stm32-firmware/28-firmware-architecture-freertos.md)
2. [硬件初始化、车型与接口](05-stm32-firmware/29-hardware-init-model-interfaces.md)
3. [电机控制与 PID](05-stm32-firmware/30-motor-control-pid.md)
4. [编译、烧录与回滚](05-stm32-firmware/31-build-flash-rollback.md)
5. [ROS 2 与 STM32 联调](05-stm32-firmware/32-ros2-stm32-integration.md)

## R680 维护

1. [识别机器人配置](01-bringup/01-identify-configuration.md)
2. [底盘标定与故障](02-chassis-control/12-calibration-and-faults.md)
3. [R680 硬件、接线与 OLED](07-r680-platform/37-r680-hardware-wiring-oled.md)
4. [R680 调试、源码与固件](07-r680-platform/38-r680-debug-source-firmware.md)
5. [日志、备份、升级与恢复](08-deployment-maintenance/40-logs-backup-upgrade-recovery.md)
