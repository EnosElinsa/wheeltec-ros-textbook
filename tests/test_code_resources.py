from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_code_resources as resources  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "code-resources-launch-chain.yml"
REVISION = "0123456789abcdef0123456789abcdef01234567"


class CodeResourceContractTests(unittest.TestCase):
    def make_source_tree(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        package = root / "ros2" / "robot" / "turn-on-wheeltec-robot"
        for relative in (
            "launch/turn_on_wheeltec_robot.launch.py",
            "launch/base_serial.launch.py",
            "src/wheeltec_robot.cpp",
        ):
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture\n", encoding="utf-8")
        for page, anchor in (
            ("docs/04-ros2-development/18-environment-and-source-selection.md", "source-package-selection"),
            ("docs/04-ros2-development/21-launch-and-parameters.md", "bringup-launch-chain"),
            ("docs/04-ros2-development/23-modify-build-rollback.md", "source-change-exercise"),
            ("docs/06-stm32-firmware/37-ros2-stm32-integration.md", "ros-serial-firmware-chain"),
        ):
            path = root / page
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# fixture {{#{anchor}}}\n", encoding="utf-8")
        evidence = root / "docs/superpowers/audits/launch-chain-build.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("{}\n", encoding="utf-8")
        return root

    def test_complete_launch_chain_mapping_validates_against_real_consumer_and_source_files(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        self.assertEqual(resources.validate_code_resource_map(mapping, self.make_source_tree()), [])
        self.assertEqual(len(mapping.resources[0].consumers), 4)

    def test_immutable_tree_url_uses_revision_not_main(self) -> None:
        self.assertEqual(
            resources.immutable_tree_url(
                "EnosElinsa/wheeltec-ros-source-reference",
                REVISION,
                "ros2/robot/turn-on-wheeltec-robot",
            ),
            "https://github.com/EnosElinsa/wheeltec-ros-source-reference/tree/"
            "0123456789abcdef0123456789abcdef01234567/ros2/robot/turn-on-wheeltec-robot",
        )

    def test_validation_rejects_missing_files_main_links_and_schema_examples(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        resource = mapping.resources[0]
        resource.consumers[0].files = ["missing.py"]
        resource.verification.environment = "schema-example"
        resource.verification.command = "https://github.com/org/repo/tree/main/path"
        errors = resources.validate_code_resource_map(mapping, self.make_source_tree())
        self.assertTrue(any("missing.py" in error for error in errors))
        self.assertTrue(any("schema-example" in error for error in errors))
        self.assertTrue(any("main" in error for error in errors))

    def test_validation_requires_mode_commands_dependencies_and_evidence(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        resource = mapping.resources[0]
        resource.consumers[1].commands = []
        resource.dependencies[0].verification = ""
        resource.verification.evidence_path = ""
        errors = resources.validate_code_resource_map(mapping, self.make_source_tree())
        self.assertTrue(any("build" in error and "command" in error for error in errors))
        self.assertTrue(any("dependency" in error and "verification" in error for error in errors))
        self.assertTrue(any("evidence_path" in error for error in errors))

    def test_appendix_requires_the_immutable_resource_link_and_every_consumer_anchor(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        resource = mapping.resources[0]
        appendix = "\n".join(
            [
                resources.immutable_tree_url(mapping.source_repository, mapping.source_revision, resource.repository_path),
                *[f"{consumer.page}#{consumer.anchor}" for consumer in resource.consumers],
            ]
        )
        resources.validate_appendix_matches_mapping(appendix, mapping)
        with self.assertRaises(ValueError):
            resources.validate_appendix_matches_mapping(appendix.replace("#source-change-exercise", ""), mapping)


if __name__ == "__main__":
    unittest.main()
