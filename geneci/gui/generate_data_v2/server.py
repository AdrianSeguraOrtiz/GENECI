"""FastAPI server for the local generate-data-v2 GUI."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import threading
import traceback
import uuid
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from geneci.core.commands.benchmarking.generate_v2 import (
    plan_generate_v2_request,
    preflight_generate_v2_scenario,
    run_generate_v2,
)
from geneci.core.commands.benchmarking.generate_v2.catalog import (
    _load_simulator_catalog,
)
from geneci.core.commands.benchmarking.generate_v2.shared import (
    KNOWN_EXTRAS,
    PROFILE_SPECS,
)
from geneci.core.commands.infer_network_v2 import _load_input_specs
from geneci.gui.common.server_files import (
    MAX_TABLE_PREVIEW_ROWS,
    MAX_TEXT_PREVIEW_BYTES,
    build_bundle_entries,
    build_zip_bundle,
    default_viewer_for_path,
    is_probably_text,
    preview_table,
    preview_text,
    read_json_if_exists,
    resolve_virtual_source,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
COMMON_STATIC_DIR = Path(__file__).resolve().parents[1] / "common" / "static"
GUI_TMP_ROOT = Path("/tmp/geneci_gui/generate_data_v2")

CANONICAL_SIMULATOR_INPUTS: dict[str, dict[str, Any]] = {
    "grn": {
        "id": "grn",
        "label": "Input GRN",
        "description": "Optional prior/source GRN with source, target and weight columns.",
        "formats": ["tsv", "csv"],
        "required_columns": ["source", "target", "weight"],
        "example": "source\ttarget\tweight\nG1\tG2\t0.83\nG3\tG2\t-0.21",
        "accept": ".tsv,.csv,.txt",
        "requires_organism": True,
    }
}

CANONICAL_OUTPUT_EXTRAS: dict[str, dict[str, Any]] = {
    "group_networks": {
        "key": "group_networks",
        "label": "group_networks/*.csv",
        "description": "Optional public truth edge lists exported one file per group under truth/group_networks/.",
        "file_kind": "directory",
        "example": "truth/group_networks/group_a.csv\ntruth/group_networks/group_b.csv",
    }
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class GuiJob:
    job_id: str
    created_at: str
    status: str
    stage: str
    request_dir: str
    output_dir: str
    scenario_request_path: Optional[str] = None
    simulator_runs_path: Optional[str] = None
    preflight_report_path: Optional[str] = None
    plan_path: Optional[str] = None
    benchmark_root: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    runtime_progress: dict[str, dict[str, Any]] = field(default_factory=dict)


class GuiState:
    def __init__(self) -> None:
        self.jobs: dict[str, GuiJob] = {}
        self.lock = threading.RLock()


STATE = GuiState()


def _load_generate_bootstrap() -> dict[str, Any]:
    _schemas, catalog = _load_simulator_catalog()
    input_specs = _load_input_specs()
    extras_by_profile: dict[str, set[str]] = {
        profile_id: set(spec.required_extras)
        for profile_id, spec in PROFILE_SPECS.items()
    }
    simulator_inputs: dict[str, dict[str, Any]] = {
        key: dict(value) for key, value in CANONICAL_SIMULATOR_INPUTS.items()
    }

    def _merge_simulator_input(item: dict[str, Any], *, simulator_id: str) -> None:
        input_id = str(item.get("id") or item.get("input") or "").strip()
        if not input_id:
            return
        existing = simulator_inputs.setdefault(
            input_id,
            {
                "id": input_id,
                "label": input_id,
                "description": str(item.get("description", "")),
                "formats": [],
                "required_columns": [],
                "accept": "",
                "requires_organism": False,
                "supported_by": [],
            },
        )
        existing.setdefault("supported_by", [])
        if simulator_id not in existing["supported_by"]:
            existing["supported_by"].append(simulator_id)
        if item.get("description") and not existing.get("description"):
            existing["description"] = str(item["description"])
        formats = item.get("formats", [])
        if isinstance(formats, list):
            existing["formats"] = sorted(
                set(existing.get("formats", [])).union(str(x) for x in formats)
            )

    for simulator_id, spec in sorted(catalog.items()):
        profile_capabilities = spec.get("profile_capabilities", {})
        if isinstance(profile_capabilities, dict):
            for profile_id, capability in profile_capabilities.items():
                if profile_id not in extras_by_profile or not isinstance(
                    capability, dict
                ):
                    continue
                extras_by_profile[profile_id].update(
                    str(x)
                    for x in capability.get("native_extras", [])
                    if isinstance(x, str) and x in KNOWN_EXTRAS
                )
                extras_by_profile[profile_id].update(
                    str(x)
                    for x in capability.get("derivable_extras", [])
                    if isinstance(x, str) and x in KNOWN_EXTRAS
                )
                truth_outputs = capability.get("truth_outputs", {})
                if isinstance(truth_outputs, dict):
                    extras_by_profile[profile_id].update(
                        key
                        for key, mode in truth_outputs.items()
                        if key in KNOWN_EXTRAS and mode in {"native", "derivable"}
                    )
        raw_inputs = spec.get("simulator_inputs", {})
        if isinstance(raw_inputs, dict):
            for group_key in ("required", "optional"):
                for item in raw_inputs.get(group_key, []):
                    if isinstance(item, dict):
                        _merge_simulator_input(item, simulator_id=simulator_id)
            for item in raw_inputs.get("conditional_required", []):
                if isinstance(item, dict):
                    _merge_simulator_input(item, simulator_id=simulator_id)

    profiles = [
        {
            "id": profile_id,
            "column_kind": spec.column_kind,
            "expression_profile": spec.expression_profile,
            "required_extras": sorted(spec.required_extras),
            "available_extras": sorted(extras_by_profile.get(profile_id, set())),
        }
        for profile_id, spec in sorted(PROFILE_SPECS.items())
    ]
    extras = []
    for key in sorted(set().union(*extras_by_profile.values())):
        spec = CANONICAL_OUTPUT_EXTRAS.get(key, input_specs.get(key, {}))
        default_suffix = ".txt" if spec.get("file_kind") == "txt_list" else ".tsv"
        extras.append(
            {
                "key": key,
                "label": str(spec.get("label", f"{key}{default_suffix}")),
                "description": str(
                    spec.get("description", f"Optional generated extra '{key}'.")
                ),
                "file_kind": str(spec.get("file_kind", "tsv")),
                "example": str(spec.get("example", "")),
            }
        )
    simulators = []
    for simulator_id, spec in sorted(catalog.items()):
        simulators.append(
            {
                "simulator_id": simulator_id,
                "id": simulator_id,
                "name": spec["name"],
                "publication": spec.get("publication", []),
                "first_author": spec.get("first_author"),
                "year": spec.get("year"),
                "simulation_summary": spec.get("simulation_summary"),
                "simulation_keywords": spec.get("simulation_keywords", []),
                "implementation_url": spec.get("implementation_url"),
                "docker_image": spec.get("docker_image"),
                "simulator_inputs": spec.get("simulator_inputs", {}),
                "profile_capabilities": spec.get("profile_capabilities", {}),
                "params_schema": spec.get("params", {}),
            }
        )
    return {
        "profiles": profiles,
        "extras": extras,
        "planning_defaults": {
            "max_parallel_tasks": max(1, int(os.cpu_count() or 1)),
        },
        "simulator_inputs": sorted(
            simulator_inputs.values(), key=lambda item: str(item.get("id", ""))
        ),
        "simulators": simulators,
    }


def _frozen_job_artifact_paths(job: GuiJob) -> dict[str, Optional[str]]:
    benchmark_root = Path(job.benchmark_root) if job.benchmark_root else None
    if benchmark_root is None or not benchmark_root.exists():
        return {
            "scenario_request_path": job.scenario_request_path,
            "simulator_runs_path": job.simulator_runs_path,
            "preflight_report_path": job.preflight_report_path,
            "plan_path": job.plan_path,
        }

    candidates = {
        "scenario_request_path": benchmark_root / "input" / "scenario-request.json",
        "simulator_runs_path": benchmark_root / "input" / "simulator-runs.json",
        "preflight_report_path": benchmark_root / "preflight-report.json",
        "plan_path": benchmark_root / "simulation-plan.json",
    }
    return {
        key: str(path.resolve()) if path.exists() else getattr(job, key)
        for key, path in candidates.items()
    }


def _job_payload(job: GuiJob) -> dict[str, Any]:
    preferred_paths = _frozen_job_artifact_paths(job)
    return {
        "job_id": job.job_id,
        "created_at": job.created_at,
        "status": job.status,
        "stage": job.stage,
        "request_dir": job.request_dir,
        "output_dir": job.output_dir,
        "scenario_request_path": preferred_paths["scenario_request_path"],
        "simulator_runs_path": preferred_paths["simulator_runs_path"],
        "preflight_report_path": preferred_paths["preflight_report_path"],
        "plan_path": preferred_paths["plan_path"],
        "benchmark_root": job.benchmark_root,
        "run_dir": job.benchmark_root,
        "error": job.error,
        "traceback": job.traceback,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


def _save_upload(upload: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as out_fh:
        file_obj = getattr(upload, "file", None)
        if file_obj is None:
            raise ValueError("Invalid uploaded file")
        file_obj.seek(0)
        shutil.copyfileobj(file_obj, out_fh)


def _scenario_payload_from_config(
    *,
    config: dict[str, Any],
    form: Any,
    request_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scenario = config.get("scenario")
    if not isinstance(scenario, dict):
        raise ValueError("config.scenario must be an object")
    options = config.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError("config.options must be an object when provided")

    payload = {
        "schema_version": "1.0",
        "id": str(scenario.get("id", "")).strip(),
        "profile": str(scenario.get("profile", "")).strip(),
        "organism": scenario.get("organism", {"kind": "synthetic", "tax_id": None}),
        "requested_extras": list(scenario.get("requested_extras", [])),
    }
    if scenario.get("base_seed") not in (None, ""):
        payload["base_seed"] = int(scenario["base_seed"])
    if str(scenario.get("notes", "")).strip():
        payload["notes"] = str(scenario["notes"]).strip()

    inputs = scenario.get("inputs") or {}
    if not isinstance(inputs, dict):
        raise ValueError("config.scenario.inputs must be an object when provided")
    resolved_inputs: dict[str, dict[str, Any]] = {
        str(input_id): dict(meta)
        for input_id, meta in inputs.items()
        if isinstance(meta, dict)
    }

    for key in form.keys():
        if not str(key).startswith("input__"):
            continue
        input_id = str(key).removeprefix("input__").strip()
        upload = form.get(key)
        if not input_id or upload is None or not getattr(upload, "filename", ""):
            continue
        suffix = Path(str(upload.filename)).suffix
        filename = f"{input_id}{suffix}" if suffix else input_id
        destination = request_dir / "inputs" / filename
        _save_upload(upload, destination)
        meta = resolved_inputs.get(input_id, {})
        meta["path"] = str(Path("inputs") / filename)
        resolved_inputs[input_id] = meta

    if resolved_inputs:
        payload["inputs"] = resolved_inputs
    return payload, options


def _write_scenario_request_file(
    *,
    request_dir: Path,
    config: dict[str, Any],
    form: Any,
) -> tuple[Path, dict[str, Any]]:
    payload, options = _scenario_payload_from_config(
        config=config,
        form=form,
        request_dir=request_dir,
    )
    scenario_path = request_dir / "scenario-request.json"
    scenario_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return scenario_path, options


def _normalize_simulator_runs(raw_runs: Any) -> dict[str, Any]:
    if not isinstance(raw_runs, list) or not raw_runs:
        raise ValueError("runs must be a non-empty array")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_runs, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"runs[{idx}] must be an object")
        simulator_id = str(raw.get("simulator_id", "")).strip()
        if not simulator_id:
            raise ValueError(f"runs[{idx}].simulator_id is required")
        run_id = str(raw.get("run_id") or f"{simulator_id}__{idx:02d}").strip()
        if not run_id:
            raise ValueError(f"runs[{idx}].run_id is required")
        if run_id in seen:
            raise ValueError(f"Duplicate run_id: {run_id}")
        seen.add(run_id)
        params = raw.get("params", {})
        if not isinstance(params, dict):
            raise ValueError(f"runs[{idx}].params must be an object")
        item: dict[str, Any] = {
            "run_id": run_id,
            "simulator_id": simulator_id,
            "replicates": int(raw.get("replicates", 1)),
            "params": params,
        }
        native_outputs = raw.get("native_outputs")
        if native_outputs is not None:
            if not isinstance(native_outputs, list):
                raise ValueError(f"runs[{idx}].native_outputs must be an array")
            item["native_outputs"] = list(
                dict.fromkeys(
                    str(value).strip()
                    for value in native_outputs
                    if str(value).strip()
                )
            )
        if raw.get("base_seed") not in (None, ""):
            item["base_seed"] = int(raw["base_seed"])
        if str(raw.get("notes", "")).strip():
            item["notes"] = str(raw["notes"]).strip()
        normalized.append(item)
    return {"schema_version": "1.0", "runs": normalized}


def _write_simulator_runs_file(*, request_dir: Path, runs_raw: Any) -> Path:
    payload = _normalize_simulator_runs(runs_raw)
    path = request_dir / "simulator-runs.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return path


def _runtime_progress_payload(job: GuiJob) -> dict[str, Any]:
    items = list(job.runtime_progress.values())
    if not items and job.plan_path:
        plan = read_json_if_exists(job.plan_path)
        if isinstance(plan, dict):
            for task in plan.get("tasks", []):
                if isinstance(task, dict):
                    items.append(
                        {
                            "task_id": task.get("task_id"),
                            "run_id": task.get("run_id"),
                            "simulator_id": task.get("simulator_id"),
                            "replicate_index": task.get("replicate_index"),
                            "seed": task.get("seed"),
                            "dataset_id": task.get("dataset_id"),
                            "percent": 0,
                            "status": "pending",
                            "phase": "pending",
                            "message": "Pending execution",
                        }
                    )
    order = {str(item.get("task_id", "")): idx for idx, item in enumerate(items)}
    plan = read_json_if_exists(job.plan_path)
    if isinstance(plan, dict):
        order = {
            str(task.get("task_id", "")): idx
            for idx, task in enumerate(plan.get("tasks", []))
            if isinstance(task, dict)
        }
    items.sort(key=lambda item: order.get(str(item.get("task_id", "")), 10_000))
    summary = {
        "total": len(items),
        "completed": sum(1 for item in items if item.get("status") == "completed"),
        "failed": sum(1 for item in items if item.get("status") == "failed"),
        "running": sum(1 for item in items if item.get("status") == "running"),
        "pending": sum(1 for item in items if item.get("status") == "pending"),
    }
    return {"tasks": items, "summary": summary}


def _progress_callback_for_job(job_id: str):
    def _callback(event: dict[str, Any]) -> None:
        task_id = str(event.get("task_id", "")).strip()
        if not task_id:
            return
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                return
            previous = job.runtime_progress.get(task_id, {})
            previous_percent = int(previous.get("percent", 0) or 0)
            next_event = dict(event)
            next_event["percent"] = max(
                previous_percent, int(next_event.get("percent", 0) or 0)
            )
            job.runtime_progress[task_id] = next_event

    return _callback


def _run_job(*, job_id: str, action: str, options: dict[str, Any]) -> None:
    with STATE.lock:
        job = STATE.jobs[job_id]
        job.status = "running"
        job.started_at = _utc_now()
        job.finished_at = None

    try:
        with STATE.lock:
            job = STATE.jobs[job_id]
            scenario_path = (
                Path(job.scenario_request_path) if job.scenario_request_path else None
            )
            simulator_runs_path = (
                Path(job.simulator_runs_path) if job.simulator_runs_path else None
            )
            plan_path = Path(job.plan_path) if job.plan_path else None
            output_dir = Path(job.output_dir)

        if action == "preflight":
            if scenario_path is None:
                raise ValueError("Job is missing scenario_request_path")
            report = preflight_generate_v2_scenario(scenario_path)
            preflight_path = Path(job.request_dir) / "preflight-report.json"
            preflight_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "preflight_ok"
                job.preflight_report_path = str(preflight_path)
                job.finished_at = _utc_now()
            return

        if action == "plan":
            if scenario_path is None or simulator_runs_path is None:
                raise ValueError("Job is missing scenario or simulator-runs path")
            output_path = Path(job.request_dir) / "simulation-plan.json"
            plan_generate_v2_request(
                scenario_request_path=scenario_path,
                simulator_runs_path=simulator_runs_path,
                output_path=output_path,
                max_parallel_tasks=int(options.get("max_parallel_tasks", 1)),
            )
            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "planned"
                job.plan_path = str(output_path)
                job.runtime_progress = {}
                job.finished_at = _utc_now()
            return

        if action == "run":
            if plan_path is None:
                raise ValueError("Job has no simulation plan to execute")
            benchmark_root = run_generate_v2(
                plan_path=plan_path,
                output_dir=output_dir,
                max_parallel_tasks=(
                    int(options["max_parallel_tasks"])
                    if options.get("max_parallel_tasks") not in (None, "")
                    else None
                ),
                progress_poll_seconds=float(options.get("progress_poll_seconds", 0.5)),
                show_progress=False,
                progress_callback=_progress_callback_for_job(job_id),
            )
            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "executed"
                job.benchmark_root = str(benchmark_root.resolve())
                frozen_paths = _frozen_job_artifact_paths(job)
                job.scenario_request_path = frozen_paths["scenario_request_path"]
                job.simulator_runs_path = frozen_paths["simulator_runs_path"]
                job.preflight_report_path = frozen_paths["preflight_report_path"]
                job.plan_path = frozen_paths["plan_path"]
                job.finished_at = _utc_now()
            return

        raise ValueError(f"Unsupported job action: {action}")
    except Exception as exc:  # noqa: BLE001
        with STATE.lock:
            job = STATE.jobs[job_id]
            job.status = "failed"
            job.error = str(exc)
            job.traceback = traceback.format_exc(limit=30)
            job.finished_at = _utc_now()


def _shell_join_pretty(args: list[str]) -> str:
    if len(args) <= 3:
        return " ".join(shlex.quote(str(item)) for item in args)
    head = " ".join(shlex.quote(str(item)) for item in args[:3])
    groups: list[str] = []
    idx = 3
    while idx < len(args):
        token = str(args[idx])
        if token.startswith("--") and idx + 1 < len(args):
            next_token = str(args[idx + 1])
            if not next_token.startswith("--"):
                groups.append(f"{shlex.quote(token)} {shlex.quote(next_token)}")
                idx += 2
                continue
        groups.append(shlex.quote(token))
        idx += 1
    return head + "".join(f" \\\n  {group}" for group in groups)


def _python_path_expr(path_value: Optional[str]) -> str:
    return f"Path({str(path_value or '')!r})"


def _build_reproducibility_payload(job: GuiJob) -> dict[str, Any]:
    benchmark_root = Path(job.benchmark_root) if job.benchmark_root else None
    if benchmark_root is None or not benchmark_root.exists():
        return {
            "available": False,
            "message": "Reproducibility snippets will be available after execution.",
        }
    scenario_file = benchmark_root / "input" / "scenario-request.json"
    simulator_runs_file = benchmark_root / "input" / "simulator-runs.json"
    plan_file = benchmark_root / "simulation-plan.json"
    if not (
        scenario_file.exists()
        and simulator_runs_file.exists()
        and plan_file.exists()
    ):
        return {
            "available": False,
            "message": "Frozen benchmark inputs are not available yet in the output directory.",
        }
    scenario_path = str(scenario_file.resolve())
    simulator_runs_path = str(simulator_runs_file.resolve())
    plan_path = str(plan_file.resolve())
    output_dir = str(benchmark_root.parent.resolve())
    progress_poll_seconds = 0.5
    plan = read_json_if_exists(plan_path) or {}
    max_parallel_tasks = int(
        (plan.get("execution") or {}).get("max_parallel_tasks", 1)
        if isinstance(plan.get("execution"), dict)
        else 1
    )
    preflight_output_json = str((benchmark_root / "preflight-report.json").resolve())

    cli_unified = [
        "geneci",
        "benchmarking",
        "generate-v2",
        "execute",
        "--scenario",
        scenario_path,
        "--simulator-runs",
        simulator_runs_path,
        "--output-dir",
        output_dir,
        "--max-parallel-tasks",
        str(max_parallel_tasks),
        "--progress-poll-seconds",
        str(progress_poll_seconds),
    ]
    cli_preflight = [
        "geneci",
        "benchmarking",
        "generate-v2",
        "preflight",
        "--scenario",
        scenario_path,
        "--output-json",
        preflight_output_json,
    ]
    cli_plan = [
        "geneci",
        "benchmarking",
        "generate-v2",
        "plan",
        "--scenario",
        scenario_path,
        "--simulator-runs",
        simulator_runs_path,
        "--max-parallel-tasks",
        str(max_parallel_tasks),
        "--out",
        plan_path,
    ]
    cli_run = [
        "geneci",
        "benchmarking",
        "generate-v2",
        "run",
        "--plan",
        plan_path,
        "--output-dir",
        output_dir,
        "--progress-poll-seconds",
        str(progress_poll_seconds),
    ]

    python_unified = "\n".join(
        [
            "from pathlib import Path",
            "",
            "from geneci.core.commands.benchmarking.generate_v2 import execute_generate_v2",
            "",
            "benchmark_root = execute_generate_v2(",
            f"    scenario_request_path={_python_path_expr(scenario_path)},",
            f"    simulator_runs_path={_python_path_expr(simulator_runs_path)},",
            f"    output_dir={_python_path_expr(output_dir)},",
            f"    max_parallel_tasks={max_parallel_tasks},",
            f"    progress_poll_seconds={progress_poll_seconds},",
            ")",
            "",
            "print(benchmark_root)",
        ]
    )
    python_steps = "\n".join(
        [
            "from pathlib import Path",
            "",
            "from geneci.core.commands.benchmarking.generate_v2 import (",
            "    plan_generate_v2_request,",
            "    preflight_generate_v2_scenario,",
            "    run_generate_v2,",
            ")",
            "",
            f"scenario_path = {_python_path_expr(scenario_path)}",
            f"simulator_runs_path = {_python_path_expr(simulator_runs_path)}",
            f"plan_path = {_python_path_expr(plan_path)}",
            f"output_dir = {_python_path_expr(output_dir)}",
            "",
            "preflight_report = preflight_generate_v2_scenario(scenario_path)",
            "plan_generate_v2_request(",
            "    scenario_request_path=scenario_path,",
            "    simulator_runs_path=simulator_runs_path,",
            "    output_path=plan_path,",
            f"    max_parallel_tasks={max_parallel_tasks},",
            ")",
            "benchmark_root = run_generate_v2(",
            "    plan_path=plan_path,",
            "    output_dir=output_dir,",
            f"    progress_poll_seconds={progress_poll_seconds},",
            ")",
            "",
            "print(preflight_report)",
            "print(benchmark_root)",
        ]
    )
    return {
        "available": True,
        "cli": {
            "title": "CLI",
            "summary": "Replay this GUI job using the frozen scenario and simulator-runs files stored in the benchmark output directory.",
            "primary_label": "Unified command",
            "primary_language": "bash",
            "primary_code": _shell_join_pretty(cli_unified),
            "steps_label": "If you prefer by steps",
            "steps": [
                {
                    "title": "1. Preflight",
                    "language": "bash",
                    "code": _shell_join_pretty(cli_preflight),
                },
                {
                    "title": "2. Plan",
                    "language": "bash",
                    "code": _shell_join_pretty(cli_plan),
                },
                {
                    "title": "3. Run",
                    "language": "bash",
                    "code": _shell_join_pretty(cli_run),
                },
            ],
        },
        "python": {
            "title": "Python",
            "summary": "Replay this GUI job using the generate-v2 Python API and the frozen benchmark inputs.",
            "primary_label": "Unified code",
            "primary_language": "python",
            "primary_code": python_unified,
            "steps_label": "If you prefer by steps",
            "steps": [
                {
                    "title": "1-3. Preflight, plan, and run",
                    "language": "python",
                    "code": python_steps,
                }
            ],
        },
    }


def _bundle_sources(
    *,
    request_dir: Path,
    benchmark_root: Optional[Path],
    mode: str,
    include_inputs: bool = True,
) -> list[tuple[str, Path]]:
    if mode not in {"light", "full"}:
        raise ValueError("mode must be one of: light, full")
    sources: list[tuple[str, Path]] = []
    if benchmark_root is None or not benchmark_root.exists():
        request_candidates = [
            request_dir / "scenario-request.json",
            request_dir / "simulator-runs.json",
            request_dir / "preflight-report.json",
            request_dir / "simulation-plan.json",
        ]
        for path in request_candidates:
            if path.exists() and path.is_file():
                sources.append((f"input/{path.name}", path))
        if include_inputs and mode == "full":
            inputs_dir = request_dir / "inputs"
            if inputs_dir.exists():
                for path in sorted(inputs_dir.rglob("*")):
                    if path.is_file():
                        sources.append(
                            (f"input/{path.relative_to(request_dir).as_posix()}", path)
                        )
        return sorted(dict(sources).items())
    if mode == "full":
        for path in sorted(benchmark_root.rglob("*")):
            if path.is_file():
                sources.append(
                    (f"benchmark/{path.relative_to(benchmark_root).as_posix()}", path)
                )
    else:
        candidates = [
            benchmark_root / "benchmark-manifest.json",
            benchmark_root / "preflight-report.json",
            benchmark_root / "simulation-plan.json",
            benchmark_root / "input" / "scenario-request.json",
            benchmark_root / "input" / "simulator-runs.json",
        ]
        input_root = benchmark_root / "input" / "inputs"
        if include_inputs and input_root.exists():
            candidates.extend(path for path in sorted(input_root.rglob("*")) if path.is_file())
        for dataset_dir in sorted((benchmark_root / "datasets").glob("*")):
            if not dataset_dir.is_dir():
                continue
            candidates.extend(
                [
                    dataset_dir / "dataset-manifest.json",
                    dataset_dir / "ground-truth-manifest.json",
                    dataset_dir / "expression.tsv",
                    dataset_dir / "truth" / "global_network.csv",
                    dataset_dir / "truth" / "legacy" / "global_gs.csv",
                    dataset_dir / "provenance" / "simulator-output-manifest.json",
                    dataset_dir / "provenance" / "simulator-run.json",
                    dataset_dir / "provenance" / "progress.json",
                ]
            )
            for folder in [
                dataset_dir / "extras",
                dataset_dir / "truth" / "group_networks",
            ]:
                if folder.exists():
                    candidates.extend(
                        path for path in sorted(folder.rglob("*")) if path.is_file()
                    )
        for path in candidates:
            if path.exists() and path.is_file():
                sources.append(
                    (f"benchmark/{path.relative_to(benchmark_root).as_posix()}", path)
                )
    unique: dict[str, Path] = {}
    for virtual_path, source_path in sources:
        unique[virtual_path] = source_path
    return sorted(unique.items(), key=lambda item: item[0])


def _viewer_for_virtual_path(path: str) -> str:
    if Path(path.lower()).name == "simulation-plan.json":
        return "plan"
    return default_viewer_for_path(path)


def _artifact_guide(path: str) -> Optional[dict[str, Any]]:
    normalized = path.lower()
    basename = Path(normalized).name
    if basename == "benchmark-manifest.json":
        return {
            "title": "Benchmark manifest",
            "summary": "Top-level index of generated datasets, simulator runs, seeds and benchmark artifacts.",
            "tips": [
                "Use this file to audit which simulator configuration produced each dataset."
            ],
        }
    if basename == "dataset-manifest.json":
        return {
            "title": "Dataset manifest",
            "summary": "Input contract consumed directly by infer-network-v2.",
            "tips": [
                "Pass this file to infer-network-v2 preflight/plan/run for one generated dataset."
            ],
        }
    if basename == "ground-truth-manifest.json":
        return {
            "title": "Ground-truth manifest",
            "summary": "Index of truth artifacts generated for this dataset.",
            "tips": [
                "Evaluation flows should use this manifest rather than guessing truth file paths."
            ],
        }
    if basename == "expression.tsv":
        return {
            "title": "Expression matrix",
            "summary": "Normalized simulated expression table with genes in rows.",
            "tips": [
                "This is the expression input referenced by dataset-manifest.json."
            ],
        }
    if basename in {
        "groups.tsv",
        "lineage_tree.tsv",
        "tf_list.txt",
        "prior_grn_by_group.tsv",
    }:
        return {
            "title": f"Extra input: {basename}",
            "summary": "Additional dataset layer requested for compatible inference tools.",
            "tips": [
                "This file is referenced from dataset-manifest.json when present."
            ],
        }
    if "truth/" in normalized:
        return {
            "title": "Truth artifact",
            "summary": "Public simulated ground truth for benchmark evaluation.",
            "tips": [
                "Use normalized edge-list truth for v2 evaluation and legacy matrix where older evaluators require it."
            ],
        }
    if basename == "simulator-output-manifest.json":
        return {
            "title": "Simulator output manifest",
            "summary": "Adapter-level normalized output contract produced before final package assembly.",
            "tips": [
                "This is provenance/debug metadata, not an infer-network-v2 input."
            ],
        }
    return None


def create_app() -> FastAPI:
    app = FastAPI(title="GENECI GUI - generate-data-v2")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount(
        "/static-common", StaticFiles(directory=COMMON_STATIC_DIR), name="static-common"
    )
    bootstrap = _load_generate_bootstrap()

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"}
        )

    @app.get("/api/generate-data-v2/bootstrap")
    async def api_bootstrap() -> JSONResponse:
        return JSONResponse(bootstrap)

    @app.get("/api/generate-data-v2/jobs")
    async def api_jobs() -> JSONResponse:
        with STATE.lock:
            jobs = [_job_payload(job) for job in STATE.jobs.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return JSONResponse({"jobs": jobs})

    @app.get("/api/generate-data-v2/jobs/{job_id}")
    async def api_job(job_id: str) -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            payload = _job_payload(job)
            runtime_progress = _runtime_progress_payload(job)
            reproducibility = _build_reproducibility_payload(job)
        return JSONResponse(
            {
                "job": payload,
                "preflight_report": read_json_if_exists(
                    payload.get("preflight_report_path")
                ),
                "plan": read_json_if_exists(payload.get("plan_path")),
                "benchmark_manifest": (
                    read_json_if_exists(
                        Path(payload["benchmark_root"]) / "benchmark-manifest.json"
                    )
                    if payload.get("benchmark_root")
                    else None
                ),
                "runtime_progress": runtime_progress,
                "reproducibility": reproducibility,
            }
        )

    @app.get("/api/generate-data-v2/jobs/{job_id}/plan")
    async def api_job_plan(job_id: str) -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            plan_path = _frozen_job_artifact_paths(job)["plan_path"]
            status = job.status
        return JSONResponse(
            {
                "status": status,
                "plan": read_json_if_exists(plan_path),
                "plan_path": plan_path,
            }
        )

    @app.get("/api/generate-data-v2/jobs/{job_id}/files")
    async def api_job_files(job_id: str, mode: str = "light") -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            benchmark_root = Path(job.benchmark_root) if job.benchmark_root else None
            status = job.status
        try:
            sources = _bundle_sources(
                request_dir=request_dir,
                benchmark_root=benchmark_root,
                mode=mode,
                include_inputs=False,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(
            {
                "status": status,
                "mode": mode,
                "entries": build_bundle_entries(
                    sources, viewer_for_path=_viewer_for_virtual_path
                ),
            }
        )

    @app.get("/api/generate-data-v2/jobs/{job_id}/file-content")
    async def api_job_file_content(
        job_id: str,
        path: str,
        mode: str = "light",
        max_rows: int = MAX_TABLE_PREVIEW_ROWS,
    ) -> JSONResponse:
        requested_path = str(path or "").strip().lstrip("/")
        if not requested_path:
            raise HTTPException(status_code=400, detail="path is required")
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            benchmark_root = Path(job.benchmark_root) if job.benchmark_root else None
        try:
            sources = _bundle_sources(
                request_dir=request_dir, benchmark_root=benchmark_root, mode=mode
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        source = resolve_virtual_source(sources=sources, virtual_path=requested_path)
        if source is None or not source.exists() or not source.is_file():
            raise HTTPException(
                status_code=404, detail=f"File not found in bundle: {requested_path}"
            )

        viewer = _viewer_for_virtual_path(requested_path)
        guide = _artifact_guide(requested_path)
        if viewer == "plan":
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "json",
                    "text": json.dumps(
                        read_json_if_exists(source) or {}, indent=2, ensure_ascii=True
                    ),
                    "guide": guide,
                }
            )
        if viewer == "json":
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
                text = json.dumps(payload, indent=2, ensure_ascii=True)
            except Exception:
                text = source.read_text(encoding="utf-8", errors="replace")
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "json",
                    "text": text,
                    "truncated": False,
                    "guide": guide,
                }
            )
        if viewer == "table_csv":
            table = preview_table(
                source=source,
                delimiter=",",
                max_rows=max(1, min(int(max_rows), MAX_TABLE_PREVIEW_ROWS)),
            )
            return JSONResponse(
                {"path": requested_path, "viewer": "table_csv", **table, "guide": guide}
            )
        if viewer == "table_tsv":
            table = preview_table(
                source=source,
                delimiter="\t",
                max_rows=max(1, min(int(max_rows), MAX_TABLE_PREVIEW_ROWS)),
            )
            return JSONResponse(
                {"path": requested_path, "viewer": "table_tsv", **table, "guide": guide}
            )
        if viewer == "text":
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "text",
                    **preview_text(source, MAX_TEXT_PREVIEW_BYTES),
                    "guide": guide,
                }
            )
        if is_probably_text(source):
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "text",
                    **preview_text(source, MAX_TEXT_PREVIEW_BYTES),
                    "guide": guide,
                }
            )
        if guide:
            return JSONResponse(
                {"path": requested_path, "viewer": "artifact_guide", **guide}
            )
        raise HTTPException(
            status_code=400,
            detail=f"Preview is not available for this file type: {requested_path}",
        )

    @app.get("/api/generate-data-v2/jobs/{job_id}/bundle")
    async def api_job_bundle(job_id: str, mode: str = "light") -> FileResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            benchmark_root = Path(job.benchmark_root) if job.benchmark_root else None
        try:
            sources = _bundle_sources(
                request_dir=request_dir, benchmark_root=benchmark_root, mode=mode
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        zip_path = request_dir / f"{job_id}_bundle_{mode}.zip"
        build_zip_bundle(zip_path=zip_path, sources=sources)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"geneci_generate_{job_id}_{mode}.zip",
        )

    @app.post("/api/generate-data-v2/preflight")
    async def api_preflight(request: Request) -> JSONResponse:
        form = await request.form()
        config_raw = form.get("config")
        if not isinstance(config_raw, str) or not config_raw.strip():
            raise HTTPException(status_code=400, detail="config JSON is required")
        try:
            config = json.loads(config_raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"config JSON is malformed at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            ) from exc
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="config must be a JSON object")

        job_id = uuid.uuid4().hex[:12]
        request_dir = (GUI_TMP_ROOT / job_id).resolve()
        request_dir.mkdir(parents=True, exist_ok=True)
        try:
            scenario_path, options = _write_scenario_request_file(
                request_dir=request_dir,
                config=config,
                form=form,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        output_dir = Path(
            str(options.get("output_dir", "./benchmarks_v2") or "./benchmarks_v2")
        ).resolve()
        job = GuiJob(
            job_id=job_id,
            created_at=_utc_now(),
            status="queued",
            stage="draft",
            request_dir=str(request_dir),
            output_dir=str(output_dir),
            scenario_request_path=str(scenario_path),
        )
        with STATE.lock:
            STATE.jobs[job_id] = job
        threading.Thread(
            target=_run_job,
            kwargs={"job_id": job_id, "action": "preflight", "options": options},
            daemon=True,
        ).start()
        return JSONResponse(
            {
                "job_id": job_id,
                "status": "queued",
                "stage": "draft",
                "scenario_request_path": str(scenario_path),
            }
        )

    @app.post("/api/generate-data-v2/plan")
    async def api_plan(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Request body must be a JSON object"
            )
        job_id = str(payload.get("job_id", "")).strip()
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        options = payload.get("options") or {}
        if not isinstance(options, dict):
            raise HTTPException(status_code=400, detail="options must be an object")
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if job.status == "running":
                raise HTTPException(status_code=409, detail="Job is already running")
            if job.stage not in {"preflight_ok", "planned", "executed"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job is not ready for planning (stage={job.stage})",
                )
            request_dir = Path(job.request_dir)
        try:
            simulator_runs_path = _write_simulator_runs_file(
                request_dir=request_dir, runs_raw=payload.get("runs")
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        with STATE.lock:
            job = STATE.jobs[job_id]
            job.status = "queued"
            job.stage = "preflight_ok"
            job.simulator_runs_path = str(simulator_runs_path)
            if options.get("output_dir") not in (None, ""):
                job.output_dir = str(Path(str(options["output_dir"])).resolve())
            job.plan_path = None
            job.benchmark_root = None
            job.error = None
            job.traceback = None
            job.runtime_progress = {}
        threading.Thread(
            target=_run_job,
            kwargs={"job_id": job_id, "action": "plan", "options": options},
            daemon=True,
        ).start()
        return JSONResponse(
            {
                "job_id": job_id,
                "status": "queued",
                "stage": "preflight_ok",
                "simulator_runs_path": str(simulator_runs_path),
            }
        )

    @app.post("/api/generate-data-v2/run")
    async def api_run(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Request body must be a JSON object"
            )
        job_id = str(payload.get("job_id", "")).strip()
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        options = payload.get("options") or {}
        if not isinstance(options, dict):
            raise HTTPException(status_code=400, detail="options must be an object")
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if job.status == "running":
                raise HTTPException(status_code=409, detail="Job is already running")
            if not job.plan_path:
                raise HTTPException(
                    status_code=400, detail="No planned simulation found for this job"
                )
            if job.stage not in {"planned", "executed"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job is not in planned state (stage={job.stage})",
                )
            if options.get("output_dir") not in (None, ""):
                job.output_dir = str(Path(str(options["output_dir"])).resolve())
            job.status = "queued"
            job.error = None
            job.traceback = None
            job.benchmark_root = None
            job.runtime_progress = {}
        threading.Thread(
            target=_run_job,
            kwargs={"job_id": job_id, "action": "run", "options": options},
            daemon=True,
        ).start()
        return JSONResponse({"job_id": job_id, "status": "queued", "stage": "planned"})

    return app


def run_server(*, host: str, port: int, open_browser: bool) -> None:
    app = create_app()
    if open_browser:
        url = f"http://{host}:{port}/"
        timer = threading.Timer(
            0.8, lambda: webbrowser.open(url, new=2, autoraise=True)
        )
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=host, port=port, log_level="info")
