# WHEELTEC ROS 工程教材

这是一套围绕 WHEELTEC 轮式机器人编写的 ROS 2 工程教材。内容从 ROS 的定位和机器人系统结构讲起，依次覆盖实机接入、底盘控制、ROS 2 开发、建图导航、STM32 固件与系统维护。

**[在线阅读教材](https://enoselinsa.github.io/wheeltec-ros-textbook/)**

## 适合哪些读者

- 第一次接触机器人、Linux 或 ROS 2 的学习者；
- 已经拿到 WHEELTEC 机器人，准备完成启动、开发和故障排查的使用者；
- 需要维护 R680、STM32 底盘固件或 ROS 1 旧设备的开发者。

第 1～5 章用于建立基础概念，其中的命令都配有代表性输出。连接实机前，建议先读完这五章。

## 教材结构

| 部分 | 主要内容 |
|---|---|
| [第一篇：从零认识 ROS 机器人](https://enoselinsa.github.io/wheeltec-ros-textbook/01-foundations/) | 机器人组成、Ubuntu、终端、程序、ROS 2、节点和通信方式 |
| [第二篇：实机接入与首次启动](https://enoselinsa.github.io/wheeltec-ros-textbook/02-bringup/) | 识别配置、供电接线、首次上电、连接主控和基线检查 |
| [第三篇：底盘控制与运动学](https://enoselinsa.github.io/wheeltec-ros-textbook/03-chassis-control/) | 坐标系、遥控、`cmd_vel`、串口、CAN、里程计与 PID |
| [第四篇：ROS 2 开发](https://enoselinsa.github.io/wheeltec-ros-textbook/04-ros2-development/) | 环境、工作空间、功能包、通信、Launch、参数、TF 与进程管理 |
| [第五篇：传感器、建图与导航](https://enoselinsa.github.io/wheeltec-ros-textbook/05-sensors-navigation/) | 雷达、摄像头、SLAM、定位、Nav2、多点导航和视觉应用 |
| [第六篇：STM32 与底盘固件](https://enoselinsa.github.io/wheeltec-ros-textbook/06-stm32-firmware/) | 固件架构、FreeRTOS、车型配置、电机控制、烧录与联调 |
| [第七篇：高级应用](https://enoselinsa.github.io/wheeltec-ros-textbook/07-advanced-applications/) | Gazebo、多机器人、Qt、毫米波雷达、深度学习和语音交互 |
| [第八篇：R680 平台](https://enoselinsa.github.io/wheeltec-ros-textbook/08-r680-platform/) | R680 硬件、接线、OLED、源码分支和固件维护 |
| [第九篇：部署、备份与维护](https://enoselinsa.github.io/wheeltec-ros-textbook/09-deployment-maintenance/) | 网络、Docker、日志、备份、升级、恢复和系统验收 |

不知道从哪里开始时，可以查看[阅读路径](https://enoselinsa.github.io/wheeltec-ros-textbook/reading-paths/)；遇到术语问题，可以查[术语表](https://enoselinsa.github.io/wheeltec-ros-textbook/glossary/)。

## 本地预览

项目使用 MkDocs Material 构建。在 Windows PowerShell 中运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\tools\build_site.ps1
.\.venv\Scripts\mkdocs.exe serve
```

然后访问 `http://127.0.0.1:8000/`。提交到 `main` 分支后，GitHub Actions 会自动更新在线网站。

## 项目说明

这是非官方学习项目，不代表 WHEELTEC 官方文档。产品名称和商标归其权利人所有。

涉及供电、接线、电机运动和固件烧录时，请先核对自己的机器人型号与控制板版本。第一次运动测试应架空轮子或清空周围区域，并准备随时断电。
