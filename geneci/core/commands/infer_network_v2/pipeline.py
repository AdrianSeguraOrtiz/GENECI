"""End-to-end orchestration for infer-network-v2.

Flow (high-level):
1. preflight: validate inputs and tool eligibility
2. plan: freeze artifacts and generate plan
3. run: execute wave schedule and merge outputs
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import Optional

from .commons.shared import DEFAULT_OUTPUT_DIR
from .plan import plan_infer_network_new
from .preflight import preflight_infer_network_new
from .run import run_infer_network_new_plan


def infer_network_new(
    *,
    dataset_manifest_path: Path,
    tools_params_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_cores: int = multiprocessing.cpu_count(),
    max_ram_gb: Optional[float] = None,
    planner: str = "auto",
    planner_time_limit_seconds: float = 10.0,
    progress_poll_seconds: float = 0.5,
    strict: bool = False,
) -> Path:
    """Execute preflight + plan + run for infer-network-v2."""
    preflight_report = preflight_infer_network_new(
        dataset_manifest_path=dataset_manifest_path,
        tools_params_path=tools_params_path,
        strict=strict,
    )
    run_dir = plan_infer_network_new(
        dataset_manifest_path=dataset_manifest_path,
        tools_params_path=tools_params_path,
        output_dir=output_dir,
        max_cores=max_cores,
        max_ram_gb=max_ram_gb,
        planner=planner,
        planner_time_limit_seconds=planner_time_limit_seconds,
        strict=strict,
        preflight_report=preflight_report,
    )
    return run_infer_network_new_plan(
        run_dir=run_dir,
        progress_poll_seconds=progress_poll_seconds,
        strict=strict,
    )
