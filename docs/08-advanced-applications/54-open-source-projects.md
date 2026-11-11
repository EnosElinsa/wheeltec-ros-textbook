---
status: complete
---

# 54. 开源项目与参考价值

定位与建图项目提供运动估计和环境表示，规划控制项目生成路径与动作，多机器人和语义导航项目进一步处理协作、物体与语言目标。算法库、完整系统与仿真工具的使用条件不同，下面分别列出其方法、输入输出、实现依赖和相关论文。

R680 使用 ROS 2 Humble、Ackermann 底盘、M10P 二维雷达、D435C 红外与深度图像，以及轮速和 IMU。依赖 RGB、三维雷达、ROS 1 或原地转向的项目需要相应适配；论文中的实验平台与硬件条件也会影响方法的适用范围。

[定位与融合](#localization) · [建图与探索](#mapping) · [规划与控制](#planning) · [多机器人](#multi-robot) · [语义与语言导航](#semantic-navigation) · [仿真与评测](#evaluation)
{: .project-navigation }

<div class="project-catalog" markdown="1">

## 54.1 定位与传感器融合 {#localization}

这一类项目估计机器人位姿，主要差别在于使用的传感器、优化方式和运动约束。标定工具确定时空参数，监测工具判断参数是否仍然有效，融合与 SLAM 系统再使用这些参数估计运动；MOLA 提供可组合的模块框架。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [robot_localization](#robot_localization) | 扩展卡尔曼滤波（EKF）、无迹卡尔曼滤波（UKF） | 轮速、IMU、里程计 → 位姿与速度 |
| [VINS-Fusion](#vins-fusion) | 滑动窗口非线性优化、IMU 预积分、回环检测 | 图像、IMU → 视觉惯性里程计 |
| [PL-VIWO](#pl-viwoimu) | 点线视觉惯性轮速联合优化 | 单目图像、IMU、轮速 → 位姿 |
| [Kalibr](#kalibr-imu) | 批量时空参数标定 | 标定图像、IMU → 内外参与时间偏移 |
| [Ts Online Optimization](#temporal-calibration) | 在线时间偏移估计、滑动窗口优化 | 图像、IMU → 时间偏移与运动状态 |
| [MiscalibrationDetection](#miscalibration-detection) | 对比学习、双模态特征分类 | 图像、三维点云 → 标定状态判断 |
| [AirSLAM](#airslam) | 学习点线特征、视觉 SLAM | 双目图像 → 位姿与地图 |
| [SE2LIO](#se2lio) | 激光惯性融合、SE(2) 运动约束 | 三维点云、IMU → 里程计 |
| [MOLA](#mola) | 模块化定位与建图优化框架 | 传感器与模块配置 → 定位与地图 |

[robot_localization](https://github.com/cra-ros-pkg/robot_localization)：融合轮速、IMU 和视觉里程计，输出连续的位姿与速度估计。协方差决定各类观测对融合结果的影响，二维约束与观测变量可按车辆运动设置。它是 R680 现有融合链路的基础；多个估计器共用轮速或 IMU 时，需要考虑输入信息的相关性。
{: #robot_localization .project-description }

论文：[A Generalized Extended Kalman Filter Implementation for the Robot Operating System](https://doi.org/10.1007/978-3-319-08338-4_25)（Moore、Stouch，IAS-13）。
{: .project-paper }

[VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion)：支持双目视觉、单目加 IMU、双目加 IMU，并提供回环模块。滑动窗口优化联合使用视觉特征与 IMU 预积分约束，可用于比较纯视觉与视觉惯性估计。原版基于 ROS 1，接入 Humble 需要移植或评估 ROS 2 分支。VINS-Mono 论文介绍其方法基础，功能范围与 VINS-Fusion 实现有差别。
{: #vins-fusion .project-description }

论文：[VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator](https://doi.org/10.1109/TRO.2018.2853729)（IEEE T-RO，2018）。
{: .project-paper }

[PL-VIWO](https://github.com/Happy-zzx/PL-VIWO)：将图像点特征、线特征、IMU 和轮速共同用于运动估计。墙边、门框等线结构可补充弱纹理区域的角点，轮速提供底盘运动约束，适合走廊、遮挡和短时视觉退化研究。实现基于 ROS Noetic，轮速测量形式和运动模型需要与 Ackermann 底盘匹配。
{: #pl-viwoimu .project-description }

论文：[PL-VIWO: A Lightweight and Robust Point-Line Monocular Visual Inertial Wheel Odometry](https://doi.org/10.1109/IROS60139.2025.11246999)（IROS，2025）。
{: .project-paper }

[Kalibr](https://github.com/ethz-asl/kalibr)：提供多相机及相机与 IMU 的时空标定，输出内参、外参和时间偏移。对 D435C 与底盘 IMU 的组合，安装关系和时间误差会直接影响融合结果；标定数据需要充分激励各轴运动，仅有平面直行通常不足以约束全部参数。
{: #kalibr-imu .project-description }

论文：[Unified Temporal and Spatial Calibration for Multi-Sensor Systems](https://doi.org/10.1109/IROS.2013.6696514)（IROS，2013）。
{: .project-paper }

[Ts Online Optimization](https://github.com/bytedance/Ts_Online_Optimization)：把相机与 IMU 的时间偏移作为优化变量，利用角速度和线速度将惯性状态对齐到图像时刻，与位姿和偏置共同估计。作者在 VINS-Mono 上提供实现与人为注入时间误差的配置，适合比较时间不同步对里程计的影响。代码基于 ROS Kinetic / Melodic 和 Ceres；迁入 Humble 时需要移植接口，并确认时间戳含义与硬件同步方式。
{: #temporal-calibration .project-description }

论文：[Universal Online Temporal Calibration for Optimization-Based Visual-Inertial Navigation Systems](https://ieeexplore.ieee.org/document/11127433/)（ICRA，2025）。
{: .project-paper }

[MiscalibrationDetection](https://github.com/TUMFTM/MiscalibrationDetection)：先用对比学习编码相机和激光观测，再训练分类器判断二者是否仍处于正确标定状态。它提供训练、推理、KITTI 数据配置和 Docker 环境，可参考其低开销标定监测方式。输入依赖图像与三维点云，检测结果用于发现外参失效，重新估计外参仍需标定算法。
{: #miscalibration-detection .project-description }

论文：[Cal or No Cal? - Real-Time Miscalibration Detection of LiDAR and Camera Sensors](https://ieeexplore.ieee.org/document/11246797/)（IROS，2025）。
{: .project-paper }

[AirSLAM](https://github.com/sair-lab/AirSLAM)：使用学习得到的点线特征进行双目视觉定位，关注光照变化下的特征提取与匹配。可参考其前端匹配与推理部署方式，分析跟踪中断、漂移和计算时间。实现依赖 ROS 1、CUDA 和 TensorRT，需要配套 NVIDIA GPU。
{: #airslam .project-description }

论文：[AirSLAM: An Efficient and Illumination-Robust Point-Line Visual SLAM System](https://doi.org/10.1109/TRO.2025.3539171)（IEEE T-RO，2025）。
{: .project-paper }

[SE2LIO](https://github.com/Jiaying001/SE2LIO)：在激光惯性估计中引入 SE(2) 地面运动约束，利用车辆运动先验约束平面位置与航向。该约束在坡面和颠簸环境中的适用范围需要单独分析。实现使用多线三维雷达，不能直接替换 M10P 二维雷达定位。
{: #se2lio .project-description }

论文：[Versatile LiDAR-Inertial Odometry With SE(2) Constraints for Ground Vehicles](https://doi.org/10.1109/LRA.2023.3268584)（IEEE RA-L，2023）。
{: .project-paper }

[MOLA](https://github.com/MOLAorg/mola)：将传感器输入、状态估计与地图处理组织为可组合模块，并提供 ROS 2 桥接。可参考其模块接口搭建多种定位方案，减少更换算法时的重复适配；导航系统仍需配套里程计、地图算法和规划控制模块。
{: #mola .project-description }

论文：[A Modular Optimization Framework for Localization and Mapping](https://doi.org/10.15607/RSS.2019.XV.043)（RSS，2019）。
{: .project-paper }

## 54.2 建图与自主探索 {#mapping}

建图组织已经观测到的环境，自主探索选择下一处观测位置。动态场景中，剔除运动区域与显式估计物体运动是两种不同处理方式；多次采集的地图还涉及跨时段对齐。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [RTAB-Map](#rtab-map) | 回环检测、位姿图优化 | 图像、深度等观测 → 轨迹、点云与占据地图 |
| [slam_toolbox](#slam_toolbox) | 扫描匹配、回环检测、位姿图优化 | 二维雷达、里程计 → 地图与定位 |
| [KISS-SLAM](#kiss-slam) | 点到点 ICP、局部地图回环、位姿图优化 | 三维点云 → 全局一致轨迹与地图 |
| [Hier-SLAM](#hier-slam) | 分层语义编码、三维高斯表示 | RGB-D → 位姿、几何与语义地图 |
| [NGD-SLAM](#ngd-slam-slam) | 异步目标检测、动态区域跟踪、视觉 SLAM | 图像等观测 → 轨迹与地图 |
| [DynoSAM](#dynosam) | 动态物体关联、联合运动估计与平滑优化 | 图像、深度等观测 → 相机及物体运动 |
| [NVMS-SLAM](#nvms-slam) | 法向量几何约束、多会话优化 | 多次三维雷达轨迹 → 一致地图 |
| [m-explore-ros2](#m-explore-ros2) | 前沿提取与目标选择、地图合并 | 占据栅格 → 探索目标与合并地图 |
| [FIT-SLAM 2](#fit-slam-2) | 前沿探索、Fisher 信息、可通行性评价 | 地图与定位信息 → 探索路线与目标 |
| [ARiADNE](#ariadne) | SAC、注意力图网络、信息增益 | 局部地图与前沿图 → 下一探索航点 |

[RTAB-Map](https://github.com/introlab/rtabmap_ros)：提供视觉里程计、回环检测、地图保存和重定位。关键帧及其约束构成位姿图，回环后的图优化修正全局地图。它是 R680 视觉建图的直接参考，RGB-D 里程计支持灰度图像，可使用正确配准的红外与深度输入；局部里程计漂移和全局地图修正应分别分析。
{: #rtab-map .project-description }

论文：[RTAB-Map as an Open-Source Lidar and Visual Simultaneous Localization and Mapping Library for Large-Scale and Long-Term Online Operation](https://doi.org/10.1002/rob.21831)（Journal of Field Robotics，2019）。
{: .project-paper }

[slam_toolbox](https://github.com/SteveMacenski/slam_toolbox)：提供二维激光 SLAM、位姿图保存和定位模式，通过扫描匹配、回环与图优化改善地图一致性。输入形式与 M10P 接近，可作为视觉建图的对比方法。占据地图与位姿图保存的信息不同，后续定位或继续建图时需要选用相应结果；R680 使用 Humble 对应版本。
{: #slam_toolbox .project-description }

论文：[SLAM Toolbox: SLAM for the Dynamic World](https://doi.org/10.21105/joss.02783)（JOSS，2021）。
{: .project-paper }

[KISS-SLAM](https://github.com/PRBonn/kiss-slam)：在 KISS-ICP 激光里程计上增加局部地图、密度投影回环匹配与位姿图优化，用较少的参数构建全局一致地图。项目提供 Python 接口和命令行，论文实验对应 IROS25 标签，后续主分支仍在发展。它适合作为三维激光 SLAM 的几何基线；输入为三维点云，M10P 二维雷达需要选择其他方法，ROS 消息和地图接口也需另行衔接。
{: #kiss-slam .project-description }

论文：[KISS-SLAM: A Simple, Robust, and Accurate 3D LiDAR SLAM System With Enhanced Generalization Capabilities](https://ieeexplore.ieee.org/document/11246613/)（IROS，2025）。
{: .project-paper }

[Hier-SLAM](https://github.com/LeeBY68/Hier-SLAM)：将语义类别组织为层级树，在三维高斯表示中联合优化几何与语义信息，以紧凑编码支持较多类别。公开实现包含 RGB-D 序列处理、语义树、跟踪建图和评测，可用于比较类别表示对地图存储与语义查询的影响。代码依赖 CUDA、PyTorch 及高斯光栅化扩展；R680 的红外与深度组合需要另行验证图像表征和语义模型的适用性。
{: #hier-slam .project-description }

论文：[Hier-SLAM: Scaling-Up Semantics in SLAM with a Hierarchically Categorical Gaussian Splatting](https://ieeexplore.ieee.org/document/11127775/)（ICRA，2025）。
{: .project-paper }

[NGD-SLAM](https://github.com/YuhaoZhang7/NGD-SLAM)：结合异步目标检测与特征跟踪，将动态区域信息在相邻帧间传播，减少行人等运动物体对定位的干扰。检测和定位分开执行，可研究算力、掩码时效与跟踪稳定性的关系。检测代码使用 CPU 后端，实机示例采用彩色与深度输入，红外图像上的检测效果需要验证。
{: #ngd-slam-slam .project-description }

论文：[NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU](https://doi.org/10.1109/IROS60139.2025.11246202)（IROS，2025）。
{: .project-paper }

[DynoSAM](https://github.com/ACFR-RPG/DynOSAM)：联合估计相机与运动物体的轨迹，构建包含动态信息的地图。它保留物体运动，与 NGD-SLAM 侧重动态区域剔除的方式不同，适合比较跨帧关联、运动建模的收益与计算代价。当前代码面向 ROS 2 Kilted，并依赖学习模型预处理，迁移 Humble 需要额外工作。
{: #dynosam .project-description }

论文：[DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM](https://doi.org/10.1109/TRO.2025.3641813)（IEEE T-RO，2026）。
{: .project-paper }

[NVMS-SLAM](https://github.com/lian-yue0515/NVMS-SLAM)：利用法向量等几何信息，对不同时间采集的室内三维激光轨迹与地图进行对齐和联合优化。可用于研究重复巡检中的地图一致性。其输入依赖三维雷达，M10P 二维雷达数据不能直接替代。
{: #nvms-slam .project-description }

论文：[NVMS-SLAM: Normal Vector-Based Multi-Session LiDAR SLAM in Indoor Environments](https://doi.org/10.1109/TASE.2026.3682733)（IEEE T-ASE，2026）。
{: .project-paper }

[m-explore-ros2](https://github.com/robo-friends/m-explore-ros2)：提供基于占据栅格的前沿探索与多机器人地图合并。前沿是已知自由空间与未知区域的交界，可据此生成探索目标。R680 可复用现有地图与 Nav2，但目标必须满足车辆可达性；多机器人地图合并还需要共同坐标系，地图配准误差与协同定位精度应分别评价。
{: #m-explore-ros2 .project-description }

[FIT-SLAM 2](https://github.com/suchetanrs/FIT-SLAM)：在探索选路中同时考虑未知区域、地形可通行性和视觉定位信息。Fisher 信息用于衡量预期观测对定位的约束能力，因此选路既考虑覆盖范围，也考虑途中定位质量。项目面向 Humble，依赖三维几何与 SLAM 地标接口；用于 R680 时需要适配地图输入、Nav2 目标和车辆可达性，并替换原地旋转动作。
{: #fit-slam-2 .project-description }

论文：[FIT-SLAM 2: Efficient 3D Exploration with Fisher Information and Traversability-Based Adaptive Roadmap](https://doi.org/10.1016/j.robot.2025.105188)（Robotics and Autonomous Systems，2025）。
{: .project-paper }

[ARiADNE](https://github.com/marmotlab/ARiADNE)：在部分已知地图上建立带有前沿信息的图，用注意力网络与 SAC 学习长期覆盖效率，逐步选择下一探索航点。作者提供训练和模型，独立的 [ROS 实现](https://github.com/marmotlab/ARiADNE-ROS-Planner/tree/humble) 提供 Humble 分支，需与 SLAM 和航点跟随器配合。可用于比较学习选点与最近前沿；地图输入、传感器范围和车辆可达性仍需适配。
{: #ariadne .project-description }

论文：[ARiADNE: A Reinforcement learning approach using Attention-based Deep Networks for Exploration](https://doi.org/10.1109/icra48891.2023.10160565)（ICRA，2023）。
{: .project-paper }

## 54.3 规划与运动控制 {#planning}

规划控制方法需要同时满足避障与车辆运动约束。优化方法显式定义模型和代价，强化学习通过奖励训练策略，扩散策略与自监督表征使用另外的学习方式。

### 54.3.1 几何规划与优化控制

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [Nav2](#nav2) | Smac Hybrid-A*、MPPI、行为树 | 地图、位姿、目标 → 路径与控制指令 |
| [mpc_planner](#mpc_planner) | 拓扑候选、并行轨迹优化、模型预测控制（MPC） | 机器人与障碍状态 → 控制轨迹 |
| [pytorch_mppi](#pytorch_mppi) | 模型预测路径积分控制（MPPI） | 动力学、状态与代价 → 控制序列 |
| [Circulation-embedded CBF](#circulation-embedded-cbf) | 控制障碍函数、绕行引导 | 目标与障碍几何 → 避障控制 |
| [CVF motion planning](#cvf-motion-planning) | 曲率约束向量场 | 目标与障碍 → 车辆运动引导 |
| [accelerated-RS-planner](#accelerated-rs-planner-reedsshepp) | 加速 Reeds–Shepp 路径计算 | 起终位姿、转弯半径 → 直线圆弧路径 |

[Nav2](https://github.com/ros-navigation/navigation2)：通过插件组织全局规划、局部控制、代价地图和行为树；行为树管理重规划、等待与恢复。R680 当前使用 Smac Hybrid-A* 与 MPPI，车体轮廓、最小转弯半径和恢复动作均需符合 Ackermann 约束。插件接口可用于替换单个规划器或控制器；系统论文介绍整体架构，各插件的方法需结合其实现理解。
{: #nav2 .project-description }

论文：[The Marathon 2: A Navigation System](https://arxiv.org/abs/2003.00368)（IROS，2020）。
{: .project-paper }

[mpc_planner](https://github.com/tud-amr/mpc_planner)：在有限预测时域内优化运动，通过不同绕障方向的候选轨迹与并行求解减少局部路线限制。它适合研究动态障碍下的路线选择，以及动力学、代价和障碍约束对决策的影响。示例独轮车模型需要替换为汽车模型，求解器选择也会影响部署成本。
{: #mpc_planner .project-description }

论文：[Topology-Driven Parallel Trajectory Optimization in Dynamic Environments](https://doi.org/10.1109/TRO.2024.3475047)（IEEE T-RO，2025）。
{: .project-paper }

[pytorch_mppi](https://github.com/UM-ARM-Lab/pytorch_mppi)：用 PyTorch 采样多组控制序列，经动力学模型预测轨迹，再按代价加权更新控制。动力学、障碍代价和控制平滑项由使用者定义，便于修改车辆模型并与 Nav2 MPPI 对照。它是算法库，ROS 接口需要另行实现；下列论文为 MPPI 方法背景。
{: #pytorch_mppi .project-description }

论文：[Information Theoretic MPC for Model-Based Reinforcement Learning](https://doi.org/10.1109/ICRA.2017.7989202)（ICRA，2017；仓库采用的 MPPI 方法参考）。
{: .project-paper }

[Circulation-embedded CBF](https://github.com/sh-keyumarsi/Circulation-embedded-CBF)：将安全距离写成控制障碍函数（CBF）约束，并加入沿障碍侧面绕行的机制，缓解停在障碍前的局部死锁。可参考其约束构造、绕行方向与状态管理。原有单积分器模型和独轮车映射不直接适用于 Ackermann 底盘，安全结论需要按车辆模型重新分析。
{: #circulation-embedded-cbf .project-description }

论文：[Circulation-Embedded Control Barrier Function for Safe Navigation: A Solution to Avoid Undesired Equilibria and Dysfunctional Circulation](https://doi.org/10.1016/j.robot.2025.105132)（Robotics and Autonomous Systems，2025）。
{: .project-paper }

[CVF motion planning](https://github.com/Y1kee/CVF-for-Nonholonomic-Motion-Planning)：以向量场给出各位置的引导方向，并通过曲率约束限制方向变化，使规划考虑非完整机器人转弯能力。它将车辆约束融入引导规律，便于分析几何可达性与轨迹可跟踪性的关系。项目以 MATLAB/Simulink 为主，提供 ROS 1 Ackermann 示例。
{: #cvf-motion-planning .project-description }

论文：[Curvature-Constrained Vector Field for Motion Planning of Nonholonomic Robots](https://doi.org/10.1109/TRO.2025.3644358)（IEEE T-RO，2026）。
{: .project-paper }

[accelerated-RS-planner](https://github.com/IbrahimSquared/accelerated-RS-planner)：根据起终位姿与最小转弯半径，计算允许前进和倒车的 Reeds–Shepp 直线圆弧连接。可作为搜索规划器直接连接目标的几何模块，并分析倒车对狭窄空间可达性的影响。完整绕障规划还需要地图搜索与碰撞检测。
{: #accelerated-rs-planner-reedsshepp .project-description }

论文：[Accelerated Reeds–Shepp and Underspecified Reeds–Shepp Algorithms for Mobile Robot Path Planning](https://doi.org/10.1109/TRO.2025.3554406)（IEEE T-RO，2025）。
{: .project-paper }

### 54.3.2 深度强化学习导航 {#drl-projects}

深度强化学习（DRL）通过奖励训练策略或价值网络。下面按任务分为人群交互、未知环境与重规划、车辆驾驶三类：PPO 和 SAC 通过环境交互学习，DQN 学习离散决策，SCALE 的隐式 Q 学习使用离线轨迹。探索覆盖另见 [ARiADNE](#ariadne)，多机器人协作另见 [MAexp](#maexp)。

#### 人群交互与社会导航 {#drl-social-navigation}

这类方法主要研究行人交互、遮挡和行为不确定性。输入中的行人位置、速度或预测轨迹通常来自检测与跟踪模块，其误差会影响策略表现。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [DRL-SFM](#drl-sfm) | SAC、社会力与局部代价地图 | 局部代价地图、目标、社会信息 → 线速度与角速度 |
| [GenSafeNav](#gen-safe-nav) | PPO / PPO-Lagrangian、自适应共形推断 | 人群预测及不确定性 → 导航动作 |
| [CrowdNav++](#crowdnav-plus-plus) | PPO、循环交互图、注意力与轨迹预测 | 人群历史、预测轨迹、目标 → 导航动作 |
| [PaS](#pas-crowdnav) | VAE 遮挡推断、PPO | 局部占据栅格序列、机器人状态 → 导航动作 |
| [NaviSTAR](#navistar) | 时空图 Transformer、偏好奖励学习、SAC | 人群与机器人动态特征 → 导航动作 |
| [Stranger Danger](#stranger-danger) | SARL、行人不可预测性估计与奖励 | 人群状态、不可预测性特征 → 避障动作 |
| [Hyp2Nav](#hyp2nav) | 双曲价值网络、树搜索、内在好奇心奖励 | 人群与机器人状态 → 离散运动动作 |

[DRL-SFM](https://github.com/FAU-FAPS/DRL-SFM)：使用 Stable-Baselines3 SAC 学习社会导航，通过社会力相关观测和奖励描述人群交互。公开资源包含 HuNavSim / Gazebo 训练、预训练模型、固定路径及多环境评估，并提供输出 Twist 的 nav2_rl_controller 插件。环境基于 Ubuntu 22.04、ROS 2 Humble、PyTorch 和 CUDA，依赖特定 HuNavSim 分支。公开仓库采用 MIT 许可证，完整日志功能涉及私有分支。策略训练需要纳入 R680 的转弯半径、转向速率和低速行为，仅对输出限幅可能改变避障表现。
{: #drl-sfm .project-description }

论文：[DRL-SFM: Learning Social Navigation from Costmaps and Social Forces for Mobile Robots and Intelligent Wheelchairs](https://doi.org/10.1109/icra57385.2026.11697464)（ICRA，2026）。
{: .project-paper }

[GenSafeNav](https://github.com/tasl-lab/GenSafeNav)：用 Gumbel Social Transformer 预测人群轨迹，通过 DtACI 自适应共形推断估计不确定性，再以约束强化学习调整导航行为。训练仓库提供训练、测试、可视化脚本和预训练模型，Docker 示例基于 PyTorch 2.3.1 / CUDA 12.1。独立的 [ROS 2 实现](https://github.com/tasl-lab/GenSafeNav-ROS2) 使用 DR-SPAAM 检测与 SORT 跟踪，在 Foxy 上测试，Humble 兼容性需要验证。二维雷达的分辨率、视场和遮挡会影响检测与预测质量。训练仓库采用 MIT 许可证，部署仓库采用 GPL-3.0。
{: #gen-safe-nav .project-description }

论文：[Towards Generalizable Safety in Crowd Navigation via Conformal Uncertainty Handling](https://proceedings.mlr.press/v305/yao25a.html)（CoRL，2025）。
{: .project-paper }

[CrowdNav++](https://github.com/Shuijing725/CrowdNav_Prediction_AttnGraph)：用循环图网络区分人与人、人与机器人的交互，以注意力聚合信息，再将行人未来轨迹加入 PPO 的观测与奖励，减少机器人穿越行人预期路线的行为。作者提供训练、测试、预训练模型和独立的 TurtleBot 实机迁移示例；轨迹预测器的训练代码位于独立 GST 项目。主实现使用 PyTorch 与 Python-RVO2，车辆部署还需处理行人跟踪和 Ackermann 动作约束。
{: #crowdnav-plus-plus .project-description }

论文：[Intention Aware Robot Crowd Navigation with Attention-Based Interaction Graph](https://doi.org/10.1109/icra48891.2023.10160660)（ICRA，2023）。
{: .project-paper }

[PaS](https://github.com/yejimun/PaS_CrowdNav)：把已观测行人的避让行为作为遮挡区域的间接线索，用变分自编码器（VAE）学习局部占据表示，再以 PPO 训练避障策略。公开实现包含数据采集、VAE 预训练和策略训练测试，论文在 TurtleBot 2i 上展示了迁移。它适合研究门口、拐角与人群遮挡；原版环境基于 Python-RVO2，感知栅格和车辆运动模型需要配套适配。
{: #pas-crowdnav .project-description }

论文：[Occlusion-Aware Crowd Navigation Using People as Sensors](https://doi.org/10.1109/icra48891.2023.10160715)（ICRA，2023）。
{: .project-paper }

[NaviSTAR](https://github.com/SMARTlab-Purdue/SAN-NaviSTAR)：用时空图 Transformer 编码人群交互，通过人工偏好学习奖励，再以 SAC 优化社会导航策略。代码提供 SAC、PPO 对照入口和预训练模型，依赖 PyTorch 与 Python-RVO2。可参考其交互编码、偏好奖励与社会评价指标；公开训练环境使用抽象行人状态，接入雷达或视觉检测后仍需处理状态估计误差。
{: #navistar .project-description }

论文：[NaviSTAR: Socially Aware Robot Navigation with Hybrid Spatio-Temporal Graph Transformer and Preference Learning](https://doi.org/10.1109/iros55552.2023.10341395)（IROS，2023）。
{: .project-paper }

[Stranger Danger](https://github.com/sarapohland/stranger-danger)：在社会注意力强化学习（SARL）中加入行人不可预测性特征，并通过行人行为扰动和奖励设计，让策略对陌生行为保持更大距离。代码包含行人数据生成、不确定性网络、导航策略训练及测试，基于 Python 3.6 与 Python-RVO2。可用于研究训练中少见的突然转向或异常行走；这是对 SARL 的扩展，移植时需要同时考虑特征估计与奖励。
{: #stranger-danger .project-description }

论文：[Stranger Danger! Identifying and Avoiding Unpredictable Pedestrians in RL-based Social Robot Navigation](https://doi.org/10.1109/icra57147.2024.10610413)（ICRA，2024）。
{: .project-paper }

[Hyp2Nav](https://github.com/GDam90/hyp2nav)：在双曲空间中表示状态价值与好奇心信号，结合树搜索选择避障动作，以较小的表示维度研究人群决策。官方 PyTorch 实现提供训练、测试和不同嵌入维度的配置，依赖 Geoopt、Python-RVO2 等组件。适合比较网络表示、内在奖励和计算开销；论文主要验证仿真人群导航，离散速度动作需要转换为车辆可执行控制。
{: #hyp2nav .project-description }

论文：[Hyp2Nav: Hyperbolic Planning and Curiosity for Crowd Navigation](https://doi.org/10.1109/iros58592.2024.10801513)（IROS，2024）。
{: .project-paper }

#### 未知环境导航与重规划 {#drl-mapless-navigation}

未知环境中的远距离决策、路径更新时机和偏航恢复属于不同层次。航点策略需要局部控制器，重规划策略需要既有规划器，视觉恢复方法则依赖图像表征与历史数据。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [Context-Aware Navigation](#context-aware-navigation) | SAC、注意力图网络、图稀疏化 | 局部已知地图、目标与图节点 → 下一航点 |
| [When2Replan](#when2replan) | DQN、分层规划 | 当前观测与参考路径 → 是否重新全局规划 |
| [ScaleNav](#scalenav) | 离线隐式 Q 学习、可供性模型、RND | 当前与目标图像 → 动作与恢复行为 |

[Context-Aware Navigation](https://github.com/marmotlab/Context_Aware_Navigation)：在不断扩展的局部地图上构建图，用注意力网络汇集不同空间尺度的信息，以 SAC 学习下一航点；图稀疏化减少大范围导航的计算量。作者提供训练、测试、模型和地图，论文还包含 Gazebo 与实机验证。它面向已知目标位置的未知环境导航，可与 Nav2 局部控制配合，但仍需要从雷达、定位和地图构造一致的图表示。
{: #context-aware-navigation .project-description }

论文：[Context-Aware Deep Reinforcement Learning for Autonomous Robotic Navigation in Unknown Area](https://proceedings.mlr.press/v229/liang23a.html)（CoRL，2023）。
{: .project-paper }

[When2Replan](https://github.com/omron-sinicx/when2replan)：用深度 Q 网络（DQN）决定是否重新调用全局规划器，在环境变化时权衡保留路径与更新路径。作者提供二维仿真、训练、评估和预训练模型，示例组合 Dijkstra 与 DWA；项目使用 Stable-Baselines3。它适合参考 Nav2 行为树中的重规划触发逻辑，策略本身不生成底盘速度，学习结果与所配套的规划器和场景有关。
{: #when2replan .project-description }

论文：[When to Replan? An Adaptive Replanning Strategy for Autonomous Navigation using Deep Reinforcement Learning](https://doi.org/10.1109/icra57147.2024.10611474)（ICRA，2024）。
{: .project-paper }

[ScaleNav](https://github.com/KubeEdge4Robotics/ScaleNav)：是作者对 SCALE 的重新实现，结合视觉编码、离线 Implicit Q-Learning（IQL）、可供性模型和 RND 新颖度估计，在偏离已知可行路线后选择自纠正动作。此处 IQL 指隐式 Q 学习，与多智能体中的 Independent Q-Learning 含义不同。恢复成功率与误触发都影响导航质量。实现基于 ROS 1 和彩色相机，数据、模型路径需要配置，旋转动作需要按车辆约束适配。
{: #scalenav .project-description }

论文：[SCALE: Self-Correcting Visual Navigation for Mobile Robots via Anti-Novelty Estimation](https://doi.org/10.1109/ICRA57147.2024.10610847)（ICRA，2024）。
{: .project-paper }

<span id="scale-drl"></span>

#### 车辆驾驶与控制 {#drl-driving-control}

车辆项目更直接涉及转向、速度、摩擦和执行延迟。高速赛车与 R680 的低速导航任务不同，但残差控制、数据利用和仿真到实机迁移方法仍可借鉴。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [Wheeled Lab](#wheeled-lab) | PPO、域随机化、并行仿真 | 车辆状态或视觉观测 → 车辆控制 |
| [FastRLAP](#fastrlap) | RLPD、视觉预训练、自主练习与恢复 | 相机图像、车辆状态与检查点 → 驾驶动作 |
| [RLPP](#rlpp) | SAC 残差策略、Pure Pursuit | 轨迹相对状态、参考轨迹 → 转向与加速度修正 |

[Wheeled Lab](https://github.com/UWRobotLearning/WheeledLab)：提供轮式平台资产、环境与训练代码，使用 RSL-RL 的 PPO，任务覆盖漂移、地形运动和视觉驾驶；视觉任务包含教师与学生学习。车辆模型、摩擦、延迟、执行器随机化可用于研究仿真到实机迁移。训练入口为 source/wheeledlab_rl/scripts/train_rl.py，环境推荐 Isaac Sim 4.5.0、Isaac Lab 2.0.2 和 Python 3.10，需要合适的 NVIDIA GPU。代码采用 BSD-3-Clause 许可证；独立的 [RealLab](https://github.com/UWRobotLearning/RealLab) 提供 HOUND / MuSHR 分支，F1TENTH 集成仍列为待提供。接入 R680 需要替换车辆参数与控制器，漂移表现不能直接代表低速室内导航能力。
{: #wheeled-lab .project-description }

论文：[Wheeled Lab: Modern Sim2Real for Low-cost, Open-source Wheeled Robotics](https://proceedings.mlr.press/v305/han25a.html)（CoRL，2025）。
{: .project-paper }

[FastRLAP](https://github.com/kylestach/fastrlap-release)：先用已有机器人数据初始化视觉表示，再将少量演示数据与在线经验用于 RLPD 强化学习，通过沿检查点自主练习和失败后重置，在真实遥控小车上学习驾驶。作者发布 ROS 实现、Gazebo 环境、MuJoCo 越野环境和 JAX 强化学习代码。可参考视觉表征复用、数据混合与自动恢复；实机练习依赖定位、路线检查点和可执行的恢复行为，RGB 输入也需匹配车辆相机。
{: #fastrlap .project-description }

论文：[FastRLAP: A System for Learning High-Speed Driving via Deep RL and Autonomous Practicing](https://proceedings.mlr.press/v229/stachowicz23a.html)（CoRL，2023）。
{: .project-paper }

[RLPP](https://github.com/ForzaETH/f1tenth_gym/tree/paper/rlpp)：保留 Pure Pursuit 的参考控制，以 SAC 学习转向和加速度残差，在 F1TENTH 平台研究从仿真直接部署到实机的赛车控制。原 RLPP 仓库已弃用，作者将实现迁至 F1TENTH Gym 的 paper/rlpp 分支，提供测试入口与预训练模型，专门的训练说明仍未补齐。它适合参考 Ackermann 底盘的控制器与残差策略组合，轮胎模型、转向延迟和速度范围需要按 R680 调整。
{: #rlpp .project-description }

论文：[RLPP: A Residual Method for Zero-Shot Real-World Autonomous Racing on Scaled Platforms](https://doi.org/10.1109/icra55743.2025.11127278)（ICRA，2025）。
{: .project-paper }

### 54.3.3 其他学习方法 {#other-learning-projects}

模型驱动学习、扩散策略和自监督表征不宜统一称为强化学习。下面三个项目分别处理控制优化、局部轨迹生成和地形表征。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [NeuPAN](#neupan) | 模型驱动学习、近端交替优化、MPC | 障碍点、车体几何、参考路径 → 控制序列 |
| [NavDP](#navdp) | 特权信息指导的扩散策略学习 | RGB-D、目标条件 → 局部轨迹 |
| [STERLING](#sterling) | 多模态自监督地形表征学习 | 地形视觉、机器人交互经验 → 地形表征与偏好 |

[NeuPAN](https://github.com/hanruihua/NeuPAN)：结合学习模块与优化模型进行导航，属于模型驱动学习。IR-SIM 示例覆盖差速、Ackermann 和全向底盘，可用于分析车辆轮廓、转弯半径与障碍间距。训练 DUNE 模型需要匹配车体几何，CVXPY 求解部分的 CPU 频率和延迟也会影响控制。代码采用 GPL-3.0 许可证。
{: #neupan .project-description }

论文：[NeuPAN: Direct Point Robot Navigation With End-to-End Model-Based Learning](https://doi.org/10.1109/tro.2025.3554252)（IEEE Transactions on Robotics，2025）。
{: .project-paper }

[NavDP](https://github.com/InternRobotics/NavDP)：利用特权信息指导扩散导航策略学习，公开仿真数据、策略训练与模型检查点。当前仓库包含后续工作，论文实验需要对应的配置和权重。R680 的红外与深度输入、RGB 可用性和相机安装位姿需要与模型观测要求匹配；许可证条款需进一步确认。
{: #navdp .project-description }

论文：[NavDP: Learning Sim-to-Real Navigation Diffusion Policy with Privileged Information Guidance](https://doi.org/10.1109/icra57385.2026.11696748)（ICRA，2026）。
{: .project-paper }

[STERLING](https://github.com/HareshKarnan/sterling_corl23)：从地形视觉、振动等交互经验学习地形表征，可用于研究视觉与地面颠簸、可通行偏好之间的联系。公开范围主要是表征训练脚本，ROS 预处理仍列为待提供，不能视为完整导航实现。RGB 输入要求与许可证条款需要进一步确认。
{: #sterling .project-description }

论文：[STERLING: Self-Supervised Terrain Representation Learning from Unconstrained Robot Experience](https://proceedings.mlr.press/v229/karnan23a.html)（CoRL，2023）。
{: .project-paper }

## 54.4 多机器人定位与协作 {#multi-robot}

协同定位解决不同机器人轨迹与地图的一致性，协作策略学习解决多台机器人怎样共同完成任务。两类方法对观测、通信和运动模型的要求不同。

### 54.4.1 协同定位、建图与通信

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [Swarm-SLAM](#swarm-slam-slam) | 跨机器人回环、分散协同 SLAM | 各机观测与摘要 → 协同地图 |
| [iMESA](#imesa) | 增量分布式图优化 | 各机测量约束 → 分布式估计 |
| [riMESA](#rimesa) | 鲁棒增量共识 ADMM | 分布式位姿图 → 一致估计 |
| [SlideSLAM](#slideslam) | 稀疏语义地标、跨机器人关联 | 感知与语义地标 → 协同地图 |
| [LAMP](#lamp) | 多传感器融合、回环、协同图优化 | 多机器人传感器 → 大规模地图 |
| [Kimera-Multi](#kimera-multi) | 分布式几何与语义建图 | 各机视觉惯性观测 → 稠密语义地图 |
| [ReALM](#realm) | 视线连通约束、图代数连通性、势函数控制 | 激光扫描、团队状态 → 保持连通的导航动作 |

[Swarm-SLAM](https://github.com/mistlab/Swarm-SLAM)：通过跨机器人回环与通信预算分配，将各自轨迹连接到共同参考系，是 ROS 2 协同 SLAM 的系统参考。它支持研究信息交换的内容、时机与带宽限制对地图精度的影响。用于 R680 时，需要选择匹配的视觉输入，并评价学习描述子在红外图像上的效果。
{: #swarm-slam-slam .project-description }

论文：[Swarm-SLAM: Sparse Decentralized Collaborative Simultaneous Localization and Mapping Framework for Multi-Robot Systems](https://doi.org/10.1109/LRA.2023.3333742)（IEEE RA-L，2024）。
{: .project-paper }

[iMESA](https://github.com/rpl-cmu/imesa)：是 riMESA 的前序方法，处理协同 SLAM 中随新观测持续到来的分布式优化。各机器人保留本地估计，通过共享信息改善共同变量的一致性，可作为分析增量更新与异常约束处理的后端对照。
{: #imesa .project-description }

论文：[iMESA: Incremental Distributed Optimization for Collaborative Simultaneous Localization and Mapping](https://doi.org/10.15607/RSS.2024.XX.085)（RSS，2024）。
{: .project-paper }

[riMESA](https://github.com/rpl-cmu/riMESA)：为协同 SLAM 提供鲁棒增量分布式图优化，处理机器人间共享测量与错误回环。可在相同位姿图和通信条件下，与集中式优化及 iMESA 比较轨迹误差、更新耗时和通信量。项目提供优化器接口，传感器前端与消息传输需要另行配套。
{: #rimesa .project-description }

论文：[riMESA: Consensus ADMM for Real-World Collaborative SLAM](https://doi.org/10.1109/TRO.2026.3706569)（IEEE T-RO，2026）。
{: .project-paper }

[SlideSLAM](https://github.com/KumarRobotics/slide_slam)：使用稀疏语义地标组织环境并支持地图合并，将大量观测压缩为较少的几何和类别信息，便于跨机器人交换与关联。可用于比较物体级匹配与低层特征匹配。主实现基于 ROS 1，实验性 ROS 2 分支面向 Jazzy，迁入 Humble 的工作量较大。
{: #slideslam .project-description }

论文：[SlideSLAM: Sparse, Lightweight, Decentralized Metric-Semantic SLAM for Multirobot Navigation](https://doi.org/10.1109/TRO.2025.3629786)（IEEE T-RO，2025）。
{: .project-paper }

[LAMP](https://github.com/nebula-autonomy/lamp)：面向地下等大规模复杂环境，组织多机器人里程计、回环和地图优化。系统架构与公开回放数据可用于分析局部误差经回环和跨机器人约束修正的过程。工程依赖较重，包含 ROS 1 和旧版 Python 组件，整套迁移成本较高。
{: #lamp .project-description }

论文：[LAMP 2.0: A Robust Multi-Robot SLAM System for Operation in Challenging Large-Scale Underground Environments](https://doi.org/10.1109/LRA.2022.3191204)（IEEE RA-L，2022）。
{: .project-paper }

[Kimera-Multi](https://github.com/MIT-SPARK/Kimera-Multi)：结合协同定位与稠密三维语义建图，输出包含几何和语义的环境表示。可研究局部感知、跨机器人关联与全局优化怎样共同影响地图一致性。与 riMESA 这类优化器相比，它涵盖更多系统模块；实现基于 ROS 1，传感器和计算依赖较多。
{: #kimera-multi .project-description }

论文：[Kimera-Multi: Robust, Distributed, Dense Metric-Semantic SLAM for Multi-Robot Systems](https://doi.org/10.1109/TRO.2021.3137751)（IEEE T-RO，2022）。
{: .project-paper }

[ReALM](https://github.com/bairuofei/LoS_constrained_navigation)：从实时激光扫描判断机器人之间的视线是否会被障碍遮挡，用连通性势函数调整各机运动，在未知环境中兼顾探索与通信。代码提供多机器人导航和探索示例，依赖 ROS Noetic 与独立的导航仿真工作空间；当前主分支还包含论文之后的拓扑优化与可见区域扩展。可参考通信约束对路线选择的影响，Humble 接口、车辆转弯约束与真实无线链路模型需要适配。
{: #realm .project-description }

论文：[Realm: Real-Time Line-of-Sight Maintenance in Multi-Robot Navigation with Unknown Obstacles](https://ieeexplore.ieee.org/document/11128211/)（ICRA，2025）。
{: .project-paper }

### 54.4.2 多机器人强化学习

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [JaxRobotarium](#jaxrobotarium) | IPPO、MAPPO、QMIX、PQN | 局部状态 → 航点或独轮车速度 |
| [CASH](#cash) | 能力条件超网络；QMIX / MAPPO 或 DAgger | 局部观测、团队能力 → 个体策略或价值网络 |
| [MAexp](#maexp) | IPPO、MAPPO 等 MARL、注意力目标生成 | 局部点云与团队观测 → 探索目标与连续运动 |

[JaxRobotarium](https://github.com/GT-STAR-Lab/JaxRobotarium)：将 JAX 并行仿真、策略训练与 Robotarium 部署连接起来，提供八类协作场景和循环策略，支持 GPU / TPU。离散动作解释为航点，连续动作解释为独轮车速度；策略可与 CBF 避碰层组合。环境使用 Python 3.10、JAX、Flax、Robotarium 模拟器子模块及作者集成的 JaxMARL 分支，许可证为 MIT。论文报告了 Robotarium 实验，标题中的训练时间依赖任务与硬件条件。用于 R680 时需要替换运动模型与安全层。
{: #jaxrobotarium .project-description }

论文：[JaxRobotarium: Training and Deploying Multi-Robot Policies in 10 Minutes](https://proceedings.mlr.press/v305/jain25a.html)（CoRL，2025）。
{: .project-paper }

[CASH](https://github.com/GT-STAR-Lab/CASH)：根据局部观测和团队能力生成个体网络参数，用于传感器、速度或载荷不同的异构机器人团队。CASH 是网络架构，可配合 QMIX、MAPPO，也可使用 DAgger 模仿学习。公开资源包括 JaxMARL 分支、能力条件策略、消防与运输环境、训练和绘图代码，采用 Apache-2.0 许可证。论文另通过 MARBLER / EPyMARL 在 Robotarium 评价，JAX 仓库不能直接等同于完整实机软件。该方法可用于研究能力下降或未见团队组合下的协作。
{: #cash .project-description }

论文：[Capability-Aware Shared Hypernetworks for Flexible Heterogeneous Multi-Robot Coordination](https://proceedings.mlr.press/v305/fu25a.html)（CoRL，2025）。
{: .project-paper }

[MAexp](https://github.com/COAI-Lab/MAexp)：为多机器人探索提供连续场景、点云地图与 MARLlib 算法接口，可比较 IPPO、MAPPO 等方法在不同环境中的覆盖行为。框架将多机器人目标生成与单机器人运动规划分开，包含随机障碍、迷宫、室内和室外场景。公开代码依赖 Python、Ray、MARLlib 与 Open3D，安装需要修改部分依赖代码；它是训练与评测平台，实机通信、定位和车辆接口需另行实现。
{: #maexp .project-description }

论文：[MAexp: A Generic Platform for RL-based Multi-Agent Exploration](https://doi.org/10.1109/icra57147.2024.10611573)（ICRA，2024）。
{: .project-paper }

## 54.5 语义地图与语言导航 {#semantic-navigation}

语义地图将物体、房间和语言描述与空间位置关联。视觉导航策略则根据图像目标或语言生成航点与动作。语义查询结果仍需转换为可到达的导航目标。

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [VLFM](#vlfm) | 视觉语言价值地图、前沿选择 | RGB、语言目标 → 探索方向 |
| [LeLaN](#lelan) | 语言条件视觉策略学习 | 语言、图像 → 目标接近动作 |
| [ViNT / NoMaD](#vint-nomad) | Transformer、目标掩码扩散策略 | 图像历史、目标图像 → 航点或动作 |
| [HOV-SG](#hov-sg) | 开放词汇表征、分层三维场景图 | 带位姿 RGB-D → 语义检索位置 |
| [ConceptGraphs](#conceptgraphs) | 跨帧物体关联、开放词汇场景图 | RGB-D → 三维物体图与语言查询结果 |
| [Language as Cost](#language-as-cost) | VLM 风险推理、开放词汇分割、高斯代价传播 | RGB-D、障碍地图 → 风险代价栅格 |

[VLFM](https://github.com/bdaiinstitute/vlfm)：根据图像与语言目标的相关性构建价值地图，引导前沿选择和未知区域搜索。语义模块可以提出地图目标，运动执行仍需几何规划与避障。实机实现面向 Spot，依赖 RGB 和 GPU 模型服务，已声明不再积极维护；与 Nav2 的组合需要适配。
{: #vlfm .project-description }

论文：[VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation](https://doi.org/10.1109/ICRA57147.2024.10610712)（ICRA，2024）。
{: .project-paper }

[LeLaN](https://github.com/NHirose/learning-language-navigation)：根据语言描述和相机图像生成接近可见目标的运动指令，侧重最后一段接近动作，可与 VLFM 的未知区域搜索互补。实现使用 ROS 1 和 RGB，速度指令包含原地转向，需要转换为车辆可执行的轨迹，并检查错误目标与不可行转向。
{: #lelan .project-description }

论文：[LeLaN: Learning a Language-Conditioned Navigation Policy from In-the-Wild Video](https://proceedings.mlr.press/v270/hirose25b.html)（CoRL 2024，PMLR 于 2025 年出版）。
{: .project-paper }

[ViNT / NoMaD](https://github.com/robodhruv/visualnav-transformer)：共享仓库提供视觉导航模型、训练与部署代码。ViNT 用观测和目标图像预测航点；NoMaD 通过目标掩码扩散策略联系目标导航与无目标探索。两者可用于研究图像目标、拓扑地图与局部动作之间的关系。实机代码依赖 RGB、外部权重和 ROS 1，生成的航点或动作仍需满足底盘运动约束。
{: #vint-nomad .project-description }

论文：[ViNT: A Foundation Model for Visual Navigation](https://proceedings.mlr.press/v229/shah23a.html)（CoRL，2023）；[NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration](https://doi.org/10.1109/ICRA57147.2024.10610665)（ICRA，2024）。
{: .project-paper }

[HOV-SG](https://github.com/hovsg/HOV-SG)：将环境组织为楼层、房间和物体层级，用开放词汇表征支持自然语言查询。例如“去厨房找杯子”可以先定位房间，再缩小物体搜索范围。输入为带位姿的 RGB-D 数据，输出语义检索位置，实际行走仍需几何导航。
{: #hov-sg .project-description }

论文：[Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation](https://doi.org/10.15607/RSS.2024.XX.077)（RSS，2024）。
{: .project-paper }

[ConceptGraphs](https://github.com/concept-graphs/concept-graphs)：从 RGB-D 观测构建开放词汇三维物体图，将不同视角下的同一物体合并，并保存其几何、语义特征与关系。与 HOV-SG 的空间层级相比，它更侧重物体实例与跨帧关联。导航时需要将物体位置转换为附近可到达的观察或接近位置。
{: #conceptgraphs .project-description }

论文：[ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning](https://doi.org/10.1109/ICRA57147.2024.10610243)（ICRA，2024）。
{: .project-paper }

[Language as Cost](https://github.com/Taekmino/LaC)：用视觉语言模型识别可能发生危险的区域，再通过 Grounded Edge SAM 定位相关物体，将风险等级投影到栅格并以高斯代价向周围传播，最后与几何障碍地图融合。它可参考为 Nav2 增加门口、湿滑区域等语义风险代价。原版基于 ROS Noetic，依赖 RGB-D、NVIDIA GPU 和模型 API；接入 R680 时需处理图像条件、推理延迟以及错误语义对路径的影响。
{: #language-as-cost .project-description }

论文：[Language as Cost: Proactive Hazard Mapping using VLM for Robot Navigation](https://ieeexplore.ieee.org/document/11246665/)（IROS，2025）。
{: .project-paper }

## 54.6 仿真环境与评测工具 {#evaluation}

仿真环境定义车辆、场景与任务，评测工具分析轨迹、传感器和运行状态。车辆动力学、任务目标和指标相同，算法结果才具有可比性。

### 54.6.1 仿真与导航基准 {#navigation-benchmarks}

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [F1TENTH Gym](#f1tenth-gymackermann) | 车辆仿真、连续控制与强化学习环境 | 转向、速度 → 车辆状态与激光观测 |
| [Habitat-Lab](#habitat-lab) | 室内任务仿真与指标评测 | 场景、动作 → 观测与评测结果 |
| [Arena-Bench 2.0](#arena-bench) | 社会导航场景与统一评测 | 地图、行人、导航方法 → 任务与交互指标 |
| [DMRP-Bench](#dmrp-bench) | 多机器人全局与局部规划对比 | 动态场景、多机任务 → 规划与交互指标 |

[F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym)：提供车辆动力学、激光观测与赛道仿真，适合研究 Ackermann 车辆的路径跟踪、MPPI、MPC 和强化学习控制。车辆尺寸、转向限制和动力学参数需要按 R680 替换，赛道表现不能直接代表室内低速导航能力。
{: #f1tenth-gymackermann .project-description }

论文：[F1TENTH: An Open-Source Evaluation Environment for Continuous Control and Reinforcement Learning](https://proceedings.mlr.press/v123/o-kelly20a.html)（PMLR 123，2020）。
{: .project-paper }

[Habitat-Lab](https://github.com/facebookresearch/habitat-lab)：与 Habitat-Sim 配合，提供室内语义导航任务、数据接口和成功率、路径效率等评测指标。可用于区分目标识别失败与目标到达失败。默认动作不反映汽车转向约束，场景数据有独立使用条件；v0.3.4 之后的版本缺少官方积极维护。
{: #habitat-lab .project-description }

论文：[Habitat: A Platform for Embodied AI Research](https://openaccess.thecvf.com/content_ICCV_2019/html/Savva_Habitat_A_Platform_for_Embodied_AI_Research_ICCV_2019_paper.html)（ICCV，2019）。
{: .project-paper }

[Arena-Bench 2.0 / Arena 4.0](https://github.com/Arena-Rosnav/arena-rosnav)：提供社会导航评测生态，可在共同场景下比较经典规划器与学习策略，统一地图、行人、任务种子和指标。Arena 4.0 将框架迁移到 ROS 2，并加入由文本或平面图生成场景的方法以及带语义标注的三维资产。Arena-Rosnav 入口仓库采用 MIT 许可证，组件与环境版本应以[官方安装文档](https://docs.arena-rosnav.org/en/latest/tutorials/installation/)为准；框架本身不代表某一种强化学习算法。
{: #arena-bench .project-description }

论文：[Arena-Bench 2.0: A Comprehensive Benchmark of Social Navigation Approaches in Collaborative Environments](https://doi.org/10.1109/iros60139.2025.11246895)（IROS，2025）；[Arena 4.0: a Comprehensive Ros2 Development and Benchmarking Platform for Human-Centric Navigation Using Generative-Model-Based Environment Generation](https://ieeexplore.ieee.org/document/11127635/)（ICRA，2025）。
{: .project-paper }

[DMRP-Bench](https://github.com/NKU-MobFly-Robotics/DMRP-Bench)：集成 CBS、ECBS、SIPP 等全局方法与 TEB、DWA、MPC 等局部规划，使用 Isaac Sim 动态场景研究阻塞、让行与多机交互，并提供录包分析脚本。README 基于 ROS Noetic、Isaac Sim 2022.2.1+，代码采用 MIT 许可证；Humble 迁移和场景资产完整性需要验证。
{: #dmrp-bench .project-description }

论文：[DMRP-Bench: An Integrated, Unified Multi-Robot Motion Planning Benchmark in Dynamic Environments](https://doi.org/10.1109/icra57385.2026.11696793)（ICRA，2026）。
{: .project-paper }

### 54.6.2 数据记录与结果分析

| 项目 | 主要算法或功能 | 输入与输出 |
|---|---|---|
| [rosbag2](#rosbag2) | ROS 2 消息记录与回放 | 传感器消息 → 可回放数据 |
| [evo](#evo) | 轨迹关联与对齐、APE / RPE | 参考和估计轨迹 → 误差统计 |
| [slam-under-perturbation](#slam-under-perturbation-slam) | 受控感知与时间扰动 | 图像、深度与时序 → 退化输入 |
| [diagnostics](#diagnostics) | 频率、时效监测与状态聚合 | 节点与设备状态 → 诊断信息 |
| [PlotJuggler](#plotjuggler) | 时序对齐、计算与可视化 | 记录或数据流 → 对比曲线 |

[rosbag2](https://github.com/ros2/rosbag2)：按时间记录和回放 ROS 2 话题，可让多个算法处理相同的相机、雷达、IMU 与轮速消息。原始观测、标定信息和时间关系决定回放的可用性。QoS、丢帧和回放速度会影响数据完整性与算法负载。
{: #rosbag2 .project-description }

[evo](https://github.com/MichaelGrupp/evo)：提供轨迹时间关联、对齐、绝对位姿误差（APE）和相对位姿误差（RPE）计算，分别反映整体偏离与局部漂移。比较结果依赖统一的时间关联、对齐方式和尺度处理；精度评价需要独立参考轨迹，地图视觉重合不能替代轨迹误差。
{: #evo .project-description }

[slam-under-perturbation](https://github.com/xiaohao-xu/slam-under-perturbation)：对图像、深度和时间对应关系施加可控扰动，用于研究误差增大、跟踪失效和恢复条件。相同数据与随机种子可用于比较多个估计器的退化表现。时间偏移以帧为单位，分析延迟时需要结合实际时间戳换算。
{: #slam-under-perturbation-slam .project-description }

论文：[Scalable Benchmarking and Robust Learning for Noise-Free Ego-Motion and 3D Reconstruction from Noisy Video](https://openreview.net/forum?id=Pz9zFea4MQ)（ICLR，2025）。
{: .project-paper }

[diagnostics](https://github.com/ros/diagnostics)：为数据频率、消息时效和设备状态提供统一诊断接口，可汇总相机掉帧、IMU 停更和节点异常。消息仍在发布不等于估计仍然可靠，定位质量还需要算法指标；阈值与告警持续时间应结合任务设置。
{: #diagnostics .project-description }

[PlotJuggler](https://github.com/facontidavide/PlotJuggler)：加载记录或实时数据，在同一时间轴上查看轮速、IMU、视觉里程计、控制指令和诊断状态。时序对齐与计算功能可用于判断跟踪抖动先出现在控制、执行还是定位环节。Humble 环境需要匹配的数据加载与流式插件。
{: #plotjuggler .project-description }

</div>

相关章节：[第 39 章 VINS 原理](../06-sensors-navigation/39-vins-principles.md)、[第 40 章视觉建图运行过程](../06-sensors-navigation/40-visual-runtime.md)、[第 34 章 Nav2 导航](../06-sensors-navigation/34-nav2-navigation.md)。

## 章节导航

[上一章：语音、多模态 AI 与 OpenClaw](53-voice-ai-openclaw.md) · [返回本篇](index.md) · [下一章：R680 硬件、接线与 OLED 状态](../09-r680-platform/55-r680-hardware-wiring-oled.md)
