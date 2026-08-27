from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = "05-sensors-navigation/ros1-bag-offline-diagnostics.md"
PAGE_LINK = "ros1-bag-offline-diagnostics.md"


class Ros1BagDiagnosticsTests(unittest.TestCase):
    def test_page_is_published_and_linked_from_related_material(self) -> None:
        page = ROOT / "docs" / PAGE_PATH
        self.assertTrue(page.is_file(), "ROS 1 Bag diagnostic page is missing")
        self.assertIn(PAGE_PATH, (ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

        related_pages = (
            "docs/appendices/a-ros1-maintenance.md",
            "docs/05-sensors-navigation/25-sensor-checks.md",
            "docs/05-sensors-navigation/26-lidar-and-mapping.md",
            "docs/05-sensors-navigation/27-map-localization-tf.md",
        )
        missing = [
            path
            for path in related_pages
            if PAGE_LINK not in (ROOT / path).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

    def test_page_uses_ros1_time_and_paused_playback_workflow(self) -> None:
        page = ROOT / "docs" / PAGE_PATH
        self.assertTrue(page.is_file(), "ROS 1 Bag diagnostic page is missing")
        text = page.read_text(encoding="utf-8")
        for phrase in (
            "rosbag info --yaml",
            "rosparam set /use_sim_time true",
            "rosbag play --clock --pause --rate 0.5",
            "不要在同一终端加载 ROS 1 与 ROS 2",
            "rostopic hz",
            "tf_echo",
        ):
            self.assertIn(phrase, text)

    def test_worked_samples_are_bounded_to_observed_capabilities(self) -> None:
        page = ROOT / "docs" / PAGE_PATH
        self.assertTrue(page.is_file(), "ROS 1 Bag diagnostic page is missing")
        text = page.read_text(encoding="utf-8")
        for phrase in (
            "约 246 秒",
            "`child_frame_id` 为空",
            "约 244 秒",
            "`sensor_msgs/MultiEchoLaserScan`",
            "没有里程计、TF 或地图",
            "不能证明 WHEELTEC 兼容",
            "不提供 Bag 文件下载",
        ):
            self.assertIn(phrase, text)

    def test_workflow_handles_clock_safety_and_evidence_edge_cases(self) -> None:
        page = ROOT / "docs" / PAGE_PATH
        self.assertTrue(page.is_file(), "ROS 1 Bag diagnostic page is missing")
        text = page.read_text(encoding="utf-8")
        for phrase in (
            'BAG_SOURCE="/absolute/path/to/source.bag"',
            'BAG_COPY="$AUDIT_DIR/input.bag"',
            "cmp source.sha256 copy.sha256",
            "rosparam set /use_sim_time true",
            "--topics",
            "唯一权威时钟",
            "rostopic hz --wall-time",
            "全零矩阵表示协方差未知",
            "疑似缺帧或记录间隙",
            "connection header",
            "callerid",
            "不可独立复核的示例审计结果",
            "ROS 图隔离不等于",
            "set -euo pipefail",
            'test -n "$SOURCE_HASH"',
            'test -n "$COPY_HASH"',
            ': "${AUDIT_DIR:?',
            ': "${BAG_COPY:?',
            'test -r "$BAG_COPY"',
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
