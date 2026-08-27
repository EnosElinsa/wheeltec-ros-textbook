from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH = "04-ros2-development/turn-on-wheeltec-robot-source-walkthrough.md"
LINK_TARGET = "turn-on-wheeltec-robot-source-walkthrough.md"


class SourceWalkthroughNavigationTests(unittest.TestCase):
    def test_walkthrough_is_published_in_the_ros2_development_navigation(self) -> None:
        self.assertTrue((ROOT / "docs" / WALKTHROUGH).is_file())
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn(WALKTHROUGH, config)

    def test_related_chapters_link_to_the_central_walkthrough(self) -> None:
        related_pages = (
            "docs/04-ros2-development/18-environment-and-source-selection.md",
            "docs/04-ros2-development/21-launch-and-parameters.md",
            "docs/04-ros2-development/23-modify-build-rollback.md",
            "docs/06-stm32-firmware/37-ros2-stm32-integration.md",
        )
        missing = [
            path
            for path in related_pages
            if LINK_TARGET not in (ROOT / path).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

    def test_walkthrough_keeps_package_workspace_and_hardware_evidence_distinct(self) -> None:
        text = (ROOT / "docs" / WALKTHROUGH).read_text(encoding="utf-8")
        for phrase in (
            "当前工作空间不自包含",
            "启动链闭合不等于数据链闭合",
            "本页的 `status: complete` 只表示导读文档已经完成",
            "只能报告 ROS 图上的静态或运行时接口证据",
            "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
