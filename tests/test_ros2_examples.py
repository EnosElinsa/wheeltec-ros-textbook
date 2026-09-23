from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPOSITORY_URL = "https://github.com/EnosElinsa/wheeltec-ros-source-reference"
SOURCE_REVISION = "62aacaed782091b06060ace276c64e9aaf84ae6b"


class Ros2ExampleBundleTests(unittest.TestCase):
    def test_chapters_link_to_the_code_repository_examples(self) -> None:
        chapter_19 = (ROOT / "docs/05-ros2-development/23-workspace-packages-build.md").read_text(
            encoding="utf-8"
        )
        chapter_20 = (ROOT / "docs/05-ros2-development/24-nodes-topics-services-actions.md").read_text(
            encoding="utf-8"
        )
        cpp_url = f"{SOURCE_REPOSITORY_URL}/tree/{SOURCE_REVISION}/examples/ros2/pubsub/cpp"
        python_url = f"{SOURCE_REPOSITORY_URL}/tree/{SOURCE_REVISION}/examples/ros2/pubsub/python"
        for text in (chapter_19, chapter_20):
            self.assertIn(cpp_url, text)
            self.assertIn(python_url, text)
            self.assertNotIn("wheeltec-ros-textbook/tree/main/examples", text)

    def test_textbook_does_not_duplicate_code_bundle(self) -> None:
        self.assertFalse((ROOT / "examples").exists())


if __name__ == "__main__":
    unittest.main()
