from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_redirects  # noqa: E402


class RedirectTests(unittest.TestCase):
    def test_map_has_unique_sources_and_no_redirect_chains(self) -> None:
        rows = generate_redirects.load_redirects(
            ROOT / "metadata" / "legacy-redirects.csv"
        )
        self.assertEqual(generate_redirects.validate_map(rows), [])
        self.assertEqual(len(rows), 56)

    def test_map_rejects_duplicate_source_and_redirect_chain(self) -> None:
        rows = [
            generate_redirects.Redirect("old/", "middle/"),
            generate_redirects.Redirect("old/", "new/"),
            generate_redirects.Redirect("middle/", "new/"),
        ]
        messages = generate_redirects.validate_map(rows)
        self.assertTrue(any("duplicate source" in message for message in messages))
        self.assertTrue(any("redirect chain" in message for message in messages))

    def test_map_rejects_absolute_and_traversal_paths(self) -> None:
        rows = [
            generate_redirects.Redirect("/old/", "new/"),
            generate_redirects.Redirect("other/", "../escape/"),
        ]
        messages = generate_redirects.validate_map(rows)
        self.assertEqual(len(messages), 2)

    def test_rendered_redirect_preserves_query_and_hash(self) -> None:
        html = generate_redirects.render_redirect(
            "00-ros2-theory/t1-what-is-ros2/",
            "01-foundations/03-what-ros2-solves/",
        )
        self.assertIn('rel="canonical"', html)
        self.assertIn('http-equiv="refresh"', html)
        self.assertIn("location.search + location.hash", html)

    def test_built_target_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            site = Path(temp_dir)
            target = (
                site
                / "01-foundations"
                / "03-what-ros2-solves"
                / "index.html"
            )
            target.parent.mkdir(parents=True)
            target.write_text("new page", encoding="utf-8")
            rows = [
                generate_redirects.Redirect(
                    "00-ros2-theory/t1-what-is-ros2/",
                    "01-foundations/03-what-ros2-solves/",
                )
            ]
            self.assertEqual(
                generate_redirects.validate_built_targets(rows, site), []
            )

    def test_writer_refuses_to_overwrite_real_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            site = Path(temp_dir)
            source = site / "old" / "index.html"
            target = site / "new" / "index.html"
            source.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            source.write_text("real page", encoding="utf-8")
            target.write_text("new page", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                generate_redirects.write_redirects(
                    [generate_redirects.Redirect("old/", "new/")], site
                )


if __name__ == "__main__":
    unittest.main()
