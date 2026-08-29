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

    def test_pages_workflow_builds_before_artifact_upload_without_redirects(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-docs.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("generate_redirects.py", workflow)
        self.assertLess(workflow.index("mkdocs build --strict"), workflow.index("upload-pages-artifact"))

    def test_site_deployment_infrastructure_is_not_a_textbook_chapter(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertNotIn("github-pages-deployment.md", config)
        self.assertFalse(
            (ROOT / "docs" / "10-deployment-maintenance" / "github-pages-deployment.md").exists()
        )

    def test_local_build_runs_strict_mkdocs_without_redirects(self) -> None:
        script = (ROOT / "tools" / "build_site.ps1").read_text(encoding="utf-8")
        self.assertIn("build --strict", script)
        self.assertNotIn("generate_redirects.py", script)

    def test_legacy_redirect_subsystem_is_absent(self) -> None:
        for relative in (
            "metadata/legacy-redirects.csv",
            "tools/generate_redirects.py",
            "tests/test_redirects.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
