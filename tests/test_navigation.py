from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import quality  # noqa: E402


def linked_markdown_paths(path: Path) -> set[Path]:
    targets: set[Path] = set()
    text = path.read_text(encoding="utf-8")
    for match in quality.LINK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        path_part = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if path_part:
            targets.add((path.parent / path_part).resolve())
    return targets


class NavigationTests(unittest.TestCase):
    def test_numbered_chapters_link_to_previous_and_next(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        numbered = [
            row for row in rows if row["kind"] in {"foundation", "chapter"}
        ]
        self.assertEqual(len(numbered), 51)
        for index, row in enumerate(numbered):
            path = ROOT / row["path"]
            links = linked_markdown_paths(path)
            if index > 0:
                self.assertIn((ROOT / numbered[index - 1]["path"]).resolve(), links, row["path"])
            if index < len(numbered) - 1:
                self.assertIn((ROOT / numbered[index + 1]["path"]).resolve(), links, row["path"])

    def test_engineering_chapter_does_not_require_a_later_chapter(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        offenders: list[str] = []
        pattern = re.compile(r"(?:已完成|完成|先完成|已经通过|先读|先阅读)第\s*(\d+)\s*章")
        for row in rows:
            if row["kind"] != "chapter":
                continue
            number = int(row["number"])
            text = (ROOT / row["path"]).read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                if int(match.group(1)) > number:
                    offenders.append(
                        f"{row['path']}: Chapter {number} requires Chapter {match.group(1)}"
                    )
        self.assertEqual(offenders, [])

    def test_public_copy_uses_ten_parts_and_no_legacy_labels(self) -> None:
        paths = sorted((ROOT / "docs").rglob("*.md"))
        paths.extend((ROOT / name) for name in ("README.md", "mkdocs.yml"))
        offenders: list[str] = []
        pattern = re.compile(r"卷零|卷[一二三四五六七八]|返回本卷|下一卷|(?:^|[：\s])T[1-4](?:[：.\s]|$)")
        for path in paths:
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_mkdocs_has_ten_parts_and_51_numbered_entries(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^  - 第(?:[一二三四五六七八九]|十)篇 ", config, re.MULTILINE)), 10)
        self.assertEqual(len(re.findall(r"^      - (?:[1-9]|[1-4][0-9]|50|51) ", config, re.MULTILINE)), 51)

    def test_entry_pages_use_current_paths(self) -> None:
        combined = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ("README.md", "docs/index.md", "docs/reading-paths.md")
        )
        for path in (
            "01-foundations",
            "02-hardware-basics",
            "03-bringup",
            "05-ros2-development",
            "06-sensors-navigation",
            "09-r680-platform",
            "10-deployment-maintenance",
        ):
            self.assertIn(path, combined)
        self.assertNotIn("00-ros2-theory", combined)
        homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        self.assertIn("## 第一次学习 ROS 2", homepage)
        expected = [
            "01-understanding-ros.md",
            "02-robot-system-overview.md",
            "03-ubuntu-terminal-programs.md",
            "04-first-ros2-observation.md",
            "05-ros2-communication.md",
        ]
        positions = [homepage.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))

    def test_one_shot_migration_tools_are_not_shipped(self) -> None:
        self.assertFalse((ROOT / "tools" / "rewrite_navigation.py").exists())
        self.assertFalse((ROOT / "tools" / "renumber_textbook.py").exists())

    def test_reading_paths_include_all_five_required_sequences(self) -> None:
        text = (ROOT / "docs" / "reading-paths.md").read_text(encoding="utf-8")
        for heading in (
            "第一次学习 ROS 2",
            "已熟悉 Linux，刚开始学 ROS 2",
            "已熟悉 ROS 2，第一次接入机器人",
            "建图与导航",
            "R680 维护",
        ):
            self.assertIn(f"## {heading}", text)
        for sequence in (
            "1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10",
            "1 → 4 → 5 → 22",
            "10 → 11 → 12 → 13 → 14",
            "29 → 30 → 31 → 32 → 33",
            "10 → 21 → 47 → 48 → 50",
        ):
            self.assertIn(sequence, text)
        self.assertGreaterEqual(text.count("前置能力"), 3)


if __name__ == "__main__":
    unittest.main()
