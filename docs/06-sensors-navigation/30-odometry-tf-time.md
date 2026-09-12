---
status: complete
---

# 30. 里程计、TF 与时间


## 30.1 为什么只有雷达数据还不够

第 29 章已经确认雷达驱动能够发布 `sensor_msgs/msg/LaserScan`。但一帧雷达扫描只说明“当前看到了什么”，没有说明机器人这一帧相对于上一帧移动了多少，也没有说明雷达安装在车体的什么位置。二维建图需要把连续扫描放到同一坐标关系和时间基准下进行匹配，因此通常还需要：

- 里程计：描述机器人根据车轮运动估计出的位姿变化；
- TF：描述 `odom`、`base_link` 和 `laser` 等坐标系之间的关系；
- 时间戳：说明每条扫描、里程计和坐标变换是在什么时候产生的。

这些数据也通过 ROS 2 话题传递。同步定位与建图（Simultaneous Localization and Mapping, SLAM）节点通常订阅 `/scan`，并从 `/tf`、`/tf_static` 以及可选的 `/odom` 获得配准所需的信息。

## 30.2 里程计从哪里来

轮式机器人最常见的里程计来源是轮式编码器。数据链路通常是：

```text
轮式编码器
  → STM32 定时器或计数接口
  → STM32 固件计算轮速和轮间位移
  → UART / CAN / USB 发送到底盘主控
  → ROS 2 底盘驱动节点解析
  → /odom（nav_msgs/msg/Odometry）
```

在轮趣 R680 这类底盘中，STM32 读取编码器并计算底盘状态，主控上的底盘 ROS 2 节点再把状态帧转换成里程计消息。`/odom` 不是编码器原始脉冲本身，而是根据轮径、轮距、车型运动学和编码器方向计算出的估计结果。

### 扩展卡尔曼滤波器 {#odometry-ekf}

注：有些系统会把轮速里程计和 IMU 一起交给扩展卡尔曼滤波器（Extended Kalman Filter, EKF）处理。例如，底盘节点先发布原始轮速里程计 `/odom_raw`，EKF 再订阅 `/odom_raw` 和 `/imu/data`，输出一个融合后的 `/odometry/filtered`。融合后的话题不是“第二个编码器”，而是根据多种测量重新估计出的结果，通常比单独轮速里程计更平滑，但它的坐标定义和发布者必须先确认。
“重复融合”是指把已经包含轮速信息的 `/odometry/filtered` 再送回同一个 EKF，或把原始 `/odom_raw` 和由它融合得到的 `/odometry/filtered` 当成两份相互独立的测量同时输入。这样会让同一份编码器信息被重复计算，导致协方差和位姿估计失真。还要避免同时运行两个都发布 `odom → base_link` 的里程计或融合节点。


检查里程计时，至少确认：

```bash
ros2 topic info /odom --verbose
ros2 topic echo --once /odom
ros2 topic hz /odom
```

重点查看时间戳、线速度和角速度；坐标字段将在后面的 TF 小节结合示例介绍。静止时速度应接近零，架空低速转动车轮时方向和轮号应符合实际。

## 30.3 先认识建图所需的坐标关系 {#odometry-slam}

坐标系是一套描述位置和方向的约定：先规定一个原点，再规定 x、y、z 轴的朝向。同一个实际位置，换一个坐标系描述后，坐标数值会改变。例如，雷达前方 1 m 处的墙面，在 `laser` 坐标系中可能写成 `x=1.0`；换算到 `base_link` 或 `map` 后，还要考虑雷达的安装位置和机器人当前位姿。机器人建图时同时使用以下几套坐标系：

| 坐标系 | 它是什么 | 数据或位姿如何使用它 |
|---|---|---|
| `map` | SLAM 建立的全局参考坐标系，原点通常在建图开始时确定 | 地图栅格和全局定位结果使用它；它不随机器人运动 |
| `odom` | 由里程计在启动时建立、原点固定在起始位置的局部参考坐标系 | 作为“从起点开始累计运动”的计算基准；短时间连续平滑，但没有绝对定位，打滑和累计误差会使它逐渐偏离真实世界 |
| `base_link` | 固定在机器人车体上的坐标系，原点和轴随车体一起移动 | 描述车体本身的当前位置、朝向和速度，也是连接轮式底盘与各传感器的中间坐标系 |
| `laser` | 固定在激光雷达上的坐标系 | `LaserScan` 的距离和角度先按这个坐标系解释；它相对车体的安装关系由 `base_link → laser` 给出 |


它们按 `map → odom → base_link → laser` 串成一条坐标变换链。这里的箭头表示“父坐标系到子坐标系”的变换关系，不是传感器数据或消息的传输方向。

`odom` 和 `base_link` 都与车体运动有关，但角色不同：`odom` 是一个固定在起点、用于计算的参考坐标系；`base_link` 是刚性固定在车体上的坐标系，会随机器人一起移动。可以把它理解为：机器人启动时在地面参考中建立一个名为 `odom` 的坐标原点，同时在车体上建立一个名为 `base_link` 的坐标原点。车体向前行驶时，地面上的 `odom` 原点不动，车体上的 `base_link` 原点随机器人移动。里程计根据编码器每一小段位移，持续计算并更新“`base_link` 在 `odom` 中的位置和朝向”，这就是 `odom → base_link`。

这段关系的作用是给系统提供连续的短时运动估计：SLAM 可以根据它判断机器人在前后两次雷达扫描之间移动了多远，再把两次扫描中的同一面墙或同一个障碍物放到地图中的相同位置；导航可以知道机器人当前朝向和速度，传感器数据也可以通过它转换到车体坐标。由于 `odom` 只靠运动积分、没有地图或 GNSS 这样的绝对参照，行驶越久误差可能越大；这时 SLAM 会把当前雷达扫描与已经建立的环境特征进行匹配，估计一个更符合环境的位置，并通过 `map → odom` 修正里程计结果在地图中的整体偏差。`base_link` 则始终代表车体本身，不能因为里程计漂移就改变其与车体的刚性关系。

!!! example "一个简单例子"
    机器人沿走廊前进后又回到原来的位置。编码器累计误差使 `odom` 认为机器人比实际多走了一点，但雷达重新看到相同的墙面和门框。SLAM 比较这些特征后发现当前扫描与原地图稍微错开，于是调整 `map → odom`，让扫描重新与墙面重合。这里修正的是里程计坐标在地图中的位置，不是修改编码器脉冲或移动 `odom` 的原点。

三段关系各自解决一个问题：`map → odom` 把会漂移的局部里程计对齐到全局地图，`odom → base_link` 提供车体的连续运动，`base_link → laser` 说明雷达装在车体的什么位置和方向。三段变换组合后，系统才能把雷达坐标系中的测量点换算到地图坐标系；缺少任意一段，SLAM 就无法确定该点在地图中的位置。

## 30.4 TF 从哪里来

TF（Transform）是 ROS 2 中描述坐标系之间位置和姿态关系的机制。二维建图常见的坐标链是：

```text
map → odom → base_link → laser
```

建图阶段通常由不同程序负责不同的坐标关系：

| 坐标关系 | 常见发布者 | 变化类型 | 含义 |
|---|---|---|---|
| `odom → base_link` | 底盘里程计节点或融合节点 | 动态 | 机器人根据运动估计出的连续位姿 |
| `base_link → laser` | URDF + `robot_state_publisher`，或静态 TF 发布器 | 静态 | 雷达相对车体的安装位置和朝向 |
| `map → odom` | SLAM 节点 | 动态 | SLAM 为修正里程计漂移而估计的全局关系 |

TF 变换也要通过 ROS 2 话题发布：会随时间变化的变换发布在 `/tf`，永远不变的安装关系发布在 `/tf_static`。例如，机器人行驶时 `odom → base_link` 会不断更新，所以属于动态 TF；雷达固定在车体支架上，`base_link → laser` 通常不变，所以属于静态 TF。

一段 TF 只能有一个明确的负责人，常见分工如下：

| TF 关系 | 通常由谁发布 | 为什么 |
|---|---|---|
| `odom → base_link` | 底盘里程计节点或 EKF | 根据车轮和 IMU 数据持续计算车体运动 |
| `base_link → laser` | `robot_state_publisher` 或静态 TF 节点 | 描述雷达相对车体的固定安装位置 |
| `map → odom` | SLAM 或定位节点 | 根据地图匹配结果修正里程计的整体漂移 |

例如，底盘里程计节点已经在发布 `odom → base_link` 时，SLAM 只需要使用这段 TF 并发布 `map → odom`，不应再发布另一份 `odom → base_link`。如果两个节点同时发布同一段关系，它们可能给出不同的位置和时间戳，TF 接收端就会在两份结果之间切换，表现为地图重影、机器人位置跳动或扫描突然错位。启动系统时应确认每段 TF 只有一个发布者。

### 在 ROS 2 程序中表达 TF 和里程计消息

在 ROS 2 中，一段 TF 通常表示为 `geometry_msgs/msg/TransformStamped` 消息：`header.frame_id` 写父坐标系，`child_frame_id` 写子坐标系，`transform.translation` 写子坐标系原点在父坐标系中的平移，`transform.rotation` 写子坐标系相对父坐标系的四元数旋转。例如 `odom → base_link` 的消息核心字段是：

```text
header.frame_id: odom       # 父坐标系
child_frame_id: base_link   # 子坐标系
transform.translation:      # 车体原点在 odom 中的位置
  x: 0.50
  y: 0.00
  z: 0.00
transform.rotation:         # 车体相对 odom 的朝向（四元数）
  x: 0.0
  y: 0.0
  z: 0.0
  w: 1.0
```

程序不是把整条链写成一条字符串，而是分别发布 `map → odom`、`odom → base_link` 和 `base_link → laser` 三段 `TransformStamped`，TF2 再按父子关系自动查询和组合它们。动态变换会进入 `/tf`，固定的安装变换会进入 `/tf_static`。可以用下面的命令查看实际结果：

```bash
ros2 topic echo --once /tf
ros2 run tf2_ros tf2_echo odom base_link
```


### `header.frame_id` 和 `child_frame_id`

在 `nav_msgs/msg/Odometry` 里，这两个字段也共同说明里程计消息中的坐标关系。它们与上面 `TransformStamped` 中的字段名称相同，但这里位于里程计消息中，用来描述 `pose` 和 `twist` 的参考关系：

- `header.frame_id` 是参考坐标系，表示 `pose` 中的位置和姿态是在哪个坐标系下描述的；
- `child_frame_id` 是被描述的机器人坐标系，通常是车体的 `base_link`。在 `nav_msgs/msg/Odometry` 中，`twist` 通常也按照这个坐标系表达。

因此，常见的里程计消息会写成：

```text
header.frame_id: odom
child_frame_id: base_link
```

它表达的是 `odom → base_link`：在连续但可能逐渐漂移的 `odom` 坐标系中，机器人车体 `base_link` 当前位于什么位置、朝向如何以及运动速度是多少。这里的字段只是描述关系，不会自动创建 TF；是否真的发布了对应的 TF，还要用 `ros2 topic echo /tf` 或 `tf2_echo` 另外确认。若把 `frame_id` 写成雷达坐标、把 `child_frame_id` 写成不存在的坐标，或者与实际 TF 链不一致，SLAM 和导航就可能出现跳变或找不到变换。

例如，执行 `ros2 topic echo --once /odom` 可能看到：

```text
header:
  stamp:
    sec: 1720000100
    nanosec: 456789000
  frame_id: odom
child_frame_id: base_link
pose:
  pose:
    position:
      x: 0.42
      y: 0.08
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: 0.017
      w: 0.999
twist:
  twist:
    linear:
      x: 0.10
      y: 0.0
      z: 0.0
    angular:
      x: 0.0
      y: 0.0
      z: 0.02
```

这个示例表示：消息描述的是 `odom` 坐标系下的 `base_link`，机器人当前估计位置约为 `x=0.42 m、y=0.08 m`，正在以约 `0.10 m/s` 前进，并有约 `0.02 rad/s` 的角速度。静止测试时，`twist.twist.linear.x` 和 `twist.twist.angular.z` 应接近零；架空让车轮向前转动时，线速度符号应与车头方向一致；只让机器人原地转动时，`angular.z` 应变化而线速度应接近零。实际消息还可能包含 `pose.covariance` 和 `twist.covariance` 等协方差字段，数值和字段是否有效应以当前底盘驱动为准。

可用下面的命令检查雷达和车体之间的变换：

```bash
ros2 run tf2_ros tf2_echo base_link laser
```

`base_link` 和 `laser` 只是示例名称，必须替换成实际消息中的 `frame_id` 和机器人 TF 使用的坐标名。若查询失败，应先补齐 URDF、静态 TF 或底盘动态 TF，再启动 SLAM。

### 结构或传感器更换后，哪些 TF 需要更新

需要根据实际改动更新 TF，但不是所有坐标关系都会改变：

| 改动 | 通常需要检查或修改的内容 |
|---|---|
| 更换雷达型号或改变安装位置、方向 | 修改 `base_link → laser` 的平移和旋转参数；若坐标名变化，还要同步修改驱动的 `frame_id` 和 SLAM 参数 |
| 更换车体、改变雷达支架或车体参考点 | 重新确认 `base_link` 的定义，并更新各传感器相对车体的静态 TF；底盘尺寸变化时还要重新检查轮距、轮径等里程计参数 |
| 仅更换雷达驱动软件，安装位置不变 | `base_link → laser` 通常不变，但要确认新驱动发布的 `frame_id` 与原坐标名一致 |

`odom → base_link` 通常仍由底盘里程计或融合节点动态发布，`map → odom` 通常仍由 SLAM 或定位节点发布；更换硬件后不应随意让新的传感器节点接管这两段关系。修改完成后，用 `tf2_echo` 检查实际变换，并在 RViz 中确认扫描方向、位置和车体模型一致。

## 30.5 时间信息从哪里来

每条 ROS 2 消息通常在 `header.stamp` 中带有时间戳。时间戳可能来自：

1. 传感器自身的硬件时钟；
2. 驱动节点收到数据时读取的主控系统时钟；
3. 仿真环境通过 `/clock` 提供的 ROS 时间。

关键不是时间戳来自哪一个时钟，而是扫描、里程计和 TF 能够使用同一时间基准，并且时间持续向前变化。仿真时所有相关节点通常要统一设置 `use_sim_time`；多设备系统则要确认主控和设备时钟已经同步。不能把停滞的时间戳或相差很大的设备时间直接交给 SLAM。

检查时间时，可以连续观察几条消息：

```bash
ros2 topic echo /scan
ros2 topic echo /odom
```

按 `Ctrl+C` 停止。比较两类消息的 `header.stamp` 是否都在递增，是否处于同一时间范围。若使用仿真，还应检查：

```bash
ros2 topic echo --once /clock
```

## 30.6 三类输入的匹配检查

启动 SLAM 前，先把实际接口记录下来：

| 检查对象 | 对应的话题或接口 | 这项检查要确认什么 | 不通过时的处理 |
|---|---|---|---|
| 雷达扫描数据 | `/scan`（实际名称可能不同） | 驱动是否持续发布 `sensor_msgs/msg/LaserScan`，频率、角度范围、量程和 `frame_id` 是否合理 | 修改雷达驱动或 SLAM 参数；仅名称不同可以重映射 |
| 轮式里程计 | `/odom`（也可能是 `/odom_raw` 或 `/odometry/filtered`） | 是否持续发布 `nav_msgs/msg/Odometry`，速度方向、频率、`frame_id` 和 `child_frame_id` 是否正确 | 修正底盘参数、编码器方向，或选择实际有效的里程计话题 |
| 车体的动态位姿 | `/tf` 中的 `odom → base_link` | 这段变换是否由底盘里程计或 EKF 持续更新，是否只有一个发布者 | 启动底盘/融合节点，停掉重复发布同一段 TF 的节点 |
| 雷达安装关系 | `/tf_static` 中的 `base_link → laser` | 雷达相对车体的平移、旋转和坐标名是否与实物安装一致 | 修正 URDF 或静态 TF 参数，并同步驱动的 `frame_id` |
| 时间一致性 | `/scan`、里程计消息和 `/tf` 的时间戳 | 各类数据的 `header.stamp` 是否递增，并且使用同一时间基准 | 修正驱动时间源、仿真时间或设备时钟同步 |

消息名称不一致可以通过重映射解决，坐标关系缺失可以补静态或动态 TF，消息类型或数据含义不一致则需要转换/适配节点。单纯把话题改名不能修复错误的单位、时间戳或坐标方向。


## 章节导航

[上一章：传感器、驱动与话题自检](29-sensor-checks.md) · [返回本篇](index.md) · [下一章：激光雷达与二维建图](31-lidar-and-mapping.md)
