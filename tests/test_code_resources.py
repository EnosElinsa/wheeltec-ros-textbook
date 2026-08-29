from __future__ import annotations

import sys
import tempfile
import unittest
import re
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

    def test_validation_requires_a_non_empty_command_for_every_executable_mode(self) -> None:
        for consumer_index, mode in ((1, "build"), (2, "run"), (3, "hardware")):
            with self.subTest(mode=mode):
                mapping = resources.load_code_resources(FIXTURE)
                mapping.resources[0].consumers[consumer_index].commands = ["  "]
                errors = resources.validate_code_resource_map(mapping, self.make_source_tree())
                self.assertTrue(any(f"{mode} mode requires commands" in error for error in errors))

    def test_validation_enforces_mode_to_verification_level_without_command_word_heuristics(self) -> None:
        cases = (
            ("static_read", "static_reviewed", False),
            ("build", "static_reviewed", True),
            ("build", "build_verified", False),
            ("run", "build_verified", True),
            ("run", "runtime_verified", False),
            ("hardware", "runtime_verified", True),
            ("hardware", "hardware_verified", False),
        )
        for mode, level, should_fail in cases:
            with self.subTest(mode=mode, level=level):
                mapping = resources.load_code_resources(FIXTURE)
                resource = mapping.resources[0]
                resource.consumers = [resource.consumers[0]]
                resource.consumers[0].mode = mode
                resource.consumers[0].commands = ["do the required step"] if mode != "static_read" else []
                resource.verification.level = level
                errors = resources.validate_code_resource_map(mapping, self.make_source_tree())
                mismatch = any("requires verification level" in error for error in errors)
                self.assertEqual(mismatch, should_fail)

    def test_load_rejects_invalid_schema_types_missing_keys_and_unknown_keys(self) -> None:
        cases = (
            ("resources: bad\nsource_repository: owner/repo\nsource_revision: " + REVISION, "resources must be a list"),
            ("resources: []\nsource_repository: [owner/repo]\nsource_revision: " + REVISION, "source_repository must be a string"),
            ("resources: []\nsource_repository: owner/repo", "missing required key: source_revision"),
            ("resources: []\nsource_repository: owner/repo\nsource_revision: " + REVISION + "\nunexpected: value", "unknown key: unexpected"),
            ("resources:\n  - bad\nsource_repository: owner/repo\nsource_revision: " + REVISION, "resource must be a mapping"),
            (
                "source_repository: owner/repo\nsource_revision: " + REVISION
                + "\nresources:\n  - id: resource\n    repository_path: code\n    consumers: bad\n    compatibility:\n      ros_distribution: baseline\n      platform: generic\n      hardware: none\n    dependencies: []\n    verification:\n      level: static_reviewed\n      source_commit: "
                + REVISION
                + "\n      environment: fixture\n      command: check\n      result: passed\n      evidence_path: docs/superpowers/audits/evidence.json\n      verified_at: now",
                "resources[0].consumers must be a list",
            ),
            (
                "source_repository: owner/repo\nsource_revision: " + REVISION
                + "\nresources:\n  - id: resource\n    repository_path: code\n    consumers: []\n    compatibility: []\n    dependencies: []\n    verification:\n      level: static_reviewed\n      source_commit: "
                + REVISION
                + "\n      environment: fixture\n      command: check\n      result: passed\n      evidence_path: docs/superpowers/audits/evidence.json\n      verified_at: now",
                "resource.compatibility must be a mapping",
            ),
        )
        for content, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "invalid.yml"
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, re.escape(message)):
                    resources.load_code_resources(path)

    def test_validation_rejects_an_empty_evidence_file(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        root = self.make_source_tree()
        evidence = root / mapping.resources[0].verification.evidence_path
        evidence.write_text("", encoding="utf-8")
        errors = resources.validate_code_resource_map(mapping, root)
        self.assertTrue(any("existing non-empty file" in error for error in errors))

    def test_appendix_requires_the_immutable_resource_link_and_every_consumer_anchor(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        self.assertTrue(hasattr(resources, "render_appendix"))
        appendix = resources.render_appendix(mapping)
        resources.validate_appendix_matches_mapping(appendix, mapping)
        mutations = (
            appendix.replace("#source-change-exercise", "#stale-anchor", 1),
            appendix.replace(REVISION, "f" * 40, 1),
            appendix.replace("ros2/robot/turn-on-wheeltec-robot", "ros2/robot/wrong-package", 1),
            appendix.replace("### ", "### duplicate\n\n" + appendix[appendix.index("### "):], 1),
            appendix + "\n### extra resource\n",
            appendix.replace("tree/" + REVISION, "tree/main", 1),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[-80:]), self.assertRaises(ValueError):
                resources.validate_appendix_matches_mapping(mutated, mapping)

    def test_appendix_render_is_deterministic_and_reader_facing(self) -> None:
        mapping = resources.load_code_resources(FIXTURE)
        first = resources.render_appendix(mapping)
        second = resources.render_appendix(mapping)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertIn("教材正文中的代码入口是主要使用位置", first)
        self.assertIn("## ROS 2 基础与启动", first)
        self.assertNotIn("/tree/main/", first)
        self.assertNotIn("docs/superpowers", first)


if __name__ == "__main__":
    unittest.main()
