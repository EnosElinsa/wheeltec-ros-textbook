from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicSourceReferenceTests(unittest.TestCase):
    def test_catalog_has_complete_public_coverage(self) -> None:
        path = ROOT / "metadata/public-source-packages.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 240)
        self.assertEqual(sum(row["content_kind"] == "source_archive" for row in rows), 220)
        self.assertEqual(
            len({row["canonical_archive_id"] for row in rows if row["publication_status"] == "publishable"}),
            204,
        )
        self.assertTrue(all(":" not in row["archive_id"] for row in rows))
        self.assertTrue(all(row["snapshot_url"] or row["publication_status"] != "publishable" for row in rows))

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
        self.assertIn("公开不等于适配当前实机", text)
        self.assertIn("实机照片补齐前", text)
        self.assertNotRegex(text, r"(?<![A-Za-z0-9])[GR]:(?:archive|firmware|video):")
        self.assertNotIn("wheeltec-ros-general-course", text)
        self.assertNotIn("wheeltec-r680-course", text)


if __name__ == "__main__":
    unittest.main()
