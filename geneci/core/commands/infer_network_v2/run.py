"""Phase C: Execution for infer-network-v2.

Phase dependencies:
1. Planned run_dir integrity checks.
2. Runtime IO prep + Docker wave execution.
3. Merge and normalization of tool outputs.
4. Final run_report persistence.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

from rich import print

from .commons.artifacts import _load_plan_waves, _verify_input_fingerprints
from .commons.catalog import _load_schema_constraints, _resolve_catalog_paths
from .commons.dataset import _parse_dataset_context
from .commons.merge import _merge_network_outputs
from .commons.runtime_helpers import (
    _ensure_docker_cli,
    _prepare_shared_inputs,
    _prepare_tool_runtime_io,
    _run_wave,
)
from .commons.shared import _load_json_object, _write_json
from .commons.tools import _collect_requirement_issues, _load_toolspec


def run_infer_network_new_plan(
    *,
    run_dir: Path,
    progress_poll_seconds: float = 0.5,
    strict: bool = False,
) -> Path:
    started_at = time.perf_counter()
    if progress_poll_seconds <= 0:
        raise ValueError("progress_poll_seconds must be > 0")

    run_dir = run_dir.resolve()
    if not run_dir.exists() or not run_dir.is_dir():
        raise ValueError(f"run_dir does not exist or is not a directory: {run_dir}")

    plan_path = run_dir / "plan.json"
    preflight_path = run_dir / "preflight_report.json"
    report_path = run_dir / "run_report.json"
    if not plan_path.exists():
        raise ValueError(f"Missing plan.json in run_dir: {plan_path}")
    if not preflight_path.exists():
        raise ValueError(f"Missing preflight_report.json in run_dir: {preflight_path}")
    if not report_path.exists():
        raise ValueError(f"Missing run_report.json in run_dir: {report_path}")

    plan_payload = _load_json_object(plan_path, "plan")
    preflight_report = _load_json_object(preflight_path, "preflight_report")
    run_report = _load_json_object(report_path, "run_report")

    fingerprints = plan_payload.get("input_fingerprints", {})
    if not isinstance(fingerprints, dict) or not fingerprints:
        raise ValueError("plan.json missing input_fingerprints")
    _verify_input_fingerprints(run_dir=run_dir, fingerprints=fingerprints)

    _selected_modes, waves, _total_eta = _load_plan_waves(plan_payload)
    runs_payload = preflight_report.get("runs", {})
    if not isinstance(runs_payload, dict):
        raise ValueError("Invalid preflight_report.runs")
    selected_tools = [x for x in runs_payload.get("selected", []) if isinstance(x, str)]
    selected_tool_catalog_ids = {
        str(k): str(v)
        for k, v in runs_payload.get("catalog_tool_ids", {}).items()
        if isinstance(k, str) and isinstance(v, str)
    }
    skipped_tools = {
        str(k): str(v)
        for k, v in runs_payload.get("skipped", {}).items()
        if isinstance(k, str)
    }

    tools_root, schemas_dir = _resolve_catalog_paths()
    constraints = _load_schema_constraints(schemas_dir)
    frozen_manifest = run_dir / "input" / "dataset-manifest.json"
    dataset = _parse_dataset_context(
        dataset_manifest_path=frozen_manifest,
        constraints=constraints,
    )

    resolved_params_by_tool = {}
    for run_id in selected_tools:
        params_path = run_dir / "tools" / run_id / "resolved_params.json"
        if not params_path.exists():
            raise ValueError(
                f"Missing resolved params for run '{run_id}': {params_path}"
            )
        resolved_params_by_tool[run_id] = _load_json_object(
            params_path,
            f"resolved_params[{run_id}]",
        )

    requirement_issues: dict[str, list[str]] = {}
    for run_id in selected_tools:
        catalog_tool_id = selected_tool_catalog_ids.get(run_id, "").strip()
        if not catalog_tool_id:
            raise ValueError(
                f"preflight report is missing catalog mapping for run '{run_id}'"
            )
        toolspec = _load_toolspec(tools_root, catalog_tool_id)
        issues = _collect_requirement_issues(
            tool_id=run_id,
            toolspec=toolspec,
            dataset=dataset,
            resolved_params=resolved_params_by_tool[run_id],
        )
        if issues:
            requirement_issues[run_id] = issues

    if requirement_issues:
        error_lines: list[str] = []
        for run_id in sorted(requirement_issues):
            for message in requirement_issues[run_id]:
                error_lines.append(f"[{run_id}] {message}")
        raise ValueError(
            "Execution blocked by missing conditional inputs:\n"
            + "\n".join(error_lines)
        )

    warnings = [str(w) for w in run_report.get("warnings", []) if isinstance(w, str)]
    execution_results = {}
    merged_raw_path = None
    merged_norm_path = None
    per_tool_rows = {}

    _ensure_docker_cli()
    shared_expression, shared_extras = _prepare_shared_inputs(
        run_dir=run_dir,
        dataset=dataset,
        constraints=constraints,
    )

    runtime_io_by_tool = {}
    for tool_id, resolved_params in resolved_params_by_tool.items():
        runtime_io_by_tool[tool_id] = _prepare_tool_runtime_io(
            run_dir=run_dir,
            tool_id=tool_id,
            resolved_params=resolved_params,
            shared_expression=shared_expression,
            shared_extras=shared_extras,
        )

    pulled_images = set()
    for wave in waves:
        wave_results = _run_wave(
            wave=wave,
            runtime_io_by_tool=runtime_io_by_tool,
            pulled_images=pulled_images,
            poll_interval_s=progress_poll_seconds,
            warnings=warnings,
        )
        execution_results.update(wave_results)

    execution_results, per_tool_rows, merged_raw_path, merged_norm_path = (
        _merge_network_outputs(
            run_dir=run_dir,
            execution_results=execution_results,
            warnings=warnings,
        )
    )

    completed_tools = sorted(
        tool_id
        for tool_id, result in execution_results.items()
        if result.status == "completed"
    )
    failed_tools = {
        tool_id: (result.error or "unknown error")
        for tool_id, result in execution_results.items()
        if result.status != "completed"
    }

    elapsed_total = round(time.perf_counter() - started_at, 3)
    run_report["status"] = "executed"
    run_report["tools"] = {
        "selected": selected_tools,
        "catalog_tool_ids": selected_tool_catalog_ids,
        "skipped": skipped_tools,
        "completed": completed_tools,
        "failed": failed_tools,
        "results": {
            tool_id: asdict(result)
            for tool_id, result in sorted(execution_results.items())
        },
    }
    run_report["outputs"] = {
        "merged_network_raw": (
            str(merged_raw_path.resolve()) if merged_raw_path else None
        ),
        "merged_network_normalized": (
            str(merged_norm_path.resolve()) if merged_norm_path else None
        ),
        "rows_per_tool": per_tool_rows,
    }
    run_report["warnings"] = warnings
    execution_info = run_report.get("execution", {})
    if not isinstance(execution_info, dict):
        execution_info = {}
    execution_info.update(
        {
            "elapsed_seconds": elapsed_total,
            "waves_total": len(waves),
            "tools_selected": len(selected_tools),
            "tools_completed": len(completed_tools),
            "tools_failed": len(failed_tools),
        }
    )
    run_report["execution"] = execution_info
    _write_json(report_path, run_report)

    print(f"[bold green]infer-network-v2 execution completed[/bold green]: {run_dir}")
    print(f"  selected tools: {len(selected_tools)}")
    print(f"  skipped tools: {len(skipped_tools)}")
    print(f"  completed tools: {len(completed_tools)}")
    print(f"  failed tools: {len(failed_tools)}")
    print(f"  elapsed time: {elapsed_total:.2f}s")
    print(f"  waves: {len(waves)}")
    if merged_raw_path:
        print(f"  merged raw: {merged_raw_path}")
    if merged_norm_path:
        print(f"  merged normalized: {merged_norm_path}")
    if warnings:
        print(f"  warnings: {len(warnings)} (see run_report.json)")

    if not completed_tools:
        raise ValueError(
            "All tool executions failed. See run_report.json and per-tool container.log files."
        )
    if strict and failed_tools:
        raise ValueError("One or more tools failed during execution (strict mode).")
    return run_dir
