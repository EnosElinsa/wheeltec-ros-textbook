---
status: draft
---

# 第八篇：高级应用

仿真、多机、视觉和 AI 功能都建立在前面各篇的控制与感知链路之上。遇到基础问题时，先回到对应章节确认底盘、传感器和 ROS 2 接口，再启动应用节点。

[从第 50 章开始](50-gazebo-simulation.md)

## 8.1 仿真学习与实验

第 50～53 章围绕同一套视觉导航实验展开：

| 章节 | 内容 |
| --- | --- |
| [50 仿真与 Gazebo](50-gazebo-simulation.md) | 实验方式、平台选择与建图导航的基本过程 |
| [51 视觉导航实验设计与评价方法](51-vision-simulation-lab.md) | 房间、车辆与传感器，建图动作，导航起点与目标，评价指标 |
| [52 视觉导航实验结果与分析](52-vision-simulation-results.md) | 实际轨迹、到点结果与 EuRoC 定位比较 |
| [53 视觉导航实验操作与复现](53-vision-simulation-reproducibility.md) | 运行步骤、原始数据、图表来源和补充测试 |

## 8.2 开源项目参考

[第 57 章：开源项目与参考价值](57-open-source-projects.md)：按定位、建图、规划、多机器人、语义导航和评测介绍 66 个项目，列出算法、输入输出和运行条件。其中 17 个提供深度强化学习相关方法，覆盖人群避障、未知环境、车辆控制与多机器人协作。

[论文与开源项目目录](https://github.com/EnosElinsa/wheeltec-smart-car-literature/blob/main/OPEN_SOURCE_PROJECTS.md)提供代码和相关论文入口。论文库的 `INDEX.html` 支持按任务、方法、环境和年份筛选，并可对比 2—4 个项目。
