---
status: complete
---

# 4. 第一次观察 ROS 2

## 本章要回答的问题

节点和节点之间的数据在终端里是什么样子？怎样在不控制机器人运动的情况下，亲眼看到两个 ROS 2 节点交换消息？

本章使用 ROS 2 自带的 talker 和 listener 示例。它们只发送和接收文字，不需要 WHEELTEC 机器人，也不会操作电机。

## 从一个具体场景开始

想象两个人使用对讲机：一个人反复说出一句话，另一个人持续收听。ROS 2 自带的示例也采用这个结构：

```text
talker 节点 → 文字消息 → listener 节点
```

Talker 表示说话者，Listener 表示收听者。运行它们以后，我们可以从第三个终端查看系统中有哪些节点、有哪些数据通道，以及通道中正在传递什么。

如果电脑没有安装 ROS 2，可以直接阅读示例输出和图示。后面的自检问题不要求实际执行命令。

## 新概念

### 让当前终端认识 ROS 2 命令

程序安装在电脑上，不代表新打开的终端已经知道到哪里寻找它。下面的命令把系统安装中的 ROS 2 命令位置加入当前终端环境：

```bash
source /opt/ros/<发行版>/setup.bash
```

把 `<发行版>` 换成实际名称，例如 `humble`。这条命令只影响当前终端；新开终端后需要重新执行。这里先把它理解为“准备当前终端”，更详细的环境组织方法留到开发篇。

### 示例节点

`demo_nodes_cpp` 是随 ROS 2 提供的一组 C++ 示例。`talker` 和 `listener` 是其中两个可执行示例，它们启动后会创建各自的节点。

### 话题与消息

Talker 不把文字直接发给某一个指定的程序，而是把消息发布到一个有名称的数据通道。ROS 2 把这种连续传递数据的通道称为话题。Listener 订阅同一个话题，因此能够收到消息。

消息是一次实际传递的数据。话题像广播频道，消息像频道中一条条播出的内容。

## 图示或逐步例子

### 1. 在第一个终端启动 talker

```bash
source /opt/ros/<发行版>/setup.bash
ros2 run demo_nodes_cpp talker
```

可能看到：

```text
[talker]: Publishing: 'Hello World: 1'
[talker]: Publishing: 'Hello World: 2'
```

终端保持运行，说明 talker 正在不断发布消息。

### 2. 在第二个终端启动 listener

```bash
source /opt/ros/<发行版>/setup.bash
ros2 run demo_nodes_cpp listener
```

可能看到：

```text
[listener]: I heard: [Hello World: 1]
[listener]: I heard: [Hello World: 2]
```

这表明 listener 收到了 talker 发布的消息。

### 3. 在第三个终端观察系统

先准备终端，再列出节点：

```bash
source /opt/ros/<发行版>/setup.bash
ros2 node list
```

典型结果包含：

```text
/talker
/listener
```

查看话题名称：

```bash
ros2 topic list
```

典型结果会包含 `/chatter`。再读取一条消息：

```bash
ros2 topic echo --once /chatter
```

可能看到：

```text
data: 'Hello World: 8'
---
```

现在可以把命令和概念对应起来：`ros2 node list` 观察程序单元，`ros2 topic list` 观察数据通道，`ros2 topic echo` 观察通道中的消息。

### 只读路线

没有 ROS 2 环境时，根据上面的预期输出完成这张图：

```text
节点：/talker
  └─ 发布到话题：/chatter
       └─ 消息内容：Hello World
            └─ 被节点 /listener 接收
```

只要能解释图中四行的关系，就达到了本章目标。

## 可选实验

完成上述实验后，按 `Ctrl+C` 分别结束 talker 和 listener。然后再次运行：

```bash
ros2 node list
```

比较结束前后的结果。节点随程序启动而出现，随程序结束而消失；话题列表中还可能存在系统使用的其他通道，不必在本章逐一解释。

## 本章小结

Talker 和 listener 是两个节点。Talker 把文字消息发布到 `/chatter` 话题，listener 订阅该话题并接收消息。ROS 2 命令行工具可以观察节点、话题和消息，而不需要修改程序。

## 自检问题

1. Talker、listener、`/chatter` 和 `Hello World` 分别对应节点、话题还是消息？
2. 为什么三个终端都要先准备 ROS 2 环境？
3. `ros2 node list` 与 `ros2 topic list` 观察的对象有什么不同？
4. 没有机器人时，为什么仍然可以完成这个实验？

## 章节导航

[上一章：ROS 2 解决什么问题](03-what-ros2-solves.md) · [返回本篇](index.md) · [下一章：ROS 2 程序怎样协作](05-ros2-communication.md)
