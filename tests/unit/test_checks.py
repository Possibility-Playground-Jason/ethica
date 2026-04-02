# ABOUTME: Unit tests for compliance checks
# ABOUTME: Tests file-exists and dependency-check implementations

"""
Tests for compliance checks.
"""

import pytest
from pathlib import Path

from ethica.checks.base import CheckStatus, CheckSeverity
from ethica.checks.file_checks import FileExistsCheck
from ethica.checks.dependency_checks import DependencyCheck


class TestFileExistsCheck:
    """Tests for FileExistsCheck"""

    def test_file_exists_pass(self, tmp_path):
        """Test that check passes when file exists"""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        check_spec = {
            "id": "test-001",
            "name": "Test File Check",
            "principle": "test",
            "severity": "error",
            "description": "Test check",
            "config": {
                "paths": ["test.md"]
            }
        }

        check = FileExistsCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "test.md" in result.message

    def test_file_exists_fail(self, tmp_path):
        """Test that check fails when file doesn't exist"""
        check_spec = {
            "id": "test-001",
            "name": "Test File Check",
            "principle": "test",
            "severity": "error",
            "description": "Test check",
            "config": {
                "paths": ["nonexistent.md"]
            }
        }

        check = FileExistsCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.FAILED
        assert "not found" in result.message.lower()
        assert result.suggestion is not None

    def test_file_exists_multiple_paths(self, tmp_path):
        """Test check with multiple possible paths"""
        # Create one of the files
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "file.md").write_text("content")

        check_spec = {
            "id": "test-001",
            "name": "Test File Check",
            "principle": "test",
            "severity": "error",
            "description": "Test check",
            "config": {
                "paths": ["file.md", "docs/file.md", "other/file.md"]
            }
        }

        check = FileExistsCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED

    def test_directory_exists(self, tmp_path):
        """Test that check works for directories"""
        # Create test directory
        test_dir = tmp_path / ".git"
        test_dir.mkdir()

        check_spec = {
            "id": "test-001",
            "name": "Test Dir Check",
            "principle": "test",
            "severity": "error",
            "description": "Test check",
            "config": {
                "paths": [".git"]
            }
        }

        check = FileExistsCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED


class TestDependencyCheck:
    """Tests for DependencyCheck"""

    def test_dependency_in_requirements(self, tmp_path):
        """Test finding dependency in requirements.txt"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy>=1.20.0\npandas>=1.3.0\n")

        check_spec = {
            "id": "test-002",
            "name": "Test Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["numpy"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "numpy" in result.message.lower()

    def test_dependency_require_any(self, tmp_path):
        """Test require_any mode"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("shap>=0.40.0\n")

        check_spec = {
            "id": "test-002",
            "name": "Test Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["shap", "lime", "interpret"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED

    def test_dependency_not_found(self, tmp_path):
        """Test when dependency is not found"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy>=1.20.0\n")

        check_spec = {
            "id": "test-002",
            "name": "Test Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["shap", "lime"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.FAILED
        assert result.suggestion is not None

    def test_dependency_pyproject_toml(self, tmp_path):
        """Test finding dependency in pyproject.toml"""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = [
    "numpy>=1.20.0",
    "shap>=0.40.0",
]
""")

        check_spec = {
            "id": "test-002",
            "name": "Test Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["shap"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED

    def test_dependency_package_json(self, tmp_path):
        """Test finding dependency in package.json (JavaScript/TypeScript)"""
        package_json = tmp_path / "package.json"
        package_json.write_text('{\n  "dependencies": {\n    "react": "^18.0.0",\n    "@tensorflow/tfjs": "^4.0.0"\n  },\n  "devDependencies": {\n    "@tensorflow/tfjs-vis": "^1.0.0"\n  }\n}')

        check_spec = {
            "id": "test-003",
            "name": "Test JS Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["@tensorflow/tfjs-vis"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED

    def test_dependency_package_json_not_found(self, tmp_path):
        """Test missing dependency in package.json"""
        package_json = tmp_path / "package.json"
        package_json.write_text('{\n  "dependencies": {\n    "react": "^18.0.0"\n  }\n}')

        check_spec = {
            "id": "test-004",
            "name": "Test JS Dependency Check",
            "principle": "test",
            "severity": "warning",
            "description": "Test check",
            "config": {
                "packages": ["shap", "lime"],
                "require_any": True
            }
        }

        check = DependencyCheck(check_spec)
        result = check.run(tmp_path)

        assert result.status == CheckStatus.FAILED
