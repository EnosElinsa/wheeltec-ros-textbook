from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PUBLIC_FILES = (
    "docs/appendices/d-resource-catalog.md",
    "docs/appendices/e-hardware-reference.md",
    "docs/appendices/f-source-provenance.md",
    "docs/appendices/humanizer-audit.md",
    "metadata/chapter-source-map.csv",
    "metadata/source-catalog.csv",
    "metadata/resource-map.csv",
    "metadata/duplicate-groups.csv",
    "metadata/image-attribution.csv",
)
FORBIDDEN_TEXT_PATTERNS = {
    "internal resource ID": re.compile(r"(?<![A-Za-z0-9])[GR]:(?:video|archive|firmware|software|dataset|document|image|code-file|supplementary|other):\d{4}\b"),
    "internal PDF source ID": re.compile(r"(?<![A-Za-z0-9])[GR]:\d{2}-[a-z0-9-]+-doc-\d{4}\b"),
    "local source library": re.compile(r"wheeltec-(?:ros-general|r680)-course"),
    "removed video/resource section": re.compile(r"^##\s+相关视频、代码和固件\s*$", re.MULTILINE),
    "removed provenance section": re.compile(r"^##\s+来源与延伸阅读\s*$", re.MULTILINE),
}


class PublicSiteHygieneTests(unittest.TestCase):
    def test_readme_is_a_reader_facing_entry_page(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://enoselinsa.github.io/wheeltec-ros-textbook/", readme)
        self.assertIn("## 教材结构", readme)
        self.assertIn("第一篇", readme)
        self.assertIn("第九篇", readme)
        self.assertNotIn("卷零", readme)
        self.assertIn("## 本地预览", readme)

    def test_internal_reference_files_are_not_public(self) -> None:
        present = [path for path in FORBIDDEN_PUBLIC_FILES if (ROOT / path).exists()]
        self.assertEqual(present, [])
        checkpoint_files = list((ROOT / "metadata" / "checkpoints").glob("*"))
        self.assertEqual(checkpoint_files, [])

    def test_public_text_has_no_internal_resource_references(self) -> None:
        offenders: list[str] = []
        paths = sorted((ROOT / "docs").rglob("*.md"))
        paths.extend((ROOT / name) for name in ("README.md", "mkdocs.yml"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for label, pattern in FORBIDDEN_TEXT_PATTERNS.items():
                if pattern.search(text):
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}: {label}")
        self.assertEqual(offenders, [])

    def test_removed_appendices_are_not_in_navigation(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        for name in (
            "d-resource-catalog.md",
            "e-hardware-reference.md",
            "f-source-provenance.md",
            "humanizer-audit.md",
        ):
            self.assertNotIn(name, config)

    def test_public_text_is_independent_of_source_material_framing(self) -> None:
        offenders: list[str] = []
        pattern = re.compile(
            r"(?:资料中|资料包中|当前资料|随货资料|本机资料中|用户资料|原始资料)"
        )
        for path in sorted((ROOT / "docs").rglob("*.md")):
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
