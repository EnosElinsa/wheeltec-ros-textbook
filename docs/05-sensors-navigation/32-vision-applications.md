---
status: complete
---

# 32. 视觉跟随、巡线、KCF、AR 标签与网页视频 {#kcf-code-resource}

## 32.1 学习目标

用同一条链理解五类视觉应用：图像输入、目标/特征、控制输出和安全限制。能从画面正常但机器人不动的现象定位到感知或控制环节。

## 32.2 适用范围

ROS 2 视觉跟随、巡线、KCF、AR 标签和 Web 视频节点。具体接口按相机和软件包版本核对。

## 32.3 操作前检查

- 第 30 章图像话题稳定，第 31 章在需要测量位置时已标定。
- 底盘低速控制和停止链已通过。
- 首次测试架空轮子或留出足够空间。

## 32.4 工作原理

第 30 章的相机驱动发布图像，OpenCV 与 cv_bridge 让视觉节点能够读取这些图像；第 31 章的内参让需要测量位置的算法知道镜头的几何关系。视觉节点从图像中提取颜色、线、跟踪框或标签位姿，再生成误差；控制器把误差换成 `cmd_vel`。Kernelized Correlation Filter（KCF）是一种需要人工给出初始框的目标跟踪方法。增强现实（Augmented Reality, AR）标签依赖标签尺寸和相机内参来估计姿态。Web 视频只输出画面，不应直接控制底盘；颜色跟随和巡线受光照影响明显。

## 32.5 操作步骤

1. 先运行“只感知”模式，显示检测结果但不发布速度。
2. 确认输入话题、图像编码、处理频率和目标参数。
3. 记录误差输出，检查目标在画面左右移动时符号是否正确。
4. 接入速度控制时限制最大线速度、角速度和目标丢失超时。
5. 遮挡或移走目标，确认速度立即归零。
6. 检查 `cmd_vel` 发布者，避免与导航同时控制。

## 32.6 验收标准

- 原始图像与处理结果都可观察。
- 目标位置变化与误差符号一致。
- 目标丢失、画面冻结或节点退出时底盘停止。
- 速度限制适合场地和制动距离。
- Web 视频访问失败不会影响底盘基础控制。

## 32.7 故障排查

先保证相机和底盘能安全工作，再确认驱动与视觉节点、图像和速度话题。画面与机器人运动不一致时检查时间、坐标与速度符号；基础链路无误后，再调整检测、跟踪或网页视频算法。

| 现象 | 检查 |
|---|---|
| 能看到画面但检测不到 | 颜色空间、阈值、标签尺寸、目标初始化 |
| 检测框正常但底盘不动 | 速度发布、订阅、控制优先级和使能 |
| 底盘向反方向修正 | 图像坐标到角速度的符号 |
| 目标消失后仍运动 | 丢失超时和最后命令清零逻辑 |
| Web 页面卡顿 | 编码、网络、分辨率和服务进程 |


!!! note "教材代码资源"
    本节使用 `applications/kcf-tracker/wheeltec_robot_kcf_model` 中的 `package.xml`、`launch/kcf_tracker.launch.py`、`wheeltec_robot_kcf_model/kcf_tracker_node.py` 和 `wheeltec_robot_kcf_model/pid_controller.py`。源码固定在 [ebae2342](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/ebae2342709c756cb8fa387ccdbd6e5733f9219a/applications/kcf-tracker/wheeltec_robot_kcf_model)。验收：能定位 KCF 节点入口；边界：依赖相机和初始跟踪框，未提供 YOLO 模型资产。

## 章节导航

[上一章：相机内参与坐标标定](31-camera-calibration.md) · [返回本篇](index.md) · [下一章：固件架构与 FreeRTOS 任务](../06-stm32-firmware/33-firmware-architecture-freertos.md)
