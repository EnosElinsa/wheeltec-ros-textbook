from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import quality  # noqa: E402


FINAL_PARTS = [
    "01-foundations",
    "02-bringup",
    "03-chassis-control",
    "04-ros2-development",
    "05-sensors-navigation",
    "06-stm32-firmware",
    "07-advanced-applications",
    "08-r680-platform",
    "09-deployment-maintenance",
]


class RenumberingTests(unittest.TestCase):
    def test_manifest_has_contiguous_chapters_1_to_46(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        numbered = [
            int(row["number"])
            for row in rows
            if row["kind"] in {"foundation", "chapter"}
        ]
        self.assertEqual(numbered, list(range(1, 47)))
        self.assertEqual(quality.check_manifest(rows), [])

    def test_final_part_directories_exist(self) -> None:
        for name in FINAL_PARTS:
            self.assertTrue((ROOT / "docs" / name / "index.md").is_file(), name)

    def test_filename_and_h1_match_manifest_number(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        for row in rows:
            if row["kind"] not in {"foundation", "chapter"}:
                continue
            number = int(row["number"])
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertTrue(path.name.startswith(f"{number:02d}-"), row["path"])
            h1 = next(
                line for line in path.read_text(encoding="utf-8").splitlines()
                if line.startswith("# ")
            )
            self.assertRegex(h1, rf"^# {number}\.\s+")

    def test_no_engineering_page_remains_in_old_part_directories(self) -> None:
        old_directories = (
            "01-bringup",
            "02-chassis-control",
            "03-ros2-development",
            "04-sensors-navigation",
            "05-stm32-firmware",
            "06-advanced-applications",
            "07-r680-platform",
            "08-deployment-maintenance",
        )
        leftovers: list[str] = []
        for name in old_directories:
            directory = ROOT / "docs" / name
            if directory.exists():
                leftovers.extend(
                    path.relative_to(ROOT).as_posix()
                    for path in directory.glob("[0-9][0-9]-*.md")
                )
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
