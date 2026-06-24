"""Unit tests to validate deployment configurations, files, and templates.
"""

import os
import unittest


class TestDeploymentValidation(unittest.TestCase):
    """Checks that all deployment assets are validly structured and present."""

    def setUp(self) -> None:
        self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_dockerfile_existence_and_structure(self) -> None:
        """Verifies Dockerfile exists and contains required keywords."""
        dockerfile_path = os.path.join(self.workspace_dir, "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path), "Dockerfile is missing.")

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("FROM", content)
        self.assertIn("ENV", content)
        self.assertIn("EXPOSE", content)
        self.assertIn("CMD", content)

    def test_dockerignore_existence(self) -> None:
        """Verifies .dockerignore exists and ignores sensitive files."""
        dockerignore_path = os.path.join(self.workspace_dir, ".dockerignore")
        self.assertTrue(os.path.exists(dockerignore_path), ".dockerignore is missing.")

        with open(dockerignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(".git", content)
        self.assertIn(".env", content)
        self.assertIn("venv", content)

    def test_env_example_existence_and_keys(self) -> None:
        """Verifies env.example exists and contains configuration placeholders."""
        env_example_path = os.path.join(self.workspace_dir, "env.example")
        self.assertTrue(os.path.exists(env_example_path), "env.example is missing.")

        with open(env_example_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("PORT", content)
        self.assertIn("GCP_PROJECT", content)
        self.assertIn("GCP_REGION", content)
        self.assertIn("CHROMADB_PERSIST_DIR", content)

    def test_deploy_script_existence(self) -> None:
        """Verifies deploy.sh exists and is present."""
        deploy_sh_path = os.path.join(self.workspace_dir, "deploy.sh")
        self.assertTrue(os.path.exists(deploy_sh_path), "deploy.sh is missing.")


if __name__ == "__main__":
    unittest.main()
