"""Public pipeline for generate-v2 benchmark package assembly."""

from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from rich import print
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .backends.registry import run_simulator_backend
from .catalog import _load_simulator_catalog
from .plan import plan_generate_v2_request
from .selection import preflight_generate_v2_scenario
from .request import validate_simulation_plan
from .shared import (
    DEFAULT_OUTPUT_DIR,
    PROFILE_SPECS,
    ResolvedSimulationPlan,
    ResolvedSimulatorRun,
    _copy_file,
    _copy_tree,
    _load_json_object,
    _relative_posix,
    _validate_json_instance,
    _write_json,
)

INFERENCE_DATASET_MANIFEST_SCHEMA = (
    Path(__file__).resolve().parents[4]
    / "inference_catalog"
    / "schemas"
    / "dataset-manifest.schema.json"
)

_STEP_PERCENT = {
    "prepare_image": 2,
    "container_started": 5,
    "validate_request": 10,
    "initialise_model": 20,
    "run_simulator": 45,
    "package_outputs": 75,
    "derive_truth": 82,
    "derive_extras": 85,
    "write_manifest": 95,
    "package_dataset": 98,
    "done": 95,
    "failed": 100,
}


def _short_progress_message(message: str, *, max_len: int = 64) -> str:
    compact = " ".join(message.strip().split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3]}..."


def _progress_snapshot(payload: dict[str, Any]) -> tuple[int, str, str, str]:
    status = str(payload.get("status", "running"))
    phase = str(payload.get("phase") or payload.get("step") or "unknown")
    message = str(payload.get("message", ""))
    raw_percent = payload.get("percent")
    if raw_percent is None:
        percent = _STEP_PERCENT.get(phase, 0)
    else:
        percent = int(raw_percent)
    if status == "completed":
        percent = 100
        status = "completed"
    elif status == "done":
        status = "running"
    elif status == "failed":
        percent = 100
    return max(0, min(100, percent)), status, phase, message


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_progress_event(
    *,
    task: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    percent, status, phase, message = _progress_snapshot(payload)
    return {
        "task_id": str(task["task_id"]),
        "run_id": str(task["run_id"]),
        "simulator_id": str(task["simulator_id"]),
        "replicate_index": int(task["replicate_index"]),
        "seed": int(task["seed"]),
        "dataset_id": str(task["dataset_id"]),
        "percent": percent,
        "status": status,
        "phase": phase,
        "message": message,
        "updated_at": _utc_now(),
    }


def _combine_progress_callbacks(
    *,
    task: dict[str, Any],
    terminal_callback: Callable[[dict[str, Any]], None] | None,
    external_callback: Callable[[dict[str, Any]], None] | None,
) -> Callable[[dict[str, Any]], None] | None:
    if terminal_callback is None and external_callback is None:
        return None

    def _callback(payload: dict[str, Any]) -> None:
        if terminal_callback is not None:
            terminal_callback(payload)
        if external_callback is not None:
            external_callback(_normalized_progress_event(task=task, payload=payload))

    return _callback


class _GenerateProgress:
    def __init__(
        self,
        *,
        tasks: list[dict[str, Any]],
        max_parallel_tasks: int,
        enabled: bool,
    ) -> None:
        self._tasks = tasks
        self._max_parallel_tasks = max_parallel_tasks
        self._enabled = enabled
        self._live = bool(enabled and sys.stdout.isatty())
        self._progress: Progress | None = None
        self._task_ids: dict[str, int] = {}
        self._last_snapshots: dict[str, tuple[int, str, str, str]] = {}
        self._lock = threading.Lock()

    def __enter__(self) -> "_GenerateProgress":
        if not self._enabled:
            return self
        print(
            f"generate-v2: starting {len(self._tasks)} simulator task(s), "
            f"max_parallel_tasks={self._max_parallel_tasks}"
        )
        if not self._live:
            return self

        self._progress = Progress(
            TextColumn("{task.fields[task]:<32}"),
            BarColumn(bar_width=24),
            TaskProgressColumn(),
            TextColumn("{task.fields[status]:<9}"),
            TextColumn("{task.fields[phase]:<18}"),
            TextColumn("{task.fields[msg]}"),
            TimeElapsedColumn(),
            transient=False,
        )
        self._progress.start()
        for task in self._tasks:
            task_id = str(task["task_id"])
            self._task_ids[task_id] = self._progress.add_task(
                "",
                total=100,
                completed=0,
                task=task_id,
                status="queued",
                phase="queued",
                msg=str(task["simulator_id"]),
            )
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._progress is not None:
            self._progress.stop()

    def callback_for(self, task_id: str) -> Callable[[dict[str, Any]], None] | None:
        if not self._enabled:
            return None

        def _callback(payload: dict[str, Any]) -> None:
            self.update(task_id, payload)

        return _callback

    def update(self, task_id: str, payload: dict[str, Any]) -> None:
        if not self._enabled:
            return
        percent, status, phase, message = _progress_snapshot(payload)
        previous = self._last_snapshots.get(task_id)
        if previous is not None:
            percent = max(percent, previous[0])
        snapshot = (percent, status, phase, message)
        with self._lock:
            if snapshot == self._last_snapshots.get(task_id):
                return
            self._last_snapshots[task_id] = snapshot
            if self._progress is not None:
                rich_task_id = self._task_ids.get(task_id)
                if rich_task_id is None:
                    rich_task_id = self._progress.add_task(
                        "",
                        total=100,
                        completed=0,
                        task=task_id,
                        status="running",
                        phase="unknown",
                        msg="",
                    )
                    self._task_ids[task_id] = rich_task_id
                self._progress.update(
                    rich_task_id,
                    completed=percent,
                    status=status,
                    phase=phase,
                    msg=_short_progress_message(message),
                )
            else:
                print(
                    f"simulator {task_id} progress: "
                    f"{percent}% | {status} | {phase} | {message}"
                )


def _run_simulator(
    *,
    request: ResolvedSimulatorRun,
    seed: int,
    stage_dir: Path,
    task_label: str,
    progress_poll_seconds: float,
    show_progress: bool,
    progress_callback: Callable[[dict[str, Any]], None] | None,
) -> Path:
    return run_simulator_backend(
        request=request,
        seed=seed,
        stage_dir=stage_dir,
        task_label=task_label,
        progress_poll_seconds=progress_poll_seconds,
        show_progress=show_progress,
        progress_callback=progress_callback,
    )


def _dataset_manifest_payload(
    *,
    dataset_id: str,
    request: ResolvedSimulatorRun,
    simulator_manifest: dict[str, Any],
) -> dict[str, Any]:
    expression = simulator_manifest["expression"]
    extras = simulator_manifest.get("extras", {})
    spec_profile = PROFILE_SPECS[request.profile]
    dataset_spec = {
        "schema_version": "1.0",
        "id": dataset_id,
        "name": dataset_id,
        "expression": {
            "genes": expression["genes"],
            "columns": expression["columns"],
            "column_kind": spec_profile.column_kind,
            "expression_profile": spec_profile.expression_profile,
        },
        "organism": dict(request.organism),
    }
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "id": f"{dataset_id}_manifest",
        "dataset": {
            "spec": dataset_spec,
            "expression_matrix": "expression.tsv",
        },
        "extras": {},
    }
    for key in ("groups", "lineage_tree", "tf_list", "prior_grn_by_group"):
        value = extras.get(key)
        if value is not None:
            payload["extras"][key] = value
    if request.notes:
        payload["notes"] = request.notes
    return payload


def _ground_truth_manifest_payload(
    *,
    dataset_id: str,
    request: ResolvedSimulatorRun,
    simulator_manifest: dict[str, Any],
) -> dict[str, Any]:
    truth = simulator_manifest["truth"]
    include_group_networks = "group_networks" in set(request.effective_extras)
    return {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "simulator_id": request.simulator_id,
        "profile": request.profile,
        "outputs": {
            "global_network": truth.get("global_network"),
            "legacy_binary_matrix": truth.get("legacy_binary_matrix"),
            "group_networks": [
                {
                    "group": str(item["group"]),
                    "path": str(item["path"]),
                }
                for item in truth.get("group_networks", [])
            ]
            if include_group_networks
            else [],
        },
        "notes": "Truth package generated by generate-v2.",
    }


def _simulator_run_payload(
    *,
    dataset_id: str,
    seed: int,
    request: ResolvedSimulatorRun,
    simulator_manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "benchmark_id": request.request_id,
        "run_id": request.run_id,
        "simulator_id": request.simulator_id,
        "profile": request.profile,
        "seed": seed,
        "inputs": request.inputs,
        "input_files": request.input_files,
        "simulator_params": request.simulator_params,
        "native_outputs": request.native_outputs,
        "requested_extras": request.requested_extras,
        "effective_extras": request.effective_extras,
        "docker_image": request.simulator_spec.get("docker_image"),
        "execution_backend": "docker_generate_v2",
        "simulator_output": simulator_manifest,
    }


def _copy_dataset_from_stage(
    *,
    stage_dir: Path,
    dataset_dir: Path,
    dataset_manifest_payload: dict[str, Any],
    ground_truth_manifest_payload: dict[str, Any],
    simulator_run_payload: dict[str, Any],
    include_group_networks: bool,
) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=False)
    _copy_file(stage_dir / "expression.tsv", dataset_dir / "expression.tsv")

    stage_extras = stage_dir / "extras"
    if stage_extras.exists():
        _copy_tree(stage_extras, dataset_dir / "extras")

    stage_native = stage_dir / "native"
    if stage_native.exists():
        _copy_tree(stage_native, dataset_dir / "native")

    stage_truth = stage_dir / "truth"
    if stage_truth.exists():
        _copy_tree(stage_truth, dataset_dir / "truth")
        if not include_group_networks:
            group_networks_dir = dataset_dir / "truth" / "group_networks"
            if group_networks_dir.exists():
                shutil.rmtree(group_networks_dir)

    stage_raw = stage_dir / "provenance" / "raw"
    if stage_raw.exists():
        _copy_tree(stage_raw, dataset_dir / "provenance" / "raw")
    stage_progress = stage_dir / "progress.json"
    if stage_progress.exists():
        _copy_file(stage_progress, dataset_dir / "provenance" / "progress.json")

    _copy_file(
        stage_dir / "simulator-output-manifest.json",
        dataset_dir / "provenance" / "simulator-output-manifest.json",
    )
    _write_json(dataset_dir / "dataset-manifest.json", dataset_manifest_payload)
    _write_json(
        dataset_dir / "ground-truth-manifest.json",
        ground_truth_manifest_payload,
    )
    _write_json(
        dataset_dir / "provenance" / "simulator-run.json", simulator_run_payload
    )


def _freeze_benchmark_input_files(
    *,
    resolved: ResolvedSimulationPlan,
    benchmark_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, str]]:
    scenario_inputs: dict[str, dict[str, Any]] = {}
    root_inputs: dict[str, dict[str, Any]] = {}
    root_input_files: dict[str, str] = {}
    for input_id, source_path in sorted(resolved.resolved_input_files.items()):
        raw_meta = dict(resolved.inputs.get(input_id, {}))
        raw_name = Path(str(raw_meta.get("path") or source_path.name)).name
        filename = raw_name or source_path.name or input_id
        root_rel_path = Path("input") / "inputs" / input_id / filename
        scenario_rel_path = Path("inputs") / input_id / filename
        _copy_file(source_path, benchmark_root / root_rel_path)

        scenario_meta = dict(raw_meta)
        scenario_meta["path"] = scenario_rel_path.as_posix()
        root_meta = dict(raw_meta)
        root_meta["path"] = root_rel_path.as_posix()

        scenario_inputs[input_id] = scenario_meta
        root_inputs[input_id] = root_meta
        root_input_files[input_id] = root_rel_path.as_posix()
    return scenario_inputs, root_inputs, root_input_files


def _frozen_scenario_payload(
    *,
    resolved: ResolvedSimulationPlan,
    scenario_inputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "id": resolved.request_id,
        "profile": resolved.profile,
        "organism": dict(resolved.organism),
        "requested_extras": list(resolved.requested_extras),
    }
    if scenario_inputs:
        payload["inputs"] = scenario_inputs
    if resolved.base_seed is not None:
        payload["base_seed"] = int(resolved.base_seed)
    if resolved.notes:
        payload["notes"] = resolved.notes
    return payload


def _frozen_simulator_runs_payload(
    *,
    resolved: ResolvedSimulationPlan,
) -> dict[str, Any]:
    raw_runs = resolved.plan_payload.get("runs", [])
    raw_runs_by_id = {
        str(item.get("run_id")): item
        for item in raw_runs
        if isinstance(item, dict) and item.get("run_id")
    }
    payload_runs: list[dict[str, Any]] = []
    for run in resolved.simulator_runs:
        raw_run = raw_runs_by_id.get(run.run_id, {})
        payload: dict[str, Any] = {
            "run_id": run.run_id,
            "simulator_id": run.simulator_id,
            "replicates": run.replicates,
            "params": dict(run.simulator_params),
        }
        if run.native_outputs:
            payload["native_outputs"] = list(run.native_outputs)
        if run.base_seed is not None:
            payload["base_seed"] = int(run.base_seed)
        notes = raw_run.get("notes")
        if isinstance(notes, str) and notes.strip():
            payload["notes"] = notes.strip()
        payload_runs.append(payload)
    payload = {"schema_version": "1.0", "runs": payload_runs}
    notes = resolved.plan_payload.get("notes")
    if isinstance(notes, str) and notes.strip():
        payload["notes"] = notes.strip()
    return payload


def _frozen_plan_payload(
    *,
    resolved: ResolvedSimulationPlan,
    root_inputs: dict[str, dict[str, Any]],
    root_input_files: dict[str, str],
    max_parallel_tasks: int,
) -> dict[str, Any]:
    payload = copy.deepcopy(resolved.plan_payload)
    payload["inputs"] = root_inputs
    payload["input_files"] = root_input_files
    payload["execution"] = {"max_parallel_tasks": int(max_parallel_tasks)}
    return payload


def _write_frozen_benchmark_request_assets(
    *,
    resolved: ResolvedSimulationPlan,
    benchmark_root: Path,
    schemas: dict[str, dict[str, Any]],
    max_parallel_tasks: int,
) -> dict[str, Any]:
    benchmark_input_dir = benchmark_root / "input"
    benchmark_input_dir.mkdir(parents=True, exist_ok=True)

    scenario_inputs, root_inputs, root_input_files = _freeze_benchmark_input_files(
        resolved=resolved,
        benchmark_root=benchmark_root,
    )

    scenario_payload = _frozen_scenario_payload(
        resolved=resolved,
        scenario_inputs=scenario_inputs,
    )
    _validate_json_instance(
        instance=scenario_payload,
        schema=schemas["scenario_request"],
        label=f"scenario-request[{resolved.request_id}]",
    )
    scenario_path = benchmark_input_dir / "scenario-request.json"
    _write_json(scenario_path, scenario_payload)

    simulator_runs_payload = _frozen_simulator_runs_payload(resolved=resolved)
    _validate_json_instance(
        instance=simulator_runs_payload,
        schema=schemas["simulator_runs"],
        label=f"simulator-runs[{resolved.request_id}]",
    )
    simulator_runs_path = benchmark_input_dir / "simulator-runs.json"
    _write_json(simulator_runs_path, simulator_runs_payload)

    plan_payload = _frozen_plan_payload(
        resolved=resolved,
        root_inputs=root_inputs,
        root_input_files=root_input_files,
        max_parallel_tasks=max_parallel_tasks,
    )
    _validate_json_instance(
        instance=plan_payload,
        schema=schemas["simulation_plan"],
        label=f"simulation-plan[{resolved.request_id}]",
    )
    plan_path = benchmark_root / "simulation-plan.json"
    _write_json(plan_path, plan_payload)

    preflight_report = preflight_generate_v2_scenario(scenario_path)
    preflight_path = benchmark_root / "preflight-report.json"
    _write_json(preflight_path, preflight_report)

    return {
        "scenario_request_path": scenario_path,
        "simulator_runs_path": simulator_runs_path,
        "plan_path": plan_path,
        "preflight_report_path": preflight_path,
        "inputs": root_inputs,
        "input_files": root_input_files,
    }


def validate_generate_v2_plan(plan_path: Path) -> dict[str, Any]:
    resolved = validate_simulation_plan(plan_path)
    return {
        "request_id": resolved.request_id,
        "profile": resolved.profile,
        "total_tasks": len(resolved.tasks),
        "requested_extras": resolved.requested_extras,
        "effective_extras": resolved.effective_extras,
        "inputs": resolved.inputs,
        "input_files": resolved.input_files,
        "runs": [
            {
                "run_id": run.run_id,
                "simulator_id": run.simulator_id,
                "simulator_params": run.simulator_params,
                "native_outputs": run.native_outputs,
                "replicates": run.replicates,
                "base_seed": run.base_seed,
                "replicate_seeds": run.replicate_seeds,
            }
            for run in resolved.simulator_runs
        ],
        "tasks": resolved.tasks,
        "execution": resolved.execution,
    }


def _validate_selected_native_outputs(
    *,
    stage_dir: Path,
    dataset_id: str,
    request: ResolvedSimulatorRun,
    simulator_manifest: dict[str, Any],
) -> dict[str, str]:
    raw_native_outputs = simulator_manifest.get("native_outputs", {})
    if not isinstance(raw_native_outputs, dict):
        raise ValueError(
            f"simulator-output-manifest[{dataset_id}].native_outputs must be an object"
        )

    resolved: dict[str, str] = {}
    for output_id in request.native_outputs:
        rel_path = raw_native_outputs.get(output_id)
        if not isinstance(rel_path, str) or not rel_path.strip():
            raise ValueError(
                f"simulator-output-manifest[{dataset_id}] is missing selected native_output '{output_id}'"
            )
        output_path = stage_dir / rel_path
        if not output_path.exists():
            raise ValueError(
                f"simulator-output-manifest[{dataset_id}] references missing native_output '{output_id}': {rel_path}"
            )
        resolved[output_id] = rel_path
    return resolved


def _execute_simulation_task(
    *,
    task: dict[str, Any],
    resolved: ResolvedSimulationPlan,
    schemas: dict[str, dict[str, Any]],
    staging_root: Path,
    datasets_root: Path,
    benchmark_root: Path,
    progress_poll_seconds: float,
    show_progress: bool,
    progress_callback: Callable[[dict[str, Any]], None] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    runs_by_id = {run.run_id: run for run in resolved.simulator_runs}
    run = runs_by_id[str(task["run_id"])]
    dataset_id = str(task["dataset_id"])
    seed = int(task["seed"])
    stage_dir = staging_root / dataset_id
    stage_dir.mkdir(parents=True, exist_ok=True)

    simulator_manifest_path = _run_simulator(
        request=run,
        seed=seed,
        stage_dir=stage_dir,
        task_label=str(task["task_id"]),
        progress_poll_seconds=progress_poll_seconds,
        show_progress=show_progress,
        progress_callback=progress_callback,
    )
    simulator_manifest = _load_json_object(
        simulator_manifest_path, f"simulator-output-manifest[{dataset_id}]"
    )
    _validate_json_instance(
        instance=simulator_manifest,
        schema=schemas["simulator_output_manifest"],
        label=f"simulator-output-manifest[{dataset_id}]",
    )
    native_output_paths = _validate_selected_native_outputs(
        stage_dir=stage_dir,
        dataset_id=dataset_id,
        request=run,
        simulator_manifest=simulator_manifest,
    )

    dataset_manifest_payload = _dataset_manifest_payload(
        dataset_id=dataset_id,
        request=run,
        simulator_manifest=simulator_manifest,
    )
    ground_truth_manifest_payload = _ground_truth_manifest_payload(
        dataset_id=dataset_id,
        request=run,
        simulator_manifest=simulator_manifest,
    )
    simulator_run_payload = _simulator_run_payload(
        dataset_id=dataset_id,
        seed=seed,
        request=run,
        simulator_manifest=simulator_manifest,
    )

    inference_dataset_schema = _load_json_object(
        INFERENCE_DATASET_MANIFEST_SCHEMA, "dataset-manifest.schema"
    )
    _validate_json_instance(
        instance=dataset_manifest_payload,
        schema=inference_dataset_schema,
        label=f"dataset-manifest[{dataset_id}]",
    )
    _validate_json_instance(
        instance=ground_truth_manifest_payload,
        schema=schemas["ground_truth_manifest"],
        label=f"ground-truth-manifest[{dataset_id}]",
    )

    dataset_dir = datasets_root / dataset_id
    if progress_callback is not None:
        progress_callback(
            {
                "status": "running",
                "step": "package_dataset",
                "message": "Copying normalized dataset package",
            }
        )
    _copy_dataset_from_stage(
        stage_dir=stage_dir,
        dataset_dir=dataset_dir,
        dataset_manifest_payload=dataset_manifest_payload,
        ground_truth_manifest_payload=ground_truth_manifest_payload,
        simulator_run_payload=simulator_run_payload,
        include_group_networks="group_networks" in set(run.effective_extras),
    )
    if progress_callback is not None:
        progress_callback(
            {
                "status": "completed",
                "step": "done",
                "message": "Dataset package written",
            }
        )

    dataset_entry = {
        "dataset_id": dataset_id,
        "run_id": run.run_id,
        "simulator_id": run.simulator_id,
        "seed": seed,
        "path": _relative_posix(dataset_dir, benchmark_root),
        "dataset_manifest": _relative_posix(
            dataset_dir / "dataset-manifest.json", benchmark_root
        ),
        "ground_truth_manifest": _relative_posix(
            dataset_dir / "ground-truth-manifest.json", benchmark_root
        ),
    }
    artifact_entry = {
        "dataset_id": dataset_id,
        "run_id": run.run_id,
        "simulator_id": run.simulator_id,
        "expression_matrix": _relative_posix(
            dataset_dir / "expression.tsv", benchmark_root
        ),
        "groups": (
            _relative_posix(dataset_dir / "extras" / "groups.tsv", benchmark_root)
            if (dataset_dir / "extras" / "groups.tsv").exists()
            else None
        ),
        "lineage_tree": (
            _relative_posix(
                dataset_dir / "extras" / "lineage_tree.tsv",
                benchmark_root,
            )
            if (dataset_dir / "extras" / "lineage_tree.tsv").exists()
            else None
        ),
        "tf_list": (
            _relative_posix(dataset_dir / "extras" / "tf_list.txt", benchmark_root)
            if (dataset_dir / "extras" / "tf_list.txt").exists()
            else None
        ),
        "prior_grn_by_group": (
            _relative_posix(
                dataset_dir / "extras" / "prior_grn_by_group.tsv",
                benchmark_root,
            )
            if (dataset_dir / "extras" / "prior_grn_by_group.tsv").exists()
            else None
        ),
        "global_network": _relative_posix(
            dataset_dir / "truth" / "global_network.csv",
            benchmark_root,
        ),
        "legacy_binary_matrix": _relative_posix(
            dataset_dir / "truth" / "legacy" / "global_gs.csv",
            benchmark_root,
        ),
        "group_networks_dir": (
            _relative_posix(
                dataset_dir / "truth" / "group_networks",
                benchmark_root,
            )
            if (dataset_dir / "truth" / "group_networks").exists()
            else None
        ),
        "native_outputs": {
            output_id: _relative_posix(dataset_dir / rel_path, benchmark_root)
            for output_id, rel_path in sorted(native_output_paths.items())
        },
    }
    return dataset_entry, artifact_entry


def run_generate_v2(
    *,
    plan_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_parallel_tasks: int | None = None,
    progress_poll_seconds: float = 0.5,
    show_progress: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    if progress_poll_seconds <= 0:
        raise ValueError("progress_poll_seconds must be > 0")
    resolved = validate_simulation_plan(plan_path)
    schemas, _catalog = _load_simulator_catalog()
    run_id = (
        f"{resolved.request_id}_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    benchmark_root = (output_dir / run_id).resolve()
    if benchmark_root.exists():
        raise ValueError(f"Benchmark output directory already exists: {benchmark_root}")
    datasets_root = benchmark_root / "datasets"
    datasets_root.mkdir(parents=True, exist_ok=False)

    benchmark_datasets: list[dict[str, Any]] = []
    benchmark_artifacts: list[dict[str, Any]] = []
    task_order = {str(task["task_id"]): idx for idx, task in enumerate(resolved.tasks)}
    if max_parallel_tasks is None:
        max_parallel_tasks = int(resolved.execution.get("max_parallel_tasks", 1))
    max_parallel_tasks = max(
        1, min(int(max_parallel_tasks), max(1, len(resolved.tasks)))
    )
    with tempfile.TemporaryDirectory(prefix="geneci_generate_v2_") as tmp:
        staging_root = Path(tmp) / "staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        with _GenerateProgress(
            tasks=resolved.tasks,
            max_parallel_tasks=max_parallel_tasks,
            enabled=show_progress,
        ) as progress_reporter:
            if progress_callback is not None:
                for task in resolved.tasks:
                    progress_callback(
                        _normalized_progress_event(
                            task=task,
                            payload={
                                "status": "pending",
                                "step": "queued",
                                "percent": 0,
                                "message": "Queued",
                            },
                        )
                    )
            with ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                future_to_task = {
                    executor.submit(
                        _execute_simulation_task,
                        task=task,
                        resolved=resolved,
                        schemas=schemas,
                        staging_root=staging_root,
                        datasets_root=datasets_root,
                        benchmark_root=benchmark_root,
                        progress_poll_seconds=progress_poll_seconds,
                        show_progress=show_progress,
                        progress_callback=_combine_progress_callbacks(
                            task=task,
                            terminal_callback=progress_reporter.callback_for(
                                str(task["task_id"])
                            ),
                            external_callback=progress_callback,
                        ),
                    ): task
                    for task in resolved.tasks
                }
                completed: list[tuple[dict[str, Any], dict[str, Any]]] = []
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        completed.append(future.result())
                    except Exception as exc:  # noqa: BLE001
                        progress_reporter.update(
                            str(task["task_id"]),
                            {
                                "status": "failed",
                                "step": "failed",
                                "message": str(exc),
                            },
                        )
                        raise
            completed.sort(
                key=lambda item: task_order[
                    item[0]["dataset_id"].removeprefix(f"{resolved.request_id}__")
                ]
            )
            for dataset_entry, artifact_entry in completed:
                benchmark_datasets.append(dataset_entry)
                benchmark_artifacts.append(artifact_entry)

    frozen_assets = _write_frozen_benchmark_request_assets(
        resolved=resolved,
        benchmark_root=benchmark_root,
        schemas=schemas,
        max_parallel_tasks=max_parallel_tasks,
    )

    benchmark_manifest = {
        "schema_version": "1.0",
        "id": resolved.request_id,
        "profile": resolved.profile,
        "organism": resolved.organism,
        "requested_extras": resolved.requested_extras,
        "effective_extras": resolved.effective_extras,
        "base_seed": resolved.base_seed,
        "inputs": frozen_assets["inputs"],
        "input_files": frozen_assets["input_files"],
        "runs": [
            {
                "run_id": run.run_id,
                "simulator_id": run.simulator_id,
                "replicates": run.replicates,
                "native_outputs": run.native_outputs,
                "base_seed": run.base_seed,
                "replicate_seeds": run.replicate_seeds,
                "resolved_simulator_params": run.simulator_params,
            }
            for run in resolved.simulator_runs
        ],
        "tasks": resolved.tasks,
        "execution": {"max_parallel_tasks": max_parallel_tasks},
        "datasets": benchmark_datasets,
        "artifacts": benchmark_artifacts,
    }
    if resolved.notes:
        benchmark_manifest["notes"] = resolved.notes
    _validate_json_instance(
        instance=benchmark_manifest,
        schema=schemas["benchmark_manifest"],
        label=f"benchmark-manifest[{resolved.request_id}]",
    )
    _write_json(benchmark_root / "benchmark-manifest.json", benchmark_manifest)
    return benchmark_root


def execute_generate_v2(
    *,
    scenario_request_path: Path,
    simulator_runs_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_parallel_tasks: int | None = None,
    progress_poll_seconds: float = 0.5,
    show_progress: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    preflight_generate_v2_scenario(scenario_request_path)
    with tempfile.TemporaryDirectory(prefix="geneci_generate_v2_plan_") as tmp:
        plan_path = Path(tmp) / "simulation-plan.json"
        plan_generate_v2_request(
            scenario_request_path=scenario_request_path,
            simulator_runs_path=simulator_runs_path,
            output_path=plan_path,
            max_parallel_tasks=max_parallel_tasks,
        )
        return run_generate_v2(
            plan_path=plan_path,
            output_dir=output_dir,
            max_parallel_tasks=max_parallel_tasks,
            progress_poll_seconds=progress_poll_seconds,
            show_progress=show_progress,
            progress_callback=progress_callback,
        )
