---
status: complete
---

# 38. 视觉建图与导航的运行过程

功能包 `src/wheeltec_vision_nav`。建图使用 `vision_mapping.launch.py`，导航使用 `vision_navigation.launch.py`。不使用激光雷达。正文中的数值来自本包源码、测试，以及 2026-09-21 车上建图与导航抓取（`docs/visual-runtime-captures/`）。

---

# 过程概要

建图和导航共用从相机到视觉里程计这一段。建图把沿途观测写入磁盘数据库，并生成俯视占用栅格。导航读取已有数据库，确定车在地图中的位置，再规划路径、向底盘发送速度。视觉里程计跟丢时，发给底盘的速度置为零。默认建图不启动底盘，每次清空数据库。

相机为 D435C。它发布两路图像：左红外是单通道亮度，深度是每个像素到场景的距离。视觉里程计在红外上提取角点，再用深度把这些点变成三维。镜头前有红外投射器：打开时深度更稳定，关闭时红外图像没有散斑。驱动按帧交替开关投射器，关掉投射器的红外和打开投射器的深度时间戳不同，因此先按投射器状态配对，再写入一条同时含亮度和深度的 `rtabmap_msgs/msg/RGBDImage`，发布在 `/rtabmap/rgbd_image`。视觉里程计和建图订阅这条消息。像素处在相机光学坐标系中；感知同时发布相机相对车体的静态变换，才能把相机坐标系中的点变换到车体坐标系。

视觉里程计根据同步后的红外与深度，估计车相对本次出发的位姿。它在红外图像上找可重复检测的点，称为特征；用对应深度得到三维位置，与内存中的局部地图匹配。匹配后仍符合刚体运动的对应称为内点。内点过少时该次估计弃用，称为跟丢；磁盘上的地图仍保留。结果发布为 `/odom_vo`。节点 `vision_hold_odom_tf` 订阅 `/odom_vo` 和 `/wheel/odom`。`/wheel/odom` 在 0.3 s 内到达时，把相对出发的轮速平面位姿写入 `/odom` 和 `odom→base_footprint`。否则转发视觉位姿；跟丢时在同一图像时间戳上转发上次有效位姿或恒等变换。有底盘时另发布轮速 TF。

红外像素、里程计位姿、占用栅格处在不同坐标系中，用 TF 给出坐标系之间的平移和转动。变换顺序为 `map → odom → base_footprint`。`map` 固连环境，表示车在场地中的位置。`odom` 固连本次出发时的姿态，表示相对出发的累计位移。`base_footprint` 固连车体在地面上的投影。短时运动记在 `odom→base_footprint`，相对环境的偏差记在 `map→odom`。相机连接在 `base_footprint` 下。有底盘时，轮速坐标系也连在车体下，使 `base_footprint` 只有一个父坐标系。

建图订阅同步后的 RGB-D 和 `/odom`。车相对上一关键帧移动足够远时写入新关键帧，外观和深度存进 `.db`。回环是当前观测与较早关键帧配准成功：车回到过的地点被认出来，`map→odom` 随之更新。深度投影到地面得到俯视占用栅格，发布在 `/map`。格子标记空闲、占用或未知。`.db` 在进程退出后仍在磁盘上，定位读取该文件。`/map` 随进程结束停止发布。

定位仍运行感知和视觉里程计。建图向数据库添加地点。定位读取已有数据库，将当前观测与库中节点配准，得到车在 `/map` 中的位置，同样发布 `map→odom`。空数据库无法定位。

规划在定位之后进行。车上已有 `/map`，以及由 TF 得到的车体在地图中的位姿。Nav2 根据目标点，在栅格上计算从当前位置到目标的路径。占用格周围会扩大成高代价区域，称为代价地图。本车是阿克曼底盘，前轮转向，不能原地转向。

控制器按路径计算速度，发布 `geometry_msgs/msg/Twist`：`linear.x` 为正表示前进，为负表示倒车。导航时底盘订阅 `/cmd_vel_safe`。看门狗接在控制器与底盘之间：视觉正常时转发 `/cmd_vel`，跟丢时发布全零并取消导航。

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

![视觉建图数据流](diagrams/vision-mapping.svg)

![视觉导航数据流](diagrams/vision-navigation.svg)

---

# 1. 感知

相机发布红外图像和深度图像。视觉里程计和建图订阅同步后的红外与深度，并需要相机相对车体的静态变换。投射器按帧开关：关闭时红外图像没有散斑，打开时深度更稳定，两帧时间戳不同，因此先配对再同步。

相机为 D435C。同步后的消息发布在 `/rtabmap/rgbd_image`。静态变换为 `base_footprint→camera_d435c_link`。

## 1.1 左红外与深度

D435C 的深度相对彩色外参是全零矩阵。若做 Depth→Color 对齐，对齐后的深度为空。左红外和深度共用光学中心（外参为单位阵），因此使用左红外作为亮度、使用原始深度作为距离。接口名仍常写成 RGB-D，内容是单通道红外，不是彩色。

驱动关闭彩色、对齐深度和点云，只开启左红外和深度：`enable_color=false`，`align_depth.enable=false`，`pointcloud.enable=false`，`enable_infra1=true`，`enable_depth=true`，`enable_infra2=false`。

话题为 `/camera/infra1/image_rect_raw`、`/camera/infra1/camera_info`、`/camera/depth/image_rect_raw`、`/camera/depth/camera_info`。没有 `/camera/color/...`，也没有 `/camera/aligned_depth_to_color/...`。外参仍为零时，不要把彩色和未对齐深度作为 RGB-D 输入。

## 1.2 图像与内参

红外和深度都是 `sensor_msgs/msg/Image`。`header.stamp` 由驱动填写。红外 `header.frame_id` 为 `camera_infra1_optical_frame`，深度为 `camera_depth_optical_frame`。`height`、`width` 为像素行列。`data` 按行存放，左上角为 `(0, 0)`，长度为 `step × height`。

```yaml
# /camera/infra1/image_rect_raw 实机
header:
  frame_id: camera_infra1_optical_frame
height: 480
width: 848
encoding: "mono8"
is_bigendian: 0
step: 848
# data_len = 407040
```

红外 `encoding` 为 `mono8`，每像素 1 字节，`step` 等于宽度。深度 `encoding` 为 `16UC1`：每像素 2 字节无符号整数，单位毫米，`step` 为 1696，`data` 长度 814080。像素值 0 表示无效深度，不是距离为零。宽高与内参一致，均为 848×480。

![左红外](visual-runtime-captures/infra1_000.png)

![深度预览，有效距离按 0–4 m 映射为灰度](visual-runtime-captures/depth_000.png)

内参是 `sensor_msgs/msg/CameraInfo`。`k` 为 3×3 矩阵，行优先。红外内参实机为 `fx = fy = 421.374`，`cx = 420.745`，`cy = 239.283`。`distortion_model` 为 `plumb_bob`。驱动为红外和深度各发布一份。同步 RGB-D 时使用红外内参。

```yaml
# /camera/infra1/camera_info 实机
header:
  frame_id: camera_infra1_optical_frame
width: 848
height: 480
distortion_model: "plumb_bob"
k: [421.374, 0.0, 420.745, 0.0, 421.374, 239.283, 0.0, 0.0, 1.0]
```

| 话题 | 类型 | 发布者 |
| --- | --- | --- |
| `/camera/infra1/image_rect_raw` | `Image` | 驱动 |
| `/camera/infra1/camera_info` | `CameraInfo` | 驱动 |
| `/camera/depth/image_rect_raw` | `Image` | 驱动 |
| `/camera/depth/camera_info` | `CameraInfo` | 驱动 |
| `/camera/infra1/metadata`、`/camera/depth/metadata` | RealSense `Metadata` | 驱动 |

驱动输出已经去畸变的 `image_rect_raw`，后续节点不修改像素值。分辨率和帧率参数为 `848x480x15`。建图抓取中驱动红外约 14.5 Hz，深度约 10.2 Hz；导航抓取中红外约 14.9 Hz，深度约 11.3 Hz。保持 848×480。空间滤波 `filter_magnitude=2`，时域滤波开启。`enable_sync=true` 为驱动侧同步。`camera_name` 为 `camera`，yaml 中 `base_frame_id` 为 `d435c_link`。驱动在名称前加上 `camera_`，发布的基座坐标系为 `camera_d435c_link`。`publish_tf=true`。

图像按 Best Effort、Volatile、队列深度 10 收发。RTAB-Map 侧 `qos: 2` 同为 Best Effort。`/map` 常见为 Reliable 加 Transient Local，启动文件未修改该项。

## 1.3 投射器交错

投射器是红外点阵光源。打开时深度更稳定；关闭时红外图像没有散斑，角点检测更稳定。同一帧无法同时得到这两项，因此 `depth_module.emitter_on_off=true`，按帧交替开关。Humble 的 `rs_launch.py` 没有该启动参数。该键写在 `config/realsense_d435c.yaml`，经启动参数 `config_file` 进入相机节点。配对使用关掉投射器的红外图像和打开投射器的深度图像，时间戳不同。

16:29 连续采集左红外，相邻帧间隔 67 ms。左图拉普拉斯响应较低，右图较高。差值图为两帧灰度差并做对比度拉伸，壁面和地面上的颗粒即散斑场。

![相邻红外](visual-runtime-captures/ir_emitter_pair.png)

![相邻红外差值](visual-runtime-captures/ir_emitter_diff.png)

## 1.4 相机相对车体的变换

像素位于光学坐标系。视觉里程计给出的是车体在地面上的位姿，因此需要相机相对车体的固定变换。该变换与相机驱动一同启动。

```text
base_footprint → camera_d435c_link
向前 0.0585 m，左右 0，高度 0.028 m，转角为零
```

```yaml
header:
  frame_id: base_footprint
child_frame_id: camera_d435c_link
transform:
  translation: { x: 0.0585, y: 0.0, z: 0.028 }
  rotation: { x: 0.0, y: 0.0, z: 0.0, w: 1.0 }
```

yaml 的 `base_frame_id` 为 `d435c_link`。`camera_name` 为 `camera` 时，驱动发布的基座坐标系是 `camera_d435c_link`。光学坐标系相对它的转动由 RealSense 发布。螺丝孔中心不是光学中心，地图与真实尺寸会有偏差。

该数值写在启动辅助函数中，不使用实机 yaml 的 `base_to_camera`（旧的 `camera_link`，senior_akm 的 URDF 已占用）。其它支架 `laser`、`base_link`、`gyro_link`、`radar` 来自实机 `robot_model.yaml`，按 `car_mode` 选择；`car_mode` 为空时从 `wheeltec_param.yaml` 读取。视觉节点不订阅 `/scan`。雷达驱动和底盘默认不启动，这些静态变换仍会发布。URDF 由 `vision_robot_state_publisher` 发布。

## 1.5 红外与深度配对

交错之后，红外与深度按投射器状态重新配对。节点 `vision_emitter_pair` 缓存最近 12 帧，每收到一帧红外或深度即尝试配对。配对成功才发布。消息 stamp 使用红外时间戳；同一红外 stamp 只发布一次。新到的深度若仍配到已发布的那一帧红外，则不再发布。

| 话题 | 内容 |
| --- | --- |
| 订阅 `/camera/infra1/image_rect_raw` 与 `camera_info` | 驱动红外 |
| 订阅 `/camera/depth/image_rect_raw` 与 `camera_info` | 驱动深度 |
| 订阅 `/camera/infra1/metadata`、`/camera/depth/metadata` | 可选，读取投射器开关 |
| 发布 `/vision/paired/infra1/image_rect_raw` 与 `camera_info` | 红外原样转发 |
| 发布 `/vision/paired/depth/image_rect_raw` 与 `camera_info` | 深度像素保留，时间戳改为红外时间戳 |

metadata 的 JSON 依次尝试 `frame_emitter_mode`、`Frame Emitter Mode`、`emitter_mode`、`FRAME_EMITTER_MODE`。值为 `0` 表示关，非 `0` 表示开。与图像 stamp 相差超过 0.02 s，或四个键都读不到，则投射器状态未知。2026-09-21 建图与导航抓取的 JSON 没有这些键，配对按无 metadata 规则。键为 `frame_number`、`clock_domain`、`frame_timestamp`、`hw_timestamp`、`time_of_arrival`、`backend_timestamp`、`actual_fps`、`raw_frame_size`。建图抓取中 `actual_fps` 为 14741。

有 metadata 时：使用关掉投射器的红外，与 0.12 s 内最近的打开投射器的深度配对。无 metadata 时：跳过时间差小于 0.02 s 的帧对（同一帧、投射器状态相同），再在 0.12 s 内取最近深度。15 Hz 时相邻可用帧间隔约为 67 ms。候选红外取缓存中最新一帧关闭或未知的；若最新一帧为打开投射器，则使用更早的关闭投射器的帧。

红外 1.07 s 关、深度 1.00 s 开，可以配对。stamp 相同且无 metadata，配对失败。间隔 0.50 s，配对失败。

深度发布时时间戳改为红外时间戳，`frame_id` 仍使用深度图像的值：

```python
depth_out = Image()
depth_out.header = ir_img.header
depth_out.header.frame_id = depth_img.header.frame_id
depth_out.height = depth_img.height
depth_out.width = depth_img.width
depth_out.encoding = depth_img.encoding
depth_out.is_bigendian = depth_img.is_bigendian
depth_out.step = depth_img.step
depth_out.data = depth_img.data
```

两路 `CameraInfo` 的 stamp 同样改为红外时间戳。红外图像不修改。尚未收到对应 `CameraInfo` 时，仍可能先发布图像。配对失败则不发布。

## 1.6 RGB-D 同步

视觉里程计和建图需要同一条 `rtabmap_msgs/msg/RGBDImage` 中同时包含亮度和深度。节点 `vision_rgbd_sync`（`rtabmap_sync`）把配对后的红外和深度写入该消息，发布到 `/rtabmap/rgbd_image`。

该接口历史上连接彩色图像，名称仍为 `rgb`，此处连接红外：

| 接口 | remap |
| --- | --- |
| `rgb/image` | `/vision/paired/infra1/image_rect_raw` |
| `rgb/camera_info` | `/vision/paired/infra1/camera_info` |
| `depth/image` | `/vision/paired/depth/image_rect_raw` |
| `rgbd_image` | `/rtabmap/rgbd_image` |

没有 remap `depth/camera_info`，内参使用红外 `CameraInfo`。建图抓取中 `/rtabmap/rgbd_image` 约 9.1 Hz，导航抓取中约 6.9 Hz。`header.frame_id` 为 `camera_infra1_optical_frame`。其中 `rgb` 为红外 `mono8`，`depth` 为 `16UC1`；两条图像的 stamp 相同，深度 `frame_id` 仍为 `camera_depth_optical_frame`。配对后红外约 11.8–13.8 Hz，配对后深度约 11.6–11.7 Hz。

```yaml
# /rtabmap/rgbd_image 实机
header:
  frame_id: camera_infra1_optical_frame
rgb:
  encoding: "mono8"
  width: 848
  height: 480
  frame_id: camera_infra1_optical_frame
depth:
  encoding: "16UC1"
  width: 848
  height: 480
  frame_id: camera_depth_optical_frame
```

`approx_sync=true`，窗口 0.10 s，只允许话题到达时间差，不再检查投射器状态。

---

# 2. 运动估计

视觉里程计根据同步后的红外与深度，估计车相对本次出发的位姿，发布 `/odom_vo`。建图节点不逐帧估计这段运动。`vision_hold_odom_tf` 把轮速或视觉位姿写入 `/odom` 和 `odom→base_footprint`。

`start_base:=true` 时底盘发布 `/wheel/odom`。该话题在 0.3 s 内到达时，写入 `/odom` 的是相对出发的轮速平面位姿。否则写入视觉估计。默认建图不启动底盘，没有 `/wheel/odom`。

## 2.1 视觉里程计

节点 `vision_rgbd_odometry`（`rtabmap_odom`）订阅同步后的 RGB-D。它在当前红外图像上提取 GFTT 角点，丢弃没有有效深度的点，将剩余点反投影为三维，与内存中的局部地图匹配，估计平移和转动。

特征是图像中可重复检测的点。内点是匹配后仍符合刚体几何的对应。内点过少称为跟丢：该段运动估计弃用，磁盘上的地图仍保留。回环由建图节点完成。

策略为帧对图：当前帧与局部地图匹配。位姿估计为二维对三维（PnP）。特征类型为 GFTT / BRIEF，上限 1500。有效深度范围 0.20–4.0 m。内点少于 10 则丢弃该次估计。`Odom/ResetCountdown=0`：估计失败时不自动清空局部地图。

发布的话题：

| 话题 | 类型 | 内容 |
| --- | --- | --- |
| `/odom_vo` | `nav_msgs/msg/Odometry` | 视觉里程计的原始位姿 |
| `/odom` | `nav_msgs/msg/Odometry` | 门控后的位姿，供建图订阅 |
| `/tf` | `odom→base_footprint` | 由 `vision_hold_odom_tf` 发布 |
| `/odom_info_lite` | `rtabmap_msgs/msg/OdomInfo` | `lost`、特征数、内点数 |

`/odom` 与这段 TF 可能不同步。2026-09-21 建图与导航均 `start_base:=true`。建图抓取中 `/odom` 的 `frame_id` 为 `odom`，`child_frame_id` 为 `base_footprint`，四元数模长 1.0，`lost=false`，内点 246，特征 613。15:46 导航抓取中内点 238，特征 553。16:15 再次导航抓取中内点 363，特征 1164，`lost=false`。`/odom` 与 `/wheel/odom` 约 20 Hz。`pose.covariance[0]` 为 0.001。

`/odom_last_frame` 是视觉里程计当前帧的三维点，坐标系 `odom`。16:27 将该点云变换到 `camera_infra1_optical_frame` 后投影到左红外，红点为投影，共 900 个点。

![视觉里程计特征](visual-runtime-captures/vo_features.png)

```yaml
# nav_msgs/Odometry 结构示例
header:
  stamp: { sec: ..., nanosec: ... }
  frame_id: "odom"
child_frame_id: "base_footprint"
pose:
  pose:
    position: { x: ..., y: ..., z: ... }
    orientation: { x: 0.0, y: 0.0, z: ..., w: ... }
  covariance: [ ... ]
twist:
  twist:
    linear: { x: ..., y: 0.0, z: 0.0 }
    angular: { x: 0.0, y: 0.0, z: ... }
```

跟丢时四元数可能全零。看门狗将模长 `< 0.5` 判定为无效。`vision_hold_odom_tf` 还将 `pose.covariance[0] >= 9000` 视为无效。

```yaml
# rtabmap_msgs/OdomInfo（lite）结构示例
lost: false
features: ...
inliers: ...
matches: ...
```

启动参数：`frame_id=base_footprint`，`odom_frame_id=odom`，`publish_tf=false`，`subscribe_rgbd=true`（订阅同步后的 RGB-D，因此 `approx_sync=false`），`wait_for_transform=0.5`，`Odom/Strategy=0`（帧对图），`Odom/ResetCountdown=0`，`Vis/EstimationType=1`（二维对三维，PnP），`Odom/GuessMotion=true`，`Vis/FeatureType=6`，`Vis/MaxFeatures=1500`，`Vis/MinInliers=10`，`Vis/MinDepth=0.20`，`Vis/MaxDepth=4.0`，`Odom/FillInfoData=true`。视觉里程计发布 `/odom_vo`。缺少 `base_footprint→camera_d435c_link` 或光学坐标系时，位姿停止更新。

## 2.2 底盘启动

默认建图时 `start_base`、`use_wheel_guess` 均为 `false`，没有 `/wheel/odom`。启动参数有 `hold_odom`，默认 `false`。节点 `vision_hold_odom_tf` 在建图和导航中都会启动。

`visual_runtime_actions()` 中：`start_chassis = start_base 或 use_wheel_guess`，然后 `use_wheel_guess = start_chassis`。启动底盘时发布轮速 TF。仅设置 `use_wheel_guess:=true` 也会启动底盘。

模型侧启动 `vision_robot_state_publisher` 和 `vision_joint_state_publisher`。后者按 URDF 以零位发布轮关节，`lb_wheel_link` 等才能变换到 `map`。有底盘时再启动：`vision_wheeltec_robot`、`wheel_odom_tf`、Madgwick。`localization=true` 时启动看门狗，与底盘是否启动无关。

底盘节点读取串口 `/dev/wheeltec_controller`，波特率 115200。`car_mode=senior_akm`，阿克曼前轮转向，无法原地转向。速度指令仍为 `Twist` 的 `linear.x` 和 `angular.z`。`robot_frame_id=base_footprint`，`odom_frame_id=wheel_odom`，里程计 remap 到 `/wheel/odom`。`akm_cmd_vel=none`。`ranger_avoid_flag` 和 `ultrasonic_avoid` 为 `false`。

建图时底盘订阅 `/cmd_vel`。导航时把底盘节点的 `/cmd_vel` remap 到 `/cmd_vel_safe`。厂商 `wheeltec_robot_node` 的订阅名是 `/cmd_vel`。

## 2.3 轮速猜测

视觉里程计不设置 `guess_frame_id`。Humble 的 `rgbd_odometry` 在上一帧猜测为恒等时，会把 `lookup(wheel_odom, base_footprint)` 的累计位姿当作相邻两帧的运动，随后该猜测在配准失败时一直保留。有底盘时仍发布轮速 TF。`/wheel/odom` 进入 `vision_hold_odom_tf`：第一帧平面位姿作为 `/odom` 原点，之后发布相对该原点的 x、y、yaw，高度为 0。该话题停止超过 0.3 s 后改回视觉位姿。

```yaml
# /wheel/odom 结构示例
header:
  stamp: { sec: ..., nanosec: ... }
  frame_id: "wheel_odom"
child_frame_id: "base_footprint"
pose:
  pose:
    position: { x: ..., y: ..., z: ... }
    orientation: { x: ..., y: ..., z: ..., w: ... }
```

消息表示的变换方向是 `wheel_odom→base_footprint`。底盘把偏航角（弧度）同时写入四元数和 `pose.position.z`，该 z 不是高度。`wheel_odom_tf` 将 z 置零，只保留 x、y、yaw，并以本节点收到的第一帧为原点，再发布逆变换：父 `base_footprint`，子 `wheel_odom`。底盘节点不发布这段 TF。`lookup(wheel_odom, base_footprint)` 得到相对该原点的轮速位姿。`base_footprint` 的父坐标系仍为 `odom`。

## 2.4 IMU

底盘发布 `/imu/data_raw`，坐标系为 `gyro_link`。Madgwick 节点 `vision_imu_filter` 不使用磁力计、不发布 TF，`world_frame=enu`，`fixed_frame=odom`，输出 `/imu/data`。视觉里程计不订阅 IMU。

```yaml
# sensor_msgs/Imu 结构示例
header:
  stamp: { sec: ..., nanosec: ... }
  frame_id: "gyro_link"
orientation: { x: ..., y: ..., z: ..., w: ... }
angular_velocity: { x: ..., y: ..., z: ... }
linear_acceleration: { x: ..., y: ..., z: ... }
```

用 `ros2 topic info /imu/data` 查看是否已有 `/imu/data`。视觉里程计根据 RGB-D 发布 `/odom_vo`。`vision_hold_odom_tf` 写入 `/odom`。

---

# 3. TF

TF 给出坐标系之间的平移和转动。红外像素、`/odom`、占用栅格分别处在不同坐标系中，需要这棵树才能互相变换。

变换顺序为 `map → odom → base_footprint`。短时运动积分会累积误差，因此不把里程计直接写入 `map`：相对出发的位移在 `odom→base_footprint`，相对环境的偏差在 `map→odom`。相机连接在 `base_footprint` 下。有底盘时，轮速坐标系连接在车体下，避免 `base_footprint` 出现两个父坐标系。

![从 map 到镜头的各段坐标系](diagrams/tf-tree.svg)

16:27 车上 RViz 使用 `~/.rviz2/vision_mapping.rviz`，固定坐标系 `map`。左侧为左红外，中央为占用栅格与车体。

![RViz](visual-runtime-captures/rviz.png)

| 名称 | 固连对象 | 含义 |
| --- | --- | --- |
| `map` | 环境 | 车在环境中的位置 |
| `odom` | 本次启动或重置时的出发姿态 | 相对出发的累计位移 |
| `base_footprint` | 车身在地面上的投影 | 车体位置和朝向 |

光学坐标系 Z 轴沿镜头前方。变换发布在 `/tf`（动态）和 `/tf_static`（启动时发布一次）上。每一项包含父、子、平移、旋转、时间戳。箭头左侧为父坐标系。

| 段 | 发布者 | 话题 |
| --- | --- | --- |
| `base_footprint→camera_d435c_link` | 静态发布器 | `/tf_static` |
| `camera_d435c_link→光学坐标系` | RealSense（`publish_tf=true`） | `/tf` 或 `/tf_static` |
| `odom→base_footprint` | `vision_hold_odom_tf` | `/tf` |
| `map→odom` | `vision_hold_odom_tf`（收到 `/map` 前发恒等变换），之后为 `vision_rtabmap` | `/tf` |
| `base_footprint→wheel_odom` | `wheel_odom_tf`（有底盘时） | `/tf` |

2026-09-21 建图与导航均启动底盘。`base_footprint` 的父坐标系为 `odom`，`odom` 的父坐标系为 `map`，`wheel_odom` 的父坐标系为 `base_footprint`。四轮连杆 `lb_wheel_link`、`lf_wheel_link`、`rb_wheel_link`、`rf_wheel_link` 的父坐标系为 `base_link`。

两个节点对同一对父子同时发布 `/tf` 时，后到达的消息覆盖先到达的。

有底盘时：

```text
map → odom → base_footprint → wheel_odom
                   ↓
              camera_d435c_link → 光学坐标系
```

逆变换：旋转取共轭，平移经该逆旋转后再取负。单位四元数时 `(1, 2, 3)` 变为 `(-1, -2, -3)`。绕竖直轴 +90° yaw、沿 x 平移 1 m：

```python
invert_pose(1.0, 0.0, 0.0, 0.0, 0.0, sqrt(0.5), sqrt(0.5))
# → x≈0, y≈1, z≈0, qz≈−√2/2, qw≈√2/2
```

车在 `wheel_odom` 中沿 x 平移 1 m 并左转 90° 之后，`wheel_odom` 原点在 `base_footprint` 中位于左侧 1 m。`lookup(wheel_odom, base_footprint)` 得到正向位姿。

有底盘时视觉里程计 `publish_tf=false`，不设置 `guess_frame_id`，里程计话题 remap 为 `/odom_vo`。节点 `vision_hold_odom_tf` 订阅 `/odom_vo` 和 `/wheel/odom`。`/wheel/odom` 在 0.3 s 内到达时，把相对出发的轮速平面位姿写入 `/odom` 和 `odom→base_footprint`，高度为 0。否则把视觉位姿转发到 `/odom` 和 `odom→base_footprint`。四元数模长 ≥ 0.5 且 `pose.covariance[0] < 9000` 视为有效。无效时在同一时间戳上转发上次有效位姿；尚无有效消息时转发恒等变换。建图订阅 `/odom`，因此跟丢时仍能写入关键帧。话题 `/odom` 使用图像或轮速时间戳。TF 在同一位姿上再以当前时间发布一次，供 RViz 按当前时刻查询。视觉有效位姿若相对上一帧跳变超过 1 m 或 1 rad，视为视觉里程计复位，把新原点接到上一帧位姿上，`/odom` 不跳回出发处。尚未收到 `/map` 时，同一节点发布恒等的 `map→odom`，RViz 固定坐标系 `map` 仍能显示车体。收到 `/map` 后停止该恒等变换，`map→odom` 由 `vision_rtabmap` 发布。实机检查：`tf2_echo odom base_footprint` 应随 `/odom` 更新；`base_footprint` 的父坐标系为 `odom`。`/odom` 的发布者为一个 `vision_hold_odom_tf`。

---

# 4. 建图

建图使用同步后的 RGB-D 和 `/odom`，产生磁盘数据库 `.db`（进程退出后仍保留，定位读取该文件）、话题 `/map`（俯视占用栅格，随进程结束停止发布）、以及 TF 段 `map→odom`（回环成功时会更新）。

节点为 `vision_rtabmap`（`rtabmap_slam`）。不订阅激光。默认建图每次清空数据库，不启动 Nav2。

订阅 `/rtabmap/rgbd_image` 和 `/odom`，`frame_id=base_footprint`。`publish_tf=true`，发布 `map→odom`。图像、IMU、里程计的 QoS 为 2。

建图时 `Mem/IncrementalMemory=true`，`Mem/InitWMWithAllNodes=false`。`wipe_db` 默认 true，启动参数带 `-d`，先清空再写入。路径默认 `~/.ros/vision_rtabmap_mapping.db`（实机 `/home/wheeltec/.ros/vision_rtabmap_mapping.db`）。再次使用默认参数启动建图会再次清空数据库。要在已有库上继续，设置 `wipe_db:=false`。

相对上一关键帧约 5 cm 或 0.05 rad 才写入新关键帧（`RGBD/LinearUpdate`、`RGBD/AngularUpdate`）。配准策略为外观（`Reg/Strategy=0`）。`Reg/Force3DoF` 为 `true`，图优化同样约束在平面。`RGBD/NeighborLinkRefining` 为 `false`。扫描 ICP 会向节点数据请求激光，本包不订阅激光。回环误差超过 3 个标准差则拒绝。回环被接受时 `map→odom` 可能跳变。缺少 `odom→base_footprint` 时，回环因无法完成 `odom` 到车体的变换而被拒绝。

占用栅格为 `nav_msgs/msg/OccupancyGrid`。`data` 中每个格子：`0` 空闲，`100` 占用，`-1` 未知。按行存储，从格子 `(0, 0)` 沿 x 写完 `info.width` 再增加 y。`info.origin` 是格子 `(0, 0)` 左下角在 `map` 中的位姿。`info.resolution` 是边长（米）。图像像素 `(0, 0)` 在画面左上角，与栅格原点的约定不同。

```text
y 向上
2 |  -1    0   100    0
1 |   0    0   100    0
0 |   0    0     0    0
    +----+----+-----+----→ x
data: [0, 0, 0, 0,  0, 0, 100, 0,  -1, 0, 100, 0]
```

```yaml
# nav_msgs/OccupancyGrid 实机（2026-09-21 建图写入、导航读取同一数据库）
header:
  frame_id: "map"
info:
  resolution: 0.05
  width: 168
  height: 272
  origin:
    position: { x: -3.504, y: -5.976, z: 0.0 }
    orientation: { x: 0.0, y: 0.0, z: 0.0, w: 1.0 }
```

宽 168、高 272 对应 8.4 m × 13.6 m。分辨率 0.05 m 与 `Grid/CellSize` 一致。数据库路径 `/home/wheeltec/.ros/vision_rtabmap_mapping.db`，2026-09-21 15:46 为 176820224 字节。建图时 `Mem/IncrementalMemory=true`。

![占用栅格。白为空闲，黑为占用，灰为未知](visual-runtime-captures/nav_map_000.png)

深度投影门限：

| 键 | 值 | 含义 |
| --- | --- | --- |
| `Grid/Sensor` | `1` | 由深度投影 |
| `Grid/3D` | `false` | 二维俯视 |
| `Grid/CellSize` | `0.05` | 5 cm |
| `Grid/RangeMin` / `Max` | `0.20` / `4.0` | 使用深度的距离范围（米） |
| `Grid/MinGroundHeight` / `MaxGroundHeight` | `-0.10` / `0.10` | 地面高度 |
| `Grid/MaxObstacleHeight` | `1.80` | 超过该高度不记为障碍 |
| `Grid/RayTracing` | `true` | 相机到障碍之间标记为空闲 |
| `Grid/NoiseFilteringRadius` | `0.10` | 飞点邻域 |
| `Grid/NoiseFilteringMinNeighbors` | `5` | 邻域点数少于此则丢弃 |

`Grid/Sensor` 为 `1` 时还发布 `/cloud_obstacles`（`PointCloud2`），导航局部层订阅该话题。启动文件没有另外 remap。

一帧的处理顺序：

1. 关掉投射器的红外与邻近的打开投射器的深度，stamp 不同。
2. `emitter_pair` 配对，深度 stamp 改为红外。失败则本帧停止。
3. `rgbd_sync` 生成 `RGBDImage`。
4. 视觉里程计提取角点、用深度反投影为三维并与局部地图匹配。内点 ≥ 10 则更新 `/odom_vo`；否则跟丢。`vision_hold_odom_tf` 在 `/wheel/odom` 到达时写入轮速相对位姿，否则写入视觉位姿或上次有效位姿。
5. 相对上一关键帧约 5 cm 或 0.05 rad，写入 `.db`。
6. 像素用内参和毫米深度得到光学坐标系中的点，再经 `光学坐标系→camera_d435c_link→base_footprint→odom→map`。高度 −0.10～0.10 m 记为空闲；0.10～1.80 m 且距离 0.20～4.0 m 记为障碍。占用格 `data=100`。

启动过程不另外保存 PGM。PGM 不能替代用于地点识别的外观数据库。配对失败则本帧没有 RGB-D，不向 `/map` 写入。视觉跟丢时，若 `/odom` 仍由轮速更新，深度仍写入占用栅格。

---

# 5. 定位

定位仍使用感知与视觉里程计。建图向数据库添加节点；定位读取已有数据库，将当前观测与库中节点配准，得到车在 `/map` 中的位置。启动文件为 `vision_navigation.launch.py`，`localization=true`。

输入仍为 RGB-D 和 `/odom`。仍发布 `/map` 和 `map→odom`。此时 `/map` 是定位所参照的地图。配准失败时 `map→odom` 不可靠，规划会使用错误的栅格位置。

空数据库无法定位。若用 `vision_mapping.launch.py` 的默认参数启动，会带 `-d` 删除数据库。定位时同样由 `vision_hold_odom_tf` 发布 `odom→base_footprint`。

定位不带 `-d`，`Mem/IncrementalMemory=false`，`Mem/InitWMWithAllNodes=true`（将数据库中已有节点载入工作内存）。`database_path` 需要指向建图留下的 `.db`。2026-09-21 导航抓取中 `vision_rtabmap.database_path` 为 `/home/wheeltec/.ros/vision_rtabmap_mapping.db`，`Mem/IncrementalMemory` 为 `false`。

当前 `/rtabmap/rgbd_image` 仍输入同一个 `rtabmap` 节点。外观将当前观测与库中节点配准。配准成功后发布 `map→odom`，`map→odom→base_footprint` 即为车在已有图中的位置。

2026-09-21 数据库含 434 个节点、121 条全局回环（`Link.type=1`）。节点 98 与 330 是其中一对：红外为同一工位、不同时刻。

![回环关键帧](visual-runtime-captures/loop_pair.png)

左为节点 98，右为节点 330。两帧从 `.db` 的 `Data.image` 读出。

节点位姿画在导航抓取的 `/map` 上。蓝线为邻接，红线为全局回环，绿点为第一关键帧，橙箭头为最后关键帧。节点 98 与 330 之间为粗红线。

![关键帧轨迹](visual-runtime-captures/map_nodes.png)

16:19 导航运行中的当前红外，以及画在 `/map` 上的 `map→base_footprint`。蓝线为 `/mapPath`。橙箭头为定位位姿，约 (0.128, 0.138)，yaw 0.28 rad。

![当前红外](visual-runtime-captures/livecap_infra1_000.png)

![定位位姿](visual-runtime-captures/localization_pose.png)

可在 `/initialpose` 提供粗略初值。类型为 `PoseWithCovarianceStamped`，`frame_id` 应为 `map`。该话题 remap 到 RTAB-Map。写导航参数时会删除厂商 yaml 中的 AMCL 键。

```yaml
# /initialpose 结构示例
header:
  frame_id: "map"
pose:
  pose:
    position: { x: ..., y: ..., z: 0.0 }
    orientation: { x: 0.0, y: 0.0, z: ..., w: ... }
  covariance: [ ... ]
```

回环和近邻仍可能微调 `map→odom`。

---

# 6. 规划

定位完成之后，车上已有 `/map`，以及由 TF 得到的车体在地图中的位姿。规划根据目标点，在栅格上计算从当前位置到目标的路径。

Nav2 执行规划。本包修改厂商 yaml：删除 AMCL 和 `map_server`，使代价地图使用视觉的 `/map` 和 `/cloud_obstacles`，不再订阅激光。`autostart` 默认为 `false`，生命周期节点常处于未激活状态，此时发送目标不会执行。

Nav2 由 `nav2_bringup/navigation_launch.py` 启动，`use_composition=False`，`use_respawn=False`。`write_visual_nav_params` 读取厂商 `param_senior_akm.yaml`（默认 `wheeltec_nav2/param/wheeltec_params/param_senior_akm.yaml`，不在本仓库），修改后写入临时文件。

删除的键：`amcl`、`amcl_map_client`、`amcl_rclcpp_node`、`map_server`、`map_saver`。`/map` 不来自 `map_server`。行为树和控制器都订阅 `/odom`。NavigateToPose 默认行为树替换为 `navigate_w_replanning_ackermann.xml`。2026-09-21 导航中 `bt_navigator.default_nav_to_pose_bt_xml` 为 `/home/wheeltec/vision_ws/install/share/wheeltec_vision_nav/behavior_trees/navigate_w_replanning_ackermann.xml`。

Nav2 先生成代价地图：在占用格周围扩大高代价区域。局部代价地图随车体附近窗口移动，坐标系为 `odom`。全局代价地图覆盖整张图。实机全局 `global_frame` 为 `map`，`robot_base_frame` 为 `base_footprint`；局部 `global_frame` 为 `odom`，`rolling_window` 为 `true`。

厂商 yaml 中若缺少 `local_costmap` 或 `global_costmap` 整段，本包不创建该段。若该段存在，将 `robot_base_frame` 改为 `base_footprint`。

局部层：插件列表去掉已有的 `voxel_layer` / `obstacle_layer`。缺少 `static_layer` 则插入列表前端，缺少 `voxel_layer` 则插入 static 之后，缺少 `inflation_layer` 则追加到列表末尾。静态层订阅 `/map` 及其更新，保留未知空间。体素层仅保留深度点云 `/cloud_obstacles`，高度 0.05～1.8 m，距离 0.20～4.0 m，可清除也可标记，删除激光 `scan` / `scan2`。点云话题暂无数据时，静态层仍可使用 `/map` 中的占用栅格。实机局部插件为 `static_layer`、`voxel_layer`、`inflation_layer`，`static_layer.map_topic` 为 `/map`，膨胀半径 0.1 m。足迹为 `[[-0.09, -0.185], [-0.09, 0.185], [0.4, 0.185], [0.4, -0.185]]`，`robot_radius` 为 0.1 m。

全局层只修改已经存在的 `voxel_layer` / `obstacle_layer`：删除激光；若 `observation_sources` 中仍包含 scan，将该字段置为空字符串；若 `depth_points.topic` 仍指向 `depth/color/points`，删除 `depth_points`。缺少的层不新建。实机全局插件为 `static_layer`、`obstacle_layer`、`inflation_layer`，膨胀半径 0.25 m。

规划动作为 `ComputePathToPose`，`planner_id=GridBased`，每秒重新规划一次。输入为目标 `/goal_pose`、全局代价地图、以及由 TF 查询得到的当前车体在 `map` 中的位姿。`/goal_pose` 的 `frame_id` 必须是 `map`。输出 `nav_msgs/msg/Path`，`header.frame_id` 应为 `map`，`poses` 为位姿序列。长度为 0 表示规划失败，车辆不运动。失败时行为树先清除全局代价地图再尝试 1 次。

```yaml
# /goal_pose 结构示例
header:
  frame_id: map
pose:
  position: { x: ..., y: ..., z: 0.0 }
  orientation: { x: 0.0, y: 0.0, z: ..., w: ... }
```

`GridBased` 对应规划器插件 `nav2_smac_planner/SmacPlannerHybrid`。规划器插件列表为 `GridBased`。它在全局代价地图上规划一条路径。阿克曼无法原地转向，起点或终点位于占用格或未知格时，`Path.poses` 常为空。

16:19 从 `/global_costmap/costmap` 读取：168×272，分辨率 0.05 m，与 `/map` 同一原点。占用 15928 格，膨胀 1632 格，空闲 1722 格。橙为膨胀带，黑为占用，白为空闲，灰为未知。蓝框为足迹，橙箭头为当时 `map→base_footprint`。

![全局代价地图](visual-runtime-captures/global_costmap.png)

同一时刻向 `/goal_pose` 发送约 1.5 m 外的自由格目标，`/plan` 返回 14 个位姿后取消 `NavigateToPose`。绿线为路径，红圈为目标，蓝框为足迹。

![Nav2 路径](visual-runtime-captures/plan.png)

---

# 7. 执行

规划得到路径之后，控制器按路径计算速度，发布到 `/cmd_vel`。阿克曼无法原地转向，车头方向被障碍阻挡时通常需要倒车。

导航时把底盘节点的 `/cmd_vel` remap 到 `/cmd_vel_safe`。看门狗接在控制器与底盘之间：正常时转发到 `/cmd_vel_safe`，跟丢时发布全零并取消导航。建图不启动看门狗；建图若启动底盘，底盘直接订阅 `/cmd_vel`。

`start_base:=false` 时路径和 `/cmd_vel` 仍可能发布，底盘不会运动。发送目标后车辆完全不动且路径长度为 0，属于规划失败。有路径但倒车或绕行，是控制器依据局部代价和底盘约束计算的速度。

行为树在规划的同时执行 `FollowPath`（`controller_id=FollowPath`）。跟踪失败则清除局部代价地图再尝试 1 次。控制器订阅 `/odom`，依据局部代价地图和路径计算 `geometry_msgs/msg/Twist`，发布到 `/cmd_vel`：

```yaml
# geometry_msgs/Twist 结构示例
linear:  { x: ..., y: 0.0, z: 0.0 }   # x 正为前进，负为倒车
angular: { x: 0.0, y: 0.0, z: ... }
```

`FollowPath.vx_min`：缺失、无法解析或 ≥ 0 时改为 −0.15；厂商值已为负数则保留。实机控制器插件为 `nav2_mppi_controller::MPPIController`，插件列表为 `FollowPath`，`FollowPath.vx_min` 为 −0.5，`FollowPath.vx_max` 为 0.5。`angular.z` 由底盘节点在串口通信中处理。

16:19 从 `/local_costmap/costmap` 读取：60×60，分辨率 0.05 m，坐标系 `odom`，边长 3.0 m。占用 2327 格，空闲 1273 格。蓝框为足迹，橙箭头为车头在局部窗中的朝向。

![局部代价地图](visual-runtime-captures/local_costmap.png)

外层 `RecoveryNode` 最多再尝试 6 次。NavigateToPose 整体失败后进入 `RoundRobin`：清除局部和全局代价地图，`BackUp` 0.25 m、0.08 m/s，`Wait` 5 s。没有 `<Spin>`。恢复期间若目标更新，则跟踪新目标。`BackUp` 是行为树中的恢复动作。`vx_min` 是控制器允许的最小纵向速度。

```text
/initialpose → RTAB-Map
/goal_pose   → bt_navigator → NavigateToPose
             → ComputePathToPose → Path
             → FollowPath → /cmd_vel
             → vo_watchdog → /cmd_vel_safe
             → 底盘（start_base 时）
```

## 7.1 视觉跟丢

节点 `vision_vo_watchdog` 在 `localization=true` 时启动，与底盘是否启动无关。订阅 `/cmd_vel`，转发到 `/cmd_vel_safe`。底盘在导航时订阅后者。

```text
FollowPath → /cmd_vel → vo_watchdog → /cmd_vel_safe → 底盘
                正常：原样转发
                跟丢：全零 Twist，并取消 NavigateToPose
```

取消导航使用服务 `/navigate_to_pose/_action/cancel_goal`（`action_msgs/srv/CancelGoal`）。内点下限 10，连续 5 帧低内点才判定为跟丢。启动文件与 2026-09-21 导航中 `/vision_vo_watchdog.min_inliers` 均为 10。

状态：`ok`、`lost`、`recovering`。需要零速度的条件是 `lost` 为真或 `status==lost`。

- 四元数模长 `< 0.5`：立即进入 `lost`，立即输出零速度。
- `OdomInfo.lost` 为真：立即进入 `lost`。
- 内点 `< 10`：连续 5 帧才判定为跟丢。
- 内点数达到下限且未标记 lost：坏帧计数清零。此前若为 `lost`，则先进入 `recovering`（此时已不再输出零速度），下一次仍正常才回到 `ok`。
- 仅有有效 `/odom`、没有 `OdomInfo` 中的 lost 或内点：不能将 `lost` 清除。

定时器周期 0.05 s。需要零速度时向 `/cmd_vel_safe` 发布空 `Twist()`，并在开始输出零速度时取消导航。不需要零速度时转发最近一份 `/cmd_vel`（新的 `/cmd_vel` 到达时也会立即转发）。状态发布到 `/vision/vo_status`（`std_msgs/String`）。导航抓取中 `/vision/vo_status` 约 12.9 Hz，值为 `ok`；`/cmd_vel` 为 0 Hz，`/cmd_vel_safe` 约 20.0 Hz，速度为零。

跟丢后置零的是 `/cmd_vel_safe`。`/cmd_vel` 仍可能非零。

---

# 附录：实机查询

建图或导航运行时，另开终端：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 launch wheeltec_vision_nav capture_runtime.launch.py
```

也可在建图、导航启动里加 `capture:=true`。文件写到 `~/vision_captures/<时间>-<pid>/`：红外/深度/`/map` 的 PNG，以及 `summary.yaml`。工作空间是合并安装。部分话题只在对应启动运行之后才出现。

2026-09-21 建图会话 `20260921-153749-95034`（`start_base:=true`，`Mem/IncrementalMemory=true`），导航会话 `20260921-154642-100790`（`Mem/IncrementalMemory=false`）。车上目录 `~/vision_captures/`，仓库中的图像与 `summary.yaml` 在 `docs/visual-runtime-captures/`。红外 `mono8`、深度 `16UC1`、848×480、光学系名、内参、占用栅格 168×272、`FollowPath.vx_min`、规划器与控制器插件类已写入正文。

建图抓取频率：`/camera/infra1/image_rect_raw` 14.5 Hz，`/camera/depth/image_rect_raw` 10.2 Hz，`/vision/paired/infra1/image_rect_raw` 11.8 Hz，`/rtabmap/rgbd_image` 9.1 Hz，`/odom` 20.0 Hz，`/wheel/odom` 20.0 Hz，`/odom_info_lite` 5.7 Hz。导航抓取频率：红外 14.9 Hz，深度 11.3 Hz，配对红外 13.8 Hz，`/rtabmap/rgbd_image` 6.9 Hz，`/odom` 19.9 Hz，`/vision/vo_status` 12.9 Hz，`/cmd_vel_safe` 20.0 Hz。

### 消息类型

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

### 图像与 RGB-D

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
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field lost
ros2 topic echo --once /odom_info_lite --qos-reliability best_effort --no-arr --field inliers
```

比较配对后两路图像的 stamp。核对 `encoding` 是否为 `mono8` / `16UC1`。同步后的 `RGBDImage` 内两条图像 stamp 应相同。

### `/map`

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /map --qos-durability transient_local --field info
```

读取 `resolution`、`width`、`height`、`origin`。2026-09-21 建图与导航为 0.05 m、168×272，原点 (−3.504, −5.976)。

回环红外来自 `/home/wheeltec/.ros/vision_rtabmap_mapping.db` 的 `Data.image`。关键帧轨迹把 `Node.pose` 画到 `/map` PNG 上。2026-09-21 16:19 另从运行中的导航读取 `/global_costmap/costmap`、`/local_costmap/costmap`、`/mapPath` 与 `map→base_footprint`。16:27 采集 `/plan`（14 点）、`/odom_last_frame` 投影、相邻红外与 RViz 窗口。会话 `20260921-161514-113444`。

导航运行时还可读取：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /global_costmap/costmap --qos-durability transient_local --field info
ros2 topic echo --once /local_costmap/costmap --qos-durability transient_local --field info
ros2 topic echo --once /plan --field header
```

### TF

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo base_footprint camera_d435c_link
ros2 run tf2_ros tf2_echo base_footprint camera_infra1_optical_frame
```

有底盘时：

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 run tf2_ros tf2_echo wheel_odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint wheel_odom
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field header
ros2 topic echo --once /wheel/odom --qos-reliability best_effort --no-arr --field child_frame_id
```

`odom→base_footprint` 应随 `/odom` 更新，发布者为 `vision_hold_odom_tf`。`/vision_rgbd_odometry` 的 `publish_tf` 为 `false`。`lookup(wheel_odom, base_footprint)` 应与 `/wheel/odom` 方向一致。消息的 `header.frame_id` 为 `wheel_odom`。`base_footprint` 的父坐标系为 `odom`。

### 参数与 IMU

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 param get /vision_rgbd_odometry guess_frame_id
ros2 param get /vision_rgbd_odometry publish_tf
ros2 param get /vision_rgbd_odometry imu_topic
ros2 param get /vision_rgbd_odometry frame_id
ros2 param get /vision_rtabmap database_path
ros2 param get /vision_rtabmap Mem/IncrementalMemory
ros2 param get /vision_rtabmap Grid/Sensor
ros2 param get /camera depth_module.emitter_on_off
ros2 param get /camera base_frame_id
ros2 param dump /camera
ros2 topic info /imu/data -v
ros2 topic echo --once /imu/data --qos-reliability best_effort --no-arr --field header
```

### 导航

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /cmd_vel
ros2 topic echo --once /cmd_vel_safe
ros2 topic info /cmd_vel -v
ros2 topic info /cmd_vel_safe -v
ros2 topic echo --once /vision/vo_status
ros2 param get /controller_server FollowPath.plugin
ros2 param get /controller_server FollowPath.vx_min
ros2 param get /controller_server FollowPath.vx_max
ros2 param get /planner_server GridBased.plugin
ros2 param get /local_costmap/local_costmap plugins
ros2 param get /local_costmap/local_costmap static_layer.map_topic
ros2 param get /global_costmap/global_costmap plugins
ros2 param get /global_costmap/global_costmap global_frame
ros2 param get /bt_navigator default_nav_to_pose_bt_xml
```

跟丢时 `/cmd_vel_safe` 应为全零，`/vision/vo_status` 为 `lost`。`vx_min` 应为负数，且不大于 −0.15。2026-09-21 导航中 `vx_min` 为 −0.5。

### metadata

```bash
source /home/wheeltec/vision_ws/source_overlay.bash
ros2 topic echo --once /camera/infra1/metadata --qos-reliability best_effort
ros2 topic echo --once /camera/depth/metadata --qos-reliability best_effort
```

在 JSON 中查找投射器键，与正文四个名称对照。2026-09-21 建图与导航抓取的 JSON 含 `frame_number`、`clock_domain`、时间戳、`actual_fps`、`raw_frame_size`，没有投射器键，配对使用 0.02 / 0.12 s 规则。建图抓取中 `actual_fps` 为 14741，对应约 14.7 Hz。

## 章节导航

[上一章：视觉跟随、巡线、KCF、AR 标签与网页视频](37-vision-applications.md) · [返回本篇](index.md) · [下一章：视觉建图与导航操作](39-visual-operation.md)

