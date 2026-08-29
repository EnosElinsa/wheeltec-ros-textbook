from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import quality  # noqa: E402
import scaffold  # noqa: E402


class ManifestTests(unittest.TestCase):
    def test_manifest_has_9_foundations_41_engineering_chapters_and_4_appendices(self) -> None:
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        foundations = [row for row in rows if row["kind"] == "foundation"]
        chapters = [row for row in rows if row["kind"] == "chapter"]
        appendices = [row for row in rows if row["kind"] == "appendix"]

        self.assertEqual([int(row["number"]) for row in foundations], list(range(1, 10)))
        self.assertEqual([int(row["number"]) for row in chapters], list(range(10, 51)))
        self.assertLess(rows.index(foundations[-1]), rows.index(chapters[0]))
        self.assertEqual([row["number"] for row in appendices], ["A", "B", "C", "D"])
        self.assertEqual(len({row["path"] for row in rows}), len(rows))
        self.assertEqual(quality.check_manifest(rows), [])

    def test_scaffold_creates_pages_without_overwriting_existing_files(self) -> None:
        rows = [
            {
                "kind": "chapter",
                "number": "10",
                "volume": "03-bringup",
                "path": "docs/03-bringup/10-identify-configuration.md",
                "title": "识别你的机器人配置",
                "status": "draft",
                "size_limit_bytes": "150000",
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = scaffold.create_pages(rows, root)
            chapter = root / rows[0]["path"]
            volume_index = root / "docs" / "03-bringup" / "index.md"
            self.assertEqual(created, [chapter, volume_index])
            self.assertIn("status: draft", chapter.read_text(encoding="utf-8"))
            chapter.write_text("保留现有内容", encoding="utf-8")
            self.assertEqual(scaffold.create_pages(rows, root), [])
            self.assertEqual(chapter.read_text(encoding="utf-8"), "保留现有内容")

    def test_set_status_updates_only_selected_volume(self) -> None:
        rows = [
            {
                "kind": "chapter",
                "number": "10",
                "volume": "03-bringup",
                "path": "docs/03-bringup/06.md",
                "title": "第一章",
                "status": "draft",
                "size_limit_bytes": "150000",
            },
            {
                "kind": "chapter",
                "number": "15",
                "volume": "04-chassis-control",
                "path": "docs/04-chassis-control/11.md",
                "title": "第十一章",
                "status": "draft",
                "size_limit_bytes": "150000",
            },
        ]
        changed = scaffold.set_status(rows, "volume", "03-bringup", "complete")
        self.assertEqual(changed, 1)
        self.assertEqual(rows[0]["status"], "complete")
        self.assertEqual(rows[1]["status"], "draft")


class ChapterQualityTests(unittest.TestCase):
    def test_valid_chapter_passes_schema_check(self) -> None:
        issues = quality.check_chapter(
            ROOT / "tests" / "fixtures" / "valid-chapter.md", 150_000, 6
        )
        self.assertEqual(issues, [])

    def test_invalid_chapter_reports_missing_section_and_promotional_copy(self) -> None:
        issues = quality.check_chapter(
            ROOT / "tests" / "fixtures" / "invalid-chapter.md", 150_000, 6
        )
        messages = [issue.message for issue in issues]
        self.assertIn("missing section: 6.6 验收标准", messages)
        self.assertIn("supplier promotional copy is not allowed", messages)

    def test_broken_internal_markdown_link_is_reported(self) -> None:
        issues = quality.check_links(
            ROOT / "tests" / "fixtures" / "invalid-chapter.md", ROOT / "tests" / "fixtures"
        )
        self.assertEqual(len(issues), 1)
        self.assertIn("missing.md", issues[0].message)

    def test_file_over_size_limit_is_reported(self) -> None:
        issues = quality.check_chapter(
            ROOT / "tests" / "fixtures" / "valid-chapter.md", 100, 6
        )
        self.assertIn("file exceeds size limit", [issue.message for issue in issues])

    def test_mkdocs_nav_contains_every_manifest_page(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        rows = quality.load_manifest(ROOT / "metadata" / "chapter-manifest.csv")
        missing = [row["path"].removeprefix("docs/") for row in rows if row["path"].removeprefix("docs/") not in config]
        self.assertEqual(missing, [])

    def test_entry_pages_stay_within_size_limits(self) -> None:
        self.assertLessEqual((ROOT / "docs" / "index.md").stat().st_size, 20_000)
        for volume_index in sorted((ROOT / "docs").glob("[0-9][0-9]-*/index.md")):
            self.assertLessEqual(volume_index.stat().st_size, 30_000)


if __name__ == "__main__":
    unittest.main()
