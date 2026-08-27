# ROS 2 发布与订阅配套实验

这里包含两个功能相同、可以互相通信的 ROS 2 功能包：

- [`cpp_pubsub`](cpp_pubsub/)：使用 `rclcpp` 编写；
- [`py_pubsub`](py_pubsub/)：使用 `rclpy` 编写。

两个包都提供 `talker` 和 `listener`，并使用 `std_msgs/msg/String` 类型的
`/course/chatter` 话题。可以用 C++ 发布、Python 订阅，也可以反过来运行。

## 适用环境

持续集成以 ROS 2 Humble 和 Ubuntu 22.04 为构建基线。其他仍受支持的 ROS 2
发行版需要自行重新构建并验证，不应直接假定二进制兼容。

## 构建

把两个包复制到同一个工作空间：

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
```

## 运行

终端 A：

```bash
source ~/wheeltec_course_ws/install/setup.bash
ros2 run cpp_pubsub talker
```

终端 B：

```bash
source ~/wheeltec_course_ws/install/setup.bash
ros2 run py_pubsub listener
```

订阅端持续显示 `C++ says hello` 消息即表示跨语言通信成功。按 `Ctrl+C`
停止节点。随后可以交换语言再次测试。

## 验收

```bash
ros2 node list
ros2 topic info /course/chatter --verbose
ros2 topic echo /course/chatter --once
```

至少应看到一个发布者、一个订阅者，消息类型为 `std_msgs/msg/String`。

## 发布边界

这些文件是为教材独立编写并清理过的教学代码，不是产品工作空间、底盘源码或
固件的完整副本。与具体主控、控制板和 ROS 发行版绑定的完整工程仍应按原目录、
版本和哈希单独保存。此目录采用 [MIT License](LICENSE)。
