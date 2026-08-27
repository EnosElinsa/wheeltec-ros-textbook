from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import quality  # noqa: E402


class FoundationSchemaTests(unittest.TestCase):
    def test_valid_foundation_passes_teaching_schema(self) -> None:
        issues = quality.check_foundation(
            ROOT / "tests" / "fixtures" / "valid-foundation.md", 150_000
        )
        self.assertEqual(issues, [])

    def test_invalid_foundation_reports_each_dependency_category(self) -> None:
        issues = quality.check_foundation(
            ROOT / "tests" / "fixtures" / "invalid-foundation.md", 150_000
        )
        messages = [issue.message for issue in issues]
        for category in (
            "later chapter prerequisite",
            "advanced middleware jargon",
            "required SSH access",
            "required robot runtime",
        ):
            self.assertTrue(
                any(category in message for message in messages),
                f"missing issue category: {category}",
            )

    def test_final_manifest_layout_accepts_foundations_1_to_5(self) -> None:
        rows: list[dict[str, str]] = []
        for number in range(1, 6):
            rows.append(
                {
                    "kind": "foundation",
                    "number": str(number),
                    "volume": "01-foundations",
                    "path": f"docs/01-foundations/{number:02d}.md",
                    "title": f"基础 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        for number in range(6, 47):
            rows.append(
                {
                    "kind": "chapter",
                    "number": str(number),
                    "volume": "02-bringup",
                    "path": f"docs/02-bringup/{number:02d}.md",
                    "title": f"工程 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        for number in ("A", "B", "C"):
            rows.append(
                {
                    "kind": "appendix",
                    "number": number,
                    "volume": "appendices",
                    "path": f"docs/appendices/{number.lower()}.md",
                    "title": f"附录 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        self.assertEqual(quality.check_manifest(rows), [])


class FoundationContentTests(unittest.TestCase):
    def test_reader_questions_have_documented_pass_results(self) -> None:
        tasks = (ROOT / "tests" / "reader-tasks.md").read_text(encoding="utf-8")
        results = (ROOT / "tests" / "reader-test-results.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(len(re.findall(r"^\d+\. ", tasks, re.MULTILINE)), 8)
        self.assertEqual(results.count("| PASS |"), 8)

    def test_chapter_1_covers_visible_robot_components(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "02-robot-system-overview.md"
        text = path.read_text(encoding="utf-8")
        for term in ("机械结构", "电源", "传感器", "主控", "控制板", "电机"):
            self.assertIn(term, text)
        self.assertIn("微控制器", text)
        self.assertIn("底层反馈控制", text)
        self.assertIn("串行通信", text)
        self.assertIn("CAN（控制器局域网）", text)
        self.assertEqual(quality.check_foundation(path, 150_000), [])

    def test_chapter_2_builds_computer_vocabulary_before_ssh(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "03-ubuntu-terminal-programs.md"
        text = path.read_text(encoding="utf-8")
        for term in ("操作系统", "文件", "目录", "终端", "命令", "程序", "进程", "SSH"):
            self.assertIn(term, text)
        self.assertLess(text.index("终端"), text.index("SSH"))
        self.assertIn("SSH（Secure Shell，安全远程登录协议）", text)
        self.assertEqual(quality.check_foundation(path, 150_000), [])

    def test_chapter_3_explains_ros2_through_nodes(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "03-what-ros2-solves.md"
        text = path.read_text(encoding="utf-8")
        for term in ("ROS 2", "节点", "一个大程序"):
            self.assertIn(term, text)
        self.assertEqual(quality.check_foundation(path, 150_000), [])

    def test_chapter_4_has_executable_and_read_only_routes(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "04-first-ros2-observation.md"
        text = path.read_text(encoding="utf-8")
        for term in (
            "demo_nodes_cpp",
            "talker",
            "listener",
            "ros2 node list",
            "ros2 topic list",
            "只读路线",
        ):
            self.assertIn(term, text)
        self.assertEqual(quality.check_foundation(path, 150_000), [])

    def test_chapter_5_introduces_communication_types_in_order(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "05-ros2-communication.md"
        text = path.read_text(encoding="utf-8")
        positions = [text.index(term) for term in ("话题", "服务", "动作", "参数")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("雷达节点", text)
        self.assertIn("底盘节点", text)
        self.assertEqual(quality.check_foundation(path, 150_000), [])


if __name__ == "__main__":
    unittest.main()
