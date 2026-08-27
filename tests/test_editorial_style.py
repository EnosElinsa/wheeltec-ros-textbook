from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import editorial_audit  # noqa: E402
import quality  # noqa: E402


class EditorialScannerTests(unittest.TestCase):
    def test_invalid_fixture_reports_prohibited_editorial_patterns(self) -> None:
        issues = editorial_audit.scan_markdown(
            ROOT / "tests" / "fixtures" / "editorial-invalid.md"
        )
        categories = {issue.category for issue in issues}
        self.assertEqual(
            categories,
            {
                "colloquial terminology",
                "chapter meta-negation",
                "exercise meta-negation",
                "filler emphasis",
                "reader prediction",
                "inflated technical prose",
                "source-material framing",
            },
        )

    def test_valid_fixture_allows_safety_prohibition_and_formal_term(self) -> None:
        issues = editorial_audit.scan_markdown(
            ROOT / "tests" / "fixtures" / "editorial-valid.md"
        )
        self.assertEqual(issues, [])

    def test_protected_content_comparison_detects_code_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            before_path = Path(temp_dir) / "before.md"
            after_path = Path(temp_dir) / "after.md"
            before_path.write_text("```bash\necho safe\n```\n", encoding="utf-8")
            after_path.write_text("```bash\necho changed\n```\n", encoding="utf-8")
            before = [editorial_audit.extract_protected_content(before_path)]
            after = [editorial_audit.extract_protected_content(after_path)]
            differences = editorial_audit.compare_protected_content(before, after)
            self.assertEqual(len(differences), 1)
            self.assertIn("fenced code", differences[0])

    def test_quality_exposes_editorial_strict_check(self) -> None:
        issues = quality.check_editorial_style(
            ROOT / "tests" / "fixtures" / "editorial-invalid.md"
        )
        self.assertGreaterEqual(len(issues), 6)


if __name__ == "__main__":
    unittest.main()
