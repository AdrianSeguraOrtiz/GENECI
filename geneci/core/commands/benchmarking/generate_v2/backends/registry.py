"""Runtime execution for generate-v2 simulators."""

from __future__ import annotations

from pathlib import Path

from ..shared import ResolvedBenchmarkRequest
from .docker_runner import run_docker_simulator


def run_simulator_backend(
    *,
    request: ResolvedBenchmarkRequest,
    seed: int,
    stage_dir: Path,
) -> Path:
    return run_docker_simulator(
        request=request,
        seed=seed,
        stage_dir=stage_dir,
    )
