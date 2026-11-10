---
status: complete
---

# 55. R680 底盘调试、源码与固件维护 {#r680-code-resource}

## 55.1 学习目标

从工程配置和主循环入手，追踪 R680 固件中的串口/CAN 通信、车型参数与电机控制，为故障排查和固件维护定位入口。

## 55.2 适用范围

示例工程对应 C50C 控制板、STM32F407、麦克纳姆轮、霍尔编码器和串口/CAN 通信。维护其他车型时，按实机选择匹配的运动学、轮号、编码器与通信配置。

!!! example "源码入口：C50C/F407 麦轮霍尔固件"
    [查看工程目录](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/62aacaed782091b06060ace276c64e9aaf84ae6b/r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01)。主要文件为 `USER/WHEELTEC.uvprojx`、`USER/main.c`、`HARDWARE/usartx.c` 和 `HARDWARE/can.c`。

## 55.3 源码阅读顺序

1. 打开 `USER/WHEELTEC.uvprojx`，查看目标芯片、启动文件、编译宏和 Flash/RAM 配置。
2. 从 `USER/main.c` 追踪初始化和主循环，找到通信接收、控制更新和状态上报的调用位置。
3. 阅读 `HARDWARE/usartx.c` 和 `HARDWARE/can.c`，整理帧格式、校验方式、速度单位及反馈字段。
4. 查找车型与编码器常量，核对电机数量、轮号、方向、减速比和计数换算。
5. 追踪自检、急停和通信超时处理，确认这些条件怎样影响电机使能。

## 55.4 实机维护准备

- 按控制板丝印确认板卡与 MCU，按原理图核对引脚、供电和通信电平。
- 保存现有固件、参数和工程配置，确认下载方式与恢复步骤；烧录流程见[第 48 章](../07-stm32-firmware/48-build-flash-rollback.md)。
- 接线与改线时断电，首次通信测试保持电机失能或车轮架空，并准备急停。
- 从零速命令开始，检查串口/CAN 回包，再逐轮核对方向与编码器反馈，最后进行低速测试。

阿克曼、差速、全向轮及多驱主从结构的控制参数和接口分配各不相同。更换固件前，逐项比较本车配置与工程设置。

## 55.5 故障记录

记录板卡、车型、编码器、固件版本、故障现象和复现步骤。通信异常附上串口/CAN 帧，运动异常记录目标速度、轮号、实际方向及编码器读数，便于区分协议、参数和硬件问题。

## 章节导航

[上一章：R680 硬件、接线与 OLED 状态](54-r680-hardware-wiring-oled.md) · [返回本篇](index.md) · [下一章：网络、Docker、系统镜像与主控差异](../10-deployment-maintenance/56-network-docker-images.md)
