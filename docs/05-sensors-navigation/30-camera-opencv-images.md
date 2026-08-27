---
status: complete
---

# 30. 摄像头、OpenCV 与图像话题

## 本章目标

从 Linux 视频设备追踪到 ROS 2 图像话题，再用 cv_bridge/OpenCV 读取一帧，区分设备、驱动、编码和算法问题。

## 适用范围

USB RGB 相机和资料中已适配的深度相机。深度图、点云和厂商 SDK 需按型号补充。

## 开始前检查

- 相机型号和 USB 端口已记录。
- 同一相机没有被多个程序独占。
- USB 带宽和供电足够。

## 工作原理

Linux 暴露 `/dev/video*`，驱动节点把帧封装成 `sensor_msgs/msg/Image`，`camera_info` 提供内参。cv_bridge 在 ROS 图像消息与 OpenCV 矩阵之间转换；编码不匹配会导致颜色或尺寸异常。

## 操作步骤

```bash
v4l2-ctl --list-devices
v4l2-ctl --device /dev/video0 --list-formats-ext
```

启动与型号匹配的相机节点后：

```bash
ros2 topic list -t | grep -E 'image|camera_info'
ros2 topic hz <图像话题>
ros2 topic echo --once <camera_info话题>
```

用 `rqt_image_view` 或 RViz 查看图像。算法节点中明确指定输入话题与编码，输出处理图像到新话题，不覆盖原始图像。

## 结果验收

- 设备格式、分辨率和帧率有记录。
- 图像和 `camera_info` 话题持续发布。
- 颜色、方向和宽高正确。
- OpenCV 读取不会显著降低原始话题频率。

## 常见故障与处理

| 现象 | 检查 |
|---|---|
| `/dev/video` 存在但节点失败 | 设备索引、权限、格式和占用 |
| 图像发绿/颜色颠倒 | YUYV/MJPEG/RGB/BGR 编码转换 |
| 帧率低 | USB 带宽、分辨率、压缩和 CPU |
| `camera_info` 空 | 标定文件路径和相机名 |

## 章节导航

[上一章：多点导航、路径跟踪与自主探索](24-waypoints-path-exploration.md) · [返回本卷](index.md) · [下一章：相机内参与坐标标定](26-camera-calibration.md)
