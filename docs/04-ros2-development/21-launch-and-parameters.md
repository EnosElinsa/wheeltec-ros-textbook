---
status: complete
---

# 21. Launch、参数与运行配置

## 21.1 学习目标

从正在使用的 Launch 文件追踪节点、参数文件和条件分支，安全修改车型、端口与传感器配置，并证明运行节点读到了新值。

## 21.2 适用范围

适用于 Python Launch 和 YAML 参数。旧 XML Launch 或 ROS 1 参数服务器见附录 A。

## 21.3 操作前检查

- 复制当前 Launch 和参数文件，记录哈希或日期。
- 确认实际加载的工作空间，不编辑同名备份。
- 停止依赖该参数的节点后再改关键端口和车型。

## 21.4 工作原理

Launch 描述一次运行需要启动哪些节点、传入哪些参数和命名空间。YAML 文件只是参数来源之一；Launch 内部默认值、命令行覆盖和节点代码默认值都可能改变最终结果。

## 21.5 操作步骤

定位入口：

```bash
ros2 pkg prefix turn_on_wheeltec_robot
ros2 pkg executables turn_on_wheeltec_robot
```

在源码中查参数文件引用：

```bash
rg -n 'wheeltec_params|parameters|yaml' <包源码目录>
```

修改前复制文件，然后只改一项。启动后验证运行值：

```bash
ros2 node list
ros2 param list <节点名>
ros2 param get <节点名> <参数名>
ros2 param dump <节点名>
```

车型、雷达、相机和串口参数要与第 6 章配置表对应。布尔值、数字和字符串保留正确 YAML 类型；缩进使用空格。

需要把顶层入口继续追到 `base_serial.launch.py`、EKF、车型 URDF、雷达和相机分支时，使用 [`turn_on_wheeltec_robot` 源码与启动链导读](turn-on-wheeltec-robot-source-walkthrough.md)。导读中的结构是追踪方法，仍应以当前工作空间文件为准。

## 21.6 验收标准

- 能从 Launch 入口追踪到实际参数文件。
- 修改只涉及一个可解释配置项。
- 运行节点的 `ros2 param get/dump` 证明新值已加载。
- 恢复备份后可回到原行为。

## 21.7 故障排查

| 现象 | 原因 |
|---|---|
| 文件改了但值没变 | 编辑了错误工作空间、Launch 使用另一文件或安装副本 |
| YAML 解析失败 | 缩进、冒号、Tab 或类型错误 |
| 参数存在但节点忽略 | 参数名/命名空间不匹配或代码未声明 |
| 同一参数被覆盖 | Launch、命令行和 YAML 多处赋值 |


!!! note "教材代码资源"
    本节使用的代码入口见[教材代码资源附录](../appendices/d-public-source-reference.md)。

## 章节导航

[上一章：节点、话题、服务与动作](20-nodes-topics-services-actions.md) · [返回本篇](index.md) · [下一章：TF、URDF 与 RViz](22-tf-urdf-rviz.md)
