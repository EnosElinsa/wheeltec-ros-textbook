# Reader task test results

本轮测试使用首页、阅读路径和站内全文搜索的入口，不依赖打开原始大 Markdown。每个问题都应先进入教材章节，再按章节导航继续阅读。

| # | 读者问题 | 首入口 | 后续章节 | 原始 PDF 是否必需 |
|---:|---|---|---|---|
| 1 | 确认车型、主控、控制板和 ROS 版本 | `docs/01-bringup/01-identify-configuration.md` | `13-environment-and-source-selection.md` | 否，除非实机标签缺失 |
| 2 | 第一次上电与正常基线 | `docs/01-bringup/03-first-power-on.md` | `05-baseline-diagnosis.md` | 否 |
| 3 | 区分遥控、STM32、通信和 ROS 故障 | `docs/01-bringup/05-baseline-diagnosis.md` | `07-remote-control.md`, `32-ros2-stm32-integration.md` | 否 |
| 4 | 检查底盘、IMU、雷达和相机话题 | `docs/04-sensors-navigation/20-sensor-checks.md` | `25-camera-opencv-images.md` | 否 |
| 5 | 建图、保存地图、定位和 Nav2 | `docs/04-sensors-navigation/21-lidar-and-mapping.md` | `22-map-localization-tf.md`, `23-nav2-navigation.md` | 否 |
| 6 | 修改配置并回滚 | `docs/03-ros2-development/18-modify-build-rollback.md` | `16-launch-and-parameters.md`, `40-logs-backup-upgrade-recovery.md` | 否 |
| 7 | R680 控制板、编码器、源码和固件选择 | `docs/07-r680-platform/37-r680-hardware-wiring-oled.md` | `38-r680-debug-source-firmware.md`, `appendices/b-platform-matrix.md` | 只在硬件证据不足时需要 |
| 8 | 升级失败后的恢复顺序 | `docs/08-deployment-maintenance/40-logs-backup-upgrade-recovery.md` | `41-system-acceptance.md`, `31-build-flash-rollback.md` | 否 |

## 测试结论

八个问题都能从教材页面进入，不需要先打开原始巨型 Markdown。涉及具体硬件版本时，读者仍必须查看实机标签、随货清单和来源资料；这是安全边界，不是教材缺口。
