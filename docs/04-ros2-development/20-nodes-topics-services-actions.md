---
status: complete
---

# 20. 节点、话题、服务与动作

## 本章目标

从正在运行的机器人识别节点和通信接口，知道何时看话题、调用服务或追踪动作，不把所有交互都当成“发布消息”。

## 适用范围

ROS 2 正文环境。ROS 1 对应命令见附录 A。

## 开始前检查

启动底盘基础节点，不启动导航和高级应用。另开一个加载相同环境的终端。

## 工作原理

- 节点是一个运行中的 ROS 功能单元。
- 话题适合连续数据流，例如速度、雷达和里程计。
- 服务适合一次请求、一次响应，例如读取或切换某项状态。
- 动作适合耗时任务，可提供反馈并允许取消，例如导航到目标点。

接口类型规定消息字段。名字相同但类型不同的接口不能直接通信。ROS 2 还受 Domain ID、DDS 实现和 QoS 影响。

话题的发布者和订阅者还要满足通信策略。`reliability` 表示是否要求可靠送达，`history` 表示怎样保存历史消息，`depth` 表示队列最多保留多少条。节点和话题都能列出来，只能证明发现过程基本成功；发布者与订阅者的策略不兼容时，订阅端仍可能收不到数据。

## 操作步骤

```bash
ros2 node list
ros2 node info <节点名>
ros2 topic list -t
ros2 service list -t
ros2 action list -t
```

检查底盘速度话题：

```bash
ros2 topic info /cmd_vel --verbose
ros2 interface show geometry_msgs/msg/Twist
```

在 `--verbose` 输出中逐个比较发布者和订阅者的类型、`reliability`、`history` 与 `depth`。先记录两端当前值，再决定是否需要修改配置。

对传感器先看频率，再看单条内容：

```bash
ros2 topic hz <话题名>
ros2 topic echo --once <话题名>
```

使用服务和动作前先查看类型：

```bash
ros2 service type <服务名>
ros2 action info <动作名>
```

需要理解连接图时运行 `rqt_graph`，但不要用图中的连线替代消息内容和 QoS 检查。

## 结果验收

- 能从底盘节点找出订阅的速度话题和发布的里程计/IMU。
- 能说明一个传感器话题的类型、频率和发布者。
- 能指出服务与动作相对话题的区别。
- 多机通信时能记录 Domain ID 和 QoS，而不是只确认“能 ping”。

## 常见故障与处理

| 现象 | 检查 |
|---|---|
| 节点列表为空 | ROS 环境、Domain ID、DDS 和网络 |
| 话题存在但收不到 | QoS、命名空间、类型和发布频率 |
| 同名节点重复 | 旧进程、重复 Launch 或命名空间缺失 |
| 动作无法取消 | 动作服务器状态、客户端实现和通信链 |

## 章节导航

[上一章：工作空间、功能包与构建](19-workspace-packages-build.md) · [返回本篇](index.md) · [下一章：Launch、参数与运行配置](21-launch-and-parameters.md)
