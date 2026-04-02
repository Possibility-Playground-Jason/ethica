# ABOUTME: Tests for the ethica API server endpoints
# ABOUTME: Uses FastAPI TestClient to verify health, frameworks, and check endpoints

"""
Tests for ethica API server.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from ethica.api.server import app

httpx = pytest.importorskip("httpx")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestFrameworksEndpoint:
    def test_list_frameworks(self):
        response = client.get("/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(fw["id"] == "unesco-2021" for fw in data)


class TestCheckEndpoint:
    def test_check_invalid_repo_url(self):
        """Requesting a non-existent repo returns 422."""
        response = client.post(
            "/check",
            json={
                "repo_url": "https://example.com/nonexistent/repo.git",
                "framework": "unesco-2021",
            },
        )
        assert response.status_code == 422
        assert "clone" in response.json()["detail"].lower()

    def test_check_invalid_framework(self):
        """Requesting a non-existent framework returns 404."""
        response = client.post(
            "/check",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "framework": "nonexistent-framework",
            },
        )
        assert response.status_code == 404

    def test_check_compliant_local_repo(self, tmp_path):
        """Test the full check flow using a mocked clone that produces a compliant project."""
        # Set up a fake compliant project in tmp_path
        (tmp_path / "project").mkdir()
        project = tmp_path / "project"
        (project / ".git").mkdir()
        (project / "docs").mkdir()
        (project / "docs" / "MODEL_CARD.md").write_text("# Model Card")
        (project / "docs" / "PRIVACY_IMPACT_ASSESSMENT.md").write_text("# PIA")
        (project / "requirements.txt").write_text("shap>=0.40\nfairlearn>=0.8\n")
        (project / "README.md").write_text("# Test Project")
        (project / "LICENSE").write_text("MIT License")

        def fake_clone(repo_url, dest, ref=None):
            """Instead of cloning, copy our fixture into dest."""
            import shutil
            shutil.copytree(str(project), str(dest), dirs_exist_ok=True)

        with patch("ethica.api.server._clone_repo", side_effect=fake_clone):
            response = client.post(
                "/check",
                json={
                    "repo_url": "https://example.com/fake/repo.git",
                    "framework": "unesco-2021",
                    "compliance_level": "standard",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ("passed", "passed with warnings")
        assert data["pass_rate"] > 0
        assert "request" in data
        assert data["request"]["repo_url"] == "https://example.com/fake/repo.git"
        assert "compliance" in data
        assert data["compliance"]["level"] == "standard"

    def test_check_report_returns_html(self, tmp_path):
        """HTML report card endpoint returns valid HTML."""
        (tmp_path / "project").mkdir()
        project = tmp_path / "project"
        (project / ".git").mkdir()
        (project / "README.md").write_text("# Test")

        def fake_clone(repo_url, dest, ref=None):
            import shutil
            shutil.copytree(str(project), str(dest), dirs_exist_ok=True)

        with patch("ethica.api.server._clone_repo", side_effect=fake_clone):
            response = client.post(
                "/check/report",
                json={
                    "repo_url": "https://example.com/fake/repo.git",
                    "framework": "unesco-2021",
                },
            )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Ethica Report Card" in response.text
        assert "unesco-2021" in response.text

    def test_check_badge_returns_svg(self, tmp_path):
        """Badge endpoint returns an SVG image."""
        (tmp_path / "project").mkdir()
        project = tmp_path / "project"
        (project / ".git").mkdir()
        (project / "README.md").write_text("# Test")

        def fake_clone(repo_url, dest, ref=None):
            import shutil
            shutil.copytree(str(project), str(dest), dirs_exist_ok=True)

        with patch("ethica.api.server._clone_repo", side_effect=fake_clone):
            response = client.post(
                "/check/badge",
                json={
                    "repo_url": "https://example.com/fake/repo.git",
                    "framework": "unesco-2021",
                },
            )

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        assert "<svg" in response.text
        assert "ethica" in response.text

    def test_badge_get_endpoint(self, tmp_path):
        """GET /badge/:owner/:repo returns SVG and builds correct clone URL."""
        (tmp_path / "project").mkdir()
        project = tmp_path / "project"
        (project / ".git").mkdir()
        (project / "README.md").write_text("# Test")

        captured_urls = []

        def fake_clone(repo_url, dest, ref=None):
            captured_urls.append(repo_url)
            import shutil
            shutil.copytree(str(project), str(dest), dirs_exist_ok=True)

        with patch("ethica.api.server._clone_repo", side_effect=fake_clone):
            response = client.get("/badge/octocat/Hello-World")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        assert "<svg" in response.text
        assert captured_urls[0] == "https://github.com/octocat/Hello-World.git"

    def test_badge_get_invalid_owner(self):
        """GET /badge with invalid characters returns 400."""
        response = client.get("/badge/bad%20owner/repo")
        assert response.status_code == 400

    def test_check_non_compliant_local_repo(self, tmp_path):
        """An empty project should fail most checks."""
        (tmp_path / "project").mkdir()
        project = tmp_path / "project"

        def fake_clone(repo_url, dest, ref=None):
            import shutil
            shutil.copytree(str(project), str(dest), dirs_exist_ok=True)

        with patch("ethica.api.server._clone_repo", side_effect=fake_clone):
            response = client.post(
                "/check",
                json={
                    "repo_url": "https://example.com/fake/empty.git",
                    "framework": "unesco-2021",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "failed"
        assert data["checks_failed"] > 0
