# ABOUTME: FastAPI service endpoint for remote AI ethics compliance checking
# ABOUTME: Accepts a git repo URL, clones it, runs checks, and returns JSON results

"""
Ethica API server — check any project by pointing at its git URL.

Usage:
    ethica serve
    # or directly:
    uvicorn ethica.api.server:app --host 0.0.0.0 --port 8000
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ethica import __version__
from ethica.core.checker import CheckEngine
from ethica.core.registry import FrameworkRegistry

app = FastAPI(
    title="Ethica",
    description="AI ethics compliance checking as a service",
    version=__version__,
)

registry = FrameworkRegistry()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CheckRequest(BaseModel):
    """Request body for the /check endpoint."""
    repo_url: str = Field(
        ...,
        description="Git clone URL of the project to check",
        examples=["https://github.com/user/my-ai-app.git"],
    )
    ref: Optional[str] = Field(
        None,
        description="Git ref (branch, tag, commit) to check. Defaults to the repo's default branch.",
    )
    framework: str = Field(
        "unesco-2021",
        description="Framework ID to check against",
    )
    compliance_level: str = Field(
        "standard",
        description="Compliance level: basic, standard, or verified",
    )


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLONE_TIMEOUT_SECONDS = 120
_MAX_CLONE_DEPTH = 1  # shallow clone for speed


def _clone_repo(repo_url: str, dest: Path, ref: Optional[str] = None) -> None:
    """Shallow-clone a git repo into *dest*."""
    cmd = [
        "git", "clone",
        "--depth", str(_MAX_CLONE_DEPTH),
        "--single-branch",
    ]
    if ref:
        cmd += ["--branch", ref]
    cmd += [repo_url, str(dest)]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_CLONE_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git clone failed")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health / readiness probe."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/frameworks")
async def list_frameworks() -> list[dict]:
    """List available compliance frameworks."""
    return registry.list_frameworks()


@app.post("/check")
async def check_repo(request: CheckRequest) -> dict:
    """
    Clone a repo, run ethics compliance checks, and return the results.

    The repo is cloned into a temporary directory that is cleaned up
    automatically after the check completes.
    """
    # Validate framework exists
    framework_spec = _load_framework(request.framework)

    tmp_dir = tempfile.mkdtemp(prefix="ethica-")
    project_path = Path(tmp_dir) / "project"

    try:
        # Clone
        try:
            _clone_repo(request.repo_url, project_path, request.ref)
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail="Timed out cloning repository",
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not clone repository: {exc}",
            )

        # Run checks
        engine = CheckEngine(framework_spec)
        results = engine.run_checks(project_path)

        # Attach request metadata
        results["request"] = {
            "repo_url": request.repo_url,
            "ref": request.ref,
            "framework": request.framework,
            "compliance_level": request.compliance_level,
        }

        # Evaluate compliance level
        level_spec = framework_spec.get("compliance_levels", {}).get(request.compliance_level)
        if level_spec:
            min_rate = level_spec.get("minimum_check_pass_rate", 0.0)
            results["compliance"] = {
                "level": request.compliance_level,
                "required_pass_rate": min_rate,
                "actual_pass_rate": results["pass_rate"],
                "meets_level": results["pass_rate"] >= min_rate,
            }

        return results

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _load_framework(framework_id: str) -> dict:
    """Load a framework spec or raise 404."""
    try:
        return registry.load_framework_spec(framework_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
