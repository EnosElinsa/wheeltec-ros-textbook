---
status: complete
---

# T3. 工作空间、功能包与运行时环境

## 本章目标

理解源码、构建结果和当前终端之间的关系。完成后，你能解释为什么改了 `src` 却没有生效，也能判断机器人是在宿主机、虚拟机还是 Docker 容器中运行 ROS 2。

## 适用范围

使用 `colcon` 的 ROS 2 工作空间，包括 WHEELTEC 原生 Ubuntu 和 Docker 镜像。

## 开始前检查

- T1、T2 的节点和通信概念已经掌握。
- 已完成第 13 章的主控和 ROS 版本记录。
- 不删除现有 `src`、`build` 或 `install`。

## 工作原理

ROS 2 工作空间通常有四个目录：

| 目录 | 保存内容 | 是否手工修改 |
|---|---|---|
| `src/` | 源码、配置、Launch、消息定义 | 是，修改前备份 |
| `build/` | CMake/Python 构建中间文件 | 否，按包清理 |
| `install/` | 可被 ROS 加载的结果 | 否，由构建生成 |
| `log/` | 构建与运行日志 | 读取和保存 |

`source /opt/ros/<发行版>/setup.bash` 载入系统 ROS；再 `source <工作空间>/install/setup.bash` 载入自己的包。后一个环境会叠加在前一个环境上。多个工作空间叠加时，ROS 可能找到旧版本包。

Launch 把节点、参数、命名空间和重映射组合起来。Docker 又增加宿主与容器的边界：源码可以挂载，USB、视频、GPU、网络和时间却必须分别传入。

## 操作步骤

### 1. 观察当前环境

```bash
printenv ROS_DISTRO
printenv AMENT_PREFIX_PATH | tr ':' '\n'
ros2 pkg prefix <包名>
```

`ros2 pkg prefix` 显示的是当前终端实际加载的包位置，不一定是你正在编辑的 `src`。

### 2. 从源码到运行结果

```bash
cd <工作空间>
colcon build --symlink-install --packages-up-to <包名>
source install/setup.bash
ros2 pkg prefix <包名>
```

构建之后在新终端重新 source，再启动节点。不要在同一个长期使用的终端里反复叠加不同工作空间。

### 3. 观察 Launch 的边界

```bash
ros2 pkg executables <包名>
rg -n 'parameters|remap|namespace|yaml' <包源码目录>
```

把 Launch 参数、YAML 参数和节点默认值分开记录。一个参数可能在多处覆盖，最终运行值要用 `ros2 param get` 验证。

### 4. 进入 Docker 后重新检查

```bash
docker ps
docker inspect <容器名>
```

进入容器后重新执行 `printenv ROS_DISTRO`、`lsusb`、设备节点和 ROS 话题检查。宿主机的命令结果不能替代容器结果。

## 结果验收

- 能指出当前包来自哪个工作空间。
- 能说明 `src`、`install` 和运行节点之间的关系。
- 能发现错误的环境叠加或旧包路径。
- 能列出 Docker 运行 ROS 所需的设备/网络/挂载边界。
- 改动后能在新终端验证运行结果。

## 常见故障与处理

| 现象 | 理论上的解释 |
|---|---|
| 改 `src` 不生效 | 节点加载的是旧 `install` 或另一工作空间 |
| 包名存在但 Launch 找不到 | 可执行文件、安装规则或环境叠加错误 |
| 宿主有串口、容器没有 | 容器边界没有传入设备和权限 |
| 同一节点参数不一致 | Launch/YAML/命令行多处覆盖 |

## 章节导航

[上一章：ROS 2 系统图与通信模型](t2-graph-and-communication.md) · [返回本卷](index.md) · [下一章：时间、QoS、TF 与实机诊断](t4-time-qos-tf-diagnosis.md)
