---
status: complete
---
# 39. 视觉建图与导航操作

功能包 `wheeltec_vision_nav`。车上工作空间为 `/home/wheeltec/vision_ws`。建图启动 `vision_mapping.launch.py`，导航启动 `vision_navigation.launch.py`。不使用激光雷达。新开的每个终端都执行 `source /home/wheeltec/vision_ws/source_overlay.bash`。建图进程与导航进程不同时运行。

---

# 过程概要

建图把沿途观测写入磁盘数据库，并发布俯视占用栅格。导航读取已有数据库，确定车在地图中的位置，再规划路径、向底盘发送速度。视觉里程计跟丢时，发给底盘的速度置为零。

相机为 D435C。它发布左红外图像和深度图像。左红外是单通道亮度，深度是每个像素到场景的距离。镜头前有红外投射器：打开时深度更稳定，关闭时红外图像没有散斑。驱动按帧交替开关投射器。配对节点 `vision_emitter_pair` 按红外图像里的亮点比例判断每一帧投射器的开关，把关掉投射器的红外和相邻一帧打开投射器的深度配对，再写入一条同时含亮度和深度的 `rtabmap_msgs/msg/RGBDImage`，发布在 `/rtabmap/rgbd_image`。

视觉里程计订阅该消息，估计车相对本次出发的位姿，发布 `/odom_vo`。底盘启动时，输入整理节点 `vision_ekf_inputs` 扣除陀螺仪零偏、给视觉速度设方差下限，EKF 节点 `vision_ekf` 融合 `/wheel/odom`、`/vision/imu` 和 `/vision/odom_vo`，写入 `/odom` 和 `odom→base_footprint`。底盘不启动时，节点 `vision_hold_odom_tf` 转发视觉位姿，跟丢时在同一图像时间戳上转发上次有效位姿。

红外像素、里程计位姿、占用栅格处在不同坐标系中。变换顺序为 `map → odom → base_footprint`。`map` 固连环境。`odom` 固连本次出发时的姿态。`base_footprint` 固连车体在地面上的投影。短时运动记在 `odom→base_footprint`，相对环境的偏差记在 `map→odom`。相机连接在 `base_footprint` 下。有底盘时，轮速坐标系连在车体下，使 `base_footprint` 只有一个父坐标系。

建图订阅同步后的 RGB-D，并由 TF 读取 `odom→base_footprint`。车相对上一关键帧移动足够远时写入新关键帧，存进 `.db`。深度投影到地面得到占用栅格，发布在 `/map`。`.db` 在进程退出后仍在磁盘上。`/map` 随进程结束停止发布。

定位仍运行感知和视觉里程计。它读取已有数据库，将当前观测与库中节点配准，得到车在 `/map` 中的位置，并发布 `map→odom`。空数据库无法定位。

规划在定位之后进行。车上已有 `/map` 和由 TF 得到的车体位姿。Nav2 根据目标点在栅格上计算路径。占用格周围扩大成高代价区域，称为代价地图。本车是阿克曼底盘，前轮转向，不能原地转向。

控制器按路径计算速度，发布 `geometry_msgs/msg/Twist`。导航时底盘订阅 `/cmd_vel_safe`。看门狗接在控制器与底盘之间，正常时转发 `/cmd_vel`。底盘不启动时，视觉跟丢即发布全零并取消导航。底盘启动时，视觉跟丢并且轮速中断或超过 5 s 没有定位成功，才发布全零并取消导航。

抓包节点订阅红外、深度、`/map`、里程计、TF 和导航相关话题，查询部分参数，把 PNG 预览和 `summary.yaml` 写入 `/home/wheeltec/vision_captures/<日期时间>-<pid>/`。建图会话与导航会话各产生一个目录。

数据按以下顺序传递：

```text
红外图像、深度图像
        ↓ 配对、同步
   RGB-D（rtabmap_msgs/RGBDImage）
        ↓ 视觉里程计
   /odom  （相对本次出发的位姿）
        ↓ 建图或定位
   /map 、磁盘 .db 、 map→odom
        ↓ 仅导航
   目标位姿 → 路径 → 速度 → 底盘
```

---

# 工作空间

远程登录后加载覆盖安装，再启动本包节点。覆盖安装脚本同时加载本包以及底层工作空间中的 RTAB-Map、Nav2 与底盘包。

```bash
ssh wheeltec@192.168.0.100
source /home/wheeltec/vision_ws/source_overlay.bash
```

系统时钟年份为 1970 时，图像时间戳与 TF 会异常。先读取时钟：

```bash
date
```

年份为 1970 时设为当前时间（示例）：

```bash
sudo timedatectl set-time '2026-09-21 13:20:00'
date
```

已有建图或导航进程会占用相机和数据库。启动文件会先结束残留的 `realsense2_camera_node`，再等待 2 s 后打开 D435C。同一时间只运行一个建图或导航启动。在启动该次 launch 的终端按 Ctrl+C 结束之后，可以直接再次启动。仍有残留时查询并结束：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
pgrep -af 'vision_mapping|vision_navigation|realsense2_camera|rgbd_odometry|rtabmap|hold_odom_tf|ekf_node|ekf_inputs|controller_server|bt_navigator|planner_server|nav2'
pkill -f vision_mapping.launch.py
pkill -f vision_navigation.launch.py
pkill -f hold_odom_tf
```

---

# 建图

建图启动相机、配对、同步、视觉里程计和 RTAB-Map。观测写入磁盘数据库，占用栅格发布在 `/map`。`start_base:=true` 时启动底盘，`/wheel/odom` 和 `/imu/data_raw` 进入融合，写入 `/odom` 的是 EKF 融合后的运动。用手推动时编码器随轮转动。相机对准 0.5～3 m 有纹理的墙面或家具。地面、白墙、强光玻璃上特征不足，视觉里程计保持跟丢，外观关键帧变少。

`wipe_db:=true` 时启动带 `-d`，先清空数据库再写。路径为 `/home/wheeltec/.ros/vision_rtabmap_mapping.db`。导航读取同一文件。再次用 `wipe_db:=true` 启动建图会清空已有地图。在已有库上继续建图时设 `wipe_db:=false`。

启动文件不启动 RViz。抓包随 `capture:=true` 一并启动。

## 启动

新终端：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 launch wheeltec_vision_nav vision_mapping.launch.py \
  start_base:=true \
  wipe_db:=true \
  capture:=true \
  capture_dir:=/home/wheeltec/vision_captures \
  database_path:=/home/wheeltec/.ros/vision_rtabmap_mapping.db
```

日志出现 `capturing to /home/wheeltec/vision_captures/` 后，抓包已在写目录。红外与深度预览每隔 5 s 存一张，每类最多 8 张。地图随推动增大。绕场数分钟后再结束，占用栅格才有可用范围。

在已有数据库上继续：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 launch wheeltec_vision_nav vision_mapping.launch.py \
  start_base:=true \
  wipe_db:=false \
  capture:=true \
  capture_dir:=/home/wheeltec/vision_captures \
  database_path:=/home/wheeltec/.ros/vision_rtabmap_mapping.db
```

启动时未加 `capture:=true` 时，另开终端：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 launch wheeltec_vision_nav capture_runtime.launch.py \
  output_dir:=/home/wheeltec/vision_captures
```

该启动文件的参数名是 `output_dir`。建图、导航启动文件里的参数名是 `capture_dir`。

## 检查

另开终端，每条命令前加载覆盖安装：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic hz /camera/infra1/image_rect_raw
ros2 topic hz /camera/depth/image_rect_raw
ros2 topic hz /rtabmap/rgbd_image
ros2 topic echo --once /vision/emitter_pair/status
ros2 topic hz /wheel/odom
ros2 topic echo --once /vision/imu --field angular_velocity
ros2 topic echo --once /odom --qos-reliability best_effort --no-arr --field pose.pose.position
ros2 topic info /odom --verbose
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field lost
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field inliers
ros2 topic echo --once /map --qos-durability transient_local --field info
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
```

建图启动日志中 `Odom: quality=` 后的数字非长期为 0。`rtabmap` 不再连续输出 `no odometry provided. Image 0 is ignored`。`Registration failed` 且 `between -1 and` 表示外观尚未建立：面对有纹理表面，放慢推动。`/map` 的 `width`、`height` 随绕场增大。`odom→base_footprint` 随 `/odom` 更新，发布者为 `vision_ekf`，底盘不启动时为 `vision_hold_odom_tf`。`base_footprint` 的父坐标系为 `odom`。推动约 1 m 后 `/odom` 的 x 或 y 约为米级。`/vision/emitter_pair/status` 的 `paired` 约为 `ir_frames` 的一半。车静止时 `/vision/imu` 的角速度接近 0。

## 结束

在建图 launch 终端按 Ctrl+C。数据库留在 `database_path` 指定的文件中。抓包进程随 launch 退出，目录保留。

```bash
ls -lt /home/wheeltec/vision_captures
ls -l /home/wheeltec/.ros/vision_rtabmap_mapping.db
ros2 run wheeltec_vision_nav inspect_map_db /home/wheeltec/.ros/vision_rtabmap_mapping.db
```

`inspect_map_db` 输出 `result: PASS` 表示回环与里程计一致、里程计约束带有朝向方差、修正量没有大的跳变。输出 `WARN` 时，`problems` 列出不正常的项。

---

# 定位

定位启动与建图相同的感知和视觉里程计，RTAB-Map 读取已有数据库，不再向库中追加地点。`Mem/IncrementalMemory` 为 false。空文件或建图阶段一直跟丢得到的库无法定位。

导航启动文件同时启动定位、Nav2 和看门狗。底盘由 `start_base:=true` 启动，轮速发布在 `/wheel/odom`，逆变换发布为 `base_footprint→wheel_odom`。视觉里程计的 `guess_frame_id` 为 `wheel_odom`，以轮速位姿作运动预测。写入 `/odom` 的是 EKF 融合后的运动。

`autostart:=true` 时 Nav2 生命周期节点进入激活。`autostart:=false` 时节点保持未激活，发送目标不会执行。电机使能由车载控制器完成。周围留出空间。

## 启动

建图已结束。新终端：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 launch wheeltec_vision_nav vision_navigation.launch.py \
  start_base:=true \
  autostart:=true \
  capture:=true \
  capture_dir:=/home/wheeltec/vision_captures \
  database_path:=/home/wheeltec/.ros/vision_rtabmap_mapping.db
```

## 检查

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 param get /vision_rtabmap Mem/IncrementalMemory
ros2 param get /vision_rtabmap database_path
ros2 topic echo --once /map --qos-durability transient_local --field info
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint wheel_odom
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field child_frame_id
```

`Mem/IncrementalMemory` 为 false。`/map` 有非零宽高。`lookup(wheel_odom, base_footprint)` 与 `/wheel/odom` 方向一致。消息的 `header.frame_id` 为 `wheel_odom`。`base_footprint` 的父坐标系仍为 `odom`。

定位与地图偏差大时，在 RViz 用 2D Pose Estimate 发布 `/initialpose`，`frame_id` 为 `map`。该话题 remap 到 RTAB-Map。

---

# 规划

定位完成后，车上已有 `/map` 和车体在地图中的位姿。Nav2 根据目标点计算路径。局部代价地图坐标系为 `odom`，没有静态层，体素层订阅 `/vision/obstacles`，这些障碍点由配对后的深度直接生成。全局代价地图坐标系为 `map`，静态层订阅 `/map`。

规划动作为 `ComputePathToPose`，`planner_id=GridBased`。`/goal_pose` 的 `frame_id` 为 `map`。输出 `nav_msgs/msg/Path`。长度为 0 表示规划失败，车辆不运动。

RViz 的 2D Goal Pose 发布导航目标。也可用动作：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

`x`、`y` 换成当前地图中可达的空闲格。目标过近或落在占用格上时路径长度为 0。

抓包在导航节点起来之后写入 `FollowPath.vx_min`、局部层 `plugins`、行为树路径。规划器插件类、足迹、膨胀半径、其余速度上限用 dump：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
CAP=$(ls -td /home/wheeltec/vision_captures/*/ | head -1)
ros2 param get /controller_server FollowPath.vx_min
ros2 param get /local_costmap/local_costmap plugins
ros2 param get /local_costmap/local_costmap voxel_layer.depth_points.topic
ros2 param get /controller_server controller_frequency
ros2 param get /bt_navigator default_nav_to_pose_bt_xml
ros2 param dump /controller_server > "${CAP}controller_server.yaml"
ros2 param dump /planner_server > "${CAP}planner_server.yaml"
ros2 param dump /local_costmap/local_costmap > "${CAP}local_costmap.yaml"
ros2 param dump /global_costmap/global_costmap > "${CAP}global_costmap.yaml"
```

`FollowPath.vx_min` 为负数，且不大于 −0.15。局部层 `plugins` 为体素层和膨胀层。`controller_frequency` 为 10.0。行为树路径含 `navigate_w_replanning_ackermann.xml`。

---

# 执行

控制器按路径计算速度，发布到 `/cmd_vel`。看门狗订阅 `/cmd_vel`、`/odom_info_lite` 和 `/odom_vo`，底盘启动时还订阅 `/wheel/odom` 和 `/localization_pose`，向 `/cmd_vel_safe` 转发或发布全零。导航时底盘订阅 `/cmd_vel_safe`。`linear.x` 为正表示前进，为负表示倒车。阿克曼无法原地转向。

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /cmd_vel
ros2 topic echo --once /cmd_vel_safe
ros2 topic echo --once /vision/vo_status
```

发送目标后车辆完全不动且路径长度为 0，属于规划失败。有路径但倒车或绕行，是控制器依据局部代价和底盘约束计算的速度。

## 视觉跟丢

看门狗在定位启动时运行。内点下限 10，连续 5 帧低于下限判定为跟丢。四元数模长小于 0.5 或 `OdomInfo.lost` 为真时立即跟丢。底盘不启动时，跟丢即向 `/cmd_vel_safe` 发布全零，并调用 `/navigate_to_pose/_action/cancel_goal`。底盘启动时，跟丢期间轮速仍在 0.3 s 内更新、`/localization_pose` 在 5 s 内出现过，看门狗继续转发速度，状态为 `lost_wheel_backup`。其中任一条件不满足才发布全零并取消导航。`/cmd_vel` 仍可能非零。控制器超过 0.5 s 没有新速度时，看门狗也发布全零。状态发布在 `/vision/vo_status`：`ok`、`lost`、`lost_wheel_backup`、`recovering`。

用手遮住红外镜头数秒：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo /vision/vo_status
ros2 topic echo /cmd_vel_safe
```

底盘不启动时，`/vision/vo_status` 为 `lost`，`/cmd_vel_safe` 为全零。底盘启动时，遮挡期间状态为 `lost_wheel_backup`，速度照常转发，遮挡超过 5 s 且期间没有定位成功后变为 `lost`，`/cmd_vel_safe` 为全零。移开遮挡、内点恢复后状态回到 `ok` 或先经过 `recovering`。

---

# 显示

启动文件不启动 RViz。在有图形界面的会话中加载车上配置。Fixed Frame 为 `map`。显示红外、`/map`、`/odom`、`/vision/obstacles` 和 URDF。相机节点在启动后约 2 s 才打开。RTAB-Map 处理第一帧之后才发布 `map→odom`，在此之前 Map 显示为 Warn。第一张占用栅格到达后 Map 为 Ok，车模随 `/odom` 在栅格上移动。

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
rviz2 -d /home/wheeltec/.rviz2/vision_mapping.rviz
```

配置也在功能包 `config/vision_runtime.rviz`。2D Pose Estimate 发布 `/initialpose`。2D Goal Pose 发布导航目标。

---

# 抓包文件

每次抓包进程启动时新建目录 `/home/wheeltec/vision_captures/<YYYYMMDD-HHMMSS>-<pid>/`。内容包括红外与深度 PNG、占用栅格 PNG、`summary.yaml`。`summary.yaml` 还记录配对状态、EKF 的输入话题、RTAB-Map 的里程计来源，以及包括 `/tf_static` 在内的坐标系父子关系。建图目录中 `vx_min` 为 null，没有 `/cmd_vel_safe`。导航目录在 Nav2 激活后写入 `vx_min`、控制频率、代价地图插件和行为树路径，定位成功后出现 `localization_pose`。发送目标后 `summary.yaml` 中才会出现非零 `/cmd_vel`。遮挡镜头后才会出现 `vo_status: lost`。

```bash
ls -lt /home/wheeltec/vision_captures
ls -lt "$(ls -td /home/wheeltec/vision_captures/*/ | head -1)"
cat "$(ls -td /home/wheeltec/vision_captures/*/ | sed -n '1p')summary.yaml"
```

导航 launch 终端按 Ctrl+C 结束。抓包目录保留。

---

# 话题

建图或导航运行时，另开终端执行。部分话题只在对应启动运行之后才出现。

## 消息类型

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 interface show sensor_msgs/msg/Image
ros2 interface show sensor_msgs/msg/CameraInfo
ros2 interface show rtabmap_msgs/msg/RGBDImage
ros2 interface show rtabmap_msgs/msg/OdomInfo
ros2 interface show nav_msgs/msg/Odometry
ros2 interface show nav_msgs/msg/OccupancyGrid
ros2 interface show geometry_msgs/msg/Twist
ros2 interface show geometry_msgs/msg/PoseStamped
ros2 interface show sensor_msgs/msg/Imu
ros2 interface show tf2_msgs/msg/TFMessage
```

## 图像与 RGB-D

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /camera/infra1/image_rect_raw --qos-reliability best_effort --no-arr --field encoding
ros2 topic echo --once /camera/infra1/image_rect_raw --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /camera/depth/image_rect_raw --qos-reliability best_effort --no-arr --field encoding
ros2 topic echo --once /camera/depth/image_rect_raw --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /vision/paired/infra1/image_rect_raw --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /vision/paired/depth/image_rect_raw --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /rtabmap/rgbd_image --qos-reliability best_effort --no-arr
ros2 topic echo --once /odom --qos-reliability best_effort --no-arr
ros2 topic echo --once /odom_vo --qos-reliability best_effort --no-arr
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field lost
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field inliers
```

红外 `encoding` 为 `mono8`，深度为 `16UC1`。同步后的 `RGBDImage` 内两条图像 stamp 相同。

## `/map`

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /map --qos-durability transient_local --field info
```

读取 `resolution`、`width`、`height`、`origin`。

## TF

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo base_footprint camera_link
```

有底盘时：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 run tf2_ros tf2_echo wheel_odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint wheel_odom
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field child_frame_id
```

## 参数与 IMU

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 param get /vision_rgbd_odometry guess_frame_id
ros2 param get /vision_rgbd_odometry publish_tf
ros2 param get /vision_rgbd_odometry imu_topic
ros2 param get /vision_rgbd_odometry frame_id
ros2 param get /vision_rtabmap database_path
ros2 param get /vision_rtabmap Mem/IncrementalMemory
ros2 param get /vision_rtabmap odom_frame_id
ros2 param get /vision_ekf imu0
ros2 param get /vision_ekf odom1
ros2 param dump /camera
ros2 topic info /imu/data_raw -v
ros2 topic echo --once /vision/imu --field angular_velocity
```

底盘不启动时 `guess_frame_id` 为空，`start_base:=true` 时为 `wheel_odom`。`publish_tf` 为 false。`/vision_rtabmap` 的 `odom_frame_id` 为 `odom`，里程计由 TF 读取。EKF 的 `imu0` 为 `/vision/imu`，`odom1` 为 `/vision/odom_vo`。IMU 话题在 `start_base:=true` 之后出现。视觉里程计不订阅 IMU。

## metadata

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /camera/infra1/metadata --qos-reliability best_effort
ros2 topic echo --once /camera/depth/metadata --qos-reliability best_effort
```

在 JSON 中查找投射器键。实机 JSON 常见 `frame_number`、`clock_domain`、时间戳、`actual_fps`、`raw_frame_size`，没有投射器状态，配对节点因此按图像判断开关，`/vision/emitter_pair/status` 的 `source` 为 `image`。

## 章节导航

[上一章：视觉建图与导航的运行过程](38-visual-runtime.md) · [返回本篇](index.md) · [下一章：固件架构与 FreeRTOS 任务](../07-stm32-firmware/40-firmware-architecture-freertos.md)
