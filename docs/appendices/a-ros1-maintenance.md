---
status: complete
---

# A. ROS 1 兼容与旧设备维护

## 本章目标

维护已经交付的 ROS 1 机器人，并把 ROS 1 概念映射到本书的 ROS 2 主线。新项目默认使用 ROS 2；只有硬件镜像、驱动或现有功能包明确要求 ROS 1 时才进入本附录。

## ROS 1 与 ROS 2 对照

| 任务 | ROS 1 | ROS 2 |
|---|---|---|
| 工作空间构建 | `catkin_make` / `catkin build` | `colcon build` |
| 启动文件 | roslaunch XML | `ros2 launch` Python/XML |
| 参数 | 参数服务器 | 节点参数与 YAML |
| 坐标 | TF1 | TF2 |
| 话题检查 | `rostopic` | `ros2 topic` |
| 节点检查 | `rosnode` | `ros2 node` |
| 导航 | Navigation Stack | Nav2 |

命令不同，故障分层方法相同：先看电源/底盘，再看设备/节点/话题，最后看导航或应用。

## 维护步骤

1. 记录 Ubuntu、ROS 发行版、源码和底盘控制板。
2. 先运行旧系统的底盘和传感器基线。
3. 修改前备份 Launch、参数、地图和固件。
4. 不把 ROS 1 工作空间 source 到 ROS 2 终端，反之亦然。
5. 迁移功能时先替换通信接口，再验证 TF、时间和 QoS/连接行为。

需要在不连接实机时检查旧话题、时间和 TF，可使用 [ROS 1 Bag 离线传感器诊断](../05-sensors-navigation/ros1-bag-offline-diagnostics.md)。先在隔离 ROS master 中完成 ROS 1 回放，再决定是否需要转换到 ROS 2。

## 常见故障

| 现象 | 处理 |
|---|---|
| ROS 1 节点找不到 | 检查 `ROS_MASTER_URI`、`ROS_IP`、环境和网络 |
| ROS 1/ROS 2 混用 | 新开终端，清理错误环境变量和工作空间 |
| TF1 迁移后坐标错 | 逐帧核对 parent/child、时间戳和静态变换 |
| 旧导航参数不能直接用 | 根据 Nav2 插件重新映射，先做短目标测试 |

## 相关资料

- 本附录只保留维护旧设备所需的关键差异；新项目优先采用 ROS 2 主线。
- 新开发优先返回第四篇和第五篇的 ROS 2 章节。


!!! note "教材代码资源"
    本节使用的代码入口见[教材代码资源附录](d-public-source-reference.md)。

## 章节导航

[返回首页](../index.md) · [下一附录：车型、主控与控制板矩阵](b-platform-matrix.md)
