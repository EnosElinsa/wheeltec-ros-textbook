---
status: complete
---

# 26. TF、URDF 与 RViz

## 26.1 学习目标

先验证机器人坐标树，再加载模型和 RViz。能够区分“模型不好看”和“传感器坐标关系错误”，并知道修改 URDF 后怎样证明运行系统使用了新模型。

## 26.2 适用范围

适用于 ROS 2 的坐标变换、机器人模型和可视化工具。TF2、URDF/Xacro 与 `robot_state_publisher` 的分工在 22.4 节说明。

## 26.3 操作前检查

- 机器人静止，底盘与传感器节点已启动。
- 记录传感器实际安装方向和高度。
- 备份 URDF/Xacro、网格和模型 Launch。

## 26.4 工作原理

### 模型、坐标树与显示

Transform Library 2（TF2）记录坐标系之间的位置和朝向关系，让雷达数据、相机图像和机器人模型能落在同一空间中。统一机器人描述格式（Unified Robot Description Format, URDF）用连杆和关节描述机器人外形；XML Macros（Xacro）是生成或复用 URDF 片段的写法，适合把不同车型的公共部分集中维护。`robot_state_publisher` 根据模型和关节状态发布 TF。

RViz 是查看模型、话题和坐标关系的桌面工具，不参与底盘控制或导航计算。导航通常要求 `map → odom → base_link → sensor` 链完整。RViz 的红色报错说明上游坐标、话题或时间有问题，应先修复数据来源。

### 静态与动态变换

TF 记录坐标系之间的关系。传感器相对机身的安装位置通常不变，属于静态变换；车体相对里程计坐标会随运动更新，属于动态变换。每条动态变换都带时间戳，使用数据的节点需要在对应时刻找到完整的坐标关系。坐标系名称正确但时间范围不重叠，仍会出现变换查询失败。

## 26.5 操作步骤

### 检查坐标树

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo base_link <传感器坐标系>
ros2 topic echo --once /robot_description
```

`view_frames` 生成当前坐标树和时间统计；`tf2_echo` 持续显示两个坐标系之间的变换。先确认父子关系和时间戳，再判断数值是否符合实物安装。

### 在 RViz 中观察

在 RViz 中先把 Fixed Frame 设为当前确实存在的坐标系，再逐个添加 RobotModel、LaserScan、PointCloud2 或 Image。

### 修改模型并验证

修改 URDF 时先调整一个 link/joint，检查父子关系、平移单位（米）、旋转单位（弧度）和网格路径。重新启动模型发布节点后，用 `/robot_description` 和 TF 验证运行结果；刷新 RViz 只能更新显示，不能证明节点已加载新模型。

主控和虚拟机各自保留模型副本时，两端必须同步；否则 RViz 可能显示旧模型而主控运行新坐标。

## 26.6 验收标准

- TF 树无断裂和循环。
- `base_link` 到雷达、相机、IMU 的变换与实物方向一致。
- 静态传感器变换不随时间漂移。
- RViz Fixed Frame 明确，模型和数据落在合理位置。
- 修改后运行中的 `/robot_description` 已变化，并可恢复旧模型。

## 26.7 故障排查

先对照实物确认传感器安装，再确认模型与 TF 发布节点；接着查看模型话题，检查时间戳和整条坐标链。定位或导航仍失败时，才检查它们引用的 frame 名称。下表保留常见显示现象及其直接检查点。

| 现象 | 检查 |
|---|---|
| RViz 提示 No transform | 帧名、发布节点、时间戳和 TF 链 |
| 模型散开 | joint parent/child、origin 和单位 |
| 雷达点云旋转/偏移 | 安装方向、静态变换和传感器自身坐标 |
| 改模型未生效 | 安装副本、错误工作空间或节点未重启 |

## 章节导航

[上一章：Launch、参数与运行配置](25-launch-and-parameters.md) · [返回本篇](index.md) · [下一章：修改、编译并回滚机器人源码](27-modify-build-rollback.md)
