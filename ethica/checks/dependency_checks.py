# ABOUTME: Dependency-based compliance checks for Python and JavaScript/TypeScript packages
# ABOUTME: Checks requirements.txt, pyproject.toml, setup.py, and package.json for required libraries

"""
Dependency-based compliance checks.
"""

import json
import re
from pathlib import Path
from typing import Set

from ethica.checks.base import BaseCheck, CheckResult, CheckStatus


class DependencyCheck(BaseCheck):
    """Check if required packages are declared as dependencies"""

    def run(self, project_path: Path) -> CheckResult:
        """
        Check if required packages are in project dependencies.

        Config:
            packages: List of package names to check for
            require_any: If True, at least one package must be present (default)
            require_all: If True, all packages must be present
        """
        packages = self.config.get("packages", [])
        require_any = self.config.get("require_any", True)
        require_all = self.config.get("require_all", False)

        if not packages:
            return self._create_result(
                CheckStatus.SKIPPED,
                "No packages configured for check",
            )

        # Get all declared dependencies
        declared_deps = self._get_project_dependencies(project_path)

        # Check which required packages are present
        found_packages = [pkg for pkg in packages if pkg.lower() in declared_deps]

        # Evaluate result based on requirements
        if require_all:
            if len(found_packages) == len(packages):
                return self._create_result(
                    CheckStatus.PASSED,
                    f"All required packages found: {', '.join(found_packages)}",
                )
            else:
                missing = [pkg for pkg in packages if pkg.lower() not in declared_deps]
                return self._create_result(
                    CheckStatus.FAILED,
                    f"Missing required packages: {', '.join(missing)}",
                    suggestion=f"Install: {', '.join(missing)}",
                )
        else:  # require_any (default)
            if found_packages:
                return self._create_result(
                    CheckStatus.PASSED,
                    f"Found package(s): {', '.join(found_packages)}",
                )
            else:
                packages_formatted = ", ".join(packages)
                return self._create_result(
                    CheckStatus.FAILED,
                    f"No required packages found. Expected at least one of: {packages_formatted}",
                    suggestion=f"Install one of: {packages_formatted}",
                )

    def _get_project_dependencies(self, project_path: Path) -> Set[str]:
        """
        Extract all declared dependencies from project files.

        Returns:
            Set of lowercase package names
        """
        dependencies: Set[str] = set()

        # Check requirements.txt
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/base.txt",
            "requirements/dev.txt",
        ]

        for req_file in requirements_files:
            req_path = project_path / req_file
            if req_path.exists():
                dependencies.update(self._parse_requirements_file(req_path))

        # Check pyproject.toml
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            dependencies.update(self._parse_pyproject_toml(pyproject_path))

        # Check setup.py
        setup_path = project_path / "setup.py"
        if setup_path.exists():
            dependencies.update(self._parse_setup_py(setup_path))

        # Check package.json (JavaScript/TypeScript)
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            dependencies.update(self._parse_package_json(package_json_path))

        return dependencies

    def _parse_requirements_file(self, file_path: Path) -> Set[str]:
        """Parse requirements.txt style file"""
        dependencies = set()

        try:
            content = file_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Extract package name (before ==, >=, etc.)
                match = re.match(r"([a-zA-Z0-9_-]+)", line)
                if match:
                    dependencies.add(match.group(1).lower())
        except Exception:
            pass

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> Set[str]:
        """Parse pyproject.toml for dependencies"""
        dependencies = set()

        try:
            content = file_path.read_text()

            in_section = False  # inside a [*.dependencies] section
            in_array = False  # inside a dependencies = [...] array

            for line in content.splitlines():
                stripped = line.strip()

                # Detect section headers like [tool.poetry.dependencies]
                if stripped.startswith("["):
                    in_array = False
                    if "dependencies" in stripped.lower():
                        in_section = True
                    else:
                        in_section = False
                    continue

                # Detect inline/multiline array: dependencies = [...]
                if re.match(r"(?:dev-)?dependencies\s*=\s*\[", stripped):
                    in_array = True

                # Extract packages from array items like "shap>=0.40.0"
                if in_array:
                    matches = re.findall(r'"([a-zA-Z0-9@/_-]+)[>=<\[]?', stripped)
                    for m in matches:
                        dependencies.add(m.lower())
                    if "]" in stripped:
                        in_array = False

                # Extract packages from section key-value like: shap = ">=0.40"
                if in_section and "=" in stripped:
                    match = re.match(r'"?([a-zA-Z0-9_-]+)"?\s*=', stripped)
                    if match:
                        dependencies.add(match.group(1).lower())

        except Exception:
            pass

        return dependencies

    def _parse_setup_py(self, file_path: Path) -> Set[str]:
        """Parse setup.py for dependencies"""
        dependencies = set()

        try:
            content = file_path.read_text()

            # Look for install_requires
            matches = re.findall(
                r'install_requires\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )

            for match in matches:
                # Extract package names
                packages = re.findall(r'"([a-zA-Z0-9_-]+)[>=<]?', match)
                dependencies.update(pkg.lower() for pkg in packages)

        except Exception:
            pass

        return dependencies

    def _parse_package_json(self, file_path: Path) -> Set[str]:
        """Parse package.json for dependencies (JavaScript/TypeScript projects)"""
        dependencies = set()

        try:
            content = file_path.read_text()
            data = json.loads(content)

            for dep_key in ("dependencies", "devDependencies", "peerDependencies"):
                deps = data.get(dep_key, {})
                if isinstance(deps, dict):
                    dependencies.update(name.lower() for name in deps.keys())

        except Exception:
            pass

        return dependencies
