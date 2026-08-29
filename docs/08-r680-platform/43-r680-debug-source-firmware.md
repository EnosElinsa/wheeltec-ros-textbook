---
status: complete
---

# 43. R680 底盘调试、源码与固件维护 {#r680-code-resource}

## 43.1 学习目标

静态阅读唯一已发布的 C50C/F407 麦轮霍尔编码器串口-CAN 固件变体，核对工程入口、协议代码和照片门禁；不执行烧录或运行测试。

## 43.2 适用范围

!!! example "唯一可消费资源：C50C/F407 麦轮霍尔/serial-can"
    资源目录：`r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01/`。查看 `USER/WHEELTEC.uvprojx`、`USER/main.c`、`HARDWARE/usartx.c`、`HARDWARE/can.c`。源码固定在 [0ecdda91](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/0ecdda9102755150f466d4de96e418ed4460575a/r680/firmware/c50c/f407-mecanum-hall-single-serial-can-b01)。

    验收：能定位工程、主循环和双协议接口。边界：无匹配实机照片、接线与测量证据时，只能静态阅读；不得烧录或声明硬件验证。

其他控制板、底盘、编码器和主从组合当前不可用、不可消费，也没有公开固件资源；不得从本变体外推。

## 43.3 静态核对

核对 UV 工程设备、启动文件、串口/CAN 源码和控制常量。架空、低速、烧录、回滚和主从测试步骤属于尚未具备硬件证据的未来流程，本仓库不提供可执行分支。

## 43.4 安全边界

没有照片、接线、测量和急停记录时，不连接电机、不烧录、不发布运行结论。其他车型的阿克曼、差速、全向轮、四驱和 8 驱主从说明均为不可消费背景，不构成操作指引。

## 43.5 故障记录

仅记录静态发现：设备字段、协议文件和工程路径。硬件异常、轮号、编码器方向与低速行为必须等待独立矩阵和实机证据。

详见[教材代码资源附录](../appendices/d-public-source-reference.md)。

## 43.6 章节导航

[上一章：R680 硬件、接线与 OLED 状态](42-r680-hardware-wiring-oled.md) · [返回本篇](index.md) · [下一章：网络、Docker、系统镜像与主控差异](../09-deployment-maintenance/44-network-docker-images.md)
