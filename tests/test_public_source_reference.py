from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVED_SOURCE_BASELINE = "6dc844bc35afc26477f3573c9191a2481b219a2d"
sys.path.insert(0, str(ROOT / "tools"))

import validate_code_resources  # noqa: E402
from workspace_paths import find_source_root  # noqa: E402


class PublicSourceReferenceTests(unittest.TestCase):
    def test_production_code_resource_map_pins_curated_source_contract(self) -> None:
        mapping = validate_code_resources.load_code_resources(ROOT / "metadata/code-resources.yml")
        self.assertEqual(mapping.source_revision, APPROVED_SOURCE_BASELINE)
        self.assertEqual(len(mapping.resources), 14)
        source_root = find_source_root(ROOT)
        if source_root is None:
            self.skipTest("standalone textbook checkout has no local public-source Git checkout")
        self.assertEqual(validate_code_resources.validate_code_resource_map(mapping, source_root, ROOT), [])

    def test_bringup_consumer_block_uses_the_mapping_anchor_and_revision(self) -> None:
        text = (ROOT / "docs/05-ros2-development/25-launch-and-parameters.md").read_text(encoding="utf-8")
        self.assertIn("{#bringup-launch-chain}", text)
        self.assertIn(APPROVED_SOURCE_BASELINE, text)
        self.assertIn("ros2/robot/turn-on-wheeltec-robot", text)

    def test_appendix_is_byte_equal_to_the_real_mapping_render(self) -> None:
        mapping = validate_code_resources.load_code_resources(ROOT / "metadata/code-resources.yml")
        actual = (ROOT / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        expected = validate_code_resources.render_appendix(mapping)
        self.assertEqual(actual, expected)
        validate_code_resources.validate_appendix_matches_mapping(actual, mapping)

    def test_appendix_has_one_immutable_entry_per_selected_resource(self) -> None:
        mapping = validate_code_resources.load_code_resources(ROOT / "metadata/code-resources.yml")
        text = (ROOT / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        immutable_links = re.findall(
            rf"https://github\.com/{re.escape(mapping.source_repository)}/tree/"
            rf"{mapping.source_revision}/([^ )]+)",
            text,
        )
        self.assertEqual(len(immutable_links), len(mapping.resources))
        self.assertEqual(sorted(immutable_links), sorted(resource.repository_path for resource in mapping.resources))

    def test_appendix_is_published_but_not_used_as_a_generic_chapter_pointer(self) -> None:
        appendix = ROOT / "docs/appendices/d-public-source-reference.md"
        self.assertTrue(appendix.is_file())
        self.assertIn("d-public-source-reference.md", (ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        related = (
            "docs/05-ros2-development/22-environment-and-source-selection.md",
            "docs/05-ros2-development/25-launch-and-parameters.md",
            "docs/05-ros2-development/27-modify-build-rollback.md",
            "docs/06-sensors-navigation/29-sensor-checks.md",
            "docs/06-sensors-navigation/31-lidar-and-mapping.md",
            "docs/06-sensors-navigation/33-nav2-navigation.md",
            "docs/06-sensors-navigation/35-camera-opencv-images.md",
            "docs/06-sensors-navigation/37-vision-applications.md",
            "docs/07-stm32-firmware/40-firmware-architecture-freertos.md",
            "docs/07-stm32-firmware/41-hardware-init-model-interfaces.md",
            "docs/07-stm32-firmware/42-motor-control-pid.md",
            "docs/07-stm32-firmware/44-ros2-stm32-integration.md",
            "docs/08-advanced-applications/45-gazebo-simulation.md",
            "docs/08-advanced-applications/46-multi-robot-and-qt.md",
            "docs/08-advanced-applications/47-mmwave-human-deep-learning.md",
            "docs/08-advanced-applications/48-voice-ai-openclaw.md",
            "docs/09-r680-platform/50-r680-debug-source-firmware.md",
            "docs/10-deployment-maintenance/52-logs-backup-upgrade-recovery.md",
            "docs/appendices/a-ros1-maintenance.md",
        )
        generic = [
            path
            for path in related
            if "本节使用的代码入口见[教材代码资源附录]" in (ROOT / path).read_text(encoding="utf-8")
            or "详见[教材代码资源附录]" in (ROOT / path).read_text(encoding="utf-8")
        ]
        self.assertEqual(generic, [])

    def test_appendix_has_safe_hardware_language_and_no_internal_ids(self) -> None:
        text = (ROOT / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        for forbidden in (
            "/tree/main/", "G-archive", "R-archive", "baseline-", "release",
            "catalog", "docs/superpowers", "C:\\", "归档整理", "构建这个代码库",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("不得烧录或声明硬件验证", text)


if __name__ == "__main__":
    unittest.main()

