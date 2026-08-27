---
status: complete
---

# T2. ROS 2 系统图与通信模型

## 本章目标

学会把一个 ROS 2 系统画成节点和接口组成的图。完成后，你不会再把“话题、服务、动作、参数”混成同一种通信，也能根据数据的性质选择观察命令。

## 适用范围

ROS 2 底盘、雷达、相机、定位和导航系统。命令在已加载正确 ROS 2 工作空间的主控终端执行。

## 开始前检查

- 已读 T1，知道 ROS 2 节点运行在主控上，STM32 负责底层执行。
- 机器人基础节点已启动，或准备使用一个最小示例包观察通信。
- 只观察通信图，不向底盘发送运动命令。

## 工作原理

ROS 2 的运行图由节点和接口组成。节点是一个功能单元，可能对应一个进程，也可能由同一进程承载多个节点；功能包是源码、配置和启动资源的组织单位。

| 接口 | 数据特点 | WHEELTEC 示例 | 典型操作 |
|---|---|---|---|
| 话题 Topic | 连续发布，发布者和订阅者解耦 | `/scan`、图像、`/odom`、`/cmd_vel` | `ros2 topic echo/hz/info` |
| 服务 Service | 一次请求、一次响应 | 读取或切换设置 | `ros2 service list/call` |
| 动作 Action | 持续任务，有反馈，可取消 | Nav2 导航目标 | `ros2 action list/info` |
| 参数 Parameter | 节点配置值 | 车型、端口、速度限制 | `ros2 param get/dump` |
| 接口 Interface | 定义消息/服务/动作字段 | `geometry_msgs/msg/Twist` | `ros2 interface show` |

以键盘控制为例：键盘节点发布 `cmd_vel`，底盘节点订阅它；底盘节点再通过串口/CAN 与 STM32 通信。以导航为例，Nav2 的动作客户端发送目标，规划器和控制器发布路径与速度，底盘节点最终执行速度。

## 操作步骤

### 1. 列出运行图

```bash
ros2 node list
ros2 topic list -t
ros2 service list -t
ros2 action list -t
```

把结果保存到文件，作为当前系统的通信快照。

### 2. 从节点追踪上下游

```bash
ros2 node info <底盘节点名>
ros2 topic info <速度话题> --verbose
```

重点记录发布者、订阅者、消息类型和 QoS。速度话题有多个发布者时，机器人可能接收相互竞争的命令。

### 3. 查看接口字段

```bash
ros2 interface show geometry_msgs/msg/Twist
ros2 interface show nav2_msgs/action/NavigateToPose
```

`Twist` 中的 `linear.x`、`linear.y` 和 `angular.z` 对应底盘运动自由度；导航动作包含目标和反馈，不能用一次 `topic echo` 代替。

### 4. 观察一个数据流

```bash
ros2 topic echo --once /cmd_vel
ros2 topic hz /odom
```

如果实际话题带命名空间，使用 `ros2 topic list -t` 的完整名称。不要假设所有 WHEELTEC 镜像都使用同一话题名。

## 结果验收

- 能画出一个底盘节点的输入和输出。
- 能说明为什么连续雷达数据使用话题，导航目标使用动作。
- 能从 `ros2 topic info --verbose` 找到速度话题的发布者和订阅者。
- 能用接口定义解释 `Twist` 或导航动作的字段。
- 看到话题无数据时，知道还要查节点、设备、QoS 和时间。

## 常见故障与处理

| 现象 | 可能原因 |
|---|---|
| 话题存在但没有消息 | 没有发布者、节点未 active、QoS 不兼容或设备驱动未出数据 |
| 速度忽快忽慢 | 多个发布者、控制周期、网络延迟或底盘限幅 |
| 服务调用无响应 | 服务端未启动、类型错误或节点未声明参数 |
| 动作目标发出但不执行 | 动作服务器状态、定位/规划前置条件或安全停止 |

## 章节导航

[上一章：ROS 2 是什么](t1-what-is-ros2.md) · [返回本卷](index.md) · [下一章：工作空间、功能包与运行时环境](t3-workspace-package-runtime.md)
