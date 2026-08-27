---
status: complete
---

# 4. 第一次观察 ROS 2

第 1 章介绍了 ROS 2 的定位，第 3 章介绍了主控上的终端。现在用 ROS 2 自带的 `talker` 和 `listener` 示例观察一条真实的数据链：一个节点发布消息，另一个节点订阅消息，第三个终端查询系统状态。

## 4.1 观察目标与准备

本次练习关注三个对象：**节点（Node）**、**话题（Topic）**和消息。`talker` 周期性发布文字，`listener` 订阅同一个话题并打印收到的内容。

```text
talker 节点 → 文字消息 → listener 节点
```

实验环境可以是安装了 ROS 2 的 Ubuntu 电脑或机器人主控。没有可用环境时，直接阅读命令后的代表性输出，并根据关系图完成练习。

## 4.2 启动 talker

在第一个终端中加载 ROS 2 环境，再运行 C++ 示例包中的 `talker`：

```bash
source /opt/ros/<发行版>/setup.bash
ros2 run demo_nodes_cpp talker
```

`<发行版>` 替换为实际名称，例如 `humble`。代表性输出如下：

```text
[talker]: Publishing: 'Hello World: 1'
[talker]: Publishing: 'Hello World: 2'
```

每出现一行，表示 `talker` 发布了一条新的文字消息。保持该终端运行，继续打开第二个终端。

## 4.3 启动 listener

在第二个终端中加载同一套 ROS 2 环境，并启动 `listener`：

```bash
source /opt/ros/<发行版>/setup.bash
ros2 run demo_nodes_cpp listener
```

代表性输出如下：

```text
[listener]: I heard: [Hello World: 1]
[listener]: I heard: [Hello World: 2]
```

`listener` 能打印 `talker` 发送的内容，说明两个节点已经通过共同的话题建立了数据交换。

## 4.4 查看节点、话题与消息

在第三个终端中加载环境。先查看当前运行的节点：

```bash
source /opt/ros/<发行版>/setup.bash
ros2 node list
```

典型输出包含：

```text
/talker
/listener
```

这条命令回答“有哪些节点正在运行”。接着查看话题名称：

```bash
ros2 topic list
```

典型结果包含 `/chatter`。再读取该话题中的一条消息：

```bash
ros2 topic echo --once /chatter
```

可能看到：

```text
data: 'Hello World: 8'
---
```

三条查询命令分别对应三个观察层次：

| 命令 | 观察对象 | 结果含义 |
|---|---|---|
| `ros2 node list` | 节点 | 查看程序单元是否在线。 |
| `ros2 topic list` | 话题 | 查看数据通道名称。 |
| `ros2 topic echo --once /chatter` | 消息 | 读取通道中一次实际传递的数据。 |

此时可以画出完整关系：

```text
/talker 节点
  └─ 发布到 /chatter 话题
       └─ 消息：Hello World
            └─ 被 /listener 节点订阅
```

没有 ROS 2 环境时，可以直接根据上面的输出完成关系图：

```text
节点：/talker
  └─ 发布到话题：/chatter
       └─ 消息内容：Hello World
            └─ 被节点 /listener 接收
```

## 4.5 结束实验并解释现象

在 `talker` 和 `listener` 终端分别按 `Ctrl+C`，再运行：

```bash
ros2 node list
```

两个示例节点会从列表中消失。话题列表可能仍包含其他系统通道，因为 ROS 2 环境中还可能有别的程序在运行。这个现象说明：节点的出现和消失与承载它的进程状态有关。

## 4.6 本章小结与练习

`talker` 和 `listener` 是两个节点，`/chatter` 是它们使用的话题，`Hello World` 是传递的消息。ROS 2 命令行工具可以分别查询节点、话题和消息。

练习：解释下面四项分别属于节点、话题还是消息，并说明它们的连接关系：`/talker`、`/listener`、`/chatter`、`Hello World`。随后回答：为什么三个终端都要先执行 `source` 命令？

## 章节导航

[上一章：Ubuntu、终端与程序](03-ubuntu-terminal-programs.md) · [返回本篇](index.md) · [下一章：ROS 2 程序怎样协作](05-ros2-communication.md)
