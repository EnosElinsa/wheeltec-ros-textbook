---
status: complete
---

# 第 33 章补充说明：坐标计算与相关方法

[第 33 章](../33-relocalization-map-dependence.md)按使用已有地图、在线建立地图和无显式地图三条路线，讨论导航的地图需求及定位恢复条件。本页补充位姿组合、导航坐标恢复的计算，并列出其他研究对正文的补充作用。参考编号与正文一致，重定位证据见[论文证据表](relocalization-evidence.csv)和[核查说明](relocalization-reference-audit.md)，在线导航证据见[补充核查](online-navigation-reference-audit.md)。

## 位姿与坐标计算

地图位姿可以由参考位姿与相对位姿组合得到。导航系统随后用地图位姿计算全局修正，使连续局部运动重新关联到原地图。两次计算使用的参考不同，下面分别说明。

### 从参考位姿得到当前位姿 {#pose-composition}

设原地图坐标系为 $M$，参考关键帧坐标系为 $K$，机器人机体坐标系为 $B$。记 ${}^{A}T_B$ 为将 $B$ 中坐标转换到 $A$ 中坐标的变换，其中包括旋转与平移。在三维情况下，其形式为：

$$
{}^{A}T_B=
\begin{bmatrix}
{}^{A}R_B & {}^{A}\mathbf p_B\\
\mathbf 0^{\mathsf T} & 1
\end{bmatrix}.
$$

旋转矩阵 ${}^{A}R_B$ 将轴向转换到 $A$，平移向量 ${}^{A}\mathbf p_B$ 给出 $B$ 原点在 $A$ 中的位置。例如，在平面示意中，关键帧位于地图的 $(10,4)$，朝向地图正 $y$ 方向，其三维表示可写为：

$$
{}^{M}R_K=
\begin{bmatrix}
0&-1&0\\
1&0&0\\
0&0&1
\end{bmatrix},
\qquad
{}^{M}\mathbf p_K=
\begin{bmatrix}10\\4\\0\end{bmatrix}\mathrm{m}.
$$

若机器人位于关键帧正前方 $2\,\mathrm{m}$，朝向相同，取关键帧的 $x$ 轴为前向，则相对旋转与平移为：

$$
{}^{K}R_B=
\begin{bmatrix}
1&0&0\\
0&1&0\\
0&0&1
\end{bmatrix},
\qquad
{}^{K}\mathbf p_B=
\begin{bmatrix}2\\0\\0\end{bmatrix}\mathrm{m}.
$$

把相对位姿与关键帧地图位姿组合，即可得到：

$$
{}^{M}T_B={}^M T_K\,{}^K T_B,
\qquad
{}^{M}\mathbf p_B={}^M R_K\,{}^K\mathbf p_B+{}^M\mathbf p_K
=\begin{bmatrix}10\\6\\0\end{bmatrix}\mathrm{m}.
$$

组合过程先把相对位移换成地图轴向，再加上关键帧的位置。BEVPlace++ 在平面位姿求解后使用的就是这种组合关系。[P19] 例中数值只用于说明坐标计算。

### 用地图位姿恢复导航坐标 {#map-odom-recovery}

局部里程计坐标系记为 $O$。里程计提供机器人位姿 ${}^{O}T_B(t)$，重定位提供地图位姿 ${}^{M}T_B(t)$。在同一时刻计算：

$$
{}^{M}T_O(t)={}^{M}T_B(t)\left({}^{O}T_B(t)\right)^{-1}.
$$

该结果给出 `map → odom` 修正。后续里程计仍持续更新 `odom → base_link`，两段关系组合后即可得到新的地图位姿。REP-105 要求 `odom` 中的位姿连续，允许 `map` 中的位姿因全局修正而发生跳变。[S03]

参与计算的两项机器人位姿必须对应同一时刻。求解较慢时，先用结果时间戳处的里程计位姿计算修正，再由后续里程计得到当前地图位姿。若求解器输出相机或雷达位姿，应先通过固定安装外参转换为机体位姿，再进行组合。

里程计进程重新启动时，还需检查 $O$ 是否已经改变。旧修正不能直接沿用到新的里程计原点，系统需要重新建立与地图的关系。若多个定位模块并行运行，应明确哪个模块负责发布全局修正。

## 其他相关方法的作用与边界 {#related-methods}

正文分别说明三条路线的运行流程。下表补充已有参考路线中的检索、求解和地图组织方法，便于按具体环节继续阅读。

| 研究 | 补充哪项问题 | 做法与适用边界 |
|---|---|---|
| UniLGL [P03] | 检索之后如何恢复三维位姿 | 先定义查询点云与数据库之间的地点检索，再构建三维全局位姿恢复方法。数据库点云仍需与地图坐标关联。 |
| LiteFT-PR [P10] | 传感器质量变化时如何改进候选检索 | 通过多模态特征、质量估计和蒸馏提高地点识别鲁棒性。PR、Recall@1、F1-max 评价检索表现，完整定位还需检查几何位姿。 |
| CMRNext [P05] | 相机怎样使用 LiDAR 地图 | 根据初始位姿把地图投影为深度图，与当前图像匹配后求解。投影依赖内参和初值，未知位置启动需另有候选来源。 |
| OneShot [P18] | 单次扫描怎样连接到地图坐标 | 保存参考片段描述子与质心位置，通过片段检索和几何一致性求解三维位姿。单次查询仍使用已有参考，论文定位率也不能直接视为本车任务恢复率。 |
| 三维地图表示比较 [P06] | 地图存储形式能否替换 | 比较点云、网格和神经辐射场生成参考视图的方式。已知参考视图位姿与深度负责建立地图坐标联系。 |
| 对象级语义关系 [P08] | 物体变化时怎样比较场景 | 用物体及其关系构成场景图，寻找相似场景。检索评价中使用位姿门限，不等于已经另行求解当前图像的完整连续位姿。 |
| OMCL [P09] | 语言信息能帮助哪一环节 | 在具有空间位置的八叉树地图中保存视觉语言特征，用自然语言提示缩小粒子初始化范围，后续仍需地图尺度的里程计与观测更新。 |
| 历史观测地图框架 [P16] | 同一批参考能否服务不同任务 | 将带位姿和时间戳的观测作为基础，再生成定位或避障所需地图。按需读取是可采用的工程组织方式，仍需实现候选搜索与求解。 |
| LiDAR Teach, Radar Repeat [P17] | 固定路线能否减少全区域建图 | 保存示教路线节点，重复运行时用雷达与节点匹配。恢复受示教覆盖限制，使用另一张导航地图时还需建立坐标对齐。 |

上述方法可以处于同一系统的不同环节。例如，地点识别算法提供候选，几何求解器给出位姿，验证模块决定是否接受。评价整套系统时，应分别记录各环节失败的原因，避免把某个模块的检索准确率直接当作任务恢复率。

## AMCL 的实现核对项 {#amcl-implementation}

正文讨论的 AMCL 能力对应 Nav2 Humble 的固定提交，具体来源见[AMCL 源码][S01]与[默认参数][S02]。实际部署可能使用不同版本和配置，需要核对本车软件。

| 核对项 | 固定版本中的行为 | 对恢复过程的影响 |
|---|---|---|
| `reinitialize_global_localization` | 通过 `globalLocalizationCallback` 重新初始化粒子 | 提供全局重新初始化入口，失效检测与调用时机仍需设计 |
| `uniformPoseGenerator` | 在地图自由空间采样位置，并采样方向 | 初始搜索依赖可用地图与粒子覆盖 |
| `recovery_alpha_fast`、`recovery_alpha_slow` | 声明默认值均为零 | 不能仅凭使用 AMCL 就假定自主恢复参数已启用 |
| RViz 的 `2D Pose Estimate` | 由人提供近似位姿分布 | 验证的是给定初始区域后的收敛，需另外测试未知位置搜索 |
| 局部代价地图 | 默认使用 `odom` 与滚动窗口 | 只维护周边障碍，仍需定位和全局路径连接原地图目标 |

全局重新初始化之后，系统还需要判断粒子是否稳定收敛到正确位置，并在导航恢复前处理错误候选与超时。软件接口的存在和完整恢复流程的实现，应分别验收。

[P03]: ../33-relocalization-map-dependence.md#p03
[P05]: ../33-relocalization-map-dependence.md#p05
[P06]: ../33-relocalization-map-dependence.md#p06
[P08]: ../33-relocalization-map-dependence.md#p08
[P09]: ../33-relocalization-map-dependence.md#p09
[P10]: ../33-relocalization-map-dependence.md#p10
[P16]: ../33-relocalization-map-dependence.md#p16
[P17]: ../33-relocalization-map-dependence.md#p17
[P18]: ../33-relocalization-map-dependence.md#p18
[P19]: ../33-relocalization-map-dependence.md#p19
[S01]: ../33-relocalization-map-dependence.md#s01
[S02]: ../33-relocalization-map-dependence.md#s02
[S03]: ../33-relocalization-map-dependence.md#s03
