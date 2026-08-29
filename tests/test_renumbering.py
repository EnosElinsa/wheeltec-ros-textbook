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
    "02-hardware-basics",
    "03-bringup",
    "04-chassis-control",
    "05-ros2-development",
    "06-sensors-navigation",
    "07-stm32-firmware",
    "08-advanced-applications",
    "09-r680-platform",
    "10-deployment-maintenance",
]


class RenumberingTests(unittest.TestCase):
    def test_foundation_manifest_uses_nine_foundation_filenames(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        first_part = [row for row in rows if row["kind"] == "foundation"]
        self.assertEqual(
            [row["path"] for row in first_part],
            [
                "docs/01-foundations/01-understanding-ros.md",
                "docs/01-foundations/02-robot-system-overview.md",
                "docs/01-foundations/03-ubuntu-terminal-programs.md",
                "docs/01-foundations/04-first-ros2-observation.md",
                "docs/01-foundations/05-ros2-communication.md",
                "docs/02-hardware-basics/06-controller-and-firmware.md",
                "docs/02-hardware-basics/07-electrical-interfaces-communication.md",
                "docs/02-hardware-basics/08-sensors-and-feedback.md",
                "docs/02-hardware-basics/09-chassis-motion-control.md",
            ],
        )

    def test_manifest_has_contiguous_chapters_1_to_50(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        numbered = [
            int(row["number"])
            for row in rows
            if row["kind"] in {"foundation", "chapter"}
        ]
        self.assertEqual(numbered, list(range(1, 51)))
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

    def test_engineering_chapters_use_numbered_task_sections(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        for row in rows:
            if row["kind"] != "chapter":
                continue
            number = int(row["number"])
            text = (ROOT / row["path"]).read_text(encoding="utf-8")
            headings = [
                re.sub(r"\s+\{#[^}]+\}$", "", heading)
                for heading in re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
            ]
            self.assertEqual(headings, quality.expected_engineering_headings(number))

    def test_no_engineering_page_remains_in_old_part_directories(self) -> None:
        old_directories = (
            "02-bringup",
            "03-chassis-control",
            "04-ros2-development",
            "05-sensors-navigation",
            "06-stm32-firmware",
            "07-advanced-applications",
            "08-r680-platform",
            "09-deployment-maintenance",
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
