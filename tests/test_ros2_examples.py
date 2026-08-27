from __future__ import annotations

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "ros2-pubsub"
REPOSITORY_URL = "https://github.com/EnosElinsa/wheeltec-ros-textbook"


def package_metadata(package_dir: Path) -> tuple[str, str, set[str], str]:
    root = ET.parse(package_dir / "package.xml").getroot()
    name = root.findtext("name", default="")
    license_name = root.findtext("license", default="")
    dependencies = {
        element.text or ""
        for tag in ("depend", "buildtool_depend")
        for element in root.findall(tag)
    }
    build_type = root.findtext("./export/build_type", default="")
    return name, license_name, dependencies, build_type


def python_console_scripts(setup_path: Path) -> set[str]:
    tree = ast.parse(setup_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg != "entry_points" or not isinstance(keyword.value, ast.Dict):
                continue
            entries = ast.literal_eval(keyword.value)
            return {
                entry.split("=", 1)[0].strip()
                for entry in entries.get("console_scripts", [])
            }
    return set()


def setup_keyword_literal(setup_path: Path, keyword_name: str):
    tree = ast.parse(setup_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == keyword_name:
                return ast.literal_eval(keyword.value)
    return None


class Ros2ExampleBundleTests(unittest.TestCase):
    def test_bundle_contains_one_buildable_package_per_language(self) -> None:
        self.assertTrue(EXAMPLES.is_dir(), "ROS 2 example bundle is missing")

        cpp = EXAMPLES / "cpp_pubsub"
        python = EXAMPLES / "py_pubsub"
        self.assertEqual(
            package_metadata(cpp),
            ("cpp_pubsub", "MIT", {"ament_cmake", "rclcpp", "std_msgs"}, "ament_cmake"),
        )
        self.assertEqual(
            package_metadata(python),
            ("py_pubsub", "MIT", {"rclpy", "std_msgs"}, "ament_python"),
        )
        self.assertTrue((cpp / "CMakeLists.txt").is_file())
        self.assertTrue((cpp / "src" / "publisher.cpp").is_file())
        self.assertTrue((cpp / "src" / "subscriber.cpp").is_file())
        self.assertEqual(
            python_console_scripts(python / "setup.py"),
            {"talker", "listener"},
        )
        self.assertEqual(
            setup_keyword_literal(python / "setup.py", "tests_require"),
            ["pytest"],
        )
        self.assertTrue((python / "py_pubsub" / "publisher.py").is_file())
        self.assertTrue((python / "py_pubsub" / "subscriber.py").is_file())

    def test_bundle_is_clean_and_has_an_explicit_redistribution_license(self) -> None:
        self.assertTrue((EXAMPLES / "LICENSE").is_file())
        forbidden_names = {"build", "install", "log", "__pycache__"}
        offenders = [
            path.relative_to(EXAMPLES).as_posix()
            for path in EXAMPLES.rglob("*")
            if path.name in forbidden_names or path.suffix == ".pyc"
        ]
        self.assertEqual(offenders, [])

        source_files = [
            path
            for path in EXAMPLES.rglob("*")
            if path.is_file() and path.suffix in {".cpp", ".py", ".xml", ".txt"}
        ]
        placeholders = [
            path.relative_to(EXAMPLES).as_posix()
            for path in source_files
            if "TODO" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(placeholders, [])

    def test_chapters_link_to_the_repository_examples(self) -> None:
        chapter_19 = (ROOT / "docs/04-ros2-development/19-workspace-packages-build.md").read_text(
            encoding="utf-8"
        )
        chapter_20 = (ROOT / "docs/04-ros2-development/20-nodes-topics-services-actions.md").read_text(
            encoding="utf-8"
        )
        cpp_url = f"{REPOSITORY_URL}/tree/main/examples/ros2-pubsub/cpp_pubsub"
        python_url = f"{REPOSITORY_URL}/tree/main/examples/ros2-pubsub/py_pubsub"
        for text in (chapter_19, chapter_20):
            self.assertIn(cpp_url, text)
            self.assertIn(python_url, text)


if __name__ == "__main__":
    unittest.main()
