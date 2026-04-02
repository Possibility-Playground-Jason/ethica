# ABOUTME: AI provider transparency checks
# ABOUTME: Scans code for model/API references and verifies provider has published system cards

"""
Provider transparency checks.

Scans project source files for AI model references (imports, model ID strings)
and cross-references against a provider registry to verify transparency status.
"""

import re
from pathlib import Path
from typing import Any, Set

import yaml

from ethica.checks.base import BaseCheck, CheckResult, CheckStatus


class ProviderCheck(BaseCheck):
    """Check that AI model providers used in the project publish system cards."""

    def run(self, project_path: Path) -> CheckResult:
        """
        Scan source files for AI provider imports and model ID references.

        Config:
            providers_file: Path to providers.yaml (default: built-in)
            scan_extensions: File extensions to scan (default: common code files)
        """
        # Load provider registry
        providers = self._load_providers()
        if not providers:
            return self._create_result(
                CheckStatus.SKIPPED,
                "Could not load provider registry",
            )

        # Scan source files
        extensions = self.config.get("scan_extensions", [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs",
            ".go", ".rs", ".java", ".kt", ".rb",
        ])
        detected = self._scan_for_providers(project_path, providers, extensions)

        if not detected:
            return self._create_result(
                CheckStatus.SKIPPED,
                "No AI model providers detected in source code",
            )

        # Evaluate transparency status
        transparent = []
        opaque = []

        for provider_id, info in detected.items():
            provider_data = providers.get(provider_id, {})
            name = provider_data.get("name", provider_id)
            has_cards = provider_data.get("publishes_system_cards", False)
            card_url = provider_data.get("system_cards_url", "")

            if has_cards:
                transparent.append(f"{name} (system cards: {card_url})")
            else:
                notes = provider_data.get("notes", "No published system cards")
                opaque.append(f"{name}: {notes}")

        if opaque:
            msg_parts = [f"Found {len(detected)} AI provider(s)."]
            msg_parts.append(f"Providers with system cards: {', '.join(transparent)}" if transparent else "")
            msg_parts.append(f"Providers WITHOUT system cards: {'; '.join(opaque)}")

            return self._create_result(
                CheckStatus.FAILED,
                " ".join(p for p in msg_parts if p),
                suggestion="Consider providers that publish system cards and safety evaluations. "
                           "See https://www.anthropic.com/system-cards for an example.",
            )
        else:
            names = [providers[pid].get("name", pid) for pid in detected]
            return self._create_result(
                CheckStatus.PASSED,
                f"All detected AI providers publish system cards: {', '.join(names)}",
            )

    def _load_providers(self) -> dict[str, Any]:
        """Load the provider registry YAML."""
        providers_file = self.config.get("providers_file")
        if providers_file:
            path = Path(providers_file)
        else:
            # Default to built-in registry
            path = Path(__file__).parent.parent.parent / "frameworks" / "providers.yaml"

        if not path.exists():
            return {}

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return data.get("providers", {})
        except Exception:
            return {}

    def _scan_for_providers(
        self,
        project_path: Path,
        providers: dict[str, Any],
        extensions: list[str],
    ) -> dict[str, dict]:
        """Scan source files and return detected providers."""
        detected: dict[str, dict] = {}

        # Collect all source content
        source_content = self._read_source_files(project_path, extensions)
        if not source_content:
            # Also check dependency manifests
            source_content = self._read_dep_files(project_path)

        # Check each provider
        for provider_id, provider_data in providers.items():
            # Check import markers
            import_markers = provider_data.get("import_markers", [])
            for marker in import_markers:
                if marker.lower() in source_content:
                    detected[provider_id] = provider_data
                    break

            # Check model ID patterns
            if provider_id not in detected:
                model_patterns = provider_data.get("model_id_patterns", [])
                for pattern in model_patterns:
                    if pattern.lower() in source_content:
                        detected[provider_id] = provider_data
                        break

        return detected

    def _read_source_files(self, project_path: Path, extensions: list[str]) -> str:
        """Read and concatenate source files (lowercase for matching)."""
        parts: list[str] = []
        try:
            for ext in extensions:
                for path in project_path.rglob(f"*{ext}"):
                    # Skip node_modules, venv, etc.
                    path_str = str(path)
                    if any(skip in path_str for skip in (
                        "node_modules", "venv", ".venv", "__pycache__",
                        ".git", "dist", "build",
                    )):
                        continue
                    try:
                        content = path.read_text(errors="ignore")
                        parts.append(content[:50_000])  # cap per file
                    except Exception:
                        continue
        except Exception:
            pass
        return "\n".join(parts).lower()

    def _read_dep_files(self, project_path: Path) -> str:
        """Read dependency manifests as fallback for import detection."""
        parts: list[str] = []
        for name in ("requirements.txt", "pyproject.toml", "package.json", "go.mod"):
            path = project_path / name
            if path.exists():
                try:
                    parts.append(path.read_text(errors="ignore"))
                except Exception:
                    pass
        return "\n".join(parts).lower()
