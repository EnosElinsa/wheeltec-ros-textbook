from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
import sys
import re
from unittest.mock import patch
from workspace_paths import find_process_root, find_source_root

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SOURCE_REVISION = "ebae2342709c756cb8fa387ccdbd6e5733f9219a"


class WorkflowContractTests(unittest.TestCase):
    def test_required_workflow_names_and_files_exist(self) -> None:
        workflows = list((ROOT / ".github/workflows").glob("*.yml"))
        names = [yaml.safe_load(path.read_text(encoding="utf-8"))["name"] for path in workflows]
        self.assertEqual(
            set(names),
            {"Test ROS 2 examples", "Validate code resources", "Deploy documentation to GitHub Pages"},
        )
        self.assertTrue((ROOT / ".github/workflows/validate-code-resources.yml").is_file())

    def test_resource_workflows_read_and_pin_mapping_revision_without_main_checkout(self) -> None:
        examples = (ROOT / ".github/workflows/test-ros2-examples.yml").read_text(encoding="utf-8")
        validation = (ROOT / ".github/workflows/validate-code-resources.yml").read_text(encoding="utf-8")
        for workflow in (examples, validation):
            self.assertIn("metadata/code-resources.yml", workflow)
            self.assertIn("source_revision", workflow)
            self.assertIn("git checkout", workflow)
            self.assertIn("\"$SOURCE_REVISION\"", workflow)
            self.assertNotIn("git checkout main", workflow)
            self.assertNotIn("/tree/main/", workflow)
        self.assertIn("examples/ros2/pubsub/cpp", examples)
        self.assertIn("examples/ros2/pubsub/python", examples)
        self.assertIn('source_repository', examples)
        self.assertIn('https://github.com/${SOURCE_REPOSITORY}.git', examples)
        self.assertNotIn('https://github.com/EnosElinsa/wheeltec-ros-source-reference.git', examples)
        self.assertIn("separate", validation.lower())
        self.assertIn('"metadata/code-resources.yml"', examples)
        self.assertLess(validation.index("pip install"), validation.index("import yaml"))

    def test_ros2_container_workflow_parses_pinned_mapping_without_a_python_dependency(self) -> None:
        workflow = (ROOT / ".github/workflows/test-ros2-examples.yml").read_text(encoding="utf-8")
        self.assertIn("container: ros:humble-ros-base-jammy", workflow)
        self.assertNotIn("Install mapping parser", workflow)
        self.assertNotIn("pip install", workflow)
        self.assertNotIn("import yaml", workflow)
        self.assertIn("read_top_level_value()", workflow)
        self.assertIn("read_top_level_value source_repository", workflow)
        self.assertIn("read_top_level_value source_revision", workflow)
        self.assertIn("test -n \"$SOURCE_REPOSITORY\"", workflow)
        self.assertIn("*[!0-9a-f]*", workflow)
        # The source tree contains a directory named ``python``; only reject
        # interpreter invocations, not that resource path.
        self.assertNotRegex(workflow, r"(?m)(?:^|[ (])python(?:\s|$)")
        self.assertNotRegex(workflow, r"(?m)(?:^|[ (])python3(?:\s|$)")

    def test_clone_source_revision_uses_an_isolated_destination_and_pinned_commit(self) -> None:
        from validate_code_resources import clone_source_revision

        with tempfile.TemporaryDirectory() as temp_dir:
            origin = Path(temp_dir) / "origin"
            destination = Path(temp_dir) / "clone"
            origin.mkdir()
            subprocess.run(["git", "init", str(origin)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(origin), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(origin), "config", "user.name", "Test"], check=True)
            (origin / "marker.txt").write_text("source\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(origin), "add", "marker.txt"], check=True)
            subprocess.run(["git", "-C", str(origin), "commit", "-m", "fixture"], check=True, capture_output=True)
            revision = subprocess.check_output(["git", "-C", str(origin), "rev-parse", "HEAD"], text=True).strip()
            clone_source_revision(str(origin), revision, destination)
            self.assertEqual((destination / "marker.txt").read_text(encoding="utf-8"), "source\n")
            self.assertEqual(subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip(), revision)
            self.assertFalse((origin / "clone").exists())
            with self.assertRaises(ValueError):
                clone_source_revision(str(origin), "main", Path(temp_dir) / "bad")

    def test_clone_failure_removes_only_the_partial_explicit_destination(self) -> None:
        from validate_code_resources import clone_source_revision

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            destination = root / "partial-clone"
            sibling = root / "keep.txt"
            sibling.write_text("keep", encoding="utf-8")

            def fail_clone(*args, **kwargs):
                destination.mkdir()
                (destination / "partial").write_text("partial", encoding="utf-8")
                raise subprocess.CalledProcessError(1, args[0])

            with patch("validate_code_resources.subprocess.run", side_effect=fail_clone):
                with self.assertRaises(subprocess.CalledProcessError):
                    clone_source_revision("owner/repository", SOURCE_REVISION, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep")

    def test_run_code_resource_validation_is_read_only_and_reports_errors(self) -> None:
        from validate_code_resources import run_code_resource_validation

        source = find_source_root(ROOT)
        if source is None:
            self.skipTest("standalone textbook checkout has no local public-source Git checkout")
        before = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
        self.assertEqual(run_code_resource_validation(ROOT, source), 0)
        after = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
        self.assertEqual(before, after)

    def test_formal_consumer_pages_and_reader_inputs_use_mapping_revision_only(self) -> None:
        import validate_code_resources

        mapping = validate_code_resources.load_code_resources(ROOT / "metadata/code-resources.yml")
        revision = mapping.source_revision
        pages = {ROOT / consumer.page for resource in mapping.resources for consumer in resource.consumers}
        process_root = find_process_root(ROOT)
        if process_root is not None:
            pages.update(
                page
                for page in (
                    process_root / "docs/superpowers/audits/code-resource-reader-test.md",
                    process_root / "docs/superpowers/audits/code-resource-reader-test.json",
                )
                if page.is_file()
            )
        for page in pages:
            text = page.read_text(encoding="utf-8")
            revisions = re.findall(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", text)
            self.assertTrue(all(found == revision for found in revisions), page)

    def test_public_source_integrity_rejects_process_roots_and_non_code_top_level_dirs(self) -> None:
        from validate_code_resources import validate_public_source_tree

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "ros2").mkdir()
            (source / "tests").mkdir()
            self.assertTrue(any("tests" in error for error in validate_public_source_tree(source)))
            (source / "tests").rmdir()
            (source / "docs").mkdir()
            self.assertTrue(any("docs" in error for error in validate_public_source_tree(source)))
            (source / "docs").rmdir()
            (source / ".github").mkdir()
            self.assertTrue(any(".github" in error for error in validate_public_source_tree(source)))
            (source / ".github").rmdir()
            (source / "ros2" / "config").mkdir(parents=True)
            self.assertEqual(validate_public_source_tree(source), [])

        current = find_source_root(ROOT)
        if current is not None:
            self.assertEqual(validate_public_source_tree(current), [])
