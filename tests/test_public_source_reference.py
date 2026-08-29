from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVED_SOURCE_BASELINE = "f36a76f6da81de698b1adb80729f596744adda7e"
sys.path.insert(0, str(ROOT / "tools"))

import validate_code_resources  # noqa: E402


class PublicSourceReferenceTests(unittest.TestCase):
    def test_production_code_resource_map_is_a_valid_empty_contract(self) -> None:
        mapping = validate_code_resources.load_code_resources(ROOT / "metadata/code-resources.yml")
        self.assertEqual(mapping.source_revision, APPROVED_SOURCE_BASELINE)
        self.assertEqual(mapping.resources, [])
        self.assertEqual(validate_code_resources.validate_code_resource_map(mapping, ROOT), [])

    def test_appendix_lists_direct_code_entries(self) -> None:
        text = (ROOT / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        links = re.findall(
            r"https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/main/([^ )]+)",
            text,
        )
        package_links = [link for link in links if not link.startswith("examples/")]
        self.assertEqual(len(package_links), 200)
        self.assertEqual(len(set(package_links)), 200)
        self.assertNotIn("catalog/", text)
        self.assertNotIn("release-manifest", text)
        self.assertNotIn("SHA-256", text)
        self.assertNotIn("下载", text)
        self.assertNotIn("G-archive-", text)
        self.assertNotIn("R-archive-", text)
        self.assertTrue(all(f"/tree/main/{root}/" in text for root in ("applications", "chassis", "platform", "r680", "ros1", "ros2", "stm32")))

    def test_appendix_is_published_and_linked_from_entry_pages(self) -> None:
        appendix = ROOT / "docs/appendices/d-public-source-reference.md"
        self.assertTrue(appendix.is_file())
        self.assertIn("d-public-source-reference.md", (ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        related = (
            "docs/04-ros2-development/18-environment-and-source-selection.md",
            "docs/04-ros2-development/21-launch-and-parameters.md",
            "docs/04-ros2-development/23-modify-build-rollback.md",
            "docs/05-sensors-navigation/25-sensor-checks.md",
            "docs/05-sensors-navigation/26-lidar-and-mapping.md",
            "docs/05-sensors-navigation/28-nav2-navigation.md",
            "docs/05-sensors-navigation/30-camera-opencv-images.md",
            "docs/05-sensors-navigation/32-vision-applications.md",
            "docs/06-stm32-firmware/33-firmware-architecture-freertos.md",
            "docs/06-stm32-firmware/34-hardware-init-model-interfaces.md",
            "docs/06-stm32-firmware/35-motor-control-pid.md",
            "docs/06-stm32-firmware/37-ros2-stm32-integration.md",
            "docs/07-advanced-applications/38-gazebo-simulation.md",
            "docs/07-advanced-applications/39-multi-robot-and-qt.md",
            "docs/07-advanced-applications/40-mmwave-human-deep-learning.md",
            "docs/07-advanced-applications/41-voice-ai-openclaw.md",
            "docs/08-r680-platform/43-r680-debug-source-firmware.md",
            "docs/09-deployment-maintenance/45-logs-backup-upgrade-recovery.md",
            "docs/appendices/a-ros1-maintenance.md",
        )
        missing = [
            path
            for path in related
            if "d-public-source-reference.md" not in (ROOT / path).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

    def test_appendix_has_safe_hardware_language_and_no_internal_ids(self) -> None:
        text = (ROOT / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        self.assertIn("实机照片补齐前", text)
        self.assertIn("硬件核对", text)
        self.assertNotRegex(text, r"(?<![A-Za-z0-9])[GR]:(?:archive|firmware|video):")
        self.assertNotIn("wheeltec-ros-general-course", text)
        self.assertNotIn("wheeltec-r680-course", text)


if __name__ == "__main__":
    unittest.main()
