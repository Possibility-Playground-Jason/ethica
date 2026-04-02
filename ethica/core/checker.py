# ABOUTME: Check engine for running compliance checks and aggregating results
# ABOUTME: Orchestrates check execution and produces structured results

"""
Check engine for running ethics compliance checks.
"""

from pathlib import Path
from typing import Any

from ethica.checks.base import CheckStatus
from ethica.checks.file_checks import FileExistsCheck
from ethica.checks.dependency_checks import DependencyCheck
from ethica.checks.provider_checks import ProviderCheck


class CheckEngine:
    """Engine for running compliance checks"""

    # Map check types to check classes
    CHECK_TYPES = {
        "file-exists": FileExistsCheck,
        "dependency-check": DependencyCheck,
        "provider-check": ProviderCheck,
    }

    def __init__(self, framework_spec: dict[str, Any]) -> None:
        """
        Initialize check engine with framework specification.

        Args:
            framework_spec: Complete framework specification
        """
        self.framework_spec = framework_spec
        self.checks = self._load_checks()

    def _load_checks(self) -> list[Any]:
        """Load and instantiate all checks from framework spec"""
        checks = []

        for check_spec in self.framework_spec.get("checks", []):
            check_type = check_spec.get("type")

            if check_type not in self.CHECK_TYPES:
                # Skip unknown check types
                continue

            check_class = self.CHECK_TYPES[check_type]
            check = check_class(check_spec)
            checks.append(check)

        return checks

    def run_checks(self, project_path: Path) -> dict[str, Any]:
        """
        Run all checks and return aggregated results.

        Args:
            project_path: Path to project directory

        Returns:
            Dictionary with structured results
        """
        # Group results by principle
        principle_results: dict[str, Any] = {}

        for check in self.checks:
            result = check.run(project_path)

            # Initialize principle if needed
            if check.principle not in principle_results:
                principle_results[check.principle] = {
                    "id": check.principle,
                    "checks": [],
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                }

            # Add check result
            principle_results[check.principle]["checks"].append(result.to_dict())

            # Update counters
            if result.status == CheckStatus.PASSED:
                principle_results[check.principle]["passed"] += 1
            elif result.status == CheckStatus.FAILED:
                principle_results[check.principle]["failed"] += 1
            elif result.status == CheckStatus.SKIPPED:
                principle_results[check.principle]["skipped"] += 1

        # Compute principle-level status
        for principle_id, principle_data in principle_results.items():
            if principle_data["failed"] > 0:
                principle_data["status"] = "failed"
            elif principle_data["passed"] > 0:
                principle_data["status"] = "passed"
            else:
                principle_data["status"] = "skipped"

        # Compute overall statistics
        total_checks = len(self.checks)
        total_passed = sum(p["passed"] for p in principle_results.values())
        total_failed = sum(p["failed"] for p in principle_results.values())
        total_skipped = sum(p["skipped"] for p in principle_results.values())

        pass_rate = total_passed / total_checks if total_checks > 0 else 0.0

        # Determine overall status
        error_failures = sum(
            1
            for p in principle_results.values()
            for check in p["checks"]
            if check["status"] == "failed" and check["severity"] == "error"
        )

        if error_failures > 0:
            overall_status = "failed"
            overall_status_color = "red"
        elif total_failed > 0:
            overall_status = "passed with warnings"
            overall_status_color = "yellow"
        else:
            overall_status = "passed"
            overall_status_color = "green"

        # Build result structure
        result = {
            "framework_id": self.framework_spec["metadata"]["id"],
            "framework_version": self.framework_spec["metadata"]["version"],
            "principles": list(principle_results.values()),
            "total_checks": total_checks,
            "checks_passed": total_passed,
            "checks_failed": total_failed,
            "checks_skipped": total_skipped,
            "pass_rate": pass_rate,
            "overall_status": overall_status,
            "overall_status_color": overall_status_color,
        }

        return result
