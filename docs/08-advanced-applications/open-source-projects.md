---
status: complete
---

# 开源项目与参考价值

这些项目可用于学习算法实现、选择实验基线或复用功能模块。选项目时，先看它解决什么问题，再看值得借鉴的模块，以及输入和运动模型是否适合自己的机器人。

R680 的现有基础是 ROS 2 Humble、Ackermann 底盘、M10P 二维雷达、D435C 红外与深度图像，以及轮速和 IMU。依赖 RGB、三维雷达或原地转向的实现需要额外适配；实际运行速度还取决于计算平台。

## 从哪里开始

| 想解决的问题 | 建议先看 |
|---|---|
| 建立可比较的定位与导航基线 | robot_localization、RTAB-Map、slam_toolbox、Nav2 |
| 改善弱纹理、遮挡或动态场景中的定位 | VINS-Fusion、PL-VIWO、NGD-SLAM |
| 让机器人自主选择探索方向 | m-explore-ros2、FIT-SLAM 2 |
| 研究车辆绕障与控制 | F1TENTH Gym、pytorch_mppi、mpc_planner |
| 根据语言寻找物体或位置 | VLFM、LeLaN、HOV-SG |
| 评估退化、故障和恢复 | rosbag2、evo、slam-under-perturbation、ScaleNav |

## 定位与传感器融合

### robot_localization：多传感器状态融合

[robot_localization](https://github.com/cra-ros-pkg/robot_localization) 使用扩展卡尔曼滤波和无迹卡尔曼滤波，融合轮速、IMU、视觉里程计等观测，输出连续的位姿和速度估计。协方差描述观测的不确定程度，决定不同传感器在融合中的影响。

它适合学习二维运动约束、观测变量选择和坐标系配置，也是 R680 现有融合链路的基础。更换视觉里程计时，可以保留其余输入，比较融合结果怎样变化。若两个估计器共享轮速或 IMU，应检查重复使用同一信息带来的相关性。

论文：[A Generalized Extended Kalman Filter Implementation for the Robot Operating System](https://doi.org/10.1007/978-3-319-08338-4_25)（Moore、Stouch，IAS-13）。

### VINS-Fusion：视觉惯性里程计

[VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion) 支持双目视觉、单目加 IMU、双目加 IMU 等配置，并提供回环模块。它在滑动窗口内联合优化近期状态，用视觉特征约束相对运动，用 IMU 预积分连接相邻图像之间的运动。

适合学习视觉与惯性信息怎样互补，也可通过双目 VO 与双目 VIO 的对照，观察 IMU 对快速运动和短时视觉退化的帮助。原版使用 ROS 1，接入 Humble 需要移植或单独评估 ROS 2 分支。仓库列出的 VINS-Mono 论文是方法基础，与 VINS-Fusion 代码的功能范围存在差别。

方法基础：[VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator](https://doi.org/10.1109/TRO.2018.2853729)（IEEE T-RO，2018）。

### PL-VIWO：点线视觉、IMU 与轮速融合

[PL-VIWO](https://github.com/Happy-zzx/PL-VIWO) 将图像点特征、线特征、IMU 和轮速共同用于运动估计。墙边、门框等线结构能补充角点较少的图像；轮速则提供来自底盘运动的约束。

适合研究走廊、弱纹理和短时遮挡，并分别关闭线特征或轮速，判断每种观测的贡献。对 R680 最值得借鉴的是轮速参与视觉惯性估计的方法，而非直接照搬配置。实现基于 ROS Noetic，轮速测量形式与运动模型需要匹配 Ackermann 底盘。

论文：[PL-VIWO: A Lightweight and Robust Point-Line Monocular Visual Inertial Wheel Odometry](https://doi.org/10.1109/IROS60139.2025.11246999)（IROS，2025）。

### Kalibr：相机与 IMU 标定

[Kalibr](https://github.com/ethz-asl/kalibr) 用于多相机标定，以及相机与 IMU 的空间、时间标定。相机内参决定像素对应的视线，外参描述传感器之间的安装关系，时间偏差则影响图像与惯性观测是否对应同一段运动。

它适合在更换估计器之前使用，帮助判断误差来自算法还是传感器参数。对于 D435C 与底盘 IMU 的组合，可借鉴其标定板采集、充分激励各轴运动和残差检查方法；只有平面直行的数据通常不足以约束全部标定参数。

论文：[Unified Temporal and Spatial Calibration for Multi-Sensor Systems](https://doi.org/10.1109/IROS.2013.6696514)（IROS，2013）。

### AirSLAM：光照变化下的视觉定位

[AirSLAM](https://github.com/sair-lab/AirSLAM) 使用学习得到的点线特征进行双目视觉定位，关注光照变化下的特征提取与匹配。相较于只看最终轨迹，它还适合用于观察前端匹配质量如何影响后端估计。

可将它与传统特征方案放在相同明暗变化序列中，比较跟踪中断、漂移和推理时间。可借鉴的模块包括点线特征前端与推理部署方式。实现依赖 ROS 1、CUDA 和 TensorRT，更适合具备 NVIDIA GPU 的实验环境。

论文：[AirSLAM: An Efficient and Illumination-Robust Point-Line Visual SLAM System](https://doi.org/10.1109/TRO.2025.3539171)（IEEE T-RO，2025）。

### SE2LIO：地面运动约束下的激光惯性估计

[SE2LIO](https://github.com/Jiaying001/SE2LIO) 在激光惯性估计中引入 SE(2) 地面运动约束，即主要关注平面位置与航向。其思路是利用车辆运动规律，减少仅凭传感器观测难以约束的状态变化。

可参考它怎样将运动先验写入估计问题，并研究平地、坡面与颠簸条件下约束的适用范围。提供的流程使用多线三维雷达，适合 R680 后续扩展三维感知时研究，不能直接替换 M10P 二维雷达定位。

论文：[Versatile LiDAR-Inertial Odometry With SE(2) Constraints for Ground Vehicles](https://doi.org/10.1109/LRA.2023.3268584)（IEEE RA-L，2023）。

### MOLA：模块化定位框架

[MOLA](https://github.com/MOLAorg/mola) 将定位与建图组织为可组合的模块，并提供 ROS 2 桥接。它关注的是怎样组织算法系统，使传感器输入、状态估计和地图处理能够按需组合。

适合需要长期比较多个定位方案的开发者：可以参考其模块接口，将输入适配与算法实现分开，减少每次更换算法时的重复工作。搭建导航系统时，需要配套里程计、地图算法和规划控制模块。

框架论文：[A Modular Optimization Framework for Localization and Mapping](https://doi.org/10.15607/RSS.2019.XV.043)（RSS，2019）。

## 建图与自主探索

### RTAB-Map：视觉建图与重定位

[RTAB-Map ROS](https://github.com/introlab/rtabmap_ros) 提供视觉里程计、回环检测、地图保存和重定位接口。关键帧及其约束组成位姿图；检测到重访地点后，通过图优化调整地图中各帧的相对位置。

它是 R680 视觉建图的直接参考，适合追踪从图像、深度到位姿图、占据栅格和 Nav2 地图的处理过程。其 RGB-D 里程计支持灰度图像，可结合正确配准的红外图像与深度图使用。应区分局部里程计漂移与回环后的全局地图修正。

论文：[RTAB-Map as an Open-Source Lidar and Visual Simultaneous Localization and Mapping Library for Large-Scale and Long-Term Online Operation](https://doi.org/10.1002/rob.21831)（Journal of Field Robotics，2019）。

### slam_toolbox：二维雷达建图

[slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) 提供二维激光 SLAM、位姿图保存和定位模式。它通过扫描匹配估计运动，再结合回环与位姿图优化改善地图一致性。

它与 M10P 的输入形式接近，适合作为视觉建图之外的对比基线：在相同路线下，比较雷达方案与红外深度方案各自在何种环境中更稳定。还可学习保存占据地图与保存位姿图的区别，理解后续定位和继续建图需要哪些信息。R680 应选用 Humble 对应版本。

论文：[SLAM Toolbox: SLAM for the Dynamic World](https://doi.org/10.21105/joss.02783)（JOSS，2021）。

### NGD-SLAM：动态物体干扰下的视觉 SLAM

[NGD-SLAM](https://github.com/YuhaoZhang7/NGD-SLAM) 结合异步目标检测与特征跟踪，减少行人等动态区域对相机定位的干扰。检测不必每帧完成，跟踪模块可以在相邻帧间传播动态区域信息。

值得借鉴的是检测与定位解耦的执行方式，适合研究有限算力下精度与延迟的取舍。评估时除了轨迹误差，还应观察掩码有多旧、跟踪是否中断。检测代码使用 CPU 后端；实机示例采用彩色与深度输入，红外检测效果需另行评估。

论文：[NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU](https://doi.org/10.1109/IROS60139.2025.11246202)（IROS，2025）。

### FIT-SLAM 2：考虑定位质量的自主探索

[FIT-SLAM 2](https://github.com/suchetanrs/FIT-SLAM) 在探索选路中同时考虑未知区域、地形可通行性和视觉定位信息。其中 Fisher 信息用于衡量预期观测对定位的约束能力，使目标选择同时考虑“能探索多少”和“途中是否容易保持定位”。

最值得复用的是探索目标与路线的评价思路，可与普通前沿探索比较覆盖率、定位丢失和完成时间。项目面向 Humble，但完整流程依赖三维几何与 SLAM 地标接口；用于 R680 时，可先提取评分逻辑，再对接现有地图与 Nav2，并替换原地旋转动作。

论文：[FIT-SLAM 2: Efficient 3D Exploration with Fisher Information and Traversability-Based Adaptive Roadmap](https://doi.org/10.1016/j.robot.2025.105188)（Robotics and Autonomous Systems，2025）。

### DynoSAM：同时估计相机与动态物体运动

[DynoSAM](https://github.com/ACFR-RPG/DynOSAM) 联合估计相机和场景中运动物体的轨迹，并构建动态地图。除了相机在哪里，它还估计物体怎样运动，因而需要跨帧关联同一物体并联合优化多个状态。

适合将动态 SLAM 与 NGD-SLAM 这类动态区域剔除方法对照，研究保留物体运动信息的收益与计算代价。可参考其数据关联和后端组织方式。当前代码面向 ROS 2 Kilted，并依赖学习模型预处理，移植工作量较大。

论文：[DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM](https://doi.org/10.1109/TRO.2025.3641813)（IEEE T-RO，2026）。

### NVMS-SLAM：多次采集与地图优化

[NVMS-SLAM](https://github.com/lian-yue0515/NVMS-SLAM) 面向室内多会话激光建图，利用法向量等几何信息处理多次采集的地图。多会话指不同时间分别运行建图，而后建立这些轨迹与地图之间的联系。

可参考其跨次采集的对齐与联合优化思路，研究重复巡检时地图能否保持一致，以及离线处理能带来多少改善。其感知基础是三维雷达，适合作为后续硬件扩展方向；只有 M10P 时可先学习方法和离线流程。

论文：[NVMS-SLAM: Normal Vector-Based Multi-Session LiDAR SLAM in Indoor Environments](https://doi.org/10.1109/TASE.2026.3682733)（IEEE T-ASE，2026）。

## 规划与运动控制

### Nav2：规划、控制与任务执行框架

[Nav2](https://github.com/ros-navigation/navigation2) 将全局规划、局部控制、代价地图和行为树组织成导航系统。规划器决定路线，控制器根据局部观测跟踪路线，行为树负责重规划、等待与恢复等任务流程。

它的插件接口适合承载算法对比：只替换目标选择、规划器或控制器，保留其他条件。R680 当前使用的 Smac Hybrid-A* 与 MPPI 是主要基线；转弯半径、车体轮廓和恢复动作需要符合 Ackermann 约束。该系统论文解释整体架构，具体插件仍应结合各自实现阅读。

系统论文：[The Marathon 2: A Navigation System](https://arxiv.org/abs/2003.00368)（IROS，2020）。

### mpc_planner：考虑障碍与不确定性的预测控制

[mpc_planner](https://github.com/tud-amr/mpc_planner) 使用模型预测控制，在有限的未来时间范围内优化运动，并持续根据新观测重新求解。它通过不同绕障方向的候选轨迹，减少优化只停留在某一种局部路线上的问题。

适合学习动力学模型、目标代价和障碍约束怎样共同影响决策，尤其适合研究动态障碍两侧的路线选择。可借鉴候选生成与并行优化模块。示例中的独轮车模型需要替换为汽车模型，求解器选择会影响部署与复现成本。

论文：[Topology-Driven Parallel Trajectory Optimization in Dynamic Environments](https://doi.org/10.1109/TRO.2024.3475047)（IEEE T-RO，2025）。

### pytorch_mppi：便于修改的采样控制器

[pytorch_mppi](https://github.com/UM-ARM-Lab/pytorch_mppi) 用 PyTorch 实现模型预测路径积分控制：采样多组控制序列，通过动力学模型预测轨迹，再根据代价对控制进行加权更新。动力学和代价函数由使用者定义。

它适合快速修改车辆模型、障碍代价与控制平滑项，观察每个设计对轨迹的影响，再与 Nav2 MPPI 对照。先在仿真中比较横向误差、最小间距和控制抖动，通常比直接改整套导航系统容易分析。它是算法库，ROS 接口需要自行实现。

方法背景：[Information Theoretic MPC for Model-Based Reinforcement Learning](https://doi.org/10.1109/ICRA.2017.7989202)（ICRA，2017；仓库采用的 MPPI 方法参考）。

### Circulation-embedded CBF：避障与脱离局部死锁

[Circulation-embedded CBF](https://github.com/sh-keyumarsi/Circulation-embedded-CBF) 在控制障碍函数中加入绕行机制，缓解机器人停在障碍前的问题。控制障碍函数将保持安全距离写成控制约束，绕行机制则帮助机器人持续沿障碍侧面运动。

适合研究安全距离、绕行方向和死锁之间的关系，并与普通避障控制器比较受阻时间。可借鉴约束构造与绕行状态的管理方式。其单积分器模型与独轮车映射不直接适用于 Ackermann 底盘，原有安全结论需要在车辆模型下重新分析。

论文：[Circulation-Embedded Control Barrier Function for Safe Navigation: A Solution to Avoid Undesired Equilibria and Dysfunctional Circulation](https://doi.org/10.1016/j.robot.2025.105132)（Robotics and Autonomous Systems，2025）。

### CVF motion planning：曲率约束下的向量场规划

[CVF motion planning](https://github.com/Y1kee/CVF-for-Nonholonomic-Motion-Planning) 研究满足非完整运动约束的曲率向量场。向量场给出不同位置的引导方向，而曲率约束限制方向变化的幅度，使运动考虑车辆的转弯能力。

适合学习几何可达性与车辆可跟踪性的区别，也可与先规划折线路径、再由控制器跟踪的方案比较。可借鉴其将转弯约束融入引导规律的方式。项目以 MATLAB/Simulink 为主，并提供 ROS 1 Ackermann 示例。

论文：[Curvature-Constrained Vector Field for Motion Planning of Nonholonomic Robots](https://doi.org/10.1109/TRO.2025.3644358)（IEEE T-RO，2026）。

### accelerated-RS-planner：加速 Reeds–Shepp 路径计算

[accelerated-RS-planner](https://github.com/IbrahimSquared/accelerated-RS-planner) 计算允许前进与倒车、满足最小转弯半径的 Reeds–Shepp 路径。输入是起点和终点的位置、朝向及转弯半径，输出由直线与圆弧组成的连接。

它适合学习车辆位姿之间的几何连接，也可作为搜索规划器尝试直接连接目标的模块。可比较其计算耗时与路径长度，并观察倒车怎样改善狭窄空间中的可达性。完整绕障规划还需要碰撞检测与地图搜索。

论文：[Accelerated Reeds–Shepp and Underspecified Reeds–Shepp Algorithms for Mobile Robot Path Planning](https://doi.org/10.1109/TRO.2025.3554406)（IEEE T-RO，2025）。

### F1TENTH Gym：Ackermann 车辆仿真

[F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym) 提供车辆运动、激光观测和赛道仿真环境。与可以原地转向的机器人仿真相比，它更适合观察转向、速度和车辆尺寸怎样影响轨迹。

可用它比较路径跟踪、MPPI 或 MPC，并通过重复相同起点和障碍设置分析参数变化。对于 R680，可借鉴其车辆仿真与控制评估接口；应替换赛车默认参数，匹配本车尺寸、转向限制和动力学，避免把赛道成绩直接当作导航能力。

论文：[F1TENTH: An Open-Source Evaluation Environment for Continuous Control and Reinforcement Learning](https://proceedings.mlr.press/v123/o-kelly20a.html)（PMLR 123，2020）。

## 多机器人与协同建图

### m-explore-ros2：前沿探索与地图合并

[m-explore-ros2](https://github.com/robo-friends/m-explore-ros2) 提供基于占据栅格的前沿探索和多机器人地图合并。前沿是已知自由空间与未知区域的交界，选择这些位置作为目标，可以逐步扩大已知地图。

它适合作为自主探索的入门基线，先观察前沿提取、目标选择和失败目标处理，再扩展到多机。R680 可复用现有地图与 Nav2，主要对接目标与车辆可达性。多机扩展需要建立共同坐标系，并分别评估地图配准误差和协同定位精度。

### Swarm-SLAM：受通信限制的协同 SLAM

[Swarm-SLAM](https://github.com/mistlab/Swarm-SLAM) 是 ROS 2 协同 SLAM 系统，涉及跨机器人回环检测和通信预算分配。跨机器人回环建立不同轨迹之间的约束，使各自地图能够放到共同参考系中。

它适合研究机器人之间交换什么信息、何时交换，以及带宽限制怎样影响地图精度。可从两段有重叠区域的记录开始，比较独立建图与协同建图的误差和通信量。用于 R680 时，需要选择匹配的视觉输入，并评估学习描述子在红外图像上的效果。

论文：[Swarm-SLAM: Sparse Decentralized Collaborative Simultaneous Localization and Mapping Framework for Multi-Robot Systems](https://doi.org/10.1109/LRA.2023.3333742)（IEEE RA-L，2024）。

### riMESA：鲁棒增量分布式优化

[riMESA](https://github.com/rpl-cmu/riMESA) 针对协同 SLAM 提供鲁棒的增量分布式图优化。它处理机器人之间共享的测量约束，并考虑错误回环对整体结果的影响。

适合从预先构造的位姿图入手，固定错误回环数量和通信中断安排，比较轨迹误差、更新耗时和交换数据量。这样可以先研究优化后端，而无需同时搭建多台机器人的感知系统。项目提供优化器接口，传感器前端与消息传输需要另行配套。

论文：[riMESA: Consensus ADMM for Real-World Collaborative SLAM](https://doi.org/10.1109/TRO.2026.3706569)（IEEE T-RO，2026）。

### iMESA：分布式优化对比基线

[iMESA](https://github.com/rpl-cmu/imesa) 是 riMESA 的前序方法，研究协同 SLAM 中随新观测持续到来的分布式优化。各机器人保留本地估计，通过共享信息逐步改善共同变量的一致性。

它适合作为后端对比基线：使用相同测量图与通信安排，对照集中式优化、iMESA 和 riMESA，观察增量更新及异常约束处理的差别。其参考价值在于分离优化方法与感知前端各自的贡献。

论文：[iMESA: Incremental Distributed Optimization for Collaborative Simultaneous Localization and Mapping](https://doi.org/10.15607/RSS.2024.XX.085)（RSS，2024）。

### SlideSLAM：稀疏语义地标协同建图

[SlideSLAM](https://github.com/KumarRobotics/slide_slam) 使用稀疏语义地标描述环境并支持地图合并。物体级地标将大量感知数据压缩为较少的几何与类别信息，便于机器人之间交换和关联。

适合研究地图表达的精简程度与定位能力之间的取舍，并比较物体级匹配与低层特征匹配。可借鉴其语义地标构建和跨机器人关联流程。主实现使用 ROS 1，实验性 ROS 2 分支面向 Jazzy，迁入 Humble 的工作量较大。

论文：[SlideSLAM: Sparse, Lightweight, Decentralized Metric-Semantic SLAM for Multirobot Navigation](https://doi.org/10.1109/TRO.2025.3629786)（IEEE T-RO，2025）。

### LAMP：复杂环境中的协同建图系统

[LAMP](https://github.com/nebula-autonomy/lamp) 面向地下等复杂环境，组织多机器人定位、回环和地图优化。它展示了长距离、受通信限制的任务中，多个感知与优化模块怎样组成可运行系统。

适合参考系统分工与公开回放数据，分析局部里程计误差如何经过回环和多机器人约束得到修正。对 R680 更有价值的是系统架构与离线评估方式。工程依赖较重，包含 ROS 1 与旧版 Python 组件，整套迁移成本较高。

论文：[LAMP 2.0: A Robust Multi-Robot SLAM System for Operation in Challenging Large-Scale Underground Environments](https://doi.org/10.1109/LRA.2022.3191204)（IEEE RA-L，2022）。

### Kimera-Multi：分布式几何与语义地图

[Kimera-Multi](https://github.com/MIT-SPARK/Kimera-Multi) 将多机器人协同定位与稠密三维语义地图结合。输出既包含环境几何，也包含语义信息，使地图能够支持超出位姿估计本身的任务。

可参考其从局部感知、跨机器人关联到全局地图的模块划分，研究轨迹优化怎样影响最终地图的几何与语义一致性。与 riMESA 这类优化器相比，它更适合系统层面的学习。项目基于 ROS 1，依赖较多，适合作为进阶参考。

论文：[Kimera-Multi: Robust, Distributed, Dense Metric-Semantic SLAM for Multi-Robot Systems](https://doi.org/10.1109/TRO.2021.3137751)（IEEE T-RO，2022）。

## 语义地图与语言导航

### VLFM：用语言目标评价探索方向

[VLFM](https://github.com/bdaiinstitute/vlfm) 根据图像与语言目标的相关性构建价值地图，引导机器人寻找指定物体。例如搜索椅子时，探索方向除了考虑未知面积，还利用已观察场景与“椅子”的语义关联。

最值得借鉴的是语义价值如何影响前沿选择。可让这一模块提出地图目标，再由几何导航执行，以分别评估目标选择和运动能力。实机实现面向 Spot，依赖 RGB 与 GPU 模型服务，且已声明不再积极维护；接入 Nav2 属于需要重新评估的系统组合。

论文：[VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation](https://doi.org/10.1109/ICRA57147.2024.10610712)（ICRA，2024）。

### LeLaN：语言指定目标的近距离接近

[LeLaN](https://github.com/NHirose/learning-language-navigation) 根据语言描述与相机图像生成运动指令，使机器人接近可见目标。它更关注目标已经出现在视野中时，怎样从语言与视觉信息得到接近动作。

适合研究最后一段目标接近，可与 VLFM 的未知区域搜索分别评估。可借鉴其语言条件输入、策略推理与部署流程，并检查错误目标和不可行转向。实现使用 ROS 1 与 RGB，速度指令包含原地转向，需要转换为车辆可执行的轨迹。

论文：[LeLaN: Learning a Language-Conditioned Navigation Policy from In-the-Wild Video](https://proceedings.mlr.press/v270/hirose25b.html)（CoRL 2024，PMLR 于 2025 年出版）。

### ViNT / NoMaD：学习视觉导航与探索策略

[ViNT / NoMaD](https://github.com/robodhruv/visualnav-transformer) 的共享仓库提供视觉导航模型、训练流程和部署代码。ViNT 根据观测与目标图像预测视觉航点；NoMaD 通过目标掩码与扩散策略，将朝目标运动和无明确目标的探索联系起来。

适合参考图像目标、拓扑地图与局部动作之间的连接，也可比较不同策略在陌生环境中的行为。实机部署依赖 RGB、外部模型权重和 ROS 1；模型生成的航点或动作仍需符合底盘运动约束。

论文：[ViNT: A Foundation Model for Visual Navigation](https://proceedings.mlr.press/v229/shah23a.html)（CoRL，2023）；[NoMaD: Goal Masked Diffusion Policies for Navigation and Exploration](https://doi.org/10.1109/ICRA57147.2024.10610665)（ICRA，2024）。

### HOV-SG：分层开放词汇语义地图

[HOV-SG](https://github.com/hovsg/HOV-SG) 将环境组织为楼层、房间和物体层级，支持自然语言检索。开放词汇表示允许使用语言描述查询地图，不必只依赖建图时预先列好的类别。

可参考它怎样把空间层级与语义特征结合，为“去厨房找杯子”这类任务逐步缩小搜索范围。适合先用带位姿的 RGB-D 数据离线建图，检查房间和物体检索，再把检索位置转为导航目标。它提供语义地图能力，实际行走仍需几何导航配合。

论文：[Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation](https://doi.org/10.15607/RSS.2024.XX.077)（RSS，2024）。

### ConceptGraphs：物体级场景图与语言查询

[ConceptGraphs](https://github.com/concept-graphs/concept-graphs) 从 RGB-D 观测构建开放词汇三维物体图，并支持语言查询。它需要将不同视角下的同一物体合并，保存物体的几何、语义特征及关系。

适合关注物体实例和场景关系的任务，可借鉴跨帧关联、物体合并与语义查询模块。与 HOV-SG 的楼层、房间层级相比，这里更适合从物体图的构建入手。实际导航还需要把物体位置转换为附近可到达的观察或接近位置。

论文：[ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning](https://doi.org/10.1109/ICRA57147.2024.10610243)（ICRA，2024）。

### Habitat-Lab：语义导航评测环境

[Habitat-Lab](https://github.com/facebookresearch/habitat-lab) 提供室内导航任务、数据接口和评测流程，并与 Habitat-Sim 配合使用。固定场景、起点、目标与停止条件后，可以在同一组任务上比较不同语义策略。

适合先评估目标成功率、行走距离与路径效率，再进入实车适配。它也有助于区分识别目标失败与到达目标失败。默认动作不反映汽车转向约束；场景数据有独立使用条件，v0.3.4 之后的版本缺少官方积极维护。

平台论文：[Habitat: A Platform for Embodied AI Research](https://openaccess.thecvf.com/content_ICCV_2019/html/Savva_Habitat_A_Platform_for_Embodied_AI_Research_ICCV_2019_paper.html)（ICCV，2019）。

## 退化恢复与实验工具

### ScaleNav：学习导航失败后的恢复

[ScaleNav](https://github.com/KubeEdge4Robotics/ScaleNav) 是作者对 SCALE 方法的重新实现，利用可通行性与新颖度信息学习恢复行为。当当前观测与已知可行路线偏离时，系统尝试通过自纠正动作返回可继续导航的状态。

适合研究恢复策略的触发与选择：除了恢复成功率，还可观察误触发是否打断正常任务。它可作为固定回退规则之外的学习方法参考。实现基于 ROS 1 和彩色相机，模型与数据路径尚不完整，并含需要适配的旋转动作。

论文：[SCALE: Self-Correcting Visual Navigation for Mobile Robots via Anti-Novelty Estimation](https://doi.org/10.1109/ICRA57147.2024.10610847)（ICRA，2024）。

### slam-under-perturbation：可重复的 SLAM 扰动实验

[slam-under-perturbation](https://github.com/xiaohao-xu/slam-under-perturbation) 对图像、深度和时间对应关系施加扰动，用受控输入模拟感知退化。改变扰动强度后，可以观察算法从误差上升到跟踪失效的过程。

可借鉴其扰动生成与分级评估方式，在相同记录和随机种子下比较多个估计器。比起只汇报正常环境下的平均误差，这样更容易找到失效边界和恢复条件。时间偏移参数以帧为单位，分析延迟时应结合实际时间戳换算。

仓库对应论文：[Scalable Benchmarking and Robust Learning for Noise-Free Ego-Motion and 3D Reconstruction from Noisy Video](https://openreview.net/forum?id=Pz9zFea4MQ)（ICLR，2025）。

### evo：轨迹误差评估

[evo](https://github.com/MichaelGrupp/evo) 提供轨迹时间关联、对齐、绝对位姿误差和相对位姿误差计算。绝对误差反映轨迹对参考的整体偏离，相对误差更便于观察一段运动内的漂移。

适合统一比较不同里程计或 SLAM 方法，并将误差与路线中的转弯、遮挡等事件对应。比较时应固定时间关联、对齐方式和尺度处理，否则数字可能不具可比性。精度指标需要独立参考轨迹，地图视觉重合不能替代轨迹评估。

### rosbag2：记录与回放原始输入

[rosbag2](https://github.com/ros2/rosbag2) 记录 ROS 2 话题并按时间回放，让多个算法使用相同的相机、雷达、IMU 和轮速输入。它是将一次实车采集转化为多次可重复实验的基础工具。

值得参考的是原始输入、标定信息和时间关系的保存方式。评估替代算法时，应保留原始传感器消息，而不只记录原算法输出。录制的 QoS、时间戳和丢帧会影响回放结果，回放速度也可能改变算法的处理负载。

### diagnostics：传感器与节点状态监测

[diagnostics](https://github.com/ros/diagnostics) 为数据频率、消息时效和设备状态提供统一诊断接口。它可以将相机掉帧、IMU 数据停更或节点报告的异常，组织为可查看和汇总的状态。

可借鉴其诊断发布与聚合方式，为定位退化检测提供输入。应区分“消息仍在发布”与“估计仍然可靠”：前者可由频率监测判断，后者还需算法质量指标。阈值、告警持续时间和异常处理策略需要结合任务定义。

### PlotJuggler：时序数据与故障分析

[PlotJuggler](https://github.com/facontidavide/PlotJuggler) 用于查看和计算多路时序数据，支持加载记录或接入数据流。将轮速、IMU、视觉里程计、控制指令和诊断状态放在同一时间轴上，可以检查异常发生的先后关系。

例如出现路径跟踪抖动时，可同时查看目标转向、实际角速度和估计航向，判断问题先出现在控制、执行还是定位环节。它适合故障分析与参数调整；用于 Humble 时，应选择匹配的数据加载与流式插件。

## 相关章节

[VINS 原理](../06-sensors-navigation/39-vins-principles.md) · [视觉建图运行过程](../06-sensors-navigation/40-visual-runtime.md) · [Nav2 导航](../06-sensors-navigation/34-nav2-navigation.md) · [返回高级应用](index.md)
