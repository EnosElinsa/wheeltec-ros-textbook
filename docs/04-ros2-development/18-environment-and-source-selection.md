---
status: complete
---

# 18. ROS 2 环境与源码版本选择

## 18.1 学习目标

确认程序实际运行在宿主系统还是容器中，找出 ROS 2 发行版、主工作空间和与硬件匹配的源码。完成后再进入编译，避免把错误平台的源码“编译成功”。

需要补充 ROS 2 节点、通信和运行时基础时，先读[第一篇：从零认识 ROS 机器人](../01-foundations/index.md)。

## 18.2 适用范围

适用于 Ubuntu 上的原生 ROS 2 和 WHEELTEC 预装 Docker 环境。TROS、Autoware 或厂商定制镜像应单独记录，不与普通 ROS 2 工作空间混用。

## 18.3 操作前检查

- 第 6 章硬件配置表已完成。
- 保存当前 `.bashrc`、工作空间路径和启动方式。
- 不解压新的 `src` 覆盖现有源码。

## 18.4 工作原理

一套可运行环境由 Ubuntu、ROS 发行版、架构、依赖、源码分支和硬件配置共同决定。ROS 2 Humble 源码不能因为目录名相近就放进 Foxy 环境；Jetson、树莓派、RDK 的相机与硬件加速依赖也不同。

Docker 还多一层边界：宿主机看到的文件、设备和网络，只有显式挂载或传入容器后才能被 ROS 使用。

## 18.5 操作步骤

在实际运行 ROS 的终端执行：

```bash
cat /etc/os-release
uname -m
printenv ROS_DISTRO
printenv ROS_VERSION
which ros2
```

若使用 Docker，先确认容器：

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

进入容器后重新执行环境检查，不能用宿主机结果代替。

查找工作空间：

```bash
find "$HOME" -maxdepth 3 -type d -name src 2>/dev/null
```

对候选工作空间记录 `src/build/install/log` 状态、源码日期和包名。当前终端的叠加顺序可从环境变量判断：

```bash
printenv AMENT_PREFIX_PATH | tr ':' '\n'
```

最后按主控、ROS 发行版、控制板、底盘和传感器选择源码。无法从文件名确认时，查看包清单、README、提交信息或版本更新记录。

## 18.6 验收标准

- 能明确说出命令运行在宿主还是容器。
- Ubuntu、架构和 `ROS_DISTRO` 已记录。
- 主工作空间只有一个明确入口。
- 源码包与主控、ROS 发行版和硬件配置有可追溯依据。
- Autoware、TROS 或其他工作空间不会无意叠加到普通机器人环境。

## 18.7 故障排查

| 现象 | 处理 |
|---|---|
| `ROS_DISTRO` 为空 | 查 `/opt/ros`，确认是否未 source 或在错误终端 |
| 同一个包解析到意外路径 | 检查 `AMENT_PREFIX_PATH` 和多个 `install/setup.bash` |
| 宿主有设备、容器没有 | 检查设备映射、权限和容器启动参数 |
| 源码目录名正确但依赖报错 | 核对发行版、架构和分支，不先强装随机版本依赖 |

## 章节导航

[上一章：直线纠偏、转向标定和常见底盘故障](../03-chassis-control/17-calibration-and-faults.md) · [返回本篇](index.md) · [下一章：工作空间、功能包与构建](19-workspace-packages-build.md)
