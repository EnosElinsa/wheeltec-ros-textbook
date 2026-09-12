from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SourceWalkthroughMigrationTests(unittest.TestCase):
    def test_package_workspace_and_hardware_evidence_remain_distinct(self) -> None:
        pages = (
            ROOT / "docs/05-ros2-development/22-environment-and-source-selection.md",
            ROOT / "docs/05-ros2-development/25-launch-and-parameters.md",
            ROOT / "docs/05-ros2-development/27-modify-build-rollback.md",
            ROOT / "docs/07-stm32-firmware/42-ros2-stm32-integration.md",
        )
        combined = "\n".join(path.read_text(encoding="utf-8") for path in pages)
        for phrase in (
            "当前工作空间不自包含",
            "启动链闭合不等于数据链闭合",
            "只能报告 ROS 图上的静态或运行时接口证据",
            "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist",
            "如果安装前缀、`colcon list` 和准备修改的目录不能对应",
        ):
            self.assertIn(phrase, combined)

    def test_launch_chain_keeps_entry_composition_and_parameter_tracing(self) -> None:
        text = (
            ROOT / "docs/05-ros2-development/25-launch-and-parameters.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "从工作空间根执行构建和启动",
            "底盘最小入口",
            "机器人组合入口",
            "传感器组合入口",
            "从参数追到运行节点",
            "rg -n 'IncludeLaunchDescription|get_package_share_directory|Node\\('",
        ):
            self.assertIn(phrase, text)

    def test_safe_change_and_ros_firmware_chain_keep_acceptance_boundaries(self) -> None:
        change = (
            ROOT / "docs/05-ros2-development/27-modify-build-rollback.md"
        ).read_text(encoding="utf-8")
        firmware = (
            ROOT / "docs/07-stm32-firmware/42-ros2-stm32-integration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("安全修改练习", change)
        self.assertIn("验收记录", change)
        self.assertIn("下行链路", change)
        self.assertIn("从 `cmd_vel` 追到 STM32，再回到 ROS 2", firmware)
        self.assertIn("节点打开串口的日志或设备句柄", firmware)


if __name__ == "__main__":
    unittest.main()
