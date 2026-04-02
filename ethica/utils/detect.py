# ABOUTME: Project type detection utility
# ABOUTME: Detects project language/ecosystem from manifest files

"""
Detect project type from file markers in a project directory.
"""

from pathlib import Path
from typing import Set


# Maps marker files to project types
_MARKERS = {
    "package.json": "nodejs",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "kotlin",
    "composer.json": "php",
    "mix.exs": "elixir",
    "Package.swift": "swift",
}


def detect_project_types(project_path: Path) -> Set[str]:
    """
    Detect which ecosystems a project belongs to.

    Returns a set of ecosystem names like {"python", "nodejs"}.
    A monorepo may return multiple types.
    """
    types: Set[str] = set()
    for marker, project_type in _MARKERS.items():
        if (project_path / marker).exists():
            types.add(project_type)
    return types
