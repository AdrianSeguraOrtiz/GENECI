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
from .commons.dataset import _load_groups_by_column, _read_expression_axes
from .commons.planner import (
    _estimate_tool_mode_options,
    _load_tool_cost_profile,
    _optimize_mode_selection,
    _optimize_mode_selection_cp_sat,
)
from .commons.shared import (
    DatasetContext,
    DEFAULT_OUTPUT_DIR,
    _detect_host_ram_gb,
    _slugify_token,
    _task_eta_note,
    _write_json,
)
from .commons.tools import _load_toolspec, _parse_execution_scope
from .preflight import preflight_infer_network_new

PLAN_SCHEMA_VERSION = "1.2"


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
    resolved_execution_by_tool = {
        str(k): v
        for k, v in runs_payload.get("resolved_execution", {}).items()
        if isinstance(k, str) and isinstance(v, dict)
    }
    requirement_issues = {
        str(k): [str(x) for x in v if isinstance(x, str)]
        for k, v in runs_payload.get("requirement_issues", {}).items()
        if isinstance(k, str) and isinstance(v, list)
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
        resolved_execution_by_tool = {
            str(k): v
            for k, v in runs_payload.get("resolved_execution", {}).items()
            if isinstance(k, str) and isinstance(v, dict)
        }
        requirement_issues = {
            str(k): [str(x) for x in v if isinstance(x, str)]
            for k, v in runs_payload.get("requirement_issues", {}).items()
            if isinstance(k, str) and isinstance(v, list)
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

    if requirement_issues:
        error_lines: list[str] = []
        for run_id in sorted(requirement_issues):
            for message in requirement_issues[run_id]:
                error_lines.append(f"[{run_id}] {message}")
        raise ValueError(
            "Planning blocked by missing conditional inputs:\n"
            + "\n".join(error_lines)
        )

    catalog_toolspec_by_run: dict[str, dict[str, Any]] = {}
    execution_scope_by_run: dict[str, str] = {}
    for run_id in selected_tools:
        catalog_tool_id = selected_tool_catalog_ids.get(run_id, "").strip()
        if not catalog_tool_id:
            raise ValueError(
                f"preflight report is missing catalog mapping for run '{run_id}'"
            )
        toolspec = _load_toolspec(tools_root, catalog_tool_id)
        catalog_toolspec_by_run[run_id] = toolspec
        execution_scope_by_run[run_id] = _parse_execution_scope(
            tool_id=run_id,
            toolspec=toolspec,
        )

    group_order: list[str] = []
    group_to_columns: dict[str, list[str]] = {}
    needs_group_partition = any(
        execution_scope_by_run.get(run_id) == "global"
        and str(
            resolved_execution_by_tool.get(run_id, {}).get("group_mode", "")
        ).strip()
        == "per_group"
        for run_id in selected_tools
    )
    if needs_group_partition:
        groups_path = dataset.extras.get("groups")
        if groups_path is None:
            raise ValueError(
                "Planning requires groups.tsv because at least one run uses execution.group_mode=per_group."
            )
        _expression_genes, expression_columns = _read_expression_axes(
            dataset.expression_matrix_path
        )
        group_order, group_to_columns = _load_groups_by_column(
            groups_path=groups_path,
            expression_columns=expression_columns,
        )

    mode_options_by_tool: dict[str, list[Any]] = {}
    logical_run_specs: dict[str, dict[str, Any]] = {}
    for run_id in selected_tools:
        catalog_tool_id = selected_tool_catalog_ids[run_id]
        toolspec = catalog_toolspec_by_run[run_id]
        execution_scope = execution_scope_by_run[run_id]
        resolved_execution = resolved_execution_by_tool.get(run_id, {})
        group_mode = str(resolved_execution.get("group_mode", "")).strip()
        if not group_mode:
            group_mode = "per_group" if execution_scope == "group" else "global"

        cost_profile, cost_warnings = _load_tool_cost_profile(
            tools_root=tools_root,
            tool_id=catalog_tool_id,
        )
        warnings.extend(cost_warnings)

        physical_tasks: list[dict[str, Any]] = []
        if execution_scope == "global" and group_mode == "per_group":
            for idx, group_label in enumerate(group_order, start=1):
                group_slug = _slugify_token(group_label)
                physical_task_id = f"{run_id}__group_{idx:02d}_{group_slug}"
                task_output_dir = f"tools/{run_id}/subruns/{idx:02d}_{group_slug}"
                group_columns = group_to_columns[group_label]
                group_dataset = DatasetContext(
                    dataset_id=dataset.dataset_id,
                    column_kind=dataset.column_kind,
                    expression_profile=dataset.expression_profile,
                    genes=dataset.genes,
                    columns=len(group_columns),
                    expression_matrix_path=dataset.expression_matrix_path,
                    extras=dataset.extras,
                )
                mode_options, plan_warnings = _estimate_tool_mode_options(
                    tool_id=physical_task_id,
                    run_id=run_id,
                    toolspec=toolspec,
                    cost_profile=cost_profile,
                    dataset=group_dataset,
                    max_cores=max_cores,
                    max_ram_gb=effective_ram,
                    output_dir=task_output_dir,
                    group_label=group_label,
                )
                warnings.extend(plan_warnings)
                mode_options_by_tool[physical_task_id] = mode_options
                physical_tasks.append(
                    {
                        "task_id": physical_task_id,
                        "group_label": group_label,
                        "columns": len(group_columns),
                        "output_dir": task_output_dir,
                    }
                )
        else:
            task_output_dir = f"tools/{run_id}"
            mode_options, plan_warnings = _estimate_tool_mode_options(
                tool_id=run_id,
                run_id=run_id,
                toolspec=toolspec,
                cost_profile=cost_profile,
                dataset=dataset,
                max_cores=max_cores,
                max_ram_gb=effective_ram,
                output_dir=task_output_dir,
            )
            warnings.extend(plan_warnings)
            mode_options_by_tool[run_id] = mode_options
            physical_tasks.append(
                {
                    "task_id": run_id,
                    "group_label": None,
                    "columns": dataset.columns,
                    "output_dir": task_output_dir,
                }
            )

        logical_run_specs[run_id] = {
            "run_id": run_id,
            "tool_id": catalog_tool_id,
            "execution_scope": execution_scope,
            "execution": resolved_execution,
            "physical_tasks": physical_tasks,
        }

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
        _write_json(
            tool_out / "resolved_execution.json",
            resolved_execution_by_tool.get(tool_id, {}),
        )

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
    selected_tasks_by_id: dict[str, dict[str, Any]] = {}
    eta_cursor = 0.0
    for wave in waves:
        wave_start = round(eta_cursor, 3)
        wave_end = round(eta_cursor + wave.eta_seconds, 3)
        eta_cursor = wave_end
        tasks_payload = []
        for task in wave.tasks:
            task_payload = asdict(task)
            note = _task_eta_note(task.eta_source)
            if note is not None:
                task_payload["note"] = note
            task_eta_start = wave_start
            task_eta_end = round(wave_start + task.eta_seconds, 3)
            task_payload["eta_start_seconds"] = task_eta_start
            task_payload["eta_end_seconds"] = task_eta_end
            tasks_payload.append(task_payload)
            selected_tasks_by_id[task.tool_id] = {
                "task": task,
                "eta_start_seconds": task_eta_start,
                "eta_end_seconds": task_eta_end,
            }
        plan_waves.append(
            {
                "index": wave.index,
                "threads_used": wave.threads_used,
                "ram_gb_used": wave.ram_gb_used,
                "eta_seconds": wave.eta_seconds,
                "eta_start_seconds": wave_start,
                "eta_end_seconds": wave_end,
                "tasks": tasks_payload,
            }
        )

    logical_runs_payload: list[dict[str, Any]] = []
    for run_id in selected_tools:
        logical_spec = logical_run_specs[run_id]
        physical_tasks_payload: list[dict[str, Any]] = []
        logical_starts: list[float] = []
        logical_ends: list[float] = []
        for raw_physical in logical_spec["physical_tasks"]:
            task_id = str(raw_physical["task_id"])
            scheduled = selected_tasks_by_id.get(task_id)
            if scheduled is None:
                raise ValueError(
                    f"Planner did not select a mode for physical task '{task_id}'"
                )
            task = scheduled["task"]
            task_start = float(scheduled["eta_start_seconds"])
            task_end = float(scheduled["eta_end_seconds"])
            logical_starts.append(task_start)
            logical_ends.append(task_end)
            task_payload = {
                "task_id": task_id,
                "group_label": raw_physical["group_label"],
                "columns": int(raw_physical["columns"]),
                "output_dir": str(raw_physical["output_dir"]),
                "threads": int(task.threads),
                "ram_gb": round(float(task.ram_gb), 3),
                "eta_seconds": round(float(task.eta_seconds), 3),
                "eta_source": str(task.eta_source),
                "eta_start_seconds": round(task_start, 3),
                "eta_end_seconds": round(task_end, 3),
            }
            note = _task_eta_note(task.eta_source)
            if note is not None:
                task_payload["note"] = note
            physical_tasks_payload.append(task_payload)

        logical_eta_start = round(min(logical_starts), 3) if logical_starts else 0.0
        logical_eta_end = round(max(logical_ends), 3) if logical_ends else 0.0
        logical_runs_payload.append(
            {
                "run_id": run_id,
                "tool_id": logical_spec["tool_id"],
                "execution_scope": logical_spec["execution_scope"],
                "execution": logical_spec["execution"],
                "physical_tasks_total": len(physical_tasks_payload),
                "eta_start_seconds": logical_eta_start,
                "eta_end_seconds": logical_eta_end,
                "eta_seconds": round(logical_eta_end - logical_eta_start, 3),
                "physical_tasks": physical_tasks_payload,
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
            "logical_runs_total": int(len(selected_tools)),
            "physical_tasks_total": int(sum(len(w.tasks) for w in waves)),
            "tasks_total": int(sum(len(w.tasks) for w in waves)),
            "waves_total": int(len(waves)),
            "threads_peak": int(max((w.threads_used for w in waves), default=0)),
            "ram_peak_gb": round(
                float(max((w.ram_gb_used for w in waves), default=0.0)), 3
            ),
        },
        "runs": logical_runs_payload,
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
            "status_by_tool": {tool_id: "pending" for tool_id in selected_tools},
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
            "physical_tasks_total": int(sum(len(w.tasks) for w in waves)),
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
