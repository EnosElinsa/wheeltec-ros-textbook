---
status: complete
---

# 37. ROS 2 与 STM32 联调

## 37.1 学习目标

沿着 `cmd_vel` 到电机、再从编码器/IMU 回到 ROS 2 的完整链路设置检查点，定位通信和单位转换问题。

**联调**是把已经分别检查过的 ROS 2 程序、串口链路和控制板固件连接起来，逐段确认数据能否到达下一层。调试时一次只跨过一个接口，这样才能分清故障来自 ROS 节点、协议转换、物理通信还是固件执行。

## 37.2 适用范围

使用 `turn_on_wheeltec_robot` 与串口底盘协议的 ROS 2 机器人。CAN 驱动可沿用同样的边界检查。

## 37.3 操作前检查

- STM32 固件已通过架空验收并可回滚。
- 串口设备别名和权限稳定。
- ROS 2 底盘节点源码与固件协议版本匹配。

## 37.4 工作原理

![ROS 2 与 STM32 的闭环链路](../assets/diagrams/ros2-stm32-loop.svg)

图中的每个箭头都是一个可单独检查的接口。常见错误包括设备端口选错、协议版本不一致、毫米每秒与米每秒漏换、角速度缩放倍数错误，以及字节序或坐标符号相反。

## 37.5 ROS—串口—固件链 {#ros-serial-firmware-chain}

### 从 `cmd_vel` 追到 STM32，再回到 ROS 2

底盘节点通常订阅 `geometry_msgs/msg/Twist` 类型的 `cmd_vel`，把线速度和角速度编码为串口下行帧。这里的**帧**是一段按协议排列的连续字节，通常包含帧头、数据字段、校验值和帧尾。STM32 返回编码器、IMU 和电压等数据后，节点解析并发布里程计、原始 IMU 和供电电压。可以按下列链路定位：

```text
/cmd_vel
  → wheeltec_robot_node 订阅回调
  → 速度缩放、车型运动学与协议封包
  → /dev/wheeltec_controller
  → STM32
  → 串口上行帧
  → 校验、单位换算和状态更新
  → /odom、/imu/data_raw、/PowerVoltage
  → EKF、TF 与上层导航
```

静态源码只能证明某条路径被实现，不能证明当前机器人正在走这条路径。运行时继续核对节点、类型、发布者/订阅者和消息内容：

```bash
ros2 node info <底盘节点名>
ros2 topic info /cmd_vel --verbose
ros2 topic echo /odom --once
ros2 topic echo /imu/data_raw --once
ros2 topic echo /PowerVoltage --once
ros2 run tf2_ros tf2_echo odom_combined base_footprint
```

将 `/odom` 的 `header.frame_id`、`child_frame_id` 与节点参数比较；将 IMU 的 `header.frame_id` 与 TF 树比较；同时记录 `ros2 topic hz` 的频率。命名空间会给一组接口增加名称前缀，**重映射（Remapping）**则在启动时把原接口名替换为另一个名称。因此，实际话题名应以 `ros2 node info` 的运行结果为准。

这些命令仍不能单独证明波特率已经生效、节点确实打开了预期设备或 STM32 已正确执行帧。硬件证据至少应包括：节点打开串口的日志或设备句柄、在电机失能/架空条件下观察到零速下行帧，以及 STM32 返回帧被节点接收并转成预期话题。缺少其中任一项，只能报告 ROS 图上的静态或运行时接口证据。

代码入口与完整文件集见第 21 章的[底盘启动链资源块](../04-ros2-development/21-launch-and-parameters.md#bringup-launch-chain)；本节只定义 ROS、串口与固件之间的验证边界，不新增独立代码资源。

## 37.6 验收标准

- 设备别名在重插后稳定。
- ROS 速度和协议整数的缩放可手算复核。
- OLED、轮速、里程计和 IMU 符号一致。
- 停止、节点退出和通信断开都能让底盘安全停机。
- 记录中包含 ROS 包版本、固件版本和抓帧证据。

## 37.7 故障排查

| 现象 | 边界 |
|---|---|
| `cmd_vel` 有值但无下行帧 | ROS 节点订阅、端口或 Control 函数 |
| 下行正确但 OLED 不变 | 线缆、波特率、帧校验或固件协议 |
| 电机动作正确但 odom 错 | 上行解析、编码器方向、正运动学或单位 |
| IMU 方向错 | 板载轴定义、固件重映射或 ROS frame_id |
| 断开主控后继续运动 | 通信超时和失能逻辑缺失，停止测试 |

## 章节导航

[上一章：修改、编译、烧录与回滚固件](36-build-flash-rollback.md) · [返回本篇](index.md) · [下一章：仿真与 Gazebo](../07-advanced-applications/38-gazebo-simulation.md)
