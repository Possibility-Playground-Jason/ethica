# ABOUTME: Project introspection for generating pre-filled documentation
# ABOUTME: Reads README, deps, git metadata, configs to build a project profile

"""
Introspect a project directory to extract metadata for documentation generation.
"""

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Optional

from ethica.utils.detect import detect_project_types


def introspect_project(project_path: Path) -> dict[str, Any]:
    """
    Scan a project directory and return a structured profile.

    This reads files that already exist -- README, dependency manifests,
    git history, config files -- and returns a dict that can seed a
    model/system card template.
    """
    profile: dict[str, Any] = {
        "project_name": project_path.name,
        "project_types": sorted(detect_project_types(project_path)),
        "date": date.today().isoformat(),
        "description": "",
        "dependencies": [],
        "ai_libraries": [],
        "fairness_libraries": [],
        "explainability_libraries": [],
        "has_tests": False,
        "has_ci": False,
        "license": "",
        "contributors": [],
        "repo_url": "",
    }

    _extract_description(project_path, profile)
    _extract_dependencies(project_path, profile)
    _classify_ai_deps(profile)
    _extract_git_info(project_path, profile)
    _detect_testing(project_path, profile)
    _detect_ci(project_path, profile)
    _extract_license(project_path, profile)

    return profile


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

def _extract_description(project_path: Path, profile: dict) -> None:
    """Pull a one-line description from README or package manifest."""
    # Try package.json first (has explicit description field)
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            if data.get("description"):
                profile["description"] = data["description"]
                return
        except Exception:
            pass

    # Try pyproject.toml
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            for line in pyproject.read_text().splitlines():
                m = re.match(r'description\s*=\s*"(.+)"', line.strip())
                if m:
                    profile["description"] = m.group(1)
                    return
        except Exception:
            pass

    # Fall back to first paragraph of README
    for readme_name in ("README.md", "README.rst", "README.txt", "README"):
        readme = project_path / readme_name
        if readme.exists():
            try:
                lines = readme.read_text().splitlines()
                for line in lines:
                    stripped = line.strip()
                    # Skip headings, badges, blank lines
                    if not stripped or stripped.startswith("#") or stripped.startswith("["):
                        continue
                    if stripped.startswith("!") or stripped.startswith("<"):
                        continue
                    profile["description"] = stripped
                    return
            except Exception:
                pass


def _extract_dependencies(project_path: Path, profile: dict) -> None:
    """Collect dependency names from all supported manifests."""
    deps: set[str] = set()

    # requirements.txt
    for req_file in ("requirements.txt", "requirements-dev.txt"):
        path = project_path / req_file
        if path.exists():
            try:
                for line in path.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        m = re.match(r"([a-zA-Z0-9@/_-]+)", line)
                        if m:
                            deps.add(m.group(1).lower())
            except Exception:
                pass

    # package.json
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            for key in ("dependencies", "devDependencies"):
                for name in data.get(key, {}).keys():
                    deps.add(name.lower())
        except Exception:
            pass

    # pyproject.toml (simple array parse)
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            in_deps = False
            for line in pyproject.read_text().splitlines():
                s = line.strip()
                if re.match(r"(?:dev-)?dependencies\s*=\s*\[", s):
                    in_deps = True
                if in_deps:
                    matches = re.findall(r'"([a-zA-Z0-9@/_-]+)', s)
                    for m in matches:
                        deps.add(m.lower())
                    if "]" in s:
                        in_deps = False
        except Exception:
            pass

    profile["dependencies"] = sorted(deps)


_AI_LIBS = {
    # Python ML/AI
    "tensorflow", "torch", "pytorch", "keras", "scikit-learn", "sklearn",
    "transformers", "huggingface-hub", "openai", "anthropic", "langchain",
    "llamaindex", "llama-index", "sentence-transformers", "spacy", "nltk",
    "xgboost", "lightgbm", "catboost", "jax", "flax", "onnx", "onnxruntime",
    "diffusers", "stable-baselines3", "ray", "mlflow", "wandb",
    # JS/TS AI
    "@tensorflow/tfjs", "@huggingface/inference", "@anthropic-ai/sdk",
    "openai", "langchain", "ai", "@ai-sdk/core",
}

_EXPLAINABILITY_LIBS = {
    "shap", "lime", "captum", "interpret", "alibi", "dalex",
    "@tensorflow/tfjs-vis", "ml-explain",
}

_FAIRNESS_LIBS = {
    "fairlearn", "aif360", "responsibleai", "ai-fairness",
}


def _classify_ai_deps(profile: dict) -> None:
    """Tag which deps are AI, explainability, and fairness libraries."""
    deps = set(profile["dependencies"])
    profile["ai_libraries"] = sorted(deps & _AI_LIBS)
    profile["explainability_libraries"] = sorted(deps & _EXPLAINABILITY_LIBS)
    profile["fairness_libraries"] = sorted(deps & _FAIRNESS_LIBS)


def _extract_git_info(project_path: Path, profile: dict) -> None:
    """Extract contributors and remote URL from git."""
    if not (project_path / ".git").exists():
        return

    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "log", "--format=%aN", "--no-merges"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            names = list(dict.fromkeys(result.stdout.strip().splitlines()))  # dedupe, preserve order
            profile["contributors"] = names[:20]  # cap at 20
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            profile["repo_url"] = result.stdout.strip()
    except Exception:
        pass


def _detect_testing(project_path: Path, profile: dict) -> None:
    """Check if the project has a test directory or test config."""
    test_markers = [
        "tests", "test", "__tests__", "spec",
        "pytest.ini", "jest.config.js", "jest.config.ts",
        "vitest.config.ts", ".mocharc.yml",
    ]
    for marker in test_markers:
        if (project_path / marker).exists():
            profile["has_tests"] = True
            return


def _detect_ci(project_path: Path, profile: dict) -> None:
    """Check if the project has CI configuration."""
    ci_markers = [
        ".github/workflows",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        ".circleci",
        ".travis.yml",
        "cloudbuild.yaml",
    ]
    for marker in ci_markers:
        if (project_path / marker).exists():
            profile["has_ci"] = True
            return


def _extract_license(project_path: Path, profile: dict) -> None:
    """Read the license type from LICENSE file or package manifest."""
    # Try package.json
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            if data.get("license"):
                profile["license"] = data["license"]
                return
        except Exception:
            pass

    # Try pyproject.toml
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            for line in pyproject.read_text().splitlines():
                m = re.match(r'.*license.*=.*"(.+)"', line.strip(), re.IGNORECASE)
                if m:
                    profile["license"] = m.group(1)
                    return
        except Exception:
            pass

    # Try first line of LICENSE file
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"):
        path = project_path / name
        if path.exists():
            try:
                first_lines = path.read_text()[:200]
                if "MIT" in first_lines:
                    profile["license"] = "MIT"
                elif "Apache" in first_lines:
                    profile["license"] = "Apache-2.0"
                elif "GPL" in first_lines:
                    profile["license"] = "GPL"
                elif "BSD" in first_lines:
                    profile["license"] = "BSD"
                else:
                    profile["license"] = "See LICENSE file"
                return
            except Exception:
                pass
