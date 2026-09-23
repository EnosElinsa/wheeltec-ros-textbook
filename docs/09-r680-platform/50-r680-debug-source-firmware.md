---
status: complete
---

# 50. R680 底盘调试、源码与固件维护 {#r680-code-resource}

## 50.1 学习目标

本章只阅读 C50C 控制板、STM32F407 微控制器、麦克纳姆轮和霍尔编码器对应的串口/CAN 固件变体。读者需要找到工程入口和协议代码，并核对是否具备匹配的实机照片、接线与测量记录。本章不执行烧录或运行测试。

## 50.2 适用范围

!!! example "唯一可消费资源：C50C/F407 麦轮霍尔/serial-can"
    资源目录：`r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01/`。查看 `USER/WHEELTEC.uvprojx`、`USER/main.c`、`HARDWARE/usartx.c`、`HARDWARE/can.c`。源码固定在 [ebae2342](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/ebae2342709c756cb8fa387ccdbd6e5733f9219a/r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01)。

    验收：能定位工程、主循环和双协议接口。边界：无匹配实机照片、接线与测量证据时，只能静态阅读；不得烧录或声明硬件验证。

本章没有提供其他控制板、底盘、编码器或主从组合的公开固件。上述变体的结论只适用于目录中明确写出的硬件组合。

## 50.3 静态核对

核对 Keil UV 工程中选择的芯片、启动文件、串口/CAN 源码和控制常量。当前材料缺少匹配实机的验证证据，因此本章停在源码阅读阶段；架空、低速、烧录、回滚和主从测试均不执行。

## 50.4 安全边界

进入实机测试前，必须先具备匹配硬件的照片、接线、测量和急停记录。缺少这些记录时，保持电机断开，不烧录固件，也不作运行结论。阿克曼、差速、全向轮、四驱和 8 驱主从结构需要各自独立的固件与实机证据。

## 50.5 故障记录

仅记录静态发现：设备字段、协议文件和工程路径。硬件异常、轮号、编码器方向与低速行为必须等待独立矩阵和实机证据。


## 50.6 章节导航

[上一章：R680 硬件、接线与 OLED 状态](49-r680-hardware-wiring-oled.md) · [返回本篇](index.md) · [下一章：网络、Docker、系统镜像与主控差异](../10-deployment-maintenance/51-network-docker-images.md)
