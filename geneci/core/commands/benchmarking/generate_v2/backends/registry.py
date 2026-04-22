"""Runtime execution for generate-v2 simulators."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..shared import ResolvedSimulatorRun
from .docker_runner import run_docker_simulator


def run_simulator_backend(
    *,
    request: ResolvedSimulatorRun,
    seed: int,
    stage_dir: Path,
    task_label: str,
    progress_poll_seconds: float,
    show_progress: bool,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    return run_docker_simulator(
        request=request,
        seed=seed,
        stage_dir=stage_dir,
        task_label=task_label,
        progress_poll_seconds=progress_poll_seconds,
        show_progress=show_progress,
        progress_callback=progress_callback,
    )
