"""Phase B: Planning for infer-network-v2.

Phase dependencies:
1. Preflight report (or run preflight inline if not provided).
2. Cost profile loading + mode estimation per requested run.
3. Planner selection (auto/cp_sat/heuristic) and wave construction.
4. Frozen run_dir artifact and metadata persistence.
"""

from __future__ import annotations

import multiprocessing
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rich import print

from .commons.artifacts import (
    _build_input_fingerprints,
    _deserialize_dataset_context,
    _materialize_frozen_inputs,
)
from .commons.catalog import _load_schema_constraints, _resolve_catalog_paths
from .commons.planner import (
    _estimate_tool_mode_options,
    _load_tool_cost_profile,
    _optimize_mode_selection,
    _optimize_mode_selection_cp_sat,
)
from .commons.shared import (
    DEFAULT_OUTPUT_DIR,
    _detect_host_ram_gb,
    _task_eta_note,
    _write_json,
)
from .commons.tools import _load_toolspec
from .preflight import preflight_infer_network_new

PLAN_SCHEMA_VERSION = "1.1"


def plan_infer_network_new(
    *,
    dataset_manifest_path: Path,
    tools_params_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_cores: int = multiprocessing.cpu_count(),
    max_ram_gb: Optional[float] = None,
    planner: str = "auto",
    planner_time_limit_seconds: float = 10.0,
    strict: bool = False,
    preflight_report: Optional[dict[str, Any]] = None,
) -> Path:
    if max_cores < 1:
        raise ValueError("max_cores must be >= 1")
    host_ram = _detect_host_ram_gb()
    effective_ram = host_ram if max_ram_gb is None else min(float(max_ram_gb), host_ram)
    if effective_ram <= 0:
        raise ValueError("max_ram_gb must be > 0")

    planner_mode = str(planner).strip().lower().replace("-", "_")
    if planner_mode not in {"auto", "heuristic", "cp_sat"}:
        raise ValueError("planner must be one of: auto, heuristic, cp_sat")
    if planner_time_limit_seconds <= 0:
        raise ValueError("planner_time_limit_seconds must be > 0")

    if preflight_report is None:
        preflight_report = preflight_infer_network_new(
            dataset_manifest_path=dataset_manifest_path,
            tools_params_path=tools_params_path,
            strict=strict,
        )

    dataset_payload = preflight_report.get("dataset", {})
    if not isinstance(dataset_payload, dict):
        raise ValueError("preflight_report.dataset is invalid")
    dataset = _deserialize_dataset_context(dataset_payload)

    tools_root, schemas_dir = _resolve_catalog_paths()
    constraints = _load_schema_constraints(schemas_dir)

    warnings = [
        str(w) for w in preflight_report.get("warnings", []) if isinstance(w, str)
    ]
    runs_payload = preflight_report.get("runs", {})
    if not isinstance(runs_payload, dict):
        raise ValueError("preflight_report.runs is invalid")
    selected_tools = [x for x in runs_payload.get("selected", []) if isinstance(x, str)]
    selected_tool_catalog_ids = {
        str(k): str(v)
        for k, v in runs_payload.get("catalog_tool_ids", {}).items()
        if isinstance(k, str) and isinstance(v, str)
    }
    resolved_params_by_tool = {
        str(k): v
        for k, v in runs_payload.get("resolved_params", {}).items()
        if isinstance(k, str) and isinstance(v, dict)
    }
    skipped_tools = {
        str(k): str(v)
        for k, v in runs_payload.get("skipped", {}).items()
        if isinstance(k, str)
    }

    if not selected_tools:
        refreshed_preflight = preflight_infer_network_new(
            dataset_manifest_path=dataset_manifest_path,
            tools_params_path=tools_params_path,
            strict=strict,
        )
        preflight_report = refreshed_preflight
        dataset_payload = refreshed_preflight.get("dataset", {})
        if not isinstance(dataset_payload, dict):
            raise ValueError("refreshed preflight report has invalid dataset payload")
        dataset = _deserialize_dataset_context(dataset_payload)
        warnings = [
            str(w)
            for w in refreshed_preflight.get("warnings", [])
            if isinstance(w, str)
        ]
        runs_payload = refreshed_preflight.get("runs", {})
        if not isinstance(runs_payload, dict):
            raise ValueError("refreshed preflight report has invalid runs payload")
        selected_tools = [
            x for x in runs_payload.get("selected", []) if isinstance(x, str)
        ]
        selected_tool_catalog_ids = {
            str(k): str(v)
            for k, v in runs_payload.get("catalog_tool_ids", {}).items()
            if isinstance(k, str) and isinstance(v, str)
        }
        resolved_params_by_tool = {
            str(k): v
            for k, v in runs_payload.get("resolved_params", {}).items()
            if isinstance(k, str) and isinstance(v, dict)
        }
        skipped_tools = {
            str(k): str(v)
            for k, v in runs_payload.get("skipped", {}).items()
            if isinstance(k, str)
        }
        if not selected_tools:
            raise ValueError(
                "No compatible tools available after validation. "
                "Check tools_params.json and dataset/tool compatibility."
            )

    mode_options_by_tool = {}
    for run_id in selected_tools:
        catalog_tool_id = selected_tool_catalog_ids.get(run_id, "").strip()
        if not catalog_tool_id:
            raise ValueError(
                f"preflight report is missing catalog mapping for run '{run_id}'"
            )
        toolspec = _load_toolspec(tools_root, catalog_tool_id)
        cost_profile, cost_warnings = _load_tool_cost_profile(
            tools_root=tools_root,
            tool_id=catalog_tool_id,
        )
        warnings.extend(cost_warnings)
        mode_options, plan_warnings = _estimate_tool_mode_options(
            tool_id=run_id,
            toolspec=toolspec,
            cost_profile=cost_profile,
            dataset=dataset,
            max_cores=max_cores,
            max_ram_gb=effective_ram,
        )
        warnings.extend(plan_warnings)
        mode_options_by_tool[run_id] = mode_options

    planner_used = "heuristic"
    planning_result = None
    if planner_mode in {"auto", "cp_sat"}:
        planning_result = _optimize_mode_selection_cp_sat(
            mode_options_by_tool=mode_options_by_tool,
            max_cores=max_cores,
            max_ram_gb=effective_ram,
            time_limit_seconds=planner_time_limit_seconds,
            warnings=warnings,
        )
        if planning_result is not None:
            planner_used = "cp_sat"
    if planning_result is None:
        planning_result = _optimize_mode_selection(
            mode_options_by_tool=mode_options_by_tool,
            max_cores=max_cores,
            max_ram_gb=effective_ram,
        )
        if planner_mode == "cp_sat":
            warnings.append("[planner=cp_sat] fallback heuristic planner was used.")

    _selected_modes, waves, total_eta = planning_result
    if planner_mode == "auto":
        print(f"[cyan]planner[/cyan]: auto -> {planner_used}")
    else:
        print(f"[cyan]planner[/cyan]: requested={planner_mode}, used={planner_used}")

    run_id = (
        f"{dataset.dataset_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    run_dir = output_dir.resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    tools_dir = run_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    for tool_id, resolved in resolved_params_by_tool.items():
        tool_out = tools_dir / tool_id
        tool_out.mkdir(parents=True, exist_ok=True)
        _write_json(tool_out / "resolved_params.json", resolved)

    frozen_manifest, frozen_tools_params, frozen_expression, frozen_extras = (
        _materialize_frozen_inputs(
            run_dir=run_dir,
            dataset_manifest_path=dataset_manifest_path,
            tools_params_path=tools_params_path,
            dataset=dataset,
            constraints=constraints,
        )
    )
    input_fingerprints = _build_input_fingerprints(
        run_dir=run_dir,
        frozen_manifest=frozen_manifest,
        frozen_tools_params=frozen_tools_params,
        frozen_expression=frozen_expression,
        frozen_extras=frozen_extras,
    )

    plan_generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    plan_waves = []
    eta_cursor = 0.0
    for wave in waves:
        eta_start = round(eta_cursor, 3)
        eta_end = round(eta_cursor + wave.eta_seconds, 3)
        eta_cursor = eta_end
        tasks_payload = []
        for task in wave.tasks:
            task_payload = asdict(task)
            note = _task_eta_note(task.eta_source)
            if note is not None:
                task_payload["note"] = note
            tasks_payload.append(task_payload)
        plan_waves.append(
            {
                "index": wave.index,
                "threads_used": wave.threads_used,
                "ram_gb_used": wave.ram_gb_used,
                "eta_seconds": wave.eta_seconds,
                "eta_start_seconds": eta_start,
                "eta_end_seconds": eta_end,
                "tasks": tasks_payload,
            }
        )

    plan_payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "generated_at_utc": plan_generated_at,
        "run_id": run_id,
        "planner": {
            "requested": planner_mode,
            "used": planner_used,
            "cp_sat_time_limit_seconds": float(planner_time_limit_seconds),
        },
        "resource_limits": {
            "max_cores": int(max_cores),
            "max_ram_gb": round(float(effective_ram), 3),
        },
        "totals": {
            "tasks_total": int(sum(len(w.tasks) for w in waves)),
            "waves_total": int(len(waves)),
            "threads_peak": int(max((w.threads_used for w in waves), default=0)),
            "ram_peak_gb": round(
                float(max((w.ram_gb_used for w in waves), default=0.0)), 3
            ),
        },
        "waves": plan_waves,
        "eta_total_seconds": total_eta,
        "input_fingerprints": input_fingerprints,
    }
    _write_json(run_dir / "plan.json", plan_payload)
    _write_json(run_dir / "preflight_report.json", preflight_report)

    report_payload = {
        "run_id": run_id,
        "status": "planned",
        "inputs": {
            "dataset_manifest_path": str(frozen_manifest.resolve()),
            "tools_params_path": str(frozen_tools_params.resolve()),
            "tools_root": str(tools_root.resolve()),
            "schemas_dir": str(schemas_dir.resolve()),
        },
        "dataset": {
            "id": dataset.dataset_id,
            "column_kind": dataset.column_kind,
            "expression_profile": dataset.expression_profile,
            "genes": dataset.genes,
            "columns": dataset.columns,
            "expression_matrix_path": str(frozen_expression.resolve()),
        },
        "tools": {
            "selected": selected_tools,
            "catalog_tool_ids": selected_tool_catalog_ids,
            "skipped": skipped_tools,
            "completed": [],
            "failed": {},
            "results": {},
        },
        "outputs": {
            "merged_network_raw": None,
            "merged_network_normalized": None,
            "rows_per_tool": {},
        },
        "warnings": warnings,
        "execution": {
            "elapsed_seconds": 0.0,
            "planner_requested": planner_mode,
            "planner_used": planner_used,
            "planner_time_limit_seconds": float(planner_time_limit_seconds),
            "waves_total": len(waves),
            "tools_selected": len(selected_tools),
            "tools_completed": 0,
            "tools_failed": 0,
        },
        "plan_file": str((run_dir / "plan.json").resolve()),
        "notes": [
            "Run directory is frozen at planning time.",
            "Use run_infer_network_new_plan(run_dir=...) to execute this plan.",
        ],
    }
    _write_json(run_dir / "run_report.json", report_payload)

    print(f"[bold green]infer-network-v2 planning completed[/bold green]: {run_dir}")
    print(f"  selected tools: {len(selected_tools)}")
    print(f"  skipped tools: {len(skipped_tools)}")
    print(f"  waves: {len(waves)}")
    print(f"  estimated total time: {total_eta:.2f}s")
    if warnings:
        print(f"  warnings: {len(warnings)} (see run_report.json)")

    return run_dir
