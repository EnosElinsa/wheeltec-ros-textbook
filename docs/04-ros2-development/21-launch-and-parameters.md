---
status: complete
---

# 21. Launch、参数与运行配置

## 21.1 学习目标

从正在使用的 Launch 文件追踪节点、参数文件和条件分支，安全修改车型、端口与传感器配置，并证明运行节点读到了新值。

## 21.2 适用范围

适用于 Python Launch 和 YAML 参数。旧 XML Launch 或 ROS 1 参数服务器见附录 A。

## 21.3 操作前检查

- 复制当前 Launch 和参数文件，记录哈希或日期。
- 确认实际加载的工作空间，不编辑同名备份。
- 停止依赖该参数的节点后再改关键端口和车型。

## 21.4 工作原理

Launch 描述一次运行需要启动哪些节点、传入哪些参数和命名空间。YAML 文件只是参数来源之一；Launch 内部默认值、命令行覆盖和节点代码默认值都可能改变最终结果。

## 21.5 操作步骤 {#bringup-launch-chain}

### `turn_on_wheeltec_robot` 源码与启动链导读

执行一条 Launch 命令后，可按本节方法从入口追踪到底盘串口节点、参数、话题、传感器和 TF。

### 从入口追踪启动链

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

#### 从工作空间根执行构建和启动

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

#### 底盘最小入口

`base_serial.launch.py` 通常负责创建 `wheeltec_robot_node`，并传入串口设备、波特率、底盘坐标系和里程计坐标系。例如常见参数包括：

- `usart_port_name`：底盘串口别名；
- `serial_baud_rate`：与 STM32 固件一致的波特率；
- `robot_frame_id`：里程计消息的子坐标系；
- `odom_frame_id`：里程计消息的父坐标系。

参数名存在不代表运行值正确。启动后必须用 `ros2 param get` 回读节点实际值。

#### 机器人组合入口

`turn_on_wheeltec_robot.launch.py` 往往在底盘节点之外继续启动 EKF、IMU 滤波、关节状态、车型 URDF 和静态 TF。车型选择可能由布尔 Launch 参数和注释切换，而不是一张集中 YAML 表。因此修改车型前要同时检查：

1. 哪个车型 Include 被加入 `LaunchDescription`；
2. 传给车型 Launch 的参数是否为真；
3. `wheeltec_robot_urdf` 中是否存在对应 URDF；
4. 雷达和相机相对 `base_footprint` 的静态变换是否与实机安装一致。

#### 传感器组合入口

`wheeltec_sensors.launch.py` 通常再包含底盘、雷达和相机三条分支。雷达和相机 Launch 会通过 `get_package_share_directory()` 查找外部驱动包，所以单独复制 `turn_on_wheeltec_robot` 不能恢复整套传感器启动链。

### 从参数追到运行节点

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

!!! example "本章代码：底盘启动链"
    仓库目录：[ros2/robot/turn-on-wheeltec-robot](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/667b1ffceb4354c19ef8f0e94969fcd25cbb5d6b/ros2/robot/turn-on-wheeltec-robot)

    使用 `launch/turn_on_wheeltec_robot.launch.py`、`launch/base_serial.launch.py`、`launch/robot_mode_description.launch.py` 和 `src/wheeltec_robot.cpp` 静态追踪入口、底盘节点和车型分支。验收：能定位入口 Launch 与底盘节点关系。边界：外部 URDF 包未随本资源发布，不能据此启动机器人。

## 21.6 验收标准

- 能从 Launch 入口追踪到实际参数文件。
- 修改只涉及一个可解释配置项。
- 运行节点的 `ros2 param get/dump` 证明新值已加载。
- 恢复备份后可回到原行为。

## 21.7 故障排查

| 现象 | 原因 |
|---|---|
| 文件改了但值没变 | 编辑了错误工作空间、Launch 使用另一文件或安装副本 |
| YAML 解析失败 | 缩进、冒号、Tab 或类型错误 |
| 参数存在但节点忽略 | 参数名/命名空间不匹配或代码未声明 |
| 同一参数被覆盖 | Launch、命令行和 YAML 多处赋值 |

## 章节导航

[上一章：节点、话题、服务与动作](20-nodes-topics-services-actions.md) · [返回本篇](index.md) · [下一章：TF、URDF 与 RViz](22-tf-urdf-rviz.md)
