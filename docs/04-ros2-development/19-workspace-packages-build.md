---
status: complete
---

# 19. 工作空间、功能包与构建

## 19.1 学习目标

在不污染当前可用环境的前提下安装依赖、构建指定包、加载结果，并能区分源码错误、依赖缺失和环境叠加问题。

## 19.2 适用范围

适用于使用 `colcon` 的 ROS 2 工作空间。不同镜像可能有规定的编译顺序或需要先停用冲突包，应以当前源码说明为准。

## 19.3 操作前检查

- 已确认主工作空间和 ROS 发行版。
- 备份 `src` 中准备修改的文件。
- 保存上一次可运行的 `install/` 或系统镜像恢复方式。
- 系统时间正确，网络和软件源可用。

## 19.4 工作原理

### 工作空间的目录关系

`src/` 存源码，`build/` 存构建中间文件，`install/` 存可加载结果，`log/` 存构建日志。终端执行 `source install/setup.bash` 后，ROS 才会优先看到这次构建的包。

### 环境叠加与查找顺序

ROS 2 环境通常分两层加载。`source /opt/ros/$ROS_DISTRO/setup.bash` 先加入系统安装的 ROS 2；`source <工作空间>/install/setup.bash` 再把当前工作空间叠加到系统环境之上。后加载的工作空间可以覆盖同名包，因此“正在编辑的源码”和“当前终端实际找到的包”未必相同。

`AMENT_PREFIX_PATH` 记录当前终端搜索 ROS 2 安装前缀的顺序。叠加多个工作空间后，应同时检查这个变量和 `ros2 pkg prefix <包名>`，不要只根据当前目录猜测节点来自哪里。

### 符号链接与构建边界

`--symlink-install` 会为部分 Python、Launch 和配置资源建立符号链接，便于迭代，但 C/C++ 修改仍需重新构建。不能据此断言所有 YAML 修改都永远无需构建；包的安装规则决定实际行为。

## 19.5 操作步骤

### 安装依赖与构建

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd <工作空间>
rosdep install --from-paths src --ignore-src -r -y
```

先构建目标包和依赖：

```bash
colcon build --symlink-install --packages-up-to <包名>
```

### 加载与验证

成功后在新终端加载：

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source <工作空间>/install/setup.bash
printenv AMENT_PREFIX_PATH | tr ':' '\n'
ros2 pkg prefix <包名>
```

在新终端按固定顺序加载环境。不要在一个长期使用的终端中反复加载不同工作空间；残留的搜索路径会让回滚结果难以判断。

### 构建配套发布订阅实验

教材仓库提供两个独立功能包：[C++ 示例](https://github.com/EnosElinsa/wheeltec-ros-textbook/tree/main/examples/ros2-pubsub/cpp_pubsub)和 [Python 示例](https://github.com/EnosElinsa/wheeltec-ros-textbook/tree/main/examples/ros2-pubsub/py_pubsub)。把它们放进同一工作空间的 `src/` 后构建：

```bash
mkdir -p ~/wheeltec_course_ws/src
cd ~/wheeltec_course_ws/src
git clone --depth 1 https://github.com/EnosElinsa/wheeltec-ros-textbook.git
cp -r wheeltec-ros-textbook/examples/ros2-pubsub/cpp_pubsub .
cp -r wheeltec-ros-textbook/examples/ros2-pubsub/py_pubsub .
cd ..
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select cpp_pubsub py_pubsub
source install/setup.bash
ros2 pkg executables cpp_pubsub
ros2 pkg executables py_pubsub
```

两个包都应列出 `talker` 和 `listener`。不要把教材仓库整体放进 `src/`；这里只复制两个功能包，避免文档目录参与包发现。

### 处理构建失败

构建失败时先看第一条有效错误，再检查对应 `log/latest_build/<包名>/`。清理范围限定在出错包：

```bash
colcon build --packages-select <包名> --cmake-clean-cache
```

不要在不理解影响时删除整套 `src` 或全局安装包。

## 19.6 验收标准

- 目标包构建退出码为 0。
- 新终端加载后 `ros2 pkg prefix` 指向预期工作空间。
- 未加载工作空间时仍能回到系统或旧版本环境。
- 构建日志和安装的依赖有记录。
- 机器人功能的启动与话题验收通过，而不只是在编译终端看到 `Summary`。

## 19.7 故障排查

| 错误 | 处理 |
|---|---|
| package not found | 检查 source 顺序、包名和构建结果 |
| 缺头文件/库 | 用 rosdep 和发行版包源核对依赖 |
| CMake 缓存指向旧路径 | 只清理对应包缓存后重建 |
| Python 修改未生效 | 查实际导入路径、符号链接和已安装副本 |
| 全量构建互相冲突 | 使用 `--packages-up-to`，按项目要求处理冲突包 |

## 章节导航

[上一章：ROS 2 环境与源码版本选择](18-environment-and-source-selection.md) · [返回本篇](index.md) · [下一章：节点、话题、服务与动作](20-nodes-topics-services-actions.md)
