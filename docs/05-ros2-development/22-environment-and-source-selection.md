---
status: complete
---

# 22. ROS 2 环境与源码版本选择

## 22.1 学习目标

确认程序实际运行在宿主系统还是容器中，找出 ROS 2 发行版、主工作空间和与硬件匹配的源码。完成后再进入编译，避免把错误平台的源码“编译成功”。

需要补充 ROS 2 节点、通信和运行时基础时，先读[第一篇：从零认识 ROS 机器人](../01-foundations/index.md)。

Docker Container Platform（Docker）可以在主控上隔离运行一套软件。宿主机是直接管理硬件的 Ubuntu 系统，容器是隔离的运行实例，镜像是创建容器时使用的软件模板；设备和目录只有显式映射后才会出现在容器中。

## 22.2 适用范围

适用于 Ubuntu 上的原生 ROS 2 和 WHEELTEC 预装 Docker 环境。TROS、Autoware 或厂商定制镜像应单独记录，不与普通 ROS 2 工作空间混用。

## 22.3 操作前检查

- 第 10 章硬件配置表已完成。
- 保存当前 `.bashrc`、工作空间路径和启动方式。
- 不解压新的 `src` 覆盖现有源码。

## 22.4 工作原理 {#runtime-environment}

ROS 2 工作空间（ROS 2 Workspace）是放置机器人程序并生成可运行版本的项目目录。它把源码、构建过程和安装结果放在同一处，方便开发者明确当前改的是哪一套程序。后续章节会在这个目录中构建功能包、启动节点和检查传感器数据。

一套可运行环境由 Ubuntu、ROS 发行版、架构、依赖、源码分支和硬件配置共同决定。ROS 2 Humble 源码不能因为目录名相近就放进 Foxy 环境；Jetson、树莓派、RDK 的相机与硬件加速依赖也不同。

Docker 还多一层边界：宿主机看到的文件、设备和网络，只有显式挂载或传入容器后才能被 ROS 使用。

机器人模型常用URDF保存连杆、关节和几何信息。第 25 章会在启动链中追踪它的加载位置，第 26 章再说明它与 TF2、RViz 的关系。

## 22.5 源码包确认 {#source-package-selection}

这份导读用于回答一个具体问题：执行一条 Launch 命令后，ROS 2 怎样从启动文件走到底盘串口节点、参数、话题、传感器和 TF？读者应在自己的机器人工作空间中完成追踪，不要把本页出现的文件名当成所有版本都相同的固定清单。

### 先确认正在查看哪一份包

同一台主控可能同时保留系统安装、旧工作空间和当前工作空间中的同名包。先在已经加载机器人环境的终端执行：

```bash
ros2 pkg prefix turn_on_wheeltec_robot
ros2 pkg executables turn_on_wheeltec_robot
ros2 pkg xml turn_on_wheeltec_robot
```

`ros2 pkg prefix` 指向的是安装结果，不一定是源码目录。再到已确认的工作空间中定位源码：

```bash
cd <机器人工作空间>
colcon list | rg '^turn_on_wheeltec_robot\s'
find src -type f -path '*/turn_on_wheeltec_robot/package.xml' -print
```

如果安装前缀、`colcon list` 和准备修改的目录不能对应，先停止，不要继续编辑或构建。

### 先判断源码是否完整

一份可用于修改和重建的包，应能根据构建类型找到与其职责对应的文件；下面是核对方向，不是要求每个包都必须同时拥有所有目录：

| 位置 | 职责 | 核对点 |
|---|---|---|
| `package.xml` | 包名、依赖、构建类型 | 是否仍有许可证或维护者占位；依赖是否与当前 ROS 发行版一致 |
| `CMakeLists.txt` 或 `setup.py` | CMake/ament 或 Python 安装规则 | 实际生成哪些可执行文件；Launch、配置和资源是否被安装 |
| `launch/`（若有） | 组合底盘、EKF、IMU、模型、雷达和相机 | 哪个是入口；它继续包含了哪些 Launch 文件 |
| `config/`（若有） | EKF、IMU、相机等参数 | 参数文件是否真的被入口引用 |
| `src/`、`include/` 或 Python 模块 | 串口收发、协议解析、里程计和 IMU 发布 | 节点订阅与发布哪些接口；单位在哪里转换 |
| `msg/`（若有） | 包内自定义消息 | 是否还依赖另一个消息包 |
| udev 脚本或规则（若有） | 固定串口设备别名 | 规则是否匹配当前 USB 芯片和序列号 |

只有 `launch/` 或几个 `.cpp` 文件的快照可用于静态阅读，不能据此声称“源码可以重建”。`build/`、`install/`、`log/`、`.pyc` 和 `__pycache__/` 是构建产物或缓存，也不能替代源码。

还要检查包外依赖：

```bash
cd <turn_on_wheeltec_robot 源码目录>
rg -n 'find_package\(|<depend>|<build_depend>|<exec_depend>' CMakeLists.txt package.xml
rg -n "get_package_share_directory\(|package='" launch
```

常见依赖包括串口库、机器人自定义消息、`wheeltec_robot_urdf`、`robot_localization`、IMU 滤波器、雷达驱动和相机驱动。缺少这些包时，只能说明当前工作空间不自包含；源码包本身仍可能是完整的。是否能够重建，要回到工作空间根目录执行构建并记录结果。

!!! note "代码资源边界"
    本节只使用环境与包查询命令，不依赖仓库中的专用代码资源；具体启动链源码在第 25 章定位。

## 22.6 验收标准

- 能明确说出命令运行在宿主还是容器。
- Ubuntu、架构和 `ROS_DISTRO` 已记录。
- 主工作空间只有一个明确入口。
- 源码包与主控、ROS 发行版和硬件配置有可追溯依据。
- Autoware、TROS 或其他工作空间不会无意叠加到普通机器人环境。

需要继续追踪底盘包的入口、依赖和运行链时，按 [`turn_on_wheeltec_robot` 源码与启动链导读](25-launch-and-parameters.md#bringup-launch-chain)从安装前缀反查到当前工作空间，不要根据目录名选择源码。

## 22.7 故障排查

环境问题先从设备映射查起，再确认驱动包和节点来自正确环境；节点启动后依次查看话题、时间与坐标，最后才读取建图或导航算法日志。下表列出在这一顺序中常见的入口现象。

| 现象 | 处理 |
|---|---|
| `ROS_DISTRO` 为空 | 查 `/opt/ros`，确认是否未 source 或在错误终端 |
| 同一个包解析到意外路径 | 检查 `AMENT_PREFIX_PATH` 和多个 `install/setup.bash` |
| 宿主有设备、容器没有 | 检查设备映射、权限和容器启动参数 |
| 源码目录名正确但依赖报错 | 核对发行版、架构和分支，不先强装随机版本依赖 |

## 章节导航

[上一章：直线纠偏、转向标定和常见底盘故障](../04-chassis-control/21-calibration-and-faults.md) · [返回本篇](index.md) · [下一章：工作空间、功能包与构建](23-workspace-packages-build.md)
