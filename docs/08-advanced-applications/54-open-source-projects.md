---
status: complete
---

# 54. 开源项目与参考价值

前面的章节已经把传感器、定位、建图、规划和上层任务连接起来。继续改进系统时，问题会变得更具体：传感器提供的信息不足时，怎样保持稳定的运动估计，机器人怎样自己选择探索方向，或者怎样把“找到一把椅子”这样的语言目标转换为可执行任务。开源项目提供了相应的算法实现、实验环境和分析工具，可以用来比较方案，也可以从中复用一个模块。

选择项目时，先确定要改进哪项能力，再把项目放回机器人数据流中：它接收什么观测，输出位姿、地图、路径还是任务目标，又要与现有哪个节点连接。例如，新的视觉里程计可以放进原有融合链路中比较；语言导航模块可以提出目标，再交给 Nav2 执行。这样更容易判断项目的参考价值，也能逐步查明改进来自哪里。

本章保留六类工程项目，并增加从论文挖掘的 DRL、多人协作与学习导航候选。先看算法和数据接口，再展开“方法、论文与接入条件”。项目比较用于选择一个可验证的改进点；本章没有宣称这些研究方法已在 R680 上完成部署。

R680 的现有基础是 ROS 2 Humble、Ackermann 底盘、M10P 二维雷达、D435C 红外与深度图像，以及轮速和 IMU。依赖 RGB、三维雷达或原地转向的实现需要额外适配；实际运行速度还取决于计算平台。

<div class="project-overview" markdown="1">

<div class="project-kicker">研究到工程 · 49 个项目家族</div>

### 三条优先研究路线

<div class="project-routes" markdown="1">

<div markdown="1">

01 / 车辆控制

[Wheeled Lab](#wheeled-lab) → [NeuPAN 等学习对照](#other-learning-projects)

PPO、车辆动力学与域随机化；用 MPPI / MPC 建立共同基线。

</div>

<div markdown="1">

02 / 人群导航

[DRL-SFM](#drl-sfm) → [GenSafeNav](#gen-safe-nav)

从 Humble / Nav2 接口起步，再研究预测不确定性与约束 PPO。

</div>

<div markdown="1">

03 / 多机协作

[JaxRobotarium](#jaxrobotarium) → [CASH](#cash)

先比较同质团队，再测试异构能力与未见团队组合。

</div>

</div>
</div>

## 54.1 按任务选择起点

| 想解决的问题 | 建议先看 |
|---|---|
| 建立可比较的定位与导航基线 | robot_localization、RTAB-Map、slam_toolbox、Nav2 |
| 改善弱纹理、遮挡或动态场景中的定位 | VINS-Fusion、PL-VIWO、NGD-SLAM |
| 让机器人自主选择探索方向 | m-explore-ros2、FIT-SLAM 2 |
| 研究车辆绕障与控制 | F1TENTH Gym、pytorch_mppi、mpc_planner、[Wheeled Lab](#wheeled-lab) |
| 研究 DRL 社会导航 | [DRL-SFM](#drl-sfm)、[GenSafeNav](#gen-safe-nav)、[共同基准](#navigation-benchmarks) |
| 研究多机器人强化学习 | [JaxRobotarium](#jaxrobotarium)、[CASH](#cash) |
| 根据语言寻找物体或位置 | VLFM、LeLaN、HOV-SG |
| 评估退化、故障和恢复 | rosbag2、evo、slam-under-perturbation、ScaleNav |

## 54.2 定位与传感器融合

这一组项目解决“机器人怎样连续估计自身运动”。可以从现有 EKF 融合链路出发，分别考察新的视觉、惯性或轮速约束；在比较估计器之前，先用标定工具确认输入参数。

### robot_localization：多传感器状态融合

<div class="project-tags"><span>EKF / UKF</span><span>现有融合链路</span></div>

数据接口： 轮速、IMU、里程计 → 融合位姿与速度。

??? info "方法、论文与接入条件"

    [robot_localization](https://github.com/cra-ros-pkg/robot_localization) 使用扩展卡尔曼滤波和无迹卡尔曼滤波，融合轮速、IMU、视觉里程计等观测，输出连续的位姿和速度估计。协方差描述观测的不确定程度，决定不同传感器在融合中的影响。

    它适合学习二维运动约束、观测变量选择和坐标系配置，也是 R680 现有融合链路的基础。更换视觉里程计时，可以保留其余输入，比较融合结果怎样变化。若两个估计器共享轮速或 IMU，应检查重复使用同一信息带来的相关性。

    论文：[A Generalized Extended Kalman Filter Implementation for the Robot Operating System](https://doi.org/10.1007/978-3-319-08338-4_25)（Moore、Stouch，IAS-13）。

### VINS-Fusion：视觉惯性里程计

<div class="project-tags"><span>滑窗非线性优化、IMU 预积分、回环</span><span>ROS 1 迁移</span></div>

数据接口： 图像、IMU → 视觉惯性里程计。

??? info "方法、论文与接入条件"

    [VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion) 支持双目视觉、单目加 IMU、双目加 IMU 等配置，并提供回环模块。它在滑动窗口内联合优化近期状态，用视觉特征约束相对运动，用 IMU 预积分连接相邻图像之间的运动。

    适合学习视觉与惯性信息怎样互补，也可通过双目 VO 与双目 VIO 的对照，观察 IMU 对快速运动和短时视觉退化的帮助。原版使用 ROS 1，接入 Humble 需要移植或单独评估 ROS 2 分支。仓库列出的 VINS-Mono 论文是方法基础，与 VINS-Fusion 代码的功能范围存在差别。

    方法基础：[VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator](https://doi.org/10.1109/TRO.2018.2853729)（IEEE T-RO，2018）。

### PL-VIWO：点线视觉、IMU 与轮速融合

<div class="project-tags"><span>点线视觉惯性轮速联合优化</span><span>轮速模型适配</span></div>

数据接口： 单目图像、IMU、轮速 → 位姿。

??? info "方法、论文与接入条件"

    [PL-VIWO](https://github.com/Happy-zzx/PL-VIWO) 将图像点特征、线特征、IMU 和轮速共同用于运动估计。墙边、门框等线结构能补充角点较少的图像；轮速则提供来自底盘运动的约束。

    适合研究走廊、弱纹理和短时遮挡，并分别关闭线特征或轮速，判断每种观测的贡献。对 R680 最值得借鉴的是轮速参与视觉惯性估计的方法，而非直接照搬配置。实现基于 ROS Noetic，轮速测量形式与运动模型需要匹配 Ackermann 底盘。

    论文：[PL-VIWO: A Lightweight and Robust Point-Line Monocular Visual Inertial Wheel Odometry](https://doi.org/10.1109/IROS60139.2025.11246999)（IROS，2025）。

### Kalibr：相机与 IMU 标定

<div class="project-tags"><span>批量时空参数标定</span><span>离线工具</span></div>

数据接口： 标定图像、IMU → 内外参与时间偏移。

??? info "方法、论文与接入条件"

    [Kalibr](https://github.com/ethz-asl/kalibr) 用于多相机标定，以及相机与 IMU 的空间、时间标定。相机内参决定像素对应的视线，外参描述传感器之间的安装关系，时间偏差则影响图像与惯性观测是否对应同一段运动。

    它适合在更换估计器之前使用，帮助判断误差来自算法还是传感器参数。对于 D435C 与底盘 IMU 的组合，可借鉴其标定板采集、充分激励各轴运动和残差检查方法；只有平面直行的数据通常不足以约束全部标定参数。

    论文：[Unified Temporal and Spatial Calibration for Multi-Sensor Systems](https://doi.org/10.1109/IROS.2013.6696514)（IROS，2013）。

### AirSLAM：光照变化下的视觉定位

<div class="project-tags"><span>学习点线特征、视觉 SLAM</span><span>CUDA / TensorRT</span></div>

数据接口： 双目图像 → 位姿与地图。

??? info "方法、论文与接入条件"

    [AirSLAM](https://github.com/sair-lab/AirSLAM) 使用学习得到的点线特征进行双目视觉定位，关注光照变化下的特征提取与匹配。相较于只看最终轨迹，它还适合用于观察前端匹配质量如何影响后端估计。

    可将它与传统特征方案放在相同明暗变化序列中，比较跟踪中断、漂移和推理时间。可借鉴的模块包括点线特征前端与推理部署方式。实现依赖 ROS 1、CUDA 和 TensorRT，更适合具备 NVIDIA GPU 的实验环境。

    论文：[AirSLAM: An Efficient and Illumination-Robust Point-Line Visual SLAM System](https://doi.org/10.1109/TRO.2025.3539171)（IEEE T-RO，2025）。

### SE2LIO：地面运动约束下的激光惯性估计

<div class="project-tags"><span>LiDAR-IMU 融合、SE(2) 约束</span><span>需三维雷达</span></div>

数据接口： 三维点云、IMU → 里程计。

??? info "方法、论文与接入条件"

    [SE2LIO](https://github.com/Jiaying001/SE2LIO) 在激光惯性估计中引入 SE(2) 地面运动约束，即主要关注平面位置与航向。其思路是利用车辆运动规律，减少仅凭传感器观测难以约束的状态变化。

    可参考它怎样将运动先验写入估计问题，并研究平地、坡面与颠簸条件下约束的适用范围。提供的流程使用多线三维雷达，适合 R680 后续扩展三维感知时研究，不能直接替换 M10P 二维雷达定位。

    论文：[Versatile LiDAR-Inertial Odometry With SE(2) Constraints for Ground Vehicles](https://doi.org/10.1109/LRA.2023.3268584)（IEEE RA-L，2023）。

### MOLA：模块化定位框架

<div class="project-tags"><span>模块化优化框架</span><span>需选择前后端</span></div>

数据接口： 传感器与模块配置 → 定位／地图。

??? info "方法、论文与接入条件"

    [MOLA](https://github.com/MOLAorg/mola) 将定位与建图组织为可组合的模块，并提供 ROS 2 桥接。它关注的是怎样组织算法系统，使传感器输入、状态估计和地图处理能够按需组合。

    适合需要长期比较多个定位方案的开发者：可以参考其模块接口，将输入适配与算法实现分开，减少每次更换算法时的重复工作。搭建导航系统时，需要配套里程计、地图算法和规划控制模块。

    框架论文：[A Modular Optimization Framework for Localization and Mapping](https://doi.org/10.15607/RSS.2019.XV.043)（RSS，2019）。

## 54.3 建图与自主探索

运动估计提供传感器的位置，建图再把连续观测组织成环境表示，自主探索则决定下一步去哪里采集信息。以下项目分别适合已有地图复用、动态场景处理和探索目标选择。

### RTAB-Map：视觉建图与重定位

<div class="project-tags"><span>回环检测、位姿图优化</span><span>已有视觉链路参考</span></div>

数据接口： RGB-D／灰度深度等 → 轨迹与地图。

??? info "方法、论文与接入条件"

    [RTAB-Map ROS](https://github.com/introlab/rtabmap_ros) 提供视觉里程计、回环检测、地图保存和重定位接口。关键帧及其约束组成位姿图；检测到重访地点后，通过图优化调整地图中各帧的相对位置。

    它是 R680 视觉建图的直接参考，适合追踪从图像、深度到位姿图、占据栅格和 Nav2 地图的处理过程。其 RGB-D 里程计支持灰度图像，可结合正确配准的红外图像与深度图使用。应区分局部里程计漂移与回环后的全局地图修正。

    论文：[RTAB-Map as an Open-Source Lidar and Visual Simultaneous Localization and Mapping Library for Large-Scale and Long-Term Online Operation](https://doi.org/10.1002/rob.21831)（Journal of Field Robotics，2019）。

### slam_toolbox：二维雷达建图

<div class="project-tags"><span>扫描匹配、位姿图优化</span><span>ROS 2 基线</span></div>

数据接口： 二维雷达、里程计 → 地图与定位。

??? info "方法、论文与接入条件"

    [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) 提供二维激光 SLAM、位姿图保存和定位模式。它通过扫描匹配估计运动，再结合回环与位姿图优化改善地图一致性。

    它与 M10P 的输入形式接近，适合作为视觉建图之外的对比基线：在相同路线下，比较雷达方案与红外深度方案各自在何种环境中更稳定。还可学习保存占据地图与保存位姿图的区别，理解后续定位和继续建图需要哪些信息。R680 应选用 Humble 对应版本。

    论文：[SLAM Toolbox: SLAM for the Dynamic World](https://doi.org/10.21105/joss.02783)（JOSS，2021）。

### NGD-SLAM：动态物体干扰下的视觉 SLAM

<div class="project-tags"><span>动态区域处理、视觉 SLAM</span><span>动态场景对照</span></div>

数据接口： 图像等观测 → 轨迹与地图。

??? info "方法、论文与接入条件"

    [NGD-SLAM](https://github.com/YuhaoZhang7/NGD-SLAM) 结合异步目标检测与特征跟踪，减少行人等动态区域对相机定位的干扰。检测不必每帧完成，跟踪模块可以在相邻帧间传播动态区域信息。

    值得借鉴的是检测与定位解耦的执行方式，适合研究有限算力下精度与延迟的取舍。评估时除了轨迹误差，还应观察掩码有多旧、跟踪是否中断。检测代码使用 CPU 后端；实机示例采用彩色与深度输入，红外检测效果需另行评估。

    论文：[NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU](https://doi.org/10.1109/IROS60139.2025.11246202)（IROS，2025）。

### FIT-SLAM 2：考虑定位质量的自主探索

<div class="project-tags"><span>前沿探索、定位质量评价</span><span>目标可达性适配</span></div>

数据接口： 地图与定位信息 → 探索目标。

??? info "方法、论文与接入条件"

    [FIT-SLAM 2](https://github.com/suchetanrs/FIT-SLAM) 在探索选路中同时考虑未知区域、地形可通行性和视觉定位信息。其中 Fisher 信息用于衡量预期观测对定位的约束能力，使目标选择同时考虑“能探索多少”和“途中是否容易保持定位”。

    最值得复用的是探索目标与路线的评价思路，可与普通前沿探索比较覆盖率、定位丢失和完成时间。项目面向 Humble，但完整流程依赖三维几何与 SLAM 地标接口；用于 R680 时，可先提取评分逻辑，再对接现有地图与 Nav2，并替换原地旋转动作。

    论文：[FIT-SLAM 2: Efficient 3D Exploration with Fisher Information and Traversability-Based Adaptive Roadmap](https://doi.org/10.1016/j.robot.2025.105188)（Robotics and Autonomous Systems，2025）。

### DynoSAM：同时估计相机与动态物体运动

<div class="project-tags"><span>动态物体关联、联合运动估计</span><span>计算与输入适配</span></div>

数据接口： 图像／深度等 → 相机与物体运动。

??? info "方法、论文与接入条件"

    [DynoSAM](https://github.com/ACFR-RPG/DynOSAM) 联合估计相机和场景中运动物体的轨迹，并构建动态地图。除了相机在哪里，它还估计物体怎样运动，因而需要跨帧关联同一物体并联合优化多个状态。

    适合将动态 SLAM 与 NGD-SLAM 这类动态区域剔除方法对照，研究保留物体运动信息的收益与计算代价。可参考其数据关联和后端组织方式。当前代码面向 ROS 2 Kilted，并依赖学习模型预处理，移植工作量较大。

    论文：[DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM](https://doi.org/10.1109/TRO.2025.3641813)（IEEE T-RO，2026）。

### NVMS-SLAM：多次采集与地图优化

<div class="project-tags"><span>法向量几何约束、多会话优化</span><span>需三维雷达</span></div>

数据接口： 多次三维雷达轨迹 → 一致地图。

??? info "方法、论文与接入条件"

    [NVMS-SLAM](https://github.com/lian-yue0515/NVMS-SLAM) 面向室内多会话激光建图，利用法向量等几何信息处理多次采集的地图。多会话指不同时间分别运行建图，而后建立这些轨迹与地图之间的联系。

    可参考其跨次采集的对齐与联合优化思路，研究重复巡检时地图能否保持一致，以及离线处理能带来多少改善。其感知基础是三维雷达，适合作为后续硬件扩展方向；只有 M10P 时可先学习方法和离线流程。

    论文：[NVMS-SLAM: Normal Vector-Based Multi-Session LiDAR SLAM in Indoor Environments](https://doi.org/10.1109/TASE.2026.3682733)（IEEE T-ASE，2026）。

## 54.4 规划与运动控制

定位与地图可用后，规划器需要生成可走的路线，控制器再把路线转换为底盘指令。对 Ackermann 车辆，比较方法时要同时考虑转弯半径、倒车能力和轨迹跟踪；车辆仿真可作为接入实机前的实验起点。

### Nav2：规划、控制与任务执行框架

<div class="project-tags"><span>Smac Hybrid-A*、MPPI、行为树</span><span>现有主要基线</span></div>

数据接口： 地图、位姿、目标 → 路线与控制。

??? info "方法、论文与接入条件"

    [Nav2](https://github.com/ros-navigation/navigation2) 将全局规划、局部控制、代价地图和行为树组织成导航系统。规划器决定路线，控制器根据局部观测跟踪路线，行为树负责重规划、等待与恢复等任务流程。

    它的插件接口适合承载算法对比：只替换目标选择、规划器或控制器，保留其他条件。R680 当前使用的 Smac Hybrid-A* 与 MPPI 是主要基线；转弯半径、车体轮廓和恢复动作需要符合 Ackermann 约束。该系统论文解释整体架构，具体插件仍应结合各自实现阅读。

    系统论文：[The Marathon 2: A Navigation System](https://arxiv.org/abs/2003.00368)（IROS，2020）。

### mpc_planner：考虑障碍与不确定性的预测控制

<div class="project-tags"><span>拓扑候选、并行轨迹优化、MPC</span><span>替换车辆模型</span></div>

数据接口： 机器人与障碍状态 → 控制轨迹。

??? info "方法、论文与接入条件"

    [mpc_planner](https://github.com/tud-amr/mpc_planner) 使用模型预测控制，在有限的未来时间范围内优化运动，并持续根据新观测重新求解。它通过不同绕障方向的候选轨迹，减少优化只停留在某一种局部路线上的问题。

    适合学习动力学模型、目标代价和障碍约束怎样共同影响决策，尤其适合研究动态障碍两侧的路线选择。可借鉴候选生成与并行优化模块。示例中的独轮车模型需要替换为汽车模型，求解器选择会影响部署与复现成本。

    论文：[Topology-Driven Parallel Trajectory Optimization in Dynamic Environments](https://doi.org/10.1109/TRO.2024.3475047)（IEEE T-RO，2025）。

### pytorch_mppi：便于修改的采样控制器

<div class="project-tags"><span>采样式 MPPI</span><span>需自建 ROS 接口</span></div>

数据接口： 动力学、状态与代价 → 控制序列。

??? info "方法、论文与接入条件"

    [pytorch_mppi](https://github.com/UM-ARM-Lab/pytorch_mppi) 用 PyTorch 实现模型预测路径积分控制：采样多组控制序列，通过动力学模型预测轨迹，再根据代价对控制进行加权更新。动力学和代价函数由使用者定义。

    它适合快速修改车辆模型、障碍代价与控制平滑项，观察每个设计对轨迹的影响，再与 Nav2 MPPI 对照。先在仿真中比较横向误差、最小间距和控制抖动，通常比直接改整套导航系统容易分析。它是算法库，ROS 接口需要自行实现。

    方法背景：[Information Theoretic MPC for Model-Based Reinforcement Learning](https://doi.org/10.1109/ICRA.2017.7989202)（ICRA，2017；仓库采用的 MPPI 方法参考）。

### Circulation-embedded CBF：避障与脱离局部死锁

<div class="project-tags"><span>CBF 约束、绕行引导</span><span>重建车辆约束</span></div>

数据接口： 目标与障碍几何 → 安全控制。

??? info "方法、论文与接入条件"

    [Circulation-embedded CBF](https://github.com/sh-keyumarsi/Circulation-embedded-CBF) 在控制障碍函数中加入绕行机制，缓解机器人停在障碍前的问题。控制障碍函数将保持安全距离写成控制约束，绕行机制则帮助机器人持续沿障碍侧面运动。

    适合研究安全距离、绕行方向和死锁之间的关系，并与普通避障控制器比较受阻时间。可借鉴约束构造与绕行状态的管理方式。其单积分器模型与独轮车映射不直接适用于 Ackermann 底盘，原有安全结论需要在车辆模型下重新分析。

    论文：[Circulation-Embedded Control Barrier Function for Safe Navigation: A Solution to Avoid Undesired Equilibria and Dysfunctional Circulation](https://doi.org/10.1016/j.robot.2025.105132)（Robotics and Autonomous Systems，2025）。

### CVF motion planning：曲率约束下的向量场规划

<div class="project-tags"><span>曲率约束向量场</span><span>MATLAB / ROS 1</span></div>

数据接口： 目标与障碍等 → 车辆引导。

??? info "方法、论文与接入条件"

    [CVF motion planning](https://github.com/Y1kee/CVF-for-Nonholonomic-Motion-Planning) 研究满足非完整运动约束的曲率向量场。向量场给出不同位置的引导方向，而曲率约束限制方向变化的幅度，使运动考虑车辆的转弯能力。

    适合学习几何可达性与车辆可跟踪性的区别，也可与先规划折线路径、再由控制器跟踪的方案比较。可借鉴其将转弯约束融入引导规律的方式。项目以 MATLAB/Simulink 为主，并提供 ROS 1 Ackermann 示例。

    论文：[Curvature-Constrained Vector Field for Motion Planning of Nonholonomic Robots](https://doi.org/10.1109/TRO.2025.3644358)（IEEE T-RO，2026）。

### accelerated-RS-planner：加速 Reeds–Shepp 路径计算

<div class="project-tags"><span>Reeds–Shepp 几何连接</span><span>补充碰撞检测</span></div>

数据接口： 起终位姿、转弯半径 → 直线圆弧路径。

??? info "方法、论文与接入条件"

    [accelerated-RS-planner](https://github.com/IbrahimSquared/accelerated-RS-planner) 计算允许前进与倒车、满足最小转弯半径的 Reeds–Shepp 路径。输入是起点和终点的位置、朝向及转弯半径，输出由直线与圆弧组成的连接。

    它适合学习车辆位姿之间的几何连接，也可作为搜索规划器尝试直接连接目标的模块。可比较其计算耗时与路径长度，并观察倒车怎样改善狭窄空间中的可达性。完整绕障规划还需要碰撞检测与地图搜索。

    论文：[Accelerated Reeds–Shepp and Underspecified Reeds–Shepp Algorithms for Mobile Robot Path Planning](https://doi.org/10.1109/TRO.2025.3554406)（IEEE T-RO，2025）。

### F1TENTH Gym：Ackermann 车辆仿真

<div class="project-tags"><span>车辆仿真与 RL 环境接口</span><span>改用本车参数</span></div>

数据接口： 转向、速度 → 状态与激光观测。

??? info "方法、论文与接入条件"

    [F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym) 提供车辆运动、激光观测和赛道仿真环境。与可以原地转向的机器人仿真相比，它更适合观察转向、速度和车辆尺寸怎样影响轨迹。

    可用它比较路径跟踪、MPPI 或 MPC，并通过重复相同起点和障碍设置分析参数变化。对于 R680，可借鉴其车辆仿真与控制评估接口；应替换赛车默认参数，匹配本车尺寸、转向限制和动力学，避免把赛道成绩直接当作导航能力。

    论文：[F1TENTH: An Open-Source Evaluation Environment for Continuous Control and Reinforcement Learning](https://proceedings.mlr.press/v123/o-kelly20a.html)（PMLR 123，2020）。

## 54.5 多机器人与协同建图

多机器人系统需要把各自的观测和轨迹连接到共同坐标系，还要处理通信开销与错误关联。下面从较容易接入的前沿探索和地图合并，逐步扩展到分布式优化、协同定位与语义建图。

### m-explore-ros2：前沿探索与地图合并

<div class="project-tags"><span>前沿选择、地图合并</span><span>Nav2 目标适配</span></div>

数据接口： 占据栅格 → 探索目标／合并地图。

??? info "方法、论文与接入条件"

    [m-explore-ros2](https://github.com/robo-friends/m-explore-ros2) 提供基于占据栅格的前沿探索和多机器人地图合并。前沿是已知自由空间与未知区域的交界，选择这些位置作为目标，可以逐步扩大已知地图。

    它适合作为自主探索的入门基线，先观察前沿提取、目标选择和失败目标处理，再扩展到多机。R680 可复用现有地图与 Nav2，主要对接目标与车辆可达性。多机扩展需要建立共同坐标系，并分别评估地图配准误差和协同定位精度。

### Swarm-SLAM：受通信限制的协同 SLAM

<div class="project-tags"><span>跨机回环、分散协同 SLAM</span><span>描述子与通信适配</span></div>

数据接口： 各机观测与摘要 → 协同地图。

??? info "方法、论文与接入条件"

    [Swarm-SLAM](https://github.com/mistlab/Swarm-SLAM) 是 ROS 2 协同 SLAM 系统，涉及跨机器人回环检测和通信预算分配。跨机器人回环建立不同轨迹之间的约束，使各自地图能够放到共同参考系中。

    它适合研究机器人之间交换什么信息、何时交换，以及带宽限制怎样影响地图精度。可从两段有重叠区域的记录开始，比较独立建图与协同建图的误差和通信量。用于 R680 时，需要选择匹配的视觉输入，并评估学习描述子在红外图像上的效果。

    论文：[Swarm-SLAM: Sparse Decentralized Collaborative Simultaneous Localization and Mapping Framework for Multi-Robot Systems](https://doi.org/10.1109/LRA.2023.3333742)（IEEE RA-L，2024）。

### riMESA：鲁棒增量分布式优化

<div class="project-tags"><span>鲁棒增量共识 ADMM</span><span>先离线后端实验</span></div>

数据接口： 分布式位姿图 → 一致估计。

??? info "方法、论文与接入条件"

    [riMESA](https://github.com/rpl-cmu/riMESA) 针对协同 SLAM 提供鲁棒的增量分布式图优化。它处理机器人之间共享的测量约束，并考虑错误回环对整体结果的影响。

    适合从预先构造的位姿图入手，固定错误回环数量和通信中断安排，比较轨迹误差、更新耗时和交换数据量。这样可以先研究优化后端，而无需同时搭建多台机器人的感知系统。项目提供优化器接口，传感器前端与消息传输需要另行配套。

    论文：[riMESA: Consensus ADMM for Real-World Collaborative SLAM](https://doi.org/10.1109/TRO.2026.3706569)（IEEE T-RO，2026）。

### iMESA：分布式优化对比基线

<div class="project-tags"><span>增量分布式图优化</span><span>后端比较基线</span></div>

数据接口： 各机测量约束 → 分布式估计。

??? info "方法、论文与接入条件"

    [iMESA](https://github.com/rpl-cmu/imesa) 是 riMESA 的前序方法，研究协同 SLAM 中随新观测持续到来的分布式优化。各机器人保留本地估计，通过共享信息逐步改善共同变量的一致性。

    它适合作为后端对比基线：使用相同测量图与通信安排，对照集中式优化、iMESA 和 riMESA，观察增量更新及异常约束处理的差别。其参考价值在于分离优化方法与感知前端各自的贡献。

    论文：[iMESA: Incremental Distributed Optimization for Collaborative Simultaneous Localization and Mapping](https://doi.org/10.15607/RSS.2024.XX.085)（RSS，2024）。

### SlideSLAM：稀疏语义地标协同建图

<div class="project-tags"><span>稀疏语义地标、跨机关联</span><span>ROS 版本与前端适配</span></div>

数据接口： 感知与语义地标 → 协同地图。

??? info "方法、论文与接入条件"

    [SlideSLAM](https://github.com/KumarRobotics/slide_slam) 使用稀疏语义地标描述环境并支持地图合并。物体级地标将大量感知数据压缩为较少的几何与类别信息，便于机器人之间交换和关联。

    适合研究地图表达的精简程度与定位能力之间的取舍，并比较物体级匹配与低层特征匹配。可借鉴其语义地标构建和跨机器人关联流程。主实现使用 ROS 1，实验性 ROS 2 分支面向 Jazzy，迁入 Humble 的工作量较大。

    论文：[SlideSLAM: Sparse, Lightweight, Decentralized Metric-Semantic SLAM for Multirobot Navigation](https://doi.org/10.1109/TRO.2025.3629786)（IEEE T-RO，2025）。

### LAMP：复杂环境中的协同建图系统

<div class="project-tags"><span>多传感器、回环与协同图优化</span><span>系统集成成本较高</span></div>

数据接口： 多机传感器 → 大规模地图。

??? info "方法、论文与接入条件"

    [LAMP](https://github.com/nebula-autonomy/lamp) 面向地下等复杂环境，组织多机器人定位、回环和地图优化。它展示了长距离、受通信限制的任务中，多个感知与优化模块怎样组成可运行系统。

    适合参考系统分工与公开回放数据，分析局部里程计误差如何经过回环和多机器人约束得到修正。对 R680 更有价值的是系统架构与离线评估方式。工程依赖较重，包含 ROS 1 与旧版 Python 组件，整套迁移成本较高。

    论文：[LAMP 2.0: A Robust Multi-Robot SLAM System for Operation in Challenging Large-Scale Underground Environments](https://doi.org/10.1109/LRA.2022.3191204)（IEEE RA-L，2022）。

### Kimera-Multi：分布式几何与语义地图

<div class="project-tags"><span>分布式几何／语义建图</span><span>传感器与算力适配</span></div>

数据接口： 各机视觉惯性等 → 语义地图。

??? info "方法、论文与接入条件"

    [Kimera-Multi](https://github.com/MIT-SPARK/Kimera-Multi) 将多机器人协同定位与稠密三维语义地图结合。输出既包含环境几何，也包含语义信息，使地图能够支持超出位姿估计本身的任务。

    可参考其从局部感知、跨机器人关联到全局地图的模块划分，研究轨迹优化怎样影响最终地图的几何与语义一致性。与 riMESA 这类优化器相比，它更适合系统层面的学习。项目基于 ROS 1，依赖较多，适合作为进阶参考。

    论文：[Kimera-Multi: Robust, Distributed, Dense Metric-Semantic SLAM for Multi-Robot Systems](https://doi.org/10.1109/TRO.2021.3137751)（IEEE T-RO，2022）。

## 54.6 语义地图与语言导航

几何导航使用坐标目标，语义导航进一步把物体、房间或语言描述与空间位置关联起来。这里可分别参考目标选择、近距离接近和语义地图查询，再与已有的几何规划及避障模块组合。

### VLFM：用语言目标评价探索方向

<div class="project-tags"><span>视觉语言价值地图、前沿选择</span><span>RGB / GPU；几何导航配套</span></div>

数据接口： RGB、语言目标 → 探索方向。

??? info "方法、论文与接入条件"

    [VLFM](https://github.com/bdaiinstitute/vlfm) 根据图像与语言目标的相关性构建价值地图，引导机器人寻找指定物体。例如搜索椅子时，探索方向除了考虑未知面积，还利用已观察场景与“椅子”的语义关联。

    最值得借鉴的是语义价值如何影响前沿选择。可让这一模块提出地图目标，再由几何导航执行，以分别评估目标选择和运动能力。实机实现面向 Spot，依赖 RGB 与 GPU 模型服务，且已声明不再积极维护；接入 Nav2 属于需要重新评估的系统组合。

    论文：[VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation](https://doi.org/10.1109/ICRA57147.2024.10610712)（ICRA，2024）。

### LeLaN：语言指定目标的近距离接近

<div class="project-tags"><span>语言条件视觉策略学习</span><span>ROS 1 / 车辆动作适配</span></div>

数据接口： 语言、图像 → 接近动作。

??? info "方法、论文与接入条件"

    [LeLaN](https://github.com/NHirose/learning-language-navigation) 根据语言描述与相机图像生成运动指令，使机器人接近可见目标。它更关注目标已经出现在视野中时，怎样从语言与视觉信息得到接近动作。

    适合研究最后一段目标接近，可与 VLFM 的未知区域搜索分别评估。可借鉴其语言条件输入、策略推理与部署流程，并检查错误目标和不可行转向。实现使用 ROS 1 与 RGB，速度指令包含原地转向，需要转换为车辆可执行的轨迹。

    论文：[LeLaN: Learning a Language-Conditioned Navigation Policy from In-the-Wild Video](https://proceedings.mlr.press/v270/hirose25b.html)（CoRL 2024，PMLR 于 2025 年出版）。

### ViNT / NoMaD：学习视觉导航与探索策略

<div class="project-tags"><span>Transformer / 目标掩码扩散策略</span><span>RGB / 模型权重</span></div>

数据接口： 图像历史、图像目标 → 航点／动作。

??? info "方法、论文与接入条件"

    [ViNT / NoMaD](https://github.com/robodhruv/visualnav-transformer) 的共享仓库提供视觉导航模型、训练流程和部署代码。ViNT 根据观测与目标图像预测视觉航点；NoMaD 通过目标掩码与扩散策略，将朝目标运动和无明确目标的探索联系起来。

    适合参考图像目标、拓扑地图与局部动作之间的连接，也可比较不同策略在陌生环境中的行为。实机部署依赖 RGB、外部模型权重和 ROS 1；模型生成的航点或动作仍需符合底盘运动约束。

    论文：[ViNT: A Foundation Model for Visual Navigation](https://proceedings.mlr.press/v229/shah23a.html)（CoRL，2023）；[NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration](https://doi.org/10.1109/ICRA57147.2024.10610665)（ICRA，2024）。

### HOV-SG：分层开放词汇语义地图

<div class="project-tags"><span>开放词汇表征、分层场景图</span><span>离线建图起步</span></div>

数据接口： 带位姿 RGB-D → 语义检索位置。

??? info "方法、论文与接入条件"

    [HOV-SG](https://github.com/hovsg/HOV-SG) 将环境组织为楼层、房间和物体层级，支持自然语言检索。开放词汇表示允许使用语言描述查询地图，不必只依赖建图时预先列好的类别。

    可参考它怎样把空间层级与语义特征结合，为“去厨房找杯子”这类任务逐步缩小搜索范围。适合先用带位姿的 RGB-D 数据离线建图，检查房间和物体检索，再把检索位置转为导航目标。它提供语义地图能力，实际行走仍需几何导航配合。

    论文：[Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation](https://doi.org/10.15607/RSS.2024.XX.077)（RSS，2024）。

### ConceptGraphs：物体级场景图与语言查询

<div class="project-tags"><span>跨帧物体关联、开放词汇场景图</span><span>配套几何导航</span></div>

数据接口： RGB-D → 三维物体图。

??? info "方法、论文与接入条件"

    [ConceptGraphs](https://github.com/concept-graphs/concept-graphs) 从 RGB-D 观测构建开放词汇三维物体图，并支持语言查询。它需要将不同视角下的同一物体合并，保存物体的几何、语义特征及关系。

    适合关注物体实例和场景关系的任务，可借鉴跨帧关联、物体合并与语义查询模块。与 HOV-SG 的楼层、房间层级相比，这里更适合从物体图的构建入手。实际导航还需要把物体位置转换为附近可到达的观察或接近位置。

    论文：[ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning](https://doi.org/10.1109/ICRA57147.2024.10610243)（ICRA，2024）。

### Habitat-Lab：语义导航评测环境

<div class="project-tags"><span>任务定义、仿真与指标评测</span><span>需车辆动作重建</span></div>

数据接口： 场景、动作 → 观测与评测结果。

??? info "方法、论文与接入条件"

    [Habitat-Lab](https://github.com/facebookresearch/habitat-lab) 提供室内导航任务、数据接口和评测流程，并与 Habitat-Sim 配合使用。固定场景、起点、目标与停止条件后，可以在同一组任务上比较不同语义策略。

    适合先评估目标成功率、行走距离与路径效率，再进入实车适配。它也有助于区分识别目标失败与到达目标失败。默认动作不反映汽车转向约束；场景数据有独立使用条件，v0.3.4 之后的版本缺少官方积极维护。

    平台论文：[Habitat: A Platform for Embodied AI Research](https://openaccess.thecvf.com/content_ICCV_2019/html/Savva_Habitat_A_Platform_for_Embodied_AI_Research_ICCV_2019_paper.html)（ICCV，2019）。

## 54.7 退化恢复与实验工具

比较算法时，需要让不同方案处理相同输入，并同时观察轨迹、控制量和故障状态。录包回放、扰动实验、轨迹评估和时序分析工具共同组成实验基础，恢复策略则用于研究失败后如何继续任务。

### ScaleNav：学习导航失败后的恢复 {#scalenav}

<div class="project-tags"><span>离线 IQL、可供性、RND</span><span>作者重实现；数据配置</span></div>

数据接口： 当前／目标图像 → 动作与恢复。

??? info "方法、论文与接入条件"

    [ScaleNav](https://github.com/KubeEdge4Robotics/ScaleNav) 是作者对 SCALE 方法的重新实现，利用可通行性与新颖度信息学习恢复行为。当当前观测与已知可行路线偏离时，系统尝试通过自纠正动作返回可继续导航的状态。

    适合研究恢复策略的触发与选择：除了恢复成功率，还可观察误触发是否打断正常任务。它可作为固定回退规则之外的学习方法参考。实现基于 ROS 1 和彩色相机，模型与数据路径尚不完整，并含需要适配的旋转动作。

    论文：[SCALE: Self-Correcting Visual Navigation for Mobile Robots via Anti-Novelty Estimation](https://doi.org/10.1109/ICRA57147.2024.10610847)（ICRA，2024）。

### slam-under-perturbation：可重复的 SLAM 扰动实验

<div class="project-tags"><span>受控感知／时间扰动</span><span>离线鲁棒性实验</span></div>

数据接口： 图像、深度与时序 → 退化输入。

??? info "方法、论文与接入条件"

    [slam-under-perturbation](https://github.com/xiaohao-xu/slam-under-perturbation) 对图像、深度和时间对应关系施加扰动，用受控输入模拟感知退化。改变扰动强度后，可以观察算法从误差上升到跟踪失效的过程。

    可借鉴其扰动生成与分级评估方式，在相同记录和随机种子下比较多个估计器。比起只汇报正常环境下的平均误差，这样更容易找到失效边界和恢复条件。时间偏移参数以帧为单位，分析延迟时应结合实际时间戳换算。

    仓库对应论文：[Scalable Benchmarking and Robust Learning for Noise-Free Ego-Motion and 3D Reconstruction from Noisy Video](https://openreview.net/forum?id=Pz9zFea4MQ)（ICLR，2025）。

### evo：轨迹误差评估

<div class="project-tags"><span>轨迹关联、对齐、APE / RPE</span><span>需独立参考轨迹</span></div>

数据接口： 参考和估计轨迹 → 误差统计。

??? info "方法、论文与接入条件"

    [evo](https://github.com/MichaelGrupp/evo) 提供轨迹时间关联、对齐、绝对位姿误差和相对位姿误差计算。绝对误差反映轨迹对参考的整体偏离，相对误差更便于观察一段运动内的漂移。

    适合统一比较不同里程计或 SLAM 方法，并将误差与路线中的转弯、遮挡等事件对应。比较时应固定时间关联、对齐方式和尺度处理，否则数字可能不具可比性。精度指标需要独立参考轨迹，地图视觉重合不能替代轨迹评估。

### rosbag2：记录与回放原始输入

<div class="project-tags"><span>时间戳记录与回放</span><span>实验输入基线</span></div>

数据接口： ROS 2 消息 → 可回放记录。

??? info "方法、论文与接入条件"

    [rosbag2](https://github.com/ros2/rosbag2) 记录 ROS 2 话题并按时间回放，让多个算法使用相同的相机、雷达、IMU 和轮速输入。它是将一次实车采集转化为多次可重复实验的基础工具。

    值得参考的是原始输入、标定信息和时间关系的保存方式。评估替代算法时，应保留原始传感器消息，而不只记录原算法输出。录制的 QoS、时间戳和丢帧会影响回放结果，回放速度也可能改变算法的处理负载。

### diagnostics：传感器与节点状态监测

<div class="project-tags"><span>频率、时效与状态聚合</span><span>阈值按任务设定</span></div>

数据接口： 节点／设备状态 → 诊断信息。

??? info "方法、论文与接入条件"

    [diagnostics](https://github.com/ros/diagnostics) 为数据频率、消息时效和设备状态提供统一诊断接口。它可以将相机掉帧、IMU 数据停更或节点报告的异常，组织为可查看和汇总的状态。

    可借鉴其诊断发布与聚合方式，为定位退化检测提供输入。应区分“消息仍在发布”与“估计仍然可靠”：前者可由频率监测判断，后者还需算法质量指标。阈值、告警持续时间和异常处理策略需要结合任务定义。

### PlotJuggler：时序数据与故障分析

<div class="project-tags"><span>时序对齐、计算与可视化</span><span>匹配 Humble 插件</span></div>

数据接口： 记录／数据流 → 对比曲线。

??? info "方法、论文与接入条件"

    [PlotJuggler](https://github.com/facontidavide/PlotJuggler) 用于查看和计算多路时序数据，支持加载记录或接入数据流。将轮速、IMU、视觉里程计、控制指令和诊断状态放在同一时间轴上，可以检查异常发生的先后关系。

    例如出现路径跟踪抖动时，可同时查看目标转向、实际角速度和估计航向，判断问题先出现在控制、执行还是定位环节。它适合故障分析与参数调整；用于 Humble 时，应选择匹配的数据加载与流式插件。

## 54.8 从现有论文挖掘 DRL 项目 {#drl-projects}

本节沿着论文中的作者链接核查代码。DRL 指用深度网络表示策略或价值函数，并通过奖励学习行为；SAC、PPO、QMIX 属于这里的训练算法。扩散策略、自监督表征和可微优化则分别列在下一节，便于选择合适的对照方法。

| 项目 / 本库论文 | 算法与学习方式 | 输入 → 输出 | 实验入口 / R680 适配重点 |
|---|---|---|---|
| [DRL-SFM](#drl-sfm) · H11 | SAC，离策略连续控制；社会力参与观测／奖励设计 | 局部代价地图、目标及社会信息 → 线速度、角速度 | ROS 2 Humble、HuNavSim、Nav2；先处理 Ackermann 可行控制 |
| [Wheeled Lab](#wheeled-lab) · H28 | PPO、域随机化、并行仿真；视觉任务包含教师／学生学习 | 车辆状态或视觉与任务观测 → 车辆控制 | Isaac Lab；优先借鉴轮式车辆模型与随机化 |
| [GenSafeNav](#gen-safe-nav) · S48 | PPO / PPO-Lagrangian、DtACI 自适应共形推断 | 人群预测与不确定性 → 导航动作 | 仿真训练、ROS 2 Foxy 部署；补齐检测跟踪和 Humble 迁移 |
| [JaxRobotarium](#jaxrobotarium) · H29 | IPPO、MAPPO、QMIX、PQN；循环策略 | 多机器人局部状态 → 航点或独轮车速度 | JAX、JaxMARL；先研究协作，车辆动力学需重建 |
| [CASH](#cash) · H26 | 能力条件超网络；QMIX / MAPPO，也支持 DAgger 模仿学习 | 局部观测、团队能力 → 个体策略／价值网络 | JaxMARL 异构协作；比较更换传感器或载荷后的泛化 |
| [SCALE / ScaleNav](#scale-drl) · S38 | 离线 Implicit Q-Learning、RND 新颖度估计 | 当前／目标图像 → 动作、恢复候选 | 已有项目的补充路线；需要离线数据和 ROS 1 适配 |

### DRL-SFM：最接近现有 Nav2 接口的社会导航候选 {#drl-sfm}

<div class="project-tags"><span>DRL · SAC</span><span>ROS 2 Humble</span><span>MIT</span></div>

[作者仓库](https://github.com/FAU-FAPS/DRL-SFM)将代价地图和社会力信息交给 SAC 策略，并提供 `nav2_rl_controller`。控制接口返回 `geometry_msgs/Twist`，便于分析怎样将学习策略接入 Nav2 的局部控制流程。论文是 [DRL-SFM](https://doi.org/10.1109/ICRA57385.2026.11697464)（ICRA 2026，H11）。

| 核查项 | 已公开内容与使用条件 |
|---|---|
| 训练与评估 | Stable-Baselines3 SAC；HuNavSim / Gazebo；训练启动器、预训练模型、固定评估路径和多环境评估脚本 |
| 环境 | Ubuntu 22.04、ROS 2 Humble、PyTorch 与 CUDA GPU；依赖特定 HuNavSim 分支 |
| 能借鉴什么 | 局部代价地图编码、社会行为奖励、Nav2 控制器插件、固定路径对照评估 |
| 首个对照实验 | 同一路线与行人设置，对照 MPPI 和 SAC；记录碰撞、成功率、最小人际距离、路径时间和控制延迟 |
| 公开范围 | README 声明完整日志功能涉及私有分支；公开训练与模型入口可读，完整日志复现仍待核实 |

策略输出包含角速度。接入 R680 时，应在训练环境里约束转弯半径、转向速率和低速行为，再评估与底盘实际执行的差异；仅对输出限幅可能改变策略学到的避障行为。

### Wheeled Lab：优先参考 Ackermann 车辆的仿真训练 {#wheeled-lab}

<div class="project-tags"><span>DRL · PPO</span><span>Isaac Lab</span><span>BSD-3-Clause</span></div>

[Wheeled Lab](https://github.com/UWRobotLearning/WheeledLab)提供轮式平台的资产、环境和训练流程。论文使用 RSL-RL 的 PPO，并研究随机化、扰动和并行训练等因素；任务覆盖漂移、地形运动和视觉驾驶。[CoRL 2025 论文](https://proceedings.mlr.press/v305/han25a.html)对应本库 H28。

| 核查项 | 已公开内容与使用条件 |
|---|---|
| 训练入口 | `source/wheeledlab_rl/scripts/train_rl.py`；漂移、地形、视觉任务配置 |
| 环境版本 | README 推荐 Isaac Sim 4.5.0、Isaac Lab 2.0.2、Python 3.10；训练需要合适的 NVIDIA GPU |
| 实机代码 | 独立的 [RealLab](https://github.com/UWRobotLearning/RealLab) 提供 HOUND / MuSHR 分支；README 将 F1TENTH 集成列为待提供 |
| 能借鉴什么 | 轴距与转向约束建模、摩擦／延迟／执行器随机化、训练与部署接口分离 |
| 首个对照实验 | 使用 R680 尺寸和低速限制，固定路线比较 PPO 与 MPPI；先做无视觉任务，再增加相机输入 |

这里的车辆任务与 Ackermann 运动更接近，但 HOUND、MuSHR 的参数和控制器仍需替换。漂移成绩也不能直接代表室内低速导航能力。

### GenSafeNav：把人群预测的不确定性带入约束强化学习 {#gen-safe-nav}

<div class="project-tags"><span>DRL · 约束 PPO</span><span>人群导航</span><span>训练 MIT / 部署 GPL-3.0</span></div>

[GenSafeNav](https://github.com/tasl-lab/GenSafeNav)用人群轨迹预测和 DtACI 自适应共形推断估计不确定性，再通过约束强化学习调节行为。作者另有 [ROS 2 部署仓库](https://github.com/tasl-lab/GenSafeNav-ROS2)。论文 [Towards Generalizable Safety in Crowd Navigation via Conformal Uncertainty Handling](https://gen-safe-nav.github.io/)为 CoRL 2025，本库 S48。

| 核查项 | 已公开内容与使用条件 |
|---|---|
| 算法组件 | PPO / PPO-Lagrangian、Gumbel Social Transformer 预测、DtACI；实机链路含 DR-SPAAM 检测与 SORT 跟踪 |
| 训练资料 | 训练、测试、可视化脚本与预训练模型；Docker 示例基于 PyTorch 2.3.1 / CUDA 12.1 |
| 部署条件 | 作者 ROS 2 仓库在 Foxy 上测试；需修改路径与传感器配置，Humble 兼容性尚需实际验证 |
| 能借鉴什么 | 将预测误差和不确定性引入观测／约束，分开评价预测模块与决策模块 |
| 首个对照实验 | 固定人群路线，分别改变行人速度、行为分布和检测漏报率，比较碰撞与过度保守停车 |

R680 的二维雷达可作为行人检测研究的输入，但扫描分辨率、视场、遮挡和跟踪质量会影响整条链路。应先录包检查检测与预测，再连接策略。训练仓库和部署仓库使用不同许可证，复用时应分别查看。

### JaxRobotarium：快速比较多机器人强化学习算法 {#jaxrobotarium}

<div class="project-tags"><span>MARL</span><span>JAX / JaxMARL</span><span>MIT</span></div>

[JaxRobotarium](https://github.com/GT-STAR-Lab/JaxRobotarium)将仿真、训练与 Robotarium 部署连接起来，支持 GPU / TPU 并行。论文比较 IPPO、MAPPO、QMIX 和 PQN，并提供八类协作场景；[CoRL 2025 论文](https://proceedings.mlr.press/v305/jain25a.html)对应 H29。

| 核查项 | 已公开内容与使用条件 |
|---|---|
| 输入输出 | 场景局部状态；离散动作解释为航点，连续动作解释为独轮车速度 |
| 环境 | Python 3.10、JAX、Flax、Robotarium 模拟器子模块；JaxMARL 使用作者的集成分支 |
| 实机依据 | 论文报告 Robotarium 上的部署；README 提供 `deploy/` 说明，本次未执行远程实验 |
| 能借鉴什么 | 统一环境 API、集中训练／分散执行、多随机种子比较、策略和 CBF 避碰层的组合 |
| 首个对照实验 | 从两到四台机器人目标交换开始，固定观测和训练步数，对照独立 PPO 与 MAPPO |

论文标题中的“10 分钟”依赖任务与硬件条件。R680 是 Ackermann 车辆，应先替换机器人运动模型和安全层，再讨论多机迁移。

### CASH：让共享策略感知每台机器人的能力 {#cash}

<div class="project-tags"><span>异构 MARL</span><span>超网络</span><span>Apache-2.0</span></div>

[CASH](https://github.com/GT-STAR-Lab/CASH)根据局部观测和团队能力生成个体网络参数，适合研究传感器、速度或载荷不同的机器人怎样协作。它是网络架构，可配合 QMIX、MAPPO，也可用 DAgger 训练；DAgger 属于模仿学习。[CoRL 2025 论文](https://proceedings.mlr.press/v305/fu25a.html)对应 H26。

| 核查项 | 已公开内容与使用条件 |
|---|---|
| 公开模块 | JaxMARL 分支、能力条件策略、消防／运输环境、QMIX、MAPPO、DAgger 和绘图代码 |
| 能力输入 | 机器人能力表示与团队能力集合；部署策略使用局部观测和可更新的能力信息 |
| 实机范围 | 论文另以 MARBLER / EPyMARL 路线在 Robotarium 评价；不可把 JAX 仓库直接等同于完整实机软件 |
| 能借鉴什么 | 将速度、传感器可用性或载荷编码成能力，并测试训练未见过的团队组合 |
| 首个对照实验 | 同质共享策略、显式能力输入和 CASH 三者对照；测试一台机器人的能力下降后协作是否恢复 |

### SCALE：已有恢复项目的离线 RL 阅读路线 {#scale-drl}

[前文 ScaleNav](#scalenav)可进一步按三个学习环节阅读：视觉编码、离线 Implicit Q-Learning（IQL）与可供性模型、RND 新颖度估计。策略从离线轨迹学习，在异常观测下搜索更熟悉的恢复候选。这里的 IQL 是 Implicit Q-Learning，与多智能体文献中的 Independent Q-Learning 含义不同。

适合先用正常路线和偏离路线的记录，评价恢复触发、误触发、恢复成功率与额外路程。仓库是作者重新实现，公开流程要求自行配置数据与模型路径；先验证离线数据格式、训练阶段和目标图像定义，再考虑 ROS 1 到 Humble 的迁移。

### Arena-Bench 2.0 与 DMRP-Bench：建立共同评测条件 {#navigation-benchmarks}

| 基准 / 本库论文 | 方法与资源 | 对我们有用的部分 | 当前接入成本 |
|---|---|---|---|
| [Arena-Rosnav](https://github.com/Arena-Rosnav/arena-rosnav) / [Arena-Bench 2.0，H36](https://doi.org/10.1109/IROS60139.2025.11246895) | 社会导航评测生态；经典与学习规划器的共同场景 | 统一行人、地图、任务种子和指标，区分策略改进与场景变化 | 入口仓库 README 很简短，需按[官方安装文档](https://docs.arena-rosnav.org/en/latest/tutorials/installation/)选定组件和版本；MIT |
| [DMRP-Bench](https://github.com/NKU-MobFly-Robotics/DMRP-Bench) / [H14](https://doi.org/10.1109/ICRA57385.2026.11696793) | CBS / ECBS / SIPP 等全局方法与 TEB / DWA / MPC 等局部规划，Isaac Sim 动态场景 | 多机阻塞、让行与交互指标；录包分析脚本 | README 基于 ROS Noetic、Isaac Sim 2022.2.1+；迁移 Humble、场景资产完整性仍需验证；MIT |

这两个项目提供评测框架，可承载 DRL 与经典算法对比。应记录具体规划器和训练版本，避免把整个框架当成一个 DRL 算法。

## 54.9 同批论文中的其他学习方法 {#other-learning-projects}

| 项目 / 论文 | 实际算法类别 | 输入 → 输出 | 借鉴点与公开范围 |
|---|---|---|---|
| [NeuPAN](https://github.com/hanruihua/NeuPAN) / [T-RO 2025，H48](https://doi.org/10.1109/TRO.2025.3554252) | 模型驱动学习、近端交替优化与 MPC | 障碍点、机器人几何、参考路径 → 控制序列 | 提供差速、Ackermann、全向 IR-SIM 示例；可优先作为车辆学习规划对照；GPL-3.0 |
| [NavDP](https://github.com/InternRobotics/NavDP) / [ICRA 2026，H09](https://doi.org/10.1109/ICRA57385.2026.11696748) | 特权信息指导的扩散导航策略学习 | RGB-D／目标条件等观测 → 局部轨迹 | 可参考仿真数据、策略训练与检查点；当前仓库含后续工作，复现 H09 需固定对应配置与权重；根目录常见 LICENSE 文件未核实 |
| [STERLING](https://github.com/HareshKarnan/sterling_corl23) / [CoRL 2023，H60](https://proceedings.mlr.press/v229/karnan23a.html) | 多模态自监督地形表征学习 | 地形视觉与机器人交互经验 → 地形表征／偏好 | 适合学习颠簸、振动与视觉地形的关联；README 明示仅公开表征训练脚本，ROS 预处理仍列为待提供；根目录常见 LICENSE 文件未核实 |

NeuPAN 的 IR-SIM 示例支持 `acker`，适合先比较车辆轮廓、最小转弯半径与障碍间距。它使用学习模块和优化模型，不能仅凭“端到端”就称作 DRL。训练其 DUNE 模型时要匹配车体几何；CVXPY 求解部分建议先评估 CPU 频率与延迟。

NavDP 和 STERLING 可帮助研究视觉信息与地形泛化。R680 的红外／深度输入、RGB 可用性和安装位姿必须与模型需要的观测逐项核对。对于只公开部分流水线的工作，可以借鉴模块思想并单独评价，先确认已有代码能覆盖哪一个实验环节。

本轮新增了 10 个项目家族，并补充了 SCALE 的 DRL 阅读路径。以上 12 个相关仓库（含独立部署仓库）在 2026-11-11 核查了 README、HEAD 提交和常见许可证文件，未运行训练或实机部署。可下载[核查记录与固定提交链接](../assets/data/open-source-projects.json)追溯所读版本；缺失的许可证信息表示本次未核实，不代表已经证明没有许可证。项目页收录与未来期刊论文的 JCR Q1 下载规则分别处理。

## 54.10 从项目选择到对照实验

先用当前系统录制一段有代表性的路线，保存传感器输入和原有结果，再选择一个模块进行替换。

| 阶段 | 固定条件 | 需要留下的结果 |
|---|---|---|
| 经典基线 | 地图、起终点、车体轮廓、速度限制、传感器与 TF | Smac Hybrid-A* + MPPI 的完成率、路径时间、最小间距和计算延迟 |
| 仿真策略 | 相同地图／人群种子、训练预算、奖励与终止条件 | 多随机种子的均值和离散程度；碰撞、超时、失败恢复分别计数 |
| 泛化对照 | 训练之外的地图、行人行为、摩擦或传感器退化 | 性能下降量，区分感知、策略和执行器误差 |
| 接口验证 | 观测时间戳、策略频率、转向与速度限制 | 策略命令与实际执行差异、超时次数、端到端延迟 |
| 实机比较 | 相同路线、速度范围、记录内容与人工接管定义 | 每次运行记录、干预次数及触发原因；不能只保留成功片段 |

建议先完成 一个经典基线 + 一个学习候选 + 一个泛化条件。对 R680，车辆控制路线可先选 Wheeled Lab 或 NeuPAN；社会导航可先选 DRL-SFM；多机算法可先在 JaxRobotarium 做独立仿真研究。训练奖励与最后评价指标分别记录，避免只用累计奖励判断导航质量。

定位实验可比较轨迹误差、跟踪中断和恢复时间；规划控制实验可比较完成率、路径偏差、最小障碍距离和计算时间。保留相同输入与评价方法后，再逐步增加探索或语言任务，便于判断每个新增模块的作用。

需要进一步理解估计器时，可读[第 39 章 VINS 原理](../06-sensors-navigation/39-vins-principles.md)；要确定模块在现有系统中的接入位置，可对照[第 40 章视觉建图运行过程](../06-sensors-navigation/40-visual-runtime.md)和[第 34 章 Nav2 导航](../06-sensors-navigation/34-nav2-navigation.md)。

## 章节导航

[上一章：语音、多模态 AI 与 OpenClaw](53-voice-ai-openclaw.md) · [返回本篇](index.md) · [下一章：R680 硬件、接线与 OLED 状态](../09-r680-platform/55-r680-hardware-wiring-oled.md)
