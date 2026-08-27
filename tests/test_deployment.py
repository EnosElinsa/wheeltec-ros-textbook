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
            "python tools/generate_redirects.py --mapping metadata/legacy-redirects.csv --site-dir site",
            "path: site",
            "actions/upload-pages-artifact@v4",
            "actions/deploy-pages@v4",
        ):
            self.assertIn(expected, workflow)

    def test_redirect_step_runs_after_build_and_before_artifact_upload(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-docs.yml").read_text(
            encoding="utf-8"
        )
        self.assertLess(workflow.index("mkdocs build --strict"), workflow.index("generate_redirects.py"))
        self.assertLess(workflow.index("generate_redirects.py"), workflow.index("upload-pages-artifact"))

    def test_site_deployment_infrastructure_is_not_a_textbook_chapter(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertNotIn("github-pages-deployment.md", config)
        self.assertFalse(
            (ROOT / "docs" / "09-deployment-maintenance" / "github-pages-deployment.md").exists()
        )

    def test_local_build_runs_redirect_generation_after_mkdocs(self) -> None:
        script = (ROOT / "tools" / "build_site.ps1").read_text(encoding="utf-8")
        self.assertIn("generate_redirects.py", script)
        self.assertLess(script.index("build --strict"), script.index("generate_redirects.py"))


if __name__ == "__main__":
    unittest.main()
