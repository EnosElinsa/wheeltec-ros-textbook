from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = {
    "ros2-system-layers.svg": (
        "docs/01-foundations/01-understanding-ros.md",
        "ROS 2 在 WHEELTEC 机器人中的位置",
    ),
    "robot-control-loop.svg": (
        "docs/01-foundations/02-robot-system-overview.md",
        "轮式机器人信息流与能量流",
    ),
    "talker-listener.svg": (
        "docs/01-foundations/04-first-ros2-observation.md",
        "talker 与 listener 的 ROS 2 通信",
    ),
    "ros2-data-chain.svg": (
        "docs/01-foundations/05-ros2-communication.md",
        "ROS 2 从雷达到电机的数据链",
    ),
    "ros2-stm32-loop.svg": (
        "docs/06-stm32-firmware/37-ros2-stm32-integration.md",
        "ROS 2 与 STM32 的闭环链路",
    ),
    "system-acceptance-pipeline.svg": (
        "docs/09-deployment-maintenance/46-system-acceptance.md",
        "WHEELTEC 全系统验收流程",
    ),
}


class TextbookDiagramTests(unittest.TestCase):
    def test_each_diagram_is_referenced_by_its_target_chapter(self) -> None:
        for filename, (chapter, alt) in DIAGRAMS.items():
            text = (ROOT / chapter).read_text(encoding="utf-8")
            self.assertIn(f"![{alt}]", text, chapter)
            self.assertIn(f"assets/diagrams/{filename}", text, chapter)

    def test_diagrams_have_accessible_svg_metadata(self) -> None:
        diagram_root = ROOT / "docs" / "assets" / "diagrams"
        self.assertEqual(
            {path.name for path in diagram_root.glob("*.svg")}, set(DIAGRAMS)
        )
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        for filename in DIAGRAMS:
            path = diagram_root / filename
            root = ET.parse(path).getroot()
            labelled_by = root.attrib.get("aria-labelledby", "").split()
            self.assertEqual(root.attrib.get("role"), "img", filename)
            self.assertEqual(root.attrib.get("viewBox"), "0 0 1280 720" if filename != "talker-listener.svg" else "0 0 1280 560")
            self.assertEqual(len(labelled_by), 2, filename)
            title = root.find("svg:title", namespace)
            desc = root.find("svg:desc", namespace)
            self.assertIsNotNone(title, filename)
            self.assertIsNotNone(desc, filename)
            self.assertEqual(title.attrib.get("id"), labelled_by[0])
            self.assertEqual(desc.attrib.get("id"), labelled_by[1])
            self.assertTrue((title.text or "").strip(), filename)
            self.assertTrue((desc.text or "").strip(), filename)
            text = path.read_text(encoding="utf-8")
            font_sizes = {int(value) for value in re.findall(r'font-size="(\d+)"', text)}
            self.assertTrue(font_sizes <= {8, 12, 16, 20, 24, 28, 32, 40}, filename)
            self.assertNotIn("JetBrains Mono", text, filename)

    def test_replaced_unicode_sketches_are_absent(self) -> None:
        forbidden = (
            "└─ ROS 2：驱动、感知、定位、导航与工具",
            "环境 → 传感器 → 主控程序 → 底盘控制",
            "talker 节点 → 文字消息 → listener 节点",
            "雷达节点 ──扫描消息──▶ 导航节点",
            "→ ROS 2 底盘节点 Control()",
        )
        combined = "\n".join(
            (ROOT / chapter).read_text(encoding="utf-8")
            for chapter, _ in DIAGRAMS.values()
        )
        for sketch in forbidden:
            self.assertNotIn(sketch, combined)
        self.assertEqual(len(re.findall(r"assets/diagrams/[^)]+\.svg", combined)), 6)


if __name__ == "__main__":
    unittest.main()
