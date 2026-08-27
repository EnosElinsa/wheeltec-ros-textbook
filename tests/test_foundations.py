from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import quality  # noqa: E402


class FoundationSchemaTests(unittest.TestCase):
    def test_valid_foundation_passes_teaching_schema(self) -> None:
        issues = quality.check_foundation(
            ROOT / "tests" / "fixtures" / "valid-foundation.md", 150_000
        )
        self.assertEqual(issues, [])

    def test_invalid_foundation_reports_each_dependency_category(self) -> None:
        issues = quality.check_foundation(
            ROOT / "tests" / "fixtures" / "invalid-foundation.md", 150_000
        )
        messages = [issue.message for issue in issues]
        for category in (
            "later chapter prerequisite",
            "advanced middleware jargon",
            "required SSH access",
            "required robot runtime",
        ):
            self.assertTrue(
                any(category in message for message in messages),
                f"missing issue category: {category}",
            )

    def test_final_manifest_layout_accepts_foundations_1_to_5(self) -> None:
        rows: list[dict[str, str]] = []
        for number in range(1, 6):
            rows.append(
                {
                    "kind": "foundation",
                    "number": str(number),
                    "volume": "01-foundations",
                    "path": f"docs/01-foundations/{number:02d}.md",
                    "title": f"基础 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        for number in range(6, 47):
            rows.append(
                {
                    "kind": "chapter",
                    "number": str(number),
                    "volume": "02-bringup",
                    "path": f"docs/02-bringup/{number:02d}.md",
                    "title": f"工程 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        for number in ("A", "B", "C"):
            rows.append(
                {
                    "kind": "appendix",
                    "number": number,
                    "volume": "appendices",
                    "path": f"docs/appendices/{number.lower()}.md",
                    "title": f"附录 {number}",
                    "status": "complete",
                    "size_limit_bytes": "150000",
                }
            )
        self.assertEqual(quality.check_manifest(rows), [])


if __name__ == "__main__":
    unittest.main()
