---
status: complete
---

# T4. 时间、QoS、TF 与实机诊断

## 本章目标

理解三个经常被忽略的运行条件：消息是否能被发现和匹配、时间戳是否可比较、坐标变换是否完整。它们决定了雷达、相机、定位和 Nav2 能否真正使用数据。

## 适用范围

ROS 2 底盘、雷达、相机、定位和 Nav2。仿真还需要额外检查 `/clock` 和 `use_sim_time`。

## 开始前检查

- T2 的节点/话题模型和 T3 的环境叠加概念已掌握。
- 机器人主控系统时间正确，实机与仿真不同时启动。
- 不通过修改 QoS 或静态 TF 来掩盖设备和接线问题。

## 工作原理

### DDS 发现和 QoS

ROS 2 通常使用 DDS 发现参与者和端点。节点列表能看到某个节点，说明发现基本成功；话题能列出，不代表发布者和订阅者的 QoS 一定兼容。可靠性、持久性、历史深度和队列深度都可能影响结果。

### 时间

每条传感器消息带时间戳。传感器、底盘和主控的时钟不一致，或仿真节点使用 `/clock` 而其他节点使用系统时间，都会造成 TF extrapolation、消息丢弃和定位跳变。

### TF

TF 维护坐标系之间的时变关系。移动机器人常见链路是 `map → odom → base_link → sensor`：定位提供全局到局部的关系，底盘提供局部到机体的里程计，静态发布器提供机体到传感器的安装变换。

## 操作步骤

### 1. 检查 QoS

```bash
ros2 topic info <话题名> --verbose
```

比较发布者和订阅者的 reliability、durability、history 与 depth。雷达或相机没有数据时，先确认 QoS，再改参数。

### 2. 检查时间

```bash
date
ros2 topic echo --once <传感器话题>
ros2 topic echo --once /clock
```

只在仿真环境期待 `/clock`。实机不应因为没有 `/clock` 就随意打开 `use_sim_time`。

### 3. 检查 TF

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo base_link <传感器坐标系>
```

记录缺失的 parent/child、时间范围和多个发布者。将传感器放到正确位置需要实物测量，不能凭 RViz 视觉效果任意平移。

### 4. 按证据分层诊断

当 `ros2 topic echo` 没有数据时，依次问：

1. Linux 是否看到设备？
2. 驱动节点是否运行？
3. 节点是否发布该话题？
4. QoS 是否匹配？
5. 消息时间戳是否有效？
6. 消费者需要的 TF 是否存在？

只有前五项通过，才讨论 Nav2 或视觉算法参数。

## 结果验收

- 能解释节点存在、话题存在和收到有效消息之间的区别。
- 能从 `topic info --verbose` 找到 QoS 不匹配。
- 实机使用系统时间，仿真使用 `/clock` 的边界明确。
- `map → odom → base_link → sensor` 链能追踪到具体发布者。
- 传感器无数据时可以按六层问题顺序排查。

## 常见故障与处理

| 现象 | 可能原因 |
|---|---|
| 话题可见但 echo 无数据 | QoS、发布者未 active、设备驱动或权限 |
| TF extrapolation | 时钟不同步、时间戳延迟或仿真时间混用 |
| RViz 显示但 Nav2 不用 | 话题类型、QoS、frame_id 或代价地图订阅 |
| 地图和扫描错位 | TF、传感器安装变换、里程计或时间 |
| 多机偶发收不到 | Domain ID、DDS 网络发现、QoS 和网络隔离 |

## 章节导航

[上一章：工作空间、功能包与运行时环境](t3-workspace-package-runtime.md) · [返回本卷](index.md) · [下一卷：实机接入与首次启动](../01-bringup/01-identify-configuration.md)
