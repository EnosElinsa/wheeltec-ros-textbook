from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MathRenderingTests(unittest.TestCase):
    def test_mkdocs_enables_arithmatex_and_mathjax(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        mathjax = ROOT / "docs" / "javascripts" / "mathjax.js"

        self.assertIn("pymdownx.arithmatex:", config)
        self.assertIn("generic: true", config)
        self.assertIn("- javascripts/mathjax.js", config)
        self.assertIn("- https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js", config)
        self.assertTrue(mathjax.is_file())
        script = mathjax.read_text(encoding="utf-8")
        self.assertIn('processHtmlClass: "arithmatex"', script)
        self.assertIn("document$.subscribe", script)

    def test_display_formula_uses_supported_block_delimiters(self) -> None:
        chapter = (
            ROOT / "docs" / "03-chassis-control" / "11-coordinate-frames-and-chassis.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "$$\nv_L = v_x - \\frac{W}{2}\\omega_z,\\qquad\nv_R = v_x + \\frac{W}{2}\\omega_z\n$$",
            chapter,
        )


if __name__ == "__main__":
    unittest.main()
