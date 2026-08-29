---
status: complete
---

# 7. 电气接口与通信

## 7.1 接线前先分清电气条件

接线前分别核对电压范围、持续电流、极性、逻辑电平、共地和连接器。插头能插入只说明机械尺寸相容，不说明电气条件相容。任何改线都在断电状态完成；电池支路、电机驱动器和裸露端子由熟悉低压直流系统的人检查。

电源线承载能量，信号线传递状态或命令。两者都需要可靠接地，但信号地不能替代功率回路。出现复位、发热或通信时有时无时，先停止动作，分开检查供电和信号。

## 7.2 USB 与串行端口

通用串行总线（Universal Serial Bus, USB）是计算机连接外部设备的通用接口，可能同时承担数据和 5 V 供电。相机、雷达和 USB 转串口适配器常接在 USB 端口上；无源集线器的供电能力不足时，设备会反复重连。

串行端口（Serial Port）在一对设备之间按顺序传输字节。Ubuntu 通常把 USB 转串口设备表示为 `/dev/ttyUSB0` 或 `/dev/ttyACM0`。端口编号会随插拔顺序改变，稳定的设备别名需要 udev 规则、序列号或固定物理端口共同保证。

## 7.3 UART、USART 与逻辑电平

通用异步收发传输器（Universal Asynchronous Receiver-Transmitter, UART）是 MCU 中逐位收发串行数据的外设。通用同步/异步收发传输器（Universal Synchronous/Asynchronous Receiver-Transmitter, USART）在此基础上还可以使用时钟线进行同步通信。波特率（Baud Rate）描述每秒传送的符号数；数据位、停止位、校验方式和流控也必须两端一致。

电脑常通过 USB-TTL 模块连接 UART/USART。晶体管—晶体管逻辑（Transistor-Transistor Logic, TTL）只描述信号电平，不能与 RS-232 的正负电压直接等同。接线通常是 TX 接对端 RX、RX 接对端 TX，并共地；VCC 是否连接要按当前板卡供电方案确认。

## 7.4 CAN 总线

控制器局域网（Controller Area Network, CAN）允许多个控制器共用一条总线交换短报文。总线通常使用 CAN_H 和 CAN_L 两根信号线，并要求合适的终端电阻和共地。每条报文带有标识符（Identifier, ID），接收设备根据 ID 判断报文用途。

CAN 适配器把电脑或 MCU 的接口转换成总线信号。适配器配置完成后，Linux SocketCAN 才能把它表示成 `can0` 等网络接口。物理层没有报文时，先查 H/L 线序、终端电阻、波特率和收发器；有报文但数据错误时，再查 ID、字节序、单位和车型。

## 7.5 字节流、数据帧与校验

串行端口连续传送的是字节流，接收端需要用帧头、长度、帧尾或超时把字节切成一帧。数据长度代码（Data Length Code, DLC）表示 CAN 数据帧中有效数据字节的数量。块校验字符（Block Check Character, BCC）是根据一段数据计算出的校验值，用来发现传输中的改变。

高位字节（Most Significant Byte, MSB）和低位字节（Least Significant Byte, LSB）的排列称为字节序。协议解析时还要明确有符号数、缩放倍数和单位；帧头、长度和帧尾正确但校验不符时，接收程序仍应丢弃该帧。

## 7.6 GPIO、I²C、SPI 与 DMA

通用输入输出（General-Purpose Input/Output, GPIO）引脚可以读取开关量，也可以输出方向、使能或片选信号。内部集成电路总线（Inter-Integrated Circuit, I²C）和串行外设接口（Serial Peripheral Interface, SPI）用于连接传感器等外设，具体引脚、电平和时序由板卡原理图决定。

直接内存访问（Direct Memory Access, DMA）让外设和内存直接交换一段数据，减少处理器逐字节搬运的工作。DMA 并不会自动解决缓冲区溢出、帧边界或协议校验问题。

## 7.7 本章小结与观察练习

USB 是设备连接标准，串行端口和 UART/USART 描述逐字节传输，CAN 是多个控制器共享的报文总线。电压和电平决定能否安全接线，帧、字节序和校验决定数据能否正确解释。

画出主控到控制板的一条通信链，标出 USB、串行端口或 CAN 所在位置。对每个接口写出需要核对的电气条件和协议字段。

## 章节导航

[上一章：主控、控制板与固件](06-controller-and-firmware.md) · [返回本篇](index.md) · [下一章：传感器与状态反馈](08-sensors-and-feedback.md)
