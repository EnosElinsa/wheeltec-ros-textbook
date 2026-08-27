# C++ 发布与订阅实验

该包使用 `rclcpp` 创建两个可执行文件：

- `talker` 每 500 ms 向 `/course/chatter` 发布一条字符串；
- `listener` 订阅同一话题并输出收到的内容。

完整构建、运行与验收步骤见[实验总说明](../README.md)。
