# ABOUTME: Framework registry for loading and managing ethics frameworks
# ABOUTME: Provides access to built-in and custom frameworks

"""
Framework registry for loading ethics framework specifications.
"""

import yaml
from pathlib import Path
from typing import Any, Optional


class FrameworkRegistry:
    """Registry for managing ethics frameworks"""

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        """
        Initialize the framework registry.

        Args:
            registry_path: Path to registry.yaml. If None, uses built-in registry.
        """
        if registry_path is None:
            # Default to built-in frameworks directory
            package_dir = Path(__file__).parent.parent.parent
            self.frameworks_dir = package_dir / "frameworks"
            registry_path = self.frameworks_dir / "registry.yaml"
        else:
            self.frameworks_dir = registry_path.parent
            registry_path = Path(registry_path)

        self.registry_path = registry_path
        self._load_registry()

    def _load_registry(self) -> None:
        """Load the framework registry from YAML"""
        if not self.registry_path.exists():
            # If no registry exists, create an empty one
            self.registry: dict[str, Any] = {"frameworks": {}}
            return

        with open(self.registry_path, "r") as f:
            self.registry = yaml.safe_load(f) or {"frameworks": {}}

    def list_frameworks(self) -> list[dict[str, Any]]:
        """
        List all available frameworks.

        Returns:
            List of framework metadata dictionaries
        """
        frameworks = []
        for category, fw_list in self.registry.get("frameworks", {}).items():
            # Skip empty categories (where fw_list is None)
            if fw_list is None:
                continue
            for fw in fw_list:
                fw_copy = fw.copy()
                fw_copy["category"] = category
                frameworks.append(fw_copy)
        return frameworks

    def get_framework(self, framework_id: str) -> Optional[dict[str, Any]]:
        """
        Get framework metadata by ID.

        Args:
            framework_id: Framework identifier

        Returns:
            Framework metadata or None if not found
        """
        for category, fw_list in self.registry.get("frameworks", {}).items():
            if fw_list is None:
                continue
            for fw in fw_list:
                if fw["id"] == framework_id:
                    fw_copy = fw.copy()
                    fw_copy["category"] = category
                    return fw_copy
        return None

    def load_framework_spec(self, framework_id: str) -> dict[str, Any]:
        """
        Load full framework specification.

        Args:
            framework_id: Framework identifier

        Returns:
            Complete framework specification

        Raises:
            ValueError: If framework not found
            FileNotFoundError: If framework file doesn't exist
        """
        framework = self.get_framework(framework_id)
        if not framework:
            raise ValueError(
                f"Framework '{framework_id}' not found in registry. "
                f"Available frameworks: {', '.join(f['id'] for f in self.list_frameworks())}"
            )

        # Construct path to framework spec
        spec_path = self.frameworks_dir / framework_id / "framework.yaml"

        if not spec_path.exists():
            raise FileNotFoundError(
                f"Framework specification not found at {spec_path}"
            )

        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)

        return spec

    def get_framework_dir(self, framework_id: str) -> Path:
        """
        Get the directory path for a framework.

        Args:
            framework_id: Framework identifier

        Returns:
            Path to framework directory

        Raises:
            ValueError: If framework not found
        """
        framework = self.get_framework(framework_id)
        if not framework:
            raise ValueError(f"Framework '{framework_id}' not found")

        return self.frameworks_dir / framework_id
