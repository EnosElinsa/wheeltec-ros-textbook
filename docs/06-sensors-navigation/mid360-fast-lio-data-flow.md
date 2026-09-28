---
status: draft
---

# MID360 与 FAST-LIO 三维建图的数据流

本页以 `/home/wheeltec/Mid360_test_ws0922` 为例，说明 MID360 的数据怎样从以太网进入 ROS 2，再经过 FAST-LIO 变成位姿、轨迹和三维点云地图。这里使用的是当前实机抓到的消息和网络数据，不把“驱动发布了什么”和“算法最后算出了什么”混成一个步骤。

## 过程概要

MID360 通过 Jetson 的 `enP8p1s0` 网口发送 UDP 数据。当前雷达地址是 `192.168.1.3`，Jetson 地址是 `192.168.1.50`。点云从雷达的 UDP 56300 端口发出，IMU 数据从 56400 端口发出。Livox SDK2 先把这些二进制数据包解析成设备数据，`livox_ros_driver2` 再把它们封装成 ROS 2 消息。

驱动节点发布 `/livox/lidar` 和 `/livox/imu`。FAST-LIO 订阅这两个话题，先按点的时间信息和配置参数处理点云，再用 IMU 推算短时间运动，最后用点云和局部地图的几何匹配修正位置和姿态。算法输出 `/Odometry`、`/path`、`/cloud_registered`、`/Laser_map` 和一段 `camera_init → body` 的 TF，RViz2 订阅这些结果并显示当前点云、累计地图和运动轨迹。

```text
MID360
  ↓ 以太网 UDP 点云包、IMU 包
Livox SDK2
  ↓ 解码设备协议
livox_ros_driver2
  ├── /livox/lidar  : livox_ros_driver2/msg/CustomMsg
  └── /livox/imu    : sensor_msgs/msg/Imu
              ↓ ROS 2 话题
FAST-LIO
  ↓ 预处理、IMU 传播、点云匹配和状态更新
  ├── /Odometry
  ├── /path
  ├── /cloud_registered
  ├── /Laser_map
  └── /tf：camera_init → body
              ↓
            RViz2
```

## 1. 两个 Launch 文件如何组成运行系统

本例不是把所有代码写在一个可执行文件里，而是用两个 Launch 文件组织节点。

`src/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py` 启动一个名为 `/livox_lidar_publisher` 的驱动节点。这个节点调用 SDK，同时发布点云和 IMU 两个话题。

`src/FAST_LIO_ROS2/launch/mapping.launch.py` 启动 `/laser_mapping` 和 `/rviz` 两个节点。`/laser_mapping` 读取 `mid360.yaml`，`/rviz` 读取 FAST-LIO 的显示配置。

因此，Launch 文件的作用是描述“启动哪些节点、使用哪些参数、节点怎样组合”，而不是替代节点本身的计算。一个 Launch 文件可以启动多个节点；一个节点也可以发布多个话题、订阅多个话题或提供服务。当前系统的连接关系可以概括为：

| 节点 | 订阅 | 发布 |
|---|---|---|
| `/livox_lidar_publisher` | 参数事件 | `/livox/lidar`、`/livox/imu` |
| `/laser_mapping` | `/livox/lidar`、`/livox/imu` | `/Odometry`、`/path`、`/cloud_registered`、`/cloud_registered_body`、`/cloud_effected`、`/Laser_map`、`/tf` |
| `/rviz` | 地图、点云、轨迹、里程计和 TF | 可视化工具话题 |

节点之间通过 ROS 2 的发布/订阅接口交换消息。FAST-LIO 并不直接调用 Livox 驱动的 C++ 函数，也不直接读取 UDP 网卡；它只按消息类型订阅 `/livox/lidar` 和 `/livox/imu`。

## 2. 从 UDP 数据到两个 ROS 2 输入话题

### 2.1 网络层实际传输了什么

在两个 Launch 都运行时抓取 100 个数据包，得到：

| 数据 | 来源 | 目标 | 抓到的包数 | UDP 负载长度 |
|---|---|---|---:|---:|
| 点云 | `192.168.1.3:56300` | `192.168.1.50:56301` | 91 | 1380 字节 |
| IMU | `192.168.1.3:56400` | `192.168.1.50:56401` | 9 | 60 字节 |

抓包过程报告了 `0 packets dropped by kernel`。这说明这次网卡抓包没有丢包，但它只说明这一小段网络采样正常，不能代替长时间运行验收。UDP 负载是设备协议的二进制数据，不是 ROS 2 消息。SDK 需要先按协议解析包头、序号、时间和测量值，再交给驱动节点组合。

同样的抓包可以在不停止驱动的情况下进行：

```bash
sudo tcpdump -ni enP8p1s0 -c 100 \
  -w /tmp/mid360_sample.pcap \
  'host 192.168.1.3 and (udp port 56300 or udp port 56400)'
```

还要注意抓包时间显示为 `1970-01-01`。这反映出 Jetson 的系统时钟没有同步。数据包能够到达并不代表时间基准正确；正式建图、录包和多传感器同步前仍需先处理系统时间。

### 2.2 点云话题

驱动把多个 UDP 点云包组合成一帧 `CustomMsg`，发布在：

```text
/livox/lidar
类型：livox_ros_driver2/msg/CustomMsg
```

当前实测一帧消息为：

```text
header.frame_id: livox_frame
point_num: 20064
points: 20064
lidar_id: 192
```

每个 `CustomPoint` 主要包含：

```text
offset_time   # 点相对本帧起始时间的偏移
x, y, z       # 雷达坐标系中的位置，单位 m
reflectivity  # 反射强度
tag           # Livox 点标记
line          # 设备通道编号
```

这里的 `line` 是当前 Livox 消息中的设备字段，不能不经确认就当作机械多线雷达算法所需的 `ring` 字段。

当前测得的 ROS 2 话题频率约为 `5.16 Hz`。UDP 点云包的数量和 ROS 2 点云帧的数量不能直接相除，因为一帧 ROS 2 点云由多个网络包组合而成。

如果设备只提供距离和角度，一个点的笛卡尔坐标可以写成：

\[
x = r\cos\varphi\cos\theta,\qquad
y = r\cos\varphi\sin\theta,\qquad
z = r\sin\varphi
\]

当前 SDK 已经提供了 `x、y、z`，因此驱动主要负责解析、组合和发布，而不是在 ROS 2 节点中重新计算每个点。

### 2.3 IMU 话题

驱动把 IMU UDP 包封装成：

```text
/livox/imu
类型：sensor_msgs/msg/Imu
```

当前实测频率约为 `199.8 Hz`，`frame_id` 为 `livox_frame`。静止采样中角速度接近零，线加速度的 z 分量约为 `0.984`。当前消息的 `orientation` 是单位四元数，不能把它当成驱动已经完成的有效姿态解算。FAST-LIO 主要使用角速度、线加速度和时间戳自行估计姿态。

加速度的单位必须按当前驱动源码和算法预期核对。不能只因为字段叫 `linear_acceleration`，就默认每个数值已经是 `m/s²`。

## 3. FAST-LIO 如何加工输入数据

FAST-LIO 收到点云和 IMU 后，并不是把点直接叠加起来。它先按 `mid360.yaml` 中的配置处理输入：

```yaml
lidar_type: 1
scan_line: 4
blind: 0.5
timestamp_unit: 3
point_filter_num: 3
```

`blind: 0.5` 表示算法处理时忽略雷达周围 0.5 m 以内的点。这是 FAST-LIO 内部的近距离过滤，不是驱动发布点云时对某个方向做角度屏蔽。

一帧点云内部的点不是同一时刻采集的。若本帧起始时间为 `timebase`，第 `i` 个点的时间可以理解为：

\[
t_i = \text{timebase} + \text{offset\_time}_i
\]

机器人运动时，如果直接把整帧点当成同一时刻，墙面会出现弯曲或撕裂。FAST-LIO 结合 IMU 的高频运动信息，对点云进行时间补偿，再把点用于匹配。

IMU 先给出短时间运动预测。简化表示为：

\[
\omega = \omega_m - b_g - n_g,\qquad
a = a_m - b_a - n_a
\]

\[
R_{k+1}=R_k\operatorname{Exp}(\omega\Delta t)
\]

\[
v_{k+1}=v_k+(R_k a+g)\Delta t
\]

\[
p_{k+1}=p_k+v_k\Delta t+\frac12(R_k a+g)\Delta t^2
\]

IMU 积分会随时间漂移，因此 FAST-LIO 再把当前点云和局部地图进行几何匹配，用点到地图平面或局部特征的误差修正位置、姿态、速度和 IMU 偏置。这里的姿态解算来自点云和 IMU 的融合，而不是来自轮式 `/odom`。

点云还需要经过雷达与 IMU 之间的外参变换。简化写成：

\[
p_{body}=R_{LI}p_{lidar}+t_{LI}
\]

\[
p_{world}=R_{WB}p_{body}+t_{WB}
\]

只有把不同时间、不同坐标系中的点变换到共同的建图坐标系，连续扫描才能叠加成地图。

## 4. FAST-LIO 的输出与 RViz2 显示

当前 FAST-LIO 发布的主要结果如下：

| 话题 | 类型 | 当前含义 |
|---|---|---|
| `/Odometry` | `nav_msgs/msg/Odometry` | `camera_init` 中的 `body` 位姿 |
| `/path` | `nav_msgs/msg/Path` | 连续位姿组成的历史轨迹 |
| `/cloud_registered` | `sensor_msgs/msg/PointCloud2` | 当前已经配准到全局坐标的点云 |
| `/Laser_map` | `sensor_msgs/msg/PointCloud2` | 累积三维点云地图 |
| `/tf` | `tf2_msgs/msg/TFMessage` | 当前发布 `camera_init → body` |
| `/map_save` | `std_srvs/srv/Trigger` 服务 | 请求保存当前点云地图 |

现场测得 `/Odometry` 约为 `9.93 Hz`。一次 `/Odometry` 样本的坐标字段为：

```text
header.frame_id: camera_init
child_frame_id: body
pose.position:
  x: 1.0656
  y: -0.1991
  z: -0.0834
```

`/cloud_registered` 的 `frame_id` 是 `camera_init`，一次采样中有 390 个点。`/Laser_map` 的 `frame_id` 也是 `camera_init`，现场采样时累计约 126 万个点。

RViz2 中的显示对应关系为：

```text
红色箭头      → /Odometry
绿色轨迹      → /path
当前配准点云  → /cloud_registered
累积地图      → /Laser_map
坐标变换      → /tf
```

这些颜色是 RViz2 的显示设置。红色箭头表示 FAST-LIO 当前估计的 `body` 位姿，绿色线是历史位姿连接出的轨迹，并不是轮式编码器单独计算出的路径。

## 5. 与二维建图输入的区别

二维 SLAM 常见的数据流是：

```text
/scan : sensor_msgs/msg/LaserScan
/odom : nav_msgs/msg/Odometry
TF：map → odom → base_link → laser
```

二维算法通常在平面上估计 `x、y、yaw`，轮式里程计提供连续的短时运动，静态 TF 提供雷达相对车体的安装关系。

当前 FAST-LIO 的数据流是：

```text
/livox/lidar + /livox/imu
  ↓
FAST-LIO 自己估计三维运动
  ↓
camera_init → body
  ↓
/Laser_map : sensor_msgs/msg/PointCloud2
```

因此，当前 FAST-LIO 建图不要求轮式 `/odom` 作为输入，但仍然需要正确的时间戳、雷达—IMU 外参和内部坐标关系。它输出的是三维点云地图，不是二维 SLAM 常见的 `/map` 栅格地图。

后续若要接 Nav2，还需要把三维地图转换为导航所需的二维地图或代价地图，并明确 `body`、`base_link` 和 `livox_frame` 的关系。不能直接把 `camera_init → body` 当作已经完整的 `map → odom → base_link → laser` 链。

## 6. 运行、检查和结束

### 启动驱动

```bash
sudo nmcli connection up mid360-direct

cd /home/wheeltec/Mid360_test_ws0922
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch livox_ros_driver2 msg_MID360_launch.py
```

### 启动 FAST-LIO 和 RViz2

另开终端：

```bash
cd /home/wheeltec/Mid360_test_ws0922
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch fast_lio mapping.launch.py \
  config_file:=mid360.yaml \
  rviz:=true
```

先让机器人静止几秒，看到 `IMU Initial Done` 和 `Initialize the map kdtree` 后，再缓慢移动机器人。检查输入和输出：

```bash
ros2 topic list -t
ros2 topic type /livox/lidar
ros2 topic hz /livox/lidar
ros2 topic hz /livox/imu
ros2 topic hz /Odometry
ros2 topic echo --once /Odometry
ros2 topic info /Laser_map --verbose
ros2 run tf2_ros tf2_echo camera_init body
```

启动时偶尔出现 `No point, skip this scan!`，可能只是点云队列尚未准备好。若在初始化后持续出现 `No Effective Points!`，则应检查点云格式、时间、外参、盲区参数和场景中的有效几何特征。

当前配置把点云保存参数写在 `mid360.yaml` 中，地图文件名为 `./test.pcd`。实际保存位置取决于启动 FAST-LIO 时的当前工作目录。若要调用节点提供的保存服务，可以在另一个终端执行：

```bash
ros2 service call /map_save std_srvs/srv/Trigger "{}"
```

停止时先在 FAST-LIO 终端按 `Ctrl+C`，再停止雷达驱动。不要同时启动 `msg_MID360_launch.py` 和 `rviz_MID360_launch.py`，因为它们会启动两套驱动；后者使用的是面向原始点云观察的输出配置，不应与 FAST-LIO 的自定义点云输入同时运行。

## 7. 数据验收顺序

遇到地图不更新时，按数据流从前往后检查：

```text
网口和 UDP 数据
  → 驱动节点
  → /livox/lidar 与 /livox/imu
  → 消息类型、频率、时间戳和单位
  → FAST-LIO 是否订阅
  → /Odometry 和 /tf
  → /cloud_registered 和 /Laser_map
  → RViz2 固定坐标系和显示项
```

只看到 RViz2 窗口并不能证明地图正确。必须同时确认设备层、ROS 2 话题层和算法输出层。当前系统已经用 UDP pcap、`ros2 node info`、话题频率和实际消息样本完成了这三层的基本核对。
