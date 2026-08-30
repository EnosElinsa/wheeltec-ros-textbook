---
status: complete
---

# 7. 电气接口与通信

第 6 章确定了主控、控制板和执行机构的设备边界。本章沿着设备之间的连接展开：先看供电与信号的边界，再区分计算机端口、串行链路和控制器总线，最后落到数据帧与控制板内部的外设接口。这样看到一个端口或一段报文时，可以判断它处在连接链的哪一层。

## 7.1 接线前先分清电气条件

连接一块板时，需要同时确认供电、信号和机械连接。电源部分看电压范围、持续电流和极性；信号部分看逻辑电平、收发方向和共地；连接器则按板卡资料核对型号与针脚。机械配合、电气条件和供电能力分别查规格。

电源线承载能量，信号线传递状态或命令，信号地回到规定的功率参考点。改线在断电状态完成；出现复位、发热或通信间歇时，先停止动作，再把供电和信号分开检查。

## 7.2 USB 与串行端口 {#usb-serial-port}

主控常通过通用串行总线（Universal Serial Bus, USB）连接相机、雷达和 USB 转串口适配器。USB 同时承载数据和供电，外设反复重连时要把端口供电能力列入检查。

适配器的另一端连接串行端口（Serial Port），串行通信（Serial Communication）按顺序传送字节。Ubuntu 通常把 USB 转串口设备表示为 `/dev/ttyUSB0` 或 `/dev/ttyACM0`；端口编号会随插拔顺序变化，稳定的设备别名需要 udev 规则、序列号或固定物理端口共同保证。

## 7.3 UART、USART 与逻辑电平 {#uart-usart-levels}

控制板内部通常由通用异步收发传输器（Universal Asynchronous Receiver-Transmitter, UART）逐位收发串行数据；通用同步/异步收发传输器（Universal Synchronous/Asynchronous Receiver-Transmitter, USART）还可以使用时钟线进行同步通信。波特率（Baud Rate）、数据位、停止位、校验方式和流控共同构成串行链路的配置。

电脑通过 USB 转串口模块连接 UART/USART。晶体管—晶体管逻辑（Transistor-Transistor Logic, TTL）与 RS-232 采用不同的电压标准，接线前先确认转换关系；通常 TX 接对端 RX、RX 接对端 TX，并共地，VCC 按当前板卡的供电方案处理。

## 7.4 CAN 总线 {#can}

当一块控制板需要和多个驱动器或扩展模块交换短报文时，常见接口是控制器局域网（Controller Area Network, CAN）。CAN_H 和 CAN_L 组成差分信号对，总线两端配置终端电阻，并按系统方案处理共地。每条报文带有标识符（Identifier, ID），接收设备根据 ID 区分报文用途。

CAN 适配器把电脑或 MCU 的接口转换成总线信号。适配器配置完成后，Linux SocketCAN 才能把它表示成 `can0` 等网络接口。排查 CAN 时，先记录连接对象、H/L 线序、终端电阻、波特率和收发器，再核对 ID、字节序、单位和车型。

## 7.5 字节流、数据帧与校验 {#frames-checksum}

串行端口连续传送字节流，协议需要规定帧头、长度、帧尾或超时等边界，接收端据此把字节组织成一帧。数据长度代码（Data Length Code, DLC）记录 CAN 数据帧中的有效字节数；块校验字符（Block Check Character, BCC）由数据计算得到，用于检测传输过程中的变化。

高位字节（Most Significant Byte, MSB）和低位字节（Least Significant Byte, LSB）的排列构成字节序。协议文档还要写明有符号数、缩放倍数和单位；校验失败的帧交给接收程序丢弃并记录。

## 7.6 GPIO、I²C、SPI 与 DMA {#gpio-i2c-spi-dma}

控制板与传感器或驱动器之间还会使用通用输入输出（General-Purpose Input/Output, GPIO）、内部集成电路总线（Inter-Integrated Circuit, I²C）和串行外设接口（Serial Peripheral Interface, SPI）。GPIO 传递开关量、方向或使能信号，I²C 和 SPI 按各自的时序交换数据；具体引脚和电平以板卡原理图为准。

直接内存访问（Direct Memory Access, DMA）让外设和内存直接交换一段数据，减轻处理器逐字节搬运的负担。缓冲区、帧边界和协议校验仍由程序负责。

## 7.7 本章小结与观察练习

本章把通信拆成三层：电源和信号决定连接条件，USB、串行端口、UART/USART 与 CAN 承载数据，帧格式和校验规定数据如何解释。第 8 章将继续说明这些链路上传回的传感器状态。

画出主控到控制板的一条通信链，标出 USB、串行端口或 CAN 所在位置。为每个接口写出连接对象、供电条件、信号方向和一项协议字段。

## 章节导航

[上一章：主控、控制板与固件](06-controller-and-firmware.md) · [返回本篇](index.md) · [下一章：传感器与状态反馈](08-sensors-and-feedback.md)
