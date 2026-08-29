from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SOURCE_REVISION = "667b1ffceb4354c19ef8f0e94969fcd25cbb5d6b"


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
        self.assertIn("separate", validation.lower())

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

    def test_run_code_resource_validation_is_read_only_and_reports_errors(self) -> None:
        from validate_code_resources import run_code_resource_validation

        source = ROOT.parent / "code-resource-curation-source"
        before = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
        self.assertEqual(run_code_resource_validation(ROOT, source), 0)
        after = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
        self.assertEqual(before, after)
