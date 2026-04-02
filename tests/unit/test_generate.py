# ABOUTME: Tests for project introspection and card generation
# ABOUTME: Verifies that project metadata is extracted and cards are pre-filled correctly

"""
Tests for ethica generate functionality.
"""

import json
from pathlib import Path

from ethica.utils.introspect import introspect_project
from ethica.utils.generate import generate_card


class TestIntrospect:
    def test_detects_python_project(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("torch>=2.0\nshap>=0.40\nfairlearn>=0.8\n")
        (tmp_path / "README.md").write_text("# My ML Project\n\nA cool project that does stuff.")

        profile = introspect_project(tmp_path)

        assert "python" in profile["project_types"]
        assert "torch" in profile["ai_libraries"]
        assert "shap" in profile["explainability_libraries"]
        assert "fairlearn" in profile["fairness_libraries"]
        assert profile["description"] == "A cool project that does stuff."

    def test_detects_node_project(self, tmp_path):
        pkg = {
            "name": "my-ai-app",
            "description": "An AI-powered widget",
            "license": "MIT",
            "dependencies": {"openai": "^4.0", "react": "^18.0"},
            "devDependencies": {"jest": "^29.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        profile = introspect_project(tmp_path)

        assert "nodejs" in profile["project_types"]
        assert "openai" in profile["ai_libraries"]
        assert profile["description"] == "An AI-powered widget"
        assert profile["license"] == "MIT"

    def test_detects_tests_and_ci(self, tmp_path):
        (tmp_path / "tests").mkdir()
        (tmp_path / ".github" / "workflows").mkdir(parents=True)

        profile = introspect_project(tmp_path)

        assert profile["has_tests"] is True
        assert profile["has_ci"] is True

    def test_empty_project(self, tmp_path):
        profile = introspect_project(tmp_path)

        assert profile["project_types"] == []
        assert profile["ai_libraries"] == []
        assert profile["description"] == ""

    def test_license_from_file(self, tmp_path):
        (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright ...")

        profile = introspect_project(tmp_path)

        assert profile["license"] == "MIT"


class TestGenerateCard:
    def test_generates_model_card_for_ml_project(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("torch>=2.0\nshap>=0.40\n")
        (tmp_path / "README.md").write_text("# My Model\n\nPredicts things.")
        (tmp_path / "tests").mkdir()

        profile = introspect_project(tmp_path)
        card = generate_card(profile)

        assert "# Model Card:" in card
        assert "torch" in card
        assert "shap" in card
        assert "Predicts things." in card
        assert "Test suite detected" in card
        assert "[TODO" in card  # still has placeholders

    def test_generates_system_card_for_non_ml_project(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"my-app","dependencies":{"react":"^18"}}')

        profile = introspect_project(tmp_path)
        card = generate_card(profile)

        assert "# System Card:" in card
        assert "[TODO" in card

    def test_card_includes_fairness_section(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("torch>=2.0\nfairlearn>=0.8\n")

        profile = introspect_project(tmp_path)
        card = generate_card(profile)

        assert "fairlearn" in card
        assert "Fairness" in card

    def test_card_footer_credits_ethica(self, tmp_path):
        profile = introspect_project(tmp_path)
        card = generate_card(profile)

        assert "Ethica" in card
        assert "[TODO]" in card
