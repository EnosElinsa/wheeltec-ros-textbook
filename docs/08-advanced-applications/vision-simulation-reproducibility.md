---
status: complete
---

# 50.10 实验复现与证据附录

本附录供复跑实验和核查结果时使用，集中保存环境、命令、原始记录索引与修订经过。理解研究问题和结论，可先阅读[实验设计](vision-simulation-lab.md)及[结果分析](vision-simulation-results.md)。以下身份对应 2026-11-12 的实验；重新构建或改变配置后，应建立新记录，不能沿用旧实验身份。

## 50.10.1 环境与版本身份

| 项目 | 实际设置 |
| --- | --- |
| 远程主机 | Ubuntu 24.04.5、AMD EPYC 9554、188 GiB 内存、RTX 4090 D |
| 隔离运行环境 | Ubuntu 22.04、ROS 2 Humble、Gazebo Fortress 6.18.0、Python 3.10 |
| 估计后端 | RTAB-Map strategy 9、固定 ROS 2 VINS 移植版、独立 Ceres 2.1 |
| 首轮代码 | [1e518ba9](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/1e518ba923e6876254ae0eddddab5ac52d42798c/ros2/navigation/vision-nav)；[对应 CI](https://github.com/EnosElinsa/wheeltec-ros-source-reference/actions/runs/43210363593) |
| 最终代码 | [d6092f1a](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/d6092f1a270ec64b24c11f8c1c9b1c8d5d473043/ros2/navigation/vision-nav) |
| VIO 关键输入修正 | [75026789](https://github.com/EnosElinsa/wheeltec-ros-source-reference/commit/750267894c90516f21debac62364c34753de3939) |
| 首轮计算资源 | EuRoC 每序列绑定 8 个 CPU；Gazebo 正式故障会话绑定 32 个 CPU、内存上限 24 GiB；例外见逐次会话记录 |
| 隔离要求 | 独立 ROS 域、数据库与结果目录；仿真不启动串口或物理 RealSense |

实验镜像身份为 `sha256:7d3475065612914a4373817087fdd8c63ee653a63aee356adbdb9f28e559bc0b`。从提交 Dockerfile 完整重建的镜像为 `sha256:be84532f7ecd6f19cf5ff680fde22c2f1e7e51fc462ae8ea9969c61f38926125`，通过 4 项 ROS 集成测试、原生执行器 CTest 1/1 及 30 s 无界面渲染会话，并正常关闭。[镜像记录](simulation-results/final-image-2026-11-12.json)保存构建与包清单证据。重建验证不替换原实验镜像身份。

固定 VINS 移植版使用 `ceres::Manifold`，系统 Ceres 2.0 不满足接口。构建脚本先在实验目录安装固定的 Ceres 2.1，再编译 VINS 与 RTAB-Map；主机原有 ROS、驱动和系统 Ceres 保持原安装。构建日志、补丁与动态库依赖保存在实验目录。

## 50.10.2 复跑入口

### 50.10.2.1 构建独立实验环境

以下命令在 Ubuntu 远程机执行，要求 Docker 与可用的 NVIDIA CDI 配置。首次安装及代理配置见固定版本源码的 [containers 说明](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/d6092f1a270ec64b24c11f8c1c9b1c8d5d473043/ros2/navigation/vision-nav/containers)。GPU 编号和 CPU 集合需按主机实际可用资源调整。

```bash
cd wheeltec-ros-source-reference/ros2/navigation/vision-nav/containers
export SIM_ROOT="$HOME/wheeltec_vision_sim"
mkdir -p "$SIM_ROOT"/{source,data,results}
cp -a . "$SIM_ROOT/containers"
for package in wheeltec_vision_nav wheeltec_tf_guard wheeltec_vision_benchmark wheeltec_vision_sim wheeltec_sim_actuator; do
  cp -a "../$package" "$SIM_ROOT/source/"
done
sudo docker build -t wheeltec-vision-sim:humble-20261112 .
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" bash build.sh
```

显式传入实验目录，避免 `sudo` 改变用户目录后挂载到其他位置。同次实验的节点放在同一容器中，首次使用容器内回环通信，并核实速度接口与实车隔离。设备查询成功后，还需以实际图像和深度检查无界面渲染，不能只以 `nvidia-smi` 成功作为传感器就绪证据。

### 50.10.2.2 EuRoC 单次与批量运行

数据保留 `mav0/cam0`、`cam1`、`imu0` 和 `state_groundtruth_estimate0` 的原始结构。下载来源明确记录；本地 SHA256、ZIP CRC 和文件检查可验证本地完整性，不能称为官方真实性认证。每次输出到新目录。

```bash
python3 fetch_euroc.py --destination "$SIM_ROOT/data" --sequence MH_01_easy
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 bash run.sh \
  ros2 run wheeltec_vision_benchmark validate_euroc \
  --dataset /work/data/MH_01_easy --output /work/results/mh01-validation --mode vio
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 bash run.sh \
  ros2 launch wheeltec_vision_benchmark euroc.launch.py \
  dataset:=/work/data/MH_01_easy output:=/work/results/mh01-vio-001 mode:=vio
```

`mode:=stereo` 选择纯双目 VO。单次结果包括身份清单、轨迹、视觉状态、播放记录、指标与图表。批量入口 `run_euroc_suite.sh` 用于三个序列、两种模式各三次运行；参数变更后的组需要新的身份记录。除了误差，须核查覆盖率、缺失尾部、数据年龄和正常退出状态。

### 50.10.2.3 建图、导航与故障会话

先建图并正常停止，再用同一场景、车模和相机配置加载数据库导航。`baseline`、`stereo`、`vio` 分别对应正文三种估计方案。

```bash
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 bash run.sh \
  ros2 launch wheeltec_vision_sim sim.launch.py estimator:=baseline mode:=mapping \
  database_path:=/work/results/room.db output:=/work/results/mapping-001
# 正常停止建图后运行：
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 bash run.sh \
  ros2 launch wheeltec_vision_sim sim.launch.py estimator:=baseline mode:=localization \
  database_path:=/work/results/room.db output:=/work/results/localization-001
```

批量会话入口统一启动、检查和关闭整组进程：

```bash
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 WHEELTEC_SIM_CPUS=32 \
  WHEELTEC_SIM_CPUSET=0-31 ROS_DOMAIN_ID=88 \
  bash run.sh python3 /work/containers/run_sim_trial.py \
  --output /work/results/mapping-suite-001 --database /work/results/room-suite.db \
  --mode mapping --estimator baseline --scenario all
```

导航使用 `--mode localization` 和已保存的地图。场景定义和其余参数见[仿真包说明](https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/d6092f1a270ec64b24c11f8c1c9b1c8d5d473043/ros2/navigation/vision-nav/wheeltec_vision_sim)。会话的命令、日志、退出码和实际判据分别保存，不能只根据进程退出码认定算法或导航通过。

CPU 配额控制总计算用量，CPU 亲和性限制可见核心；图像库线程数也需记录。并行会话使用不同 CPU 集合、ROS 域和数据库。一次会话的三次检查不重置车辆，独立起点实验需另行启动世界。

### 50.10.2.4 30 分钟静止长测

```bash
sudo env WHEELTEC_SIM_ROOT="$SIM_ROOT" WHEELTEC_SIM_GPU=1 WHEELTEC_SIM_CPUS=16 \
  WHEELTEC_SIM_CPUSET=0-15 ROS_DOMAIN_ID=92 \
  bash run.sh python3 /work/containers/run_soak_trial.py \
  --output /work/results/stationary-load-001 --duration 1800 --estimator baseline
```

该入口创建新地图、不发送运动指令，并在结束时关闭整组进程。使用修正后的 schema 2 记录器逐回调记录安全指令、轮速和时钟，周期保存资源与健康状态。保留异常及提前退出摘要；健康快照与原始输入接收证据分别解释。

## 50.10.3 输入、坐标与计时核对

EuRoC 时间以原始整数纳秒读取，保留左右图像配对；整流图像、标定与光学坐标必须一致。相机、IMU 与参考传感器的完整安装变换参与评分，参考传感器 YAML 原文及哈希随结果保存。MH05 的一帧边界排除仍计入原始覆盖率分母。

IMU 噪声转换清单保存源单位、采样频率、转换策略和派生参数。当前积分器的两端测量注入与每步零偏注入采用近似离散模型，共享端点及高阶相关性未完整建模，不能把生成配置称为实车噪声标定。

仿真轮速由关节观测生成，世界位姿仅用于评分。`odom → base_footprint` 保持唯一发布者，RTAB-Map 提供 `map → odom`；RViz 的初始恒等变换不作为可信定位证据。VIO 删除 EKF 中全部 `imu0*` 参数以避免重复融合，同时使用独立的 `require_wheel/require_imu` 监测关键输入，`wheel_backup=false` 禁止视觉降级。

普通合成相机不具有 D435C 的投影交替元数据，使用同步输入适配并记录合成来源。避障使用原始有效深度，保留观测年龄。仿真节点跟随仿真时钟，保护定时器使用单调墙钟。慢速诊断要报告实时因子，不关闭保护来换取通过。

## 50.10.4 修订与失败记录

### 50.10.4.1 输入处理与试验准备

早期 Humble Python 消息对普通 `bytes` 图像载荷逐字节检查，后改用内容相同的类型化数组；图像像素、编码和时间戳不变。点云逐点 Python 转换改为结构化 NumPy 批量读取，原始观测年龄继续参与保护。精确时间 TF 暂缺时，仅在原始接收和采样期限内短暂缓存，新的非法观测清除待处理旧帧。

动态 TF 队列积压曾导致保护停车后无法恢复，改为有界队列后恢复检查通过。早期稀疏纹理引起 RGB-D 低内点丢失，当前纹理场景重新运行的结果单独保存；不能把场景改善后的通过归为低纹理通过。早期场景日志保留在远程实验目录。

导航准备增加等待全部七个生命周期节点 ACTIVE，并在每项试验前连续 0.5 s 检查健康、轮速、真值、五路接触和前向走廊；45 s 内未就绪则失败。Gazebo 服务等待期间继续接收观测。准备阶段单独标记，活动试验中的证据要求不放宽。

地图与真值的初始对齐使用首次静止观测的相同时间，允许有界等待对应 TF，不以最新 TF 替代。旧运行中出现任务成功而真值终点偏差约 0.6 m，被正确判失败；启用 Humble 的 `always_reload_bt_xml` 后，新目标重建行为树节点，避免沿用上一目标的节流与动作状态，黑板仍由 Nav2 管理。

### 50.10.4.2 VIO 最终保护复测

早期 `wheel_backup=false` 同时关闭关键输入订阅，造成 IMU 先经 VIO 停输出再触发保护。修正后直接监测轮速与 IMU。16 CPU 建图复测中，执行器试验同时发生 VO 断流和上层零速，23/24 的失败结果保留；32 CPU 复测为 24/24。最终导航为 24/24。这些运行的资源和版本分别保存，未合并成同条件重复。

### 50.10.4.3 长测记录器的失效与重跑

| 记录 | 实际观察 | 保留与处理方式 |
| --- | --- | --- |
| 旧 schema 1，约 1800.001 s | 35999 条零速；间隔 P95/P99 52.08/54.18 ms，最大 60.75 ms；1793 个约 1 Hz READY 快照 | 开窗时清空最后接收状态，约 0.3 ms 的首快照误报缺失；原 `passed=false` 保留，连续接收证据也不足 |
| 旧 schema 1 资源 | 忙碌核数中位数/P99 6.33/6.58；RSS 首尾约 3.49/4.07 GiB；快照视觉年龄 P95/P99 97.46/108.05 ms | 未采温度、未逐帧测有效帧率；不作为最终通过证据 |
| schema 2 首次 30 s 抽查 | 将旧健康快照外推为源未更新，产生误判 | 失败摘要保留，改为按实际收到的快照判断源状态 |
| 修正后 30 s 抽查 | 600 条安全指令、1362 个轮速、130 个 READY 回调，无失败；含窗口首尾最大指令覆盖间隔 57.61 ms | 通过后再验证独立会话启动与关闭 |
| 独立会话 30 s 抽查 | 启动进程持续存活，结束仅发送 SIGINT，全部进程及地图正常关闭 | 无 TERM/KILL 升级，再开展正式长测 |
| 最终独立长测 | 1800.006 s，记录与会话均通过 | 正文采用此组结果，旧结果不覆盖 |

## 50.10.5 原始证据索引 {#evidence-index}

Git 仓库收录紧凑 JSON 与必要图表，完整图像、数据库、构建产物和原始日志保留在实验目录。JSON 中的运行身份和哈希用于关联对应产物。下表同时保留通过、失败和修正前结果。

| 实验或证据 | 记录入口 |
| --- | --- |
| EuRoC 原配置 18 次 | [逐次评分](simulation-results/euroc-2026-11-12.json) |
| 新噪声配置 MH01 诊断 | [三次诊断](simulation-results/euroc-noise-2026-11-12.json) |
| 新噪声配置三序列 9 次 | [完整摘要](simulation-results/euroc-noise-three-sequence-2026-11-12.json) |
| RGB-D、双目 VO、VIO 首轮建图 | [RGB-D](simulation-results/mapping-baseline-2026-11-12.json)；[双目 VO](simulation-results/mapping-stereo-2026-11-12.json)；[VIO](simulation-results/mapping-vio-2026-11-12.json) |
| 三方案首轮导航 | [RGB-D](simulation-results/localization-baseline-2026-11-12.json)；[双目 VO](simulation-results/localization-stereo-2026-11-12.json)；[VIO](simulation-results/localization-vio-2026-11-12.json) |
| 首轮六个闭环会话 | [命令、资源、日志与退出身份](simulation-results/sessions-2026-11-12.json) |
| 最终 VIO 建图：16 CPU 失败、32 CPU 通过 | [失败](simulation-results/mapping-vio-required-inputs-failed-2026-11-12.json)；[复测](simulation-results/mapping-vio-required-inputs-2026-11-12.json) |
| 最终 VIO 导航及会话身份 | [导航](simulation-results/localization-vio-required-inputs-2026-11-12.json)；[会话](simulation-results/vio-required-inputs-sessions-2026-11-12.json) |
| 独立关键输入 ROS 测试 | [直接响应测量](simulation-results/ros-critical-inputs-2026-11-12.json) |
| 旧 schema 1 长测 | [原失败与派生统计](simulation-results/stationary-2026-11-12.json) |
| schema 2 抽查及修正 | [旧快照外推失败](simulation-results/stationary-schema2-smoke-2026-11-12.json)；[修正后抽查](simulation-results/stationary-schema2-smoke-corrected-2026-11-12.json) |
| 独立会话抽查与正式长测 | [30 s](simulation-results/stationary-session-schema2-smoke-2026-11-12.json)；[1800 s 最终记录](simulation-results/stationary-final-2026-11-12.json) |
| 镜像构建与重建验证 | [身份记录](simulation-results/final-image-2026-11-12.json) |

RGB-D/VIO 首轮建图的安全指令接收年龄 P95 分别为 45.9/46.8 ms，P99 为 51.0/52.4 ms，实时因子中位数约 0.895。故障注入期旧观测也进入年龄统计，不能将其作为健康状态传感器延迟。场景布局来自固定版本的 [model.py](https://github.com/EnosElinsa/wheeltec-ros-source-reference/blob/d6092f1a270ec64b24c11f8c1c9b1c8d5d473043/ros2/navigation/vision-nav/wheeltec_vision_sim/wheeltec_vision_sim/model.py)，任务与临时障碍来自 [mission_runner.py](https://github.com/EnosElinsa/wheeltec-ros-source-reference/blob/d6092f1a270ec64b24c11f8c1c9b1c8d5d473043/ros2/navigation/vision-nav/wheeltec_vision_sim/wheeltec_vision_sim/mission_runner.py)。图 50.1 据模型几何绘制，是场景示意图。

## 50.10.6 软件检查与实车待验项目

代码与工具的既有本地复核为 692 项通过、8 项按 ROS/POSIX 环境跳过；Linux/Windows Python 3.10、3.12 及 Humble CI 已通过。隔离 Humble 环境的关键输入集成测试为 5 项通过、耗时 19.23 s；POSIX 会话退出测试 7 项、原生执行器 CTest 1/1 通过。五个本地 ROS 包已构建，无界面图像、深度、IMU、关节、五路接触与独立真值均实际输出。

这些软件检查为对应版本的实现证据，不作为定位精度、导航可靠性或实车制动的替代指标。仍需完成 VIO 全程稳定性、独立场景导航、障碍清除、行驶负载和实车标定、同步、失联停车。实车操作见[第 41 章](../06-sensors-navigation/41-visual-operation.md)，最终系统验收见[第 59 章](../10-deployment-maintenance/59-system-acceptance.md)。

[返回：50.9 实验结果](vision-simulation-results.md) · [返回：50 仿真与 Gazebo](50-gazebo-simulation.md)
