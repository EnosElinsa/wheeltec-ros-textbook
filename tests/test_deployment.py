from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentConfigurationTests(unittest.TestCase):
    def test_pages_workflow_builds_and_deploys_mkdocs_site(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-docs.yml").read_text(
            encoding="utf-8"
        )
        for expected in (
            "pages: write",
            "id-token: write",
            "pip install -r requirements.txt",
            "mkdocs build --strict",
            "path: site",
            "actions/upload-pages-artifact@v4",
            "actions/deploy-pages@v4",
        ):
            self.assertIn(expected, workflow)

    def test_deployment_page_is_exposed_in_volume_eight_navigation(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("42-github-pages-deployment.md", config)
        self.assertTrue(
            (ROOT / "docs" / "08-deployment-maintenance" / "42-github-pages-deployment.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
