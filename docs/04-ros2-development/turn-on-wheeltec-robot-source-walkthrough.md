---
status: complete
---

# `turn_on_wheeltec_robot` 源码与启动链导读

这份导读用于回答一个具体问题：执行一条 Launch 命令后，ROS 2 怎样从启动文件走到底盘串口节点、参数、话题、传感器和 TF？读者应在自己的机器人工作空间中完成追踪，不要把本页出现的文件名当成所有版本都相同的固定清单。

本页的 `status: complete` 只表示导读文档已经完成，不表示任何一台具体机器人已经通过实机验收。

## 先确认正在查看哪一份包

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

## 先判断源码是否完整

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

## 从入口追踪启动链

不要从最长的 Launch 文件开始猜。先列出入口及其包含关系：

```bash
cd <turn_on_wheeltec_robot 源码目录>
rg -n 'IncludeLaunchDescription|get_package_share_directory|Node\(' launch
```

一套常见结构如下；文件名、节点名和层级均为观察启动链时的示例，不是当前版本的固定接口：

```text
wheeltec_sensors.launch.py
├── turn_on_wheeltec_robot.launch.py
│   ├── base_serial.launch.py
│   │   └── wheeltec_robot_node
│   ├── wheeltec_ekf.launch.py
│   │   └── robot_localization/ekf_node
│   ├── robot_state_publisher + 车型 URDF
│   ├── static_transform_publisher
│   ├── joint_state_publisher
│   └── imu_filter_madgwick_node
├── wheeltec_lidar.launch.py
└── wheeltec_camera.launch.py
```

这张树只是追踪方法，不是所有版本的保证。实际入口可能只启动底盘，也可能把雷达和相机一起启动；以当前工作空间的源码和运行节点为准。

启动链闭合不等于数据链闭合：某个雷达或相机进程被启动，只能证明 Launch 创建了它；还要检查 EKF 配置、remap、话题类型、频率和 TF，才能证明数据真正被消费。

### 从工作空间根执行构建和启动

以下命令中的 `<工作空间>`、`<入口.launch.py>` 和参数值必须替换为当前机器实际存在的内容：

```bash
cd <工作空间>
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-up-to turn_on_wheeltec_robot
source install/setup.bash
ros2 launch turn_on_wheeltec_robot <入口.launch.py>
```

如果 `ros2 launch` 找不到入口，先运行 `ros2 pkg prefix`、`ros2 pkg executables` 和 `find src`，不要猜测文件名。

### 底盘最小入口

`base_serial.launch.py` 通常负责创建 `wheeltec_robot_node`，并传入串口设备、波特率、底盘坐标系和里程计坐标系。例如常见参数包括：

- `usart_port_name`：底盘串口别名；
- `serial_baud_rate`：与 STM32 固件一致的波特率；
- `robot_frame_id`：里程计消息的子坐标系；
- `odom_frame_id`：里程计消息的父坐标系。

参数名存在不代表运行值正确。启动后必须用 `ros2 param get` 回读节点实际值。

### 机器人组合入口

`turn_on_wheeltec_robot.launch.py` 往往在底盘节点之外继续启动 EKF、IMU 滤波、关节状态、车型 URDF 和静态 TF。车型选择可能由布尔 Launch 参数和注释切换，而不是一张集中 YAML 表。因此修改车型前要同时检查：

1. 哪个车型 Include 被加入 `LaunchDescription`；
2. 传给车型 Launch 的参数是否为真；
3. `wheeltec_robot_urdf` 中是否存在对应 URDF；
4. 雷达和相机相对 `base_footprint` 的静态变换是否与实机安装一致。

### 传感器组合入口

`wheeltec_sensors.launch.py` 通常再包含底盘、雷达和相机三条分支。雷达和相机 Launch 会通过 `get_package_share_directory()` 查找外部驱动包，所以单独复制 `turn_on_wheeltec_robot` 不能恢复整套传感器启动链。

## 从参数追到运行节点

按“Launch 赋值 → 节点声明 → 节点读取 → 运行值”四步核对：

```bash
cd <turn_on_wheeltec_robot 源码目录>
rg -n 'parameters=|DeclareLaunchArgument|LaunchConfiguration' launch
rg -n 'declare_parameter|get_parameter' src include

ros2 node list
ros2 param list <底盘节点名>
ros2 param get <底盘节点名> usart_port_name
ros2 param get <底盘节点名> serial_baud_rate
ros2 param get <底盘节点名> robot_frame_id
ros2 param get <底盘节点名> odom_frame_id
```

若源码默认值、Launch 传入值和运行值不同，优先确认是否加载了另一工作空间或另一 Launch 入口，而不是立即修改第三处参数。

## 从 `cmd_vel` 追到 STM32，再回到 ROS 2

底盘节点通常订阅 `geometry_msgs/msg/Twist` 类型的 `cmd_vel`，把线速度和角速度编码为串口下行帧。STM32 返回编码器、IMU 和电压等数据后，节点解析并发布里程计、原始 IMU 和供电电压。可以按下列链路定位：

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

将 `/odom` 的 `header.frame_id`、`child_frame_id` 与节点参数比较；将 IMU 的 `header.frame_id` 与 TF 树比较；同时记录 `ros2 topic hz` 的频率。话题名称可能被命名空间或 remap 改写，应以 `ros2 node info` 的实际结果为准。

这些命令仍不能单独证明波特率已经生效、节点确实打开了预期设备或 STM32 已正确执行帧。硬件证据至少应包括：节点打开串口的日志或设备句柄、在电机失能/架空条件下观察到零速下行帧，以及 STM32 返回帧被节点接收并转成预期话题。缺少其中任一项，只能报告 ROS 图上的静态或运行时接口证据。

## 安全修改练习

第一次练习只追踪，不改协议和车型：

1. 保存 `git status`、当前提交、包安装前缀和节点列表；
2. 画出实际 Launch 包含树，并把它与实际节点列表分开记录；
3. 记录底盘节点的串口、波特率和 frame 参数；
4. 记录 `cmd_vel`、里程计、IMU、电压和 TF 的实际接口、类型和频率；
5. 回到工作空间根，用 `colcon build --packages-up-to turn_on_wheeltec_robot` 验证能否重建；
6. 新终端执行 `source <工作空间>/install/setup.bash`，再次确认 `ros2 pkg prefix`；
7. 仅在急停可用、电机失能或架空轮子条件下启动节点；先发布零速 `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"`，再根据节点日志和串口工具确认零速帧与 STM32 回包；
8. 分别检查 `/odom` 的两个 frame 字段、IMU frame、TF 路径和传感器频率；
9. 恢复原环境，确认基线仍可运行。

只有启动链、ROS 数据链和必要的硬件证据都闭合后，才进入第 23 章的单一修改和回滚流程。涉及车型、串口协议和底盘运动时，还要保持急停可用、从零速开始，并验证通信断开后的失能行为。

## 验收记录

完成导读后应留下以下记录：

| 项目 | 记录内容 |
|---|---|
| 环境 | Ubuntu、架构、`ROS_DISTRO`、宿主或容器 |
| 包来源 | 工作空间、提交或版本日期、`ros2 pkg prefix` |
| 完整性 | 缺失的包、URDF、驱动或配置；是否只完成静态导读 |
| 启动入口 | 顶层 Launch 及其包含树 |
| 底盘节点 | 可执行文件、串口、波特率、参数和命名空间 |
| 下行链路 | `cmd_vel` 到串口帧的源码位置和单位 |
| 上行链路 | 里程计、IMU、电压和 TF 的实际名称与类型 |
| 构建验收 | 构建命令、退出码和加载后的包前缀 |
| 回滚 | 原环境或原文件的恢复方法 |

如果缺少任何一项，应把结论写成“待核对”或“仅完成静态导读”，不要扩大为实机兼容或可运行结论。
