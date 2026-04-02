# ABOUTME: Integration tests for UNESCO framework checks
# ABOUTME: Tests complete check workflow with real framework

"""
Integration tests for UNESCO framework checks.
"""

import pytest
from pathlib import Path

from ethica.core.registry import FrameworkRegistry
from ethica.core.checker import CheckEngine


def test_compliant_project():
    """Test checking a compliant project"""
    # Get test fixture path
    test_dir = Path(__file__).parent.parent / "fixtures" / "compliant_project"

    # Load UNESCO framework
    registry = FrameworkRegistry()
    spec = registry.load_framework_spec("unesco-2021")

    # Run checks
    engine = CheckEngine(spec)
    results = engine.run_checks(test_dir)

    # Verify results structure
    assert results["framework_id"] == "unesco-2021"
    assert "principles" in results
    assert results["total_checks"] == 9  # transparency(2) + fairness(1) + privacy(1) + accountability(2) + safety(2) + sustainability(1)

    # Should have high pass rate for compliant project
    assert results["pass_rate"] >= 0.8

    # Check that we tested all expected principles
    principle_ids = {p["id"] for p in results["principles"]}
    assert "transparency" in principle_ids
    assert "fairness" in principle_ids
    assert "privacy" in principle_ids
    assert "accountability" in principle_ids
    assert "safety" in principle_ids
    assert "sustainability" in principle_ids


def test_non_compliant_project():
    """Test checking a non-compliant project"""
    # Get test fixture path
    test_dir = Path(__file__).parent.parent / "fixtures" / "non_compliant_project"

    # Load UNESCO framework
    registry = FrameworkRegistry()
    spec = registry.load_framework_spec("unesco-2021")

    # Run checks
    engine = CheckEngine(spec)
    results = engine.run_checks(test_dir)

    # Should have low pass rate
    assert results["pass_rate"] < 0.5

    # Should have failed checks
    assert results["checks_failed"] > 0


def test_principle_grouping():
    """Test that results are properly grouped by principle"""
    test_dir = Path(__file__).parent.parent / "fixtures" / "compliant_project"

    registry = FrameworkRegistry()
    spec = registry.load_framework_spec("unesco-2021")

    engine = CheckEngine(spec)
    results = engine.run_checks(test_dir)

    # Each principle should have checks
    for principle in results["principles"]:
        assert "id" in principle
        assert "checks" in principle
        assert len(principle["checks"]) > 0
        assert "status" in principle

        # Each check should have required fields
        for check in principle["checks"]:
            assert "id" in check
            assert "name" in check
            assert "status" in check
            assert "severity" in check
            assert "message" in check


def test_check_results_to_dict():
    """Test that check results can be serialized"""
    test_dir = Path(__file__).parent.parent / "fixtures" / "compliant_project"

    registry = FrameworkRegistry()
    spec = registry.load_framework_spec("unesco-2021")

    engine = CheckEngine(spec)
    results = engine.run_checks(test_dir)

    # Should be serializable (no custom objects)
    import json
    json_str = json.dumps(results)
    assert len(json_str) > 0

    # Should be deserializable
    parsed = json.loads(json_str)
    assert parsed["framework_id"] == "unesco-2021"
