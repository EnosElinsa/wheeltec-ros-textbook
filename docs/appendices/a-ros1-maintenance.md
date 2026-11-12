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

## A.4 ROS 1 Bag 离线诊断 {#ros1-bag-offline-diagnostics}

### ROS 1 Bag 离线传感器诊断

ROS 1 Bag 保存一次运行的话题消息。离线回放可以检查数据类型、频率、时间戳、frame 和 TF；复现建图时，还需要配套消息定义、算法参数和传感器安装关系。

### 先判断格式和使用环境

ROS 1 的 `.bag` 与 ROS 2 的 rosbag2 存储格式不同。`ros2 bag play` 不能直接把旧 `.bag` 当作 ROS 2 Bag 使用。第一轮诊断应在匹配消息定义的 ROS 1 环境完成，不要先转换，也不要在同一终端加载 ROS 1 与 ROS 2。

在一台不连接实机执行器的 Linux/ROS 1 环境中创建工作副本。以下准备步骤应在稍后用于回放的终端 B 中执行，变量才能继续使用：

```bash
set -euo pipefail
BAG_SOURCE="/absolute/path/to/source.bag"
AUDIT_DIR="$(mktemp -d)"
BAG_COPY="$AUDIT_DIR/input.bag"

SOURCE_HASH="$(sha256sum "$BAG_SOURCE" | awk '{print $1}')"
test -n "$SOURCE_HASH"
printf '%s\n' "$SOURCE_HASH" > "$AUDIT_DIR/source.sha256"
cp --preserve=timestamps -- "$BAG_SOURCE" "$BAG_COPY"
COPY_HASH="$(sha256sum "$BAG_COPY" | awk '{print $1}')"
test -n "$COPY_HASH"
printf '%s\n' "$COPY_HASH" > "$AUDIT_DIR/copy.sha256"
cd "$AUDIT_DIR"
cmp source.sha256 copy.sha256
rosbag info --yaml "$BAG_COPY" > bag-info.yaml
printf 'Audit directory: %s\n' "$AUDIT_DIR"
```

把 `BAG_SOURCE` 改成实际绝对路径，保留引号以处理空格。脚本复制文件并比较哈希，任一步失败都会停止。后续诊断、`reindex` 或 `fix` 均在 `BAG_COPY` 上进行。结束后保存 `bag-info.yaml`、哈希文件和实验记录。

### 第一阶段：只读盘点

先从 `bag-info.yaml` 提取：

- Bag 版本、开始时间、结束时间和持续时间；
- 消息总数、压缩方式和分块信息；
- 每个话题的消息类型、消息数和连接数；
- 是否包含 `/clock`、`/tf`、`/tf_static`、里程计、扫描、IMU、图像、控制命令或地图；
- 是否出现自定义消息或当前环境未知的旧类型。

用消息数除以整个 Bag 持续时间可估算频率；若某话题开始较晚或提前结束，应改用该话题自身的首末记录时间。检查停顿、突发和时间回跳时，逐条比较相邻 `header.stamp`。

#### 建图所需信息检查

一个可用于二维建图诊断的 Bag 通常需要：

1. 激光扫描或点云；
2. 扫描消息中的有效时间戳和 `frame_id`；
3. 能把传感器 frame 连到机器人基座的 TF；
4. 里程计或与所选算法匹配的运动估计；
5. 一致的录制时钟。

只有扫描和 IMU 时，可以先检查频率、frame 和数值范围。若所选建图算法需要 `odom → base_link → laser`，则需补充对应的运动估计和传感器安装变换。

### 第二阶段：隔离并暂停回放

先审查完整话题清单，建立只包含诊断输入的白名单，排除 `cmd_vel`、执行器命令、服务触发和其他控制接口。使用独立 ROS master，避免白名单话题触发现有机器人节点。三个终端都设置相同的隔离地址；不要连接真实底盘或运行会订阅控制话题的节点。

终端 A：

```bash
export ROS_MASTER_URI=http://127.0.0.1:11312
roscore -p 11312
```

终端 B：

```bash
set -euo pipefail
export ROS_MASTER_URI=http://127.0.0.1:11312
: "${AUDIT_DIR:?Run the preparation block in terminal B or set AUDIT_DIR to the printed path}"
: "${BAG_COPY:?Run the preparation block in terminal B or set BAG_COPY to input.bag}"
test -r "$BAG_COPY"
rosparam set /use_sim_time true
cd "$AUDIT_DIR"

# 用 rosbag info 得到的实际输入话题替换这个示例白名单；不要加入控制话题或 /clock。
DIAG_TOPICS=(/tf /odom /scan /imu/data_raw)
rosbag play --clock --pause --rate 0.5 "$BAG_COPY" --topics "${DIAG_TOPICS[@]}"
```

如果准备步骤已在另一个终端运行，把打印的目录赋给终端 B 中的 `AUDIT_DIR`，再设置 `BAG_COPY="$AUDIT_DIR/input.bag"`。

回放以暂停状态开始。先启动观察工具，再按空格继续；再次按空格可暂停。`--clock` 根据 Bag 记录时间轴生成 `/clock`，消息自身的 `header.stamp` 则需单独检查。`/use_sim_time` 让随后启动的 ROS 节点使用模拟时间；若观察节点在设置参数前已经启动，应重启该节点。

#### 选择唯一权威时钟

上面的推荐命令适用于白名单不含 Bag 自带 `/clock` 的情况，由播放器生成唯一权威时钟。若 `rosbag info` 显示 Bag 已录制 `/clock`，必须二选一：

1. 排除录制的 `/clock`，保留播放器 `--clock`；
2. 先验证录制 `/clock` 单调且符合预期，然后移除 `--clock`，把 `/clock` 加入白名单并回放原时钟。

不能同时回放原 `/clock` 又让播放器生成 `/clock`。记录中应写清使用了哪一种时钟来源。

终端 C：

```bash
export ROS_MASTER_URI=http://127.0.0.1:11312
rostopic list
TOPIC="/replace/with/an/observed/topic"
rostopic type "$TOPIC"
rostopic info "$TOPIC"
rostopic hz "$TOPIC"
rostopic echo -n 1 "$TOPIC"
```

用当前 Bag 的 `rosbag info` 和回放后的 `rostopic list` 确定话题名。

### 第三阶段：逐层检查数据

#### 时间与频率

对每个关键话题记录：

- `header.stamp` 是否随 Bag 时间单调前进；
- 消息 frame 是否稳定；
- `rostopic hz` 的平均值、最小/最大周期和窗口长度；
- 暂停 Bag 后话题是否停止，继续后是否恢复；
- 不同传感器时间戳是否处于同一时间基准。

设置 `/use_sim_time=true` 并使用 `/clock` 时，`rostopic hz "$TOPIC"` 默认按 ROS 时间统计，通常仍接近 Bag 时间轴上的原频率。若当前 ROS 1 发行版支持，可用 `rostopic hz --wall-time "$TOPIC"` 按墙上时间统计；0.5 倍速时，墙上时间到达频率通常约为 Bag 时间频率的一半。最终报告必须注明使用的是消息时间戳、Bag 记录时间、ROS 模拟时间还是墙上时间。

#### 激光与 IMU

激光扫描检查：消息类型、角度范围、角分辨率、`scan_time`、`time_increment`、量程上下限、数组长度、可选 intensities、有限值比例及 `frame_id`。验证数组长度与角度字段是否一致。`Inf` 或 `NaN` 可能表示超量程或无回波，不应自动判定为文件损坏。普通 `LaserScan` 的每个角度通常对应一个距离；`MultiEchoLaserScan` 的每个角度可以包含多个回波，不能直接按单回波数组处理。

IMU 检查：角速度、线加速度、orientation 及三个协方差矩阵。三个 covariance 数组要分别判断：首元素为 `-1` 表示对应的 orientation、angular velocity 或 linear acceleration 未提供估计；全零矩阵表示协方差未知。接入估计器前，应确认姿态和各项协方差的实际来源及有效性。

#### TF 与里程计

先列 TF frame，再检查目标链：

```bash
rosrun tf view_frames
PARENT_FRAME="odom"
CHILD_FRAME="base_link"
ODOM_TOPIC="/replace/with/an/observed/odometry/topic"
rosrun tf tf_echo "$PARENT_FRAME" "$CHILD_FRAME"
rostopic echo -n 1 "$ODOM_TOPIC"
```

在回放推进期间运行 `view_frames`；它可能需要 Graphviz 才能生成 PDF。分别记录里程计的 `header.frame_id`、`child_frame_id`、pose/twist covariance 和 TF 中的 parent/child。Odometry 的 pose 由 `header.frame_id` 表达，twist 以 `child_frame_id` 为参考；消息中的 `child_frame_id` 与 TF 发布分别检查：前者应填写速度参考坐标系，后者按实际的 parent/child 核对。

检查 `/tf` 中的目标 frame 是否连通，并核对里程计字段。回放后的 `rostopic info /tf` 通常显示 rosbag player；追溯原始发布节点时，读取 Bag 的 connection header 与 `callerid`。出现 TF 冲突时，检查同一 child 的 parent 变化、重复变换和时间关系。

#### RViz 观察

在同一隔离 master 和模拟时间设置下启动 RViz，先选择一个实际存在且连通的 Fixed Frame，再添加 LaserScan、TF、Odometry 或 Image。若扫描不显示，先看状态栏错误、消息 frame、TF 和时间，不要先修改数据。

### 常见数据问题

| 现象 | 检查与处理 |
|---|---|
| 里程计 `child_frame_id` 为空 | 查明速度参考坐标系，同时检查 `odom → base_link` 的 TF |
| 雷达、IMU 和相机使用不同 frame，Bag 中缺少 TF | 从采集时的 URDF 或标定文件补充安装变换 |
| `orientation_covariance[0]` 为 `-1` | 姿态未提供估计；角速度和加速度分别检查 |
| covariance 全零 | 协方差未知，按传感器规格或标定结果配置 |
| 扫描类型为 `sensor_msgs/MultiEchoLaserScan` | 确认算法支持多回波，或明确选择回波的转换规则 |
| 平均频率与名义扫描周期不符 | 比较相邻时间戳，检查缺帧、录制间隙和局部抖动 |
| 压缩图像回放正常，但视觉算法无法启动 | 检查图像解码、`CameraInfo`、内参与图像时间同步 |

### 转换到 ROS 2

转换或桥接时，逐项检查：

1. 旧消息类型到 ROS 2 类型的映射，例如 `tf/tfMessage` 到 `tf2_msgs/msg/TFMessage`；
2. 自定义消息是否在两侧具有完全一致的定义；
3. frame 名称、前导斜杠和命名空间差异；
4. Bag 时间到 ROS 2 `/clock` 和 `use_sim_time` 的行为；
5. QoS 与 ROS 1 连接语义的差异；
6. 转换后消息数、时间范围、类型和关键字段是否与原 Bag 一致。

若确需生成 ROS 2 Bag，应把它作为新的派生数据保存，记录转换工具、版本、命令和原文件哈希，并重新执行本页全部诊断。原 ROS 1 Bag 继续只读保存。

### 验收记录

| 项目 | 记录内容 |
|---|---|
| 文件身份 | 工作副本路径、大小、哈希、Bag 格式 |
| 运行环境 | Ubuntu、ROS 1 发行版、消息包版本、隔离 master 地址 |
| 时间 | 开始/结束、持续时间、是否使用 `/clock`、回放倍率 |
| 连接表 | 话题、类型、消息数、连接数 |
| 数据检查 | 实测频率、时间戳、frame、数值范围、缺失字段 |
| TF/里程计 | 目标链、断点、冲突 parent/child、里程计两个 frame 字段；原始发布节点可查 connection header/callerid |
| 待解决问题 | 缺失话题、TF、标定文件或消息定义及其处理方式 |
| 转换状态 | 未转换 / 转换待验证 / 已逐项对照验证 |

## 常见故障

| 现象 | 处理 |
|---|---|
| ROS 1 节点找不到 | 检查 `ROS_MASTER_URI`、`ROS_IP`、环境和网络 |
| ROS 1/ROS 2 混用 | 新开终端，清理错误环境变量和工作空间 |
| TF1 迁移后坐标错 | 逐帧核对 parent/child、时间戳和静态变换 |
| 旧导航参数不能直接用 | 根据 Nav2 插件重新映射，先做短目标测试 |

## 相关资料

- [第五篇：ROS 2 开发](../05-ros2-development/index.md)
- [第六篇：传感器、建图与导航](../06-sensors-navigation/index.md)

## 章节导航

[返回首页](../index.md) · [下一附录：车型、主控与控制板矩阵](b-platform-matrix.md)
