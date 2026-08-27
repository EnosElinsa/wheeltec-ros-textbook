---
status: complete
---

# 17. TF、URDF 与 RViz

## 本章目标

先验证机器人坐标树，再加载模型和 RViz。能够区分“模型不好看”和“传感器坐标关系错误”，并知道修改 URDF 后怎样证明运行系统使用了新模型。

## 适用范围

适用于 ROS 2 的 TF2、URDF/Xacro 和 `robot_state_publisher`。

## 开始前检查

- 机器人静止，底盘与传感器节点已启动。
- 记录传感器实际安装方向和高度。
- 备份 URDF/Xacro、网格和模型 Launch。

## 工作原理

URDF 描述连杆和关节；`robot_state_publisher` 根据模型和关节状态发布 TF。导航通常要求 `map → odom → base_link → sensor` 链完整。RViz 只是显示客户端，红色报错反映的是上游坐标、话题或时间问题。

## 操作步骤

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo base_link <传感器坐标系>
ros2 topic echo --once /robot_description
```

在 RViz 中先把 Fixed Frame 设为当前确实存在的坐标系，再逐个添加 RobotModel、LaserScan、PointCloud2 或 Image。

修改 URDF 时先调整一个 link/joint，检查：父子关系、平移单位（米）、旋转单位（弧度）和网格路径。重新启动模型发布节点后，再用 `/robot_description` 和 TF 验证，而不是只刷新 RViz。

主控和虚拟机各自保留模型副本时，两端必须同步；否则 RViz 可能显示旧模型而主控运行新坐标。

## 结果验收

- TF 树无断裂和循环。
- `base_link` 到雷达、相机、IMU 的变换与实物方向一致。
- 静态传感器变换不随时间漂移。
- RViz Fixed Frame 明确，模型和数据落在合理位置。
- 修改后运行中的 `/robot_description` 已变化，并可恢复旧模型。

## 常见故障与处理

| 现象 | 检查 |
|---|---|
| RViz 提示 No transform | 帧名、发布节点、时间戳和 TF 链 |
| 模型散开 | joint parent/child、origin 和单位 |
| 雷达点云旋转/偏移 | 安装方向、静态变换和传感器自身坐标 |
| 改模型未生效 | 安装副本、错误工作空间或节点未重启 |

## 章节导航

[上一章：Launch、参数与运行配置](16-launch-and-parameters.md) · [返回本卷](index.md) · [下一章：修改、编译并回滚机器人源码](18-modify-build-rollback.md)
