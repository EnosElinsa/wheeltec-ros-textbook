from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConceptPlacementTests(unittest.TestCase):
    def assertPageContains(self, relative: str, terms: tuple[str, ...]) -> None:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for term in terms:
            self.assertIn(term, text, f"{relative} is missing {term}")

    def test_workspace_semantics_live_in_chapter_19(self) -> None:
        self.assertPageContains(
            "docs/05-ros2-development/23-workspace-packages-build.md",
            (
                "`src/`",
                "`build/`",
                "`install/`",
                "`log/`",
                "/opt/ros/$ROS_DISTRO/setup.bash",
                "install/setup.bash",
                "AMENT_PREFIX_PATH",
            ),
        )

    def test_endpoint_compatibility_lives_in_chapter_20(self) -> None:
        self.assertPageContains(
            "docs/05-ros2-development/24-nodes-topics-services-actions.md",
            ("发布者", "订阅者", "reliability", "history", "depth"),
        )

    def test_transform_and_timestamp_tools_live_in_chapter_22(self) -> None:
        self.assertPageContains(
            "docs/05-ros2-development/26-tf-urdf-rviz.md",
            ("坐标系", "静态变换", "动态变换", "时间戳", "view_frames"),
        )

    def test_sensor_diagnosis_order_lives_in_chapter_25(self) -> None:
        self.assertPageContains(
            "docs/06-sensors-navigation/29-sensor-checks.md",
            (
                "设备 → 节点 → 话题 → 通信匹配 → 时间",
                "Linux 内核驱动和 SDK 本身通常不发布 ROS 2 话题",
                "`sensor_msgs/msg/LaserScan`",
                "`sensor_msgs/msg/Image`",
                "`sensor_msgs/msg/Imu`",
                "`sensor_msgs/msg/NavSatFix`",
                "`ros2 node info`",
            ),
        )

    def test_navigation_frame_ownership_lives_in_chapter_27(self) -> None:
        self.assertPageContains(
            "docs/06-sensors-navigation/32-map-localization-tf.md",
            (
                "map → odom → base_link → sensor",
                "定位系统估计 `map → odom`",
                "底盘里程计提供 `odom → base_link`",
            ),
        )

    def test_container_boundary_lives_in_chapter_44(self) -> None:
        self.assertPageContains(
            "docs/10-deployment-maintenance/49-network-docker-images.md",
            ("宿主", "容器", "USB", "GPU", "网络", "时间"),
        )


if __name__ == "__main__":
    unittest.main()
