---
status: complete
---

# 34. 摄像头、OpenCV 与图像话题

## 34.1 学习目标

从 Linux 视频设备追踪到 ROS 2 图像话题，再用 cv_bridge/OpenCV 读取一帧，区分设备、驱动、编码和算法问题。

## 34.2 适用范围

USB RGB 相机和常见深度相机。深度图、点云和厂商 SDK 需按型号补充。

## 34.3 操作前检查

- 相机型号和 USB 端口已记录。
- 同一相机没有被多个程序独占。
- USB 带宽和供电足够。

## 34.4 工作原理 {#camera-opencv}

相机设备先由 Linux 表示为 `/dev/video*`，相机驱动节点再把每一帧封装成 `sensor_msgs/msg/Image` 话题，`camera_info` 话题提供相机内参。Open Source Computer Vision Library（OpenCV）是处理图像的程序库，可用于颜色转换、去畸变和目标检测。cv_bridge 是 ROS 2 与 OpenCV 之间的转换包：它把图像消息变成 OpenCV 矩阵，也能把处理结果转回新话题。原始图像由驱动发布，视觉算法通过 cv_bridge 读取并输出结果；第 35 章补充内参标定，第 36 章再把检测结果接到控制逻辑。编码不匹配会导致颜色或尺寸异常。

## 34.5 操作步骤

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

## 34.6 验收标准

- 设备格式、分辨率和帧率有记录。
- 图像和 `camera_info` 话题持续发布。
- 颜色、方向和宽高正确。
- OpenCV 读取不会显著降低原始话题频率。

## 34.7 故障排查

从相机供电和 `/dev/video*` 开始，随后检查相机驱动节点、图像话题与编码。图像要与其他传感器配合时继续检查时间戳和相机坐标；基础数据正常后，才调 cv_bridge 或 OpenCV 算法参数。

| 现象 | 检查 |
|---|---|
| `/dev/video` 存在但节点失败 | 设备索引、权限、格式和占用 |
| 图像发绿/颜色颠倒 | YUYV/MJPEG/RGB/BGR 编码转换 |
| 帧率低 | USB 带宽、分辨率、压缩和 CPU |
| `camera_info` 空 | 标定文件路径和相机名 |


!!! note "代码资源边界"
    本章使用相机驱动、ROS 图像工具和 OpenCV 最小片段，不依赖源码仓库中的专用代码资源。

## 章节导航

[上一章：多点导航、路径跟踪与自主探索](33-waypoints-path-exploration.md) · [返回本篇](index.md) · [下一章：相机内参与坐标标定](35-camera-calibration.md)
