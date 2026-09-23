# 术语表

本表统一教材中的中英文写法。首次出现的术语采用正式全称，后文使用表中约定的简称或中文名称。

| 术语 | 定义 | 讲解章节 |
|---|---|---|
| 机器人操作系统（Robot Operating System, ROS） | 面向机器人软件开发的开源框架、工具和工程约定。 | 第 1 章 |
| 机器人操作系统 2（Robot Operating System 2, ROS 2） | ROS 的第二代平台，面向跨平台、复杂网络和工程部署场景。 | 第 1 章 |
| 操作系统（Operating System, OS） | 管理处理器、内存、文件、网络和设备资源的软件。 | 第 3 章 |
| 安全外壳协议（Secure Shell, SSH） | 为远程终端提供加密连接的协议。 | 第 3 章 |
| 控制器局域网（Controller Area Network, CAN） | 用于控制器之间可靠交换短报文的现场总线。 | 第 7 章 |
| 传感器（Sensor） | 将环境或机器人自身状态转换为程序可读数据的设备。 | 第 2 章 |
| 激光雷达（Light Detection And Ranging, LiDAR） | 通过光束返回信号测量周围物体距离的传感器。 | 第 8 章 |
| 编码器（Encoder） | 将车轮或电机轴的转动转换为脉冲、角度或位置数据的器件。 | 第 8 章 |
| 惯性测量单元（Inertial Measurement Unit, IMU） | 测量加速度和角速度的传感器模块。 | 第 8 章 |
| 微控制器（Microcontroller Unit, MCU） | 集成处理器、存储器和输入输出接口、用于实时控制的小型计算机。 | 第 6 章 |
| STM32 | STMicroelectronics 的 32 位微控制器产品系列，常见于底盘控制板。 | 第 6 章 |
| 串行通信（Serial Communication） | 按顺序逐个传送数据位的通信方式。 | 第 7 章 |
| 串行端口（Serial Port） | 计算机与外部设备交换字节流的接口，在 Ubuntu 中常表现为 `/dev/ttyUSB0` 等设备文件。 | 第 7 章 |
| 波特率（Baud Rate） | 描述通信链路每秒传送符号数的参数；两端配置必须匹配。 | 第 7 章 |
| 电机驱动器（Motor Driver） | 按控制信号向电机提供和调节电流的功率电子部件。 | 第 9 章 |
| 通用串行总线（Universal Serial Bus, USB） | 连接计算机与外部设备的通用接口标准。 | 第 7 章 |
| 终端（Terminal） | 输入文字命令并查看程序输出的交互窗口。 | 第 3 章 |
| 文件（File） | 保存在存储设备中的数据或程序内容。 | 第 3 章 |
| 目录（Directory） | 用于组织文件和下级目录的路径节点。 | 第 3 章 |
| 进程（Process） | 程序运行后由操作系统创建的实例，具有独立的运行状态和资源。 | 第 3 章 |
| 命令解释器（Shell） | 读取终端命令并调用相应程序执行的软件。 | 第 3 章 |
| 固件（Firmware） | 存放在控制板非易失存储器中、上电后直接运行的程序。 | 第 6 章 |
| 实时操作系统（Real-Time Operating System, RTOS） | 按确定的优先级和时间约束调度任务的操作系统。 | 第 40 章 |
| FreeRTOS | 面向微控制器的实时操作系统内核和软件组件。 | 第 40 章 |
| 通用异步收发传输器（Universal Asynchronous Receiver-Transmitter, UART） | 以约定的波特率和帧格式逐位收发串行数据的硬件外设。 | 第 7 章 |
| 通用同步/异步收发传输器（Universal Synchronous/Asynchronous Receiver-Transmitter, USART） | 同时支持同步和异步串行通信的微控制器外设。 | 第 7 章 |
| 脉宽调制（Pulse-Width Modulation, PWM） | 通过改变固定周期内有效电平所占比例来调节平均输出的方式。 | 第 9 章 |
| 比例—积分—微分控制（Proportional–Integral–Derivative Control, PID） | 根据目标值与测量值误差计算控制输出的反馈控制方法。 | 第 9 章 |
| 比例—积分控制（Proportional–Integral Control, PI） | 只使用比例项和积分项的反馈控制形式。 | 第 9 章 |
| 有机发光二极管（Organic Light-Emitting Diode, OLED） | 通过有机发光材料显示文字和图形的屏幕。 | 第 8 章 |
| 巨磁阻（Giant Magnetoresistance, GMR） | 利用磁阻随磁场变化检测转动的编码器。 | 第 8 章 |
| 霍尔效应编码器（Hall Effect Encoder） | 利用霍尔元件检测磁场变化并输出转动脉冲的编码器。 | 第 8 章 |
| 直接内存访问（Direct Memory Access, DMA） | 让外设与内存直接交换数据、减少处理器逐字节参与的机制。 | 第 7 章 |
| Transform Library 2（TF2） | ROS 2 中记录并查询坐标系之间位置和姿态关系的库。 | 第 26 章 |
| XML Macros（Xacro） | 通过宏和参数生成可复用 URDF 片段的格式。 | 第 26 章 |
| ROS Visualization（RViz） | 显示机器人模型、传感器数据和坐标关系的桌面工具。 | 第 26 章 |
| Launch System（Launch） | 按配置同时启动 ROS 2 节点、参数和条件分支的机制。 | 第 25 章 |
| 同步定位与建图（Simultaneous Localization and Mapping, SLAM） | 同时估计机器人位姿并逐步建立环境地图的方法。 | 第 31 章 |
| Navigation2（Nav2） | ROS 2 的二维导航框架，负责规划路径、控制速度和处理恢复。 | 第 33 章 |
| Open Source Computer Vision Library（OpenCV） | 用于图像处理和计算机视觉的开源程序库。 | 第 35 章 |
| cv_bridge | 在 ROS 图像消息与 OpenCV 图像矩阵之间转换的 ROS 软件包。 | 第 35 章 |
| 快速扩展随机树（Rapidly-Exploring Random Tree, RRT） | 在可通行空间中逐步随机扩展树结构以搜索路径的方法。 | 第 34 章 |
| Kernelized Correlation Filter（KCF） | 根据初始目标框在连续图像中跟踪目标的算法。 | 第 37 章 |
| 增强现实标签（Augmented Reality Tag, AR Tag） | 在图像中识别带编码图案并估计其位姿的标记。 | 第 37 章 |
| Gazebo Simulation Platform（Gazebo） | 用物理模型计算机器人、环境和虚拟传感器行为的平台。 | 第 45 章 |
| Qt Application Framework（Qt） | 用于开发桌面图形界面的跨平台软件框架。 | 第 46 章 |
| 网络文件系统（Network File System, NFS） | 通过网络把远程计算机目录挂载到本地的文件系统协议。 | 第 51 章 |
| Docker Container Platform（Docker） | 用镜像隔离运行进程、文件和依赖的软件平台。 | 第 22 章 |
| 应用程序编程接口（Application Programming Interface, API） | 程序之间调用功能和交换数据时遵循的接口约定。 | 第 48 章 |
| 互联网协议地址（Internet Protocol Address, IP Address） | 标识网络中设备的地址，常简称 IP。 | 第 13 章 |
| 虚拟网络计算（Virtual Network Computing, VNC） | 通过网络传输远程计算机图形桌面的协议和工具。 | 第 13 章 |
| 扩展卡尔曼滤波器（Extended Kalman Filter, EKF） | 在线融合带噪声测量并估计系统状态的滤波方法。 | 第 30 章 |
| 全局导航卫星系统（Global Navigation Satellite System, GNSS） | 通过卫星信号估计接收机位置和时间的系统。 | 第 8 章 |
| 数据长度代码（Data Length Code, DLC） | CAN 数据帧中表示有效数据字节数的字段。 | 第 7 章 |
| 标识符（Identifier, ID） | 用于区分 CAN 报文用途的数值字段。 | 第 7 章 |
| 块校验字符（Block Check Character, BCC） | 对一段通信数据计算得到、用于发现传输错误的校验值。 | 第 7 章 |
| 里程计（Odometry） | 根据轮速或其他运动观测推算机器人位姿和速度的结果。 | 第 9 章 |
| 底盘运动模型（Chassis Kinematics） | 描述车体速度与各轮速度之间换算关系的模型。 | 第 9 章 |
| 通用输入输出（General-Purpose Input/Output, GPIO） | 微控制器上可配置为数字输入或输出的引脚接口。 | 第 7 章 |
| 内部集成电路总线（Inter-Integrated Circuit, I²C） | 使用时钟线和数据线连接低速外设的串行总线。 | 第 7 章 |
| 串行外设接口（Serial Peripheral Interface, SPI） | 使用时钟和片选信号连接高速外设的同步串行总线。 | 第 7 章 |
| 晶体管—晶体管逻辑（Transistor-Transistor Logic, TTL） | 用逻辑高低电平表示数字信号的电气电平标准。 | 第 7 章 |
| 电可擦可编程只读存储器（Electrically Erasable Programmable Read-Only Memory, EEPROM） | 断电后仍能保存少量配置数据的非易失存储器。 | 第 6 章 |
| 中央处理器（Central Processing Unit, CPU） | 执行通用程序指令的处理器。 | 第 6 章 |
| 图形处理器（Graphics Processing Unit, GPU） | 并行执行图形或机器学习计算的处理器。 | 第 6 章 |
| 域标识符（Domain Identifier, Domain ID） | 用于隔离不同 ROS 2 通信域的编号。 | 第 24 章 |
| 可扩展标记语言（Extensible Markup Language, XML） | 用标签描述层次化数据的文本格式。 | 第 26 章 |
| YAML 配置格式（YAML Ain't Markup Language, YAML） | 用缩进表示层次结构的文本配置格式。 | 第 25 章 |
| 世界（World） | Gazebo 仿真中描述地面、墙体和障碍物的场景文件。 | 第 45 章 |
| 插件（Plugin） | 在宿主程序中加载、扩展特定功能的软件模块。 | 第 45 章 |
| 哈希值（Hash Value） | 根据文件内容计算出的固定长度结果，用于校验复制前后是否一致。 | 第 52 章 |
| 数据分发服务（Data Distribution Service, DDS） | ROS 2 使用的通信中间件标准，负责发现参与者并传递数据。 | 第 24 章 |
| 服务质量（Quality of Service, QoS） | 描述消息可靠性、持久性和时延等通信策略的配置。 | 第 24 章 |
| 统一机器人描述格式（Unified Robot Description Format, URDF） | 用 XML 描述机器人连杆、关节、几何外观和坐标关系的格式。 | 第 26 章 |
| 节点（Node） | 在 ROS 2 中承担一项明确工作的程序单元。 | 第 5 章 |
| 话题（Topic） | 节点之间传递连续数据的命名通道。 | 第 5 章 |
| 发布者（Publisher） | 向话题写入消息的节点接口。 | 第 5 章 |
| 订阅者（Subscriber） | 从话题读取消息的节点接口。 | 第 5 章 |
| 服务（Service） | 表示一次请求和一次响应的接口。 | 第 5 章 |
| 动作（Action） | 支持目标、反馈、结果和取消的耗时任务接口。 | 第 5 章 |
| 参数（Parameter） | 描述节点运行配置的键值。 | 第 5 章 |
| 工作空间（Workspace） | 组织源码、构建结果和安装文件的目录结构。 | 第 23 章 |
| 功能包（Package） | ROS 2 中可独立构建和分发的代码与资源单元。 | 第 23 章 |
| 主控 | 运行 Ubuntu、ROS 2 和上层应用的计算机。 | 第 6 章 |
| 底盘控制板 | 运行固件、采集反馈并执行电机控制的控制器。 | 第 6 章 |
| cmd_vel | 常见的机器人速度目标话题名称。 | 第 17 章 |
| base_link | 表示机器人主体的基础坐标系名称。 | 第 26 章 |
| odom | 表示局部连续里程计坐标系的名称。 | 第 9 章 |
| map | 建图和定位使用的全局坐标系名称。 | 第 32 章 |
| TF | ROS 中维护坐标系变换关系的机制。 | 第 26 章 |
| 人工智能（Artificial Intelligence, AI） | 用于理解语音、图像或文字并生成高层任务意图的技术集合。 | 第 48 章 |
| 文本转语音（Text-to-Speech, TTS） | 把文字转换为可播放语音的技术。 | 第 48 章 |

若某个术语只在单个章节中出现，正文会直接给出中文含义，不为它额外引入缩写。
