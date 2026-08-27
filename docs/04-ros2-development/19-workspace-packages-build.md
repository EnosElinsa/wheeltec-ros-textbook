---
status: complete
---

# 19. 工作空间、功能包与构建

## 本章目标

在不污染当前可用环境的前提下安装依赖、构建指定包、加载结果，并能区分源码错误、依赖缺失和环境叠加问题。

## 适用范围

适用于使用 `colcon` 的 ROS 2 工作空间。供应商镜像可能有规定的编译顺序或需先停用冲突包，应以当前源码说明为准。

## 开始前检查

- 已确认主工作空间和 ROS 发行版。
- 备份 `src` 中准备修改的文件。
- 保存上一次可运行的 `install/` 或系统镜像恢复方式。
- 系统时间正确，网络和软件源可用。

## 工作原理

`src/` 存源码，`build/` 存构建中间文件，`install/` 存可加载结果，`log/` 存构建日志。终端执行 `source install/setup.bash` 后，ROS 才会优先看到这次构建的包。

`--symlink-install` 会为部分 Python、Launch 和配置资源建立符号链接，便于迭代，但 C/C++ 修改仍需重新构建。不能据此断言所有 YAML 修改都永远无需构建；包的安装规则决定实际行为。

## 操作步骤

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd <工作空间>
rosdep install --from-paths src --ignore-src -r -y
```

先构建目标包和依赖：

```bash
colcon build --symlink-install --packages-up-to <包名>
```

成功后在新终端加载：

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source <工作空间>/install/setup.bash
ros2 pkg prefix <包名>
```

构建失败时先看第一条有效错误，不要只看末尾汇总。检查对应 `log/latest_build/<包名>/`。清理应局限于出错包：

```bash
colcon build --packages-select <包名> --cmake-clean-cache
```

不要在不理解影响时删除整套 `src` 或全局安装包。

## 结果验收

- 目标包构建退出码为 0。
- 新终端加载后 `ros2 pkg prefix` 指向预期工作空间。
- 未加载工作空间时仍能回到系统或旧版本环境。
- 构建日志和安装的依赖有记录。
- 机器人功能的启动与话题验收通过，而不只是在编译终端看到 `Summary`。

## 常见故障与处理

| 错误 | 处理 |
|---|---|
| package not found | 检查 source 顺序、包名和构建结果 |
| 缺头文件/库 | 用 rosdep 和发行版包源核对依赖 |
| CMake 缓存指向旧路径 | 只清理对应包缓存后重建 |
| Python 修改未生效 | 查实际导入路径、符号链接和已安装副本 |
| 全量构建互相冲突 | 使用 `--packages-up-to`，按供应商要求处理冲突包 |

## 章节导航

[上一章：环境与源码版本选择](13-environment-and-source-selection.md) · [返回本卷](index.md) · [下一章：节点、话题、服务与动作](15-nodes-topics-services-actions.md)
