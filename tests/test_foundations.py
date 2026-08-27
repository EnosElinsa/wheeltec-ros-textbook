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
        self.assertEqual(len(re.findall(r"^\d+\. ", tasks, re.MULTILINE)), 10)
        self.assertEqual(results.count("| PASS |"), 10)
        for section in ("1.2", "1.3", "1.4", "1.6", "2.1", "3.3", "4.4", "5.6"):
            self.assertIn(section, results)

    def test_chapter_1_covers_visible_robot_components(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "02-robot-system-overview.md"
        text = path.read_text(encoding="utf-8")
        for term in ("机械结构", "电源", "传感器", "主控", "控制板", "电机"):
            self.assertIn(term, text)
        self.assertIn("微控制器", text)
        self.assertIn("底层反馈控制", text)
        self.assertIn("串行通信", text)
        self.assertIn("控制器局域网（Controller Area Network, CAN）", text)
        self.assertEqual(quality.check_foundation(path, 150_000, 2), [])

    def test_chapter_2_builds_computer_vocabulary_before_ssh(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "03-ubuntu-terminal-programs.md"
        text = path.read_text(encoding="utf-8")
        for term in ("操作系统", "文件", "目录", "终端", "命令", "程序", "进程", "SSH"):
            self.assertIn(term, text)
        self.assertIn("操作系统（Operating System, OS）", text)
        self.assertLess(text.index("终端"), text.index("SSH"))
        self.assertIn("安全外壳协议（Secure Shell, SSH）", text)
        headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        self.assertEqual(headings[:3], [
            "3.1 主控首先是一台计算机",
            "3.2 操作系统管理什么",
            "3.3 文件与目录",
        ])
        self.assertEqual(quality.check_foundation(path, 150_000, 3), [])

    def test_chapter_1_introduces_ros_identity_history_and_evolution(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "01-understanding-ros.md"
        text = path.read_text(encoding="utf-8")
        for term in (
            "机器人操作系统（Robot Operating System, ROS）",
            "机器人操作系统 2（Robot Operating System 2, ROS 2）",
            "2007", "STAIR", "Willow Garage", "2015", "Alpha 1",
            "2017", "Ardent Apalone",
        ):
            self.assertIn(term, text)
        headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        self.assertEqual(headings, [
            "1.1 从机器人软件的难题说起",
            "1.2 ROS 的名称与定位",
            "1.3 ROS 的发展历程",
            "1.4 从 ROS 1 到 ROS 2",
            "1.5 ROS 2 提供哪些基础能力",
            "1.6 ROS 2 在机器人系统中的位置",
            "1.7 本章小结",
            "1.8 思考与练习",
            "章节导航",
        ])
        self.assertNotIn("新概念", text)
        self.assertNotIn("节点的英文是 Node", text)
        self.assertEqual(quality.check_foundation(path, 150_000, 1), [])

    def test_chapter_4_has_executable_and_read_only_routes(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "04-first-ros2-observation.md"
        text = path.read_text(encoding="utf-8")
        for term in (
            "demo_nodes_cpp",
            "talker",
            "listener",
            "ros2 node list",
            "ros2 topic list",
            "代表性输出",
        ):
            self.assertIn(term, text)
        self.assertEqual(quality.check_foundation(path, 150_000, 4), [])

    def test_chapter_5_introduces_communication_types_in_order(self) -> None:
        path = ROOT / "docs" / "01-foundations" / "05-ros2-communication.md"
        text = path.read_text(encoding="utf-8")
        headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        positions = [headings.index(term) for term in (
            "5.2 话题：持续发布的数据流",
            "5.3 服务：一次请求与一次响应",
            "5.4 动作：可以反馈和取消的耗时任务",
            "5.5 参数：节点自己的配置",
        )]
        self.assertEqual(positions, sorted(positions))
        for term in (
            "节点（Node）", "话题（Topic）", "发布者（Publisher）",
            "订阅者（Subscriber）", "服务（Service）", "动作（Action）",
            "参数（Parameter）",
        ):
            self.assertIn(term, text)
        self.assertEqual(headings[:6], [
            "5.1 节点：把任务拆成独立程序",
            "5.2 话题：持续发布的数据流",
            "5.3 服务：一次请求与一次响应",
            "5.4 动作：可以反馈和取消的耗时任务",
            "5.5 参数：节点自己的配置",
            "5.6 从雷达到电机的数据链",
        ])
        self.assertIn("雷达节点", text)
        self.assertIn("底盘节点", text)
        self.assertEqual(quality.check_foundation(path, 150_000, 5), [])


if __name__ == "__main__":
    unittest.main()
