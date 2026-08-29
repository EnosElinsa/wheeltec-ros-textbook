from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/appendices/a-ros1-maintenance.md"


class Ros1BagDiagnosticsMigrationTests(unittest.TestCase):
    def test_appendix_uses_ros1_time_and_paused_playback_workflow(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        for phrase in (
            "rosbag info --yaml",
            "rosparam set /use_sim_time true",
            "rosbag play --clock --pause --rate 0.5",
            "不要在同一终端加载 ROS 1 与 ROS 2",
            "rostopic hz",
            "tf_echo",
        ):
            self.assertIn(phrase, text)

    def test_worked_samples_remain_bounded_to_observed_capabilities(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
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

    def test_workflow_keeps_clock_safety_and_evidence_edge_cases(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        for phrase in (
            'BAG_SOURCE="/absolute/path/to/source.bag"',
            'BAG_COPY="$AUDIT_DIR/input.bag"',
            "cmp source.sha256 copy.sha256",
            "唯一权威时钟",
            "rostopic hz --wall-time",
            "全零矩阵表示协方差未知",
            "connection header",
            "callerid",
            "不可独立复核的示例审计结果",
            "ROS 图隔离不等于",
            'test -r "$BAG_COPY"',
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
