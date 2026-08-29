---
status: complete
---

# 第二篇：机器人硬件、接口与控制基础

这一篇先讲清楚机器人由哪些硬件组成、它们怎样交换数据，以及车轮反馈如何变成可控运动。读完第 6～9 章，再进入第三篇的实机接入；这样遇到异常时，读者知道应该检查哪一层。

## 学习顺序

```text
主控与固件 → 电气接口与通信 → 传感器与反馈 → 底盘运动与闭环控制
```

## 本篇内容

1. [第 6 章：主控、控制板与固件](06-controller-and-firmware.md)：区分计算机、微控制器、固件和电机功率级。
2. [第 7 章：电气接口与通信](07-electrical-interfaces-communication.md)：理解 USB、串口、UART、CAN、帧和校验。
3. [第 8 章：传感器与状态反馈](08-sensors-and-feedback.md)：理解编码器、IMU、OLED、激光雷达和时间坐标。
4. [第 9 章：底盘运动与闭环控制](09-chassis-motion-control.md)：把坐标、里程计、PWM 和 PID 串成控制链。

完成本篇后，继续阅读[原实机接入章节](../02-bringup/06-identify-configuration.md)。任务 3 完成编号迁移后，这个入口会更新为第三篇的新索引。

## 章节导航

[第 6 章：主控、控制板与固件](06-controller-and-firmware.md) · [返回教材首页](../index.md)
