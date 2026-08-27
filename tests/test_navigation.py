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
        self.assertEqual(len(numbered), 46)
        for index, row in enumerate(numbered):
            path = ROOT / row["path"]
            links = linked_markdown_paths(path)
            if index > 0:
                self.assertIn((ROOT / numbered[index - 1]["path"]).resolve(), links, row["path"])
            if index < len(numbered) - 1:
                self.assertIn((ROOT / numbered[index + 1]["path"]).resolve(), links, row["path"])

    def test_public_copy_uses_nine_parts_and_no_legacy_labels(self) -> None:
        paths = sorted((ROOT / "docs").rglob("*.md"))
        paths.extend((ROOT / name) for name in ("README.md", "mkdocs.yml"))
        offenders: list[str] = []
        pattern = re.compile(r"卷零|卷[一二三四五六七八]|返回本卷|下一卷|(?:^|[：\s])T[1-4](?:[：.\s]|$)")
        for path in paths:
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_mkdocs_has_nine_parts_and_46_numbered_entries(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^  - 第[一二三四五六七八九]篇 ", config, re.MULTILINE)), 9)
        self.assertEqual(len(re.findall(r"^      - (?:[1-9]|[1-3][0-9]|4[0-6]) ", config, re.MULTILINE)), 46)

    def test_entry_pages_use_current_paths(self) -> None:
        combined = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ("README.md", "docs/index.md", "docs/reading-paths.md")
        )
        for path in (
            "01-foundations",
            "02-bringup",
            "04-ros2-development",
            "05-sensors-navigation",
            "08-r680-platform",
            "09-deployment-maintenance",
        ):
            self.assertIn(path, combined)
        self.assertNotIn("00-ros2-theory", combined)


if __name__ == "__main__":
    unittest.main()
