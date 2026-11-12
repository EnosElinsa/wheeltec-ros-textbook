---
status: draft
---

# 第八篇：高级应用

仿真、多机、视觉和 AI 功能都建立在前面各篇的控制与感知链路之上。遇到基础问题时，先回到对应章节确认底盘、传感器和 ROS 2 接口，再启动应用节点。

[从第 50 章开始](50-gazebo-simulation.md)

## 8.1 仿真学习与实验

第一次接触机器人仿真，可先阅读[第 50 章：仿真与 Gazebo](50-gazebo-simulation.md)，了解数据回放、闭环仿真与实车实验的分工，以及不同研究任务为什么选择不同平台。

视觉导航部分按研究过程连续编排：[50.8 实验设计与评价方法](vision-simulation-lab.md)交代对照方案、场景和指标；[50.9 实验结果与分析](vision-simulation-results.md)解释实测结果与结论范围；[50.10 复现与证据附录](vision-simulation-reproducibility.md)保存运行命令、版本和原始记录。理解实验时可先读正文，需要复跑时再查附录。

## 8.2 开源项目参考

[第 54 章：开源项目与参考价值](54-open-source-projects.md)：按定位、建图、规划、多机器人、语义导航和评测介绍 66 个项目，列出算法、输入输出和运行条件。其中 17 个提供深度强化学习相关方法，覆盖人群避障、未知环境、车辆控制与多机器人协作。

[论文与开源项目目录](https://github.com/EnosElinsa/wheeltec-smart-car-literature/blob/main/OPEN_SOURCE_PROJECTS.md)提供代码和相关论文入口。论文库的 `INDEX.html` 支持按任务、方法、环境和年份筛选，并可对比 2—4 个项目。
