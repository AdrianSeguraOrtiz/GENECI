"""Scenario-first planning helpers for generate-v2."""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import Any

from .catalog import _load_simulator_catalog
from .request import (
    _resolve_simulator_params,
    validate_simulation_plan_payload,
)
from .scenario import validate_scenario_request
from .selection import evaluate_simulator_for_scenario
from .shared import (
    MAX_SEED_32BIT,
    _load_json_object,
    _stable_seed_base,
    _validate_json_instance,
    _write_json,
)


def _load_simulator_runs_payload(path: Path) -> dict[str, Any]:
    payload = _load_json_object(path, "simulator-runs")
    schemas, _catalog = _load_simulator_catalog()
    _validate_json_instance(
        instance=payload,
        schema=schemas["simulator_runs"],
        label="simulator-runs",
    )
    return payload


def _replicate_seeds(base_seed: int, replicates: int) -> list[int]:
    return [
        ((int(base_seed) - 1 + idx) % MAX_SEED_32BIT) + 1 for idx in range(replicates)
    ]


def _build_simulation_plan_payload(
    *,
    scenario_request_path: Path,
    simulator_runs_path: Path,
    max_parallel_tasks: int | None = None,
) -> dict[str, Any]:
    scenario = validate_scenario_request(scenario_request_path)
    simulator_runs_payload = _load_simulator_runs_payload(simulator_runs_path)
    _schemas, catalog = _load_simulator_catalog()

    selected_runs = simulator_runs_payload.get("runs", [])
    run_ids = [str(item.get("run_id", "")) for item in selected_runs]
    duplicated = sorted({run_id for run_id in run_ids if run_ids.count(run_id) > 1})
    if duplicated:
        raise ValueError(
            "Duplicate run_id values are not allowed: " + ", ".join(duplicated)
        )

    resolved_runs: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    seed_offset = 0
    for run_config in selected_runs:
        run_id = str(run_config["run_id"])
        simulator_id = str(run_config["simulator_id"])
        replicates = int(run_config.get("replicates", 0))
        if replicates < 1:
            raise ValueError(f"simulator-runs.runs[{run_id}].replicates must be >= 1")
        if simulator_id not in catalog:
            raise ValueError(f"Unknown simulator_id: {simulator_id}")
        simulator_spec = catalog[simulator_id]
        entry = evaluate_simulator_for_scenario(
            simulator_id=simulator_id,
            spec=simulator_spec,
            scenario=scenario,
        )
        if entry["status"] == "blocked":
            raise ValueError(
                f"Simulator run '{run_id}' is blocked for scenario '{scenario.request_id}': "
                + "; ".join(entry["blocking_reasons"])
            )
        resolved_params = _resolve_simulator_params(
            simulator_id=simulator_id,
            user_params=dict(run_config.get("params", {})),
            spec_params=simulator_spec.get("params", {}),
        )
        base_seed = run_config.get("base_seed")
        if base_seed is None:
            if scenario.base_seed is None:
                base_seed = _stable_seed_base(
                    request_id=scenario.request_id,
                    profile=scenario.profile,
                    simulator_id=f"{run_id}|{simulator_id}",
                )
            else:
                base_seed = (
                    (int(scenario.base_seed) - 1 + seed_offset) % MAX_SEED_32BIT
                ) + 1
        seeds = _replicate_seeds(int(base_seed), replicates)
        seed_offset += replicates
        resolved_runs.append(
            {
                "run_id": run_id,
                "simulator_id": simulator_id,
                "simulator_params": resolved_params,
                "replicates": replicates,
                "base_seed": int(base_seed),
                "replicate_seeds": seeds,
                **({"notes": run_config["notes"]} if run_config.get("notes") else {}),
            }
        )
        for replicate_index, seed in enumerate(seeds, start=1):
            task_id = f"{run_id}__r{replicate_index:02d}"
            tasks.append(
                {
                    "task_id": task_id,
                    "run_id": run_id,
                    "simulator_id": simulator_id,
                    "replicate_index": replicate_index,
                    "seed": seed,
                    "dataset_id": f"{scenario.request_id}__{task_id}",
                }
            )

    if max_parallel_tasks is None:
        max_parallel_tasks = multiprocessing.cpu_count()
    max_parallel_tasks = max(1, min(int(max_parallel_tasks), max(1, len(tasks))))

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "id": scenario.request_id,
        "profile": scenario.profile,
        "organism": dict(scenario.organism),
        "requested_extras": list(scenario.requested_extras),
        "effective_extras": list(scenario.effective_extras),
        "inputs": {
            key: {**scenario.inputs[key], "path": str(path)}
            for key, path in sorted(scenario.resolved_input_files.items())
        },
        "input_files": {
            key: str(path)
            for key, path in sorted(scenario.resolved_input_files.items())
        },
        "runs": resolved_runs,
        "tasks": tasks,
        "execution": {
            "max_parallel_tasks": max_parallel_tasks,
        },
        "base_seed": scenario.base_seed,
    }
    if scenario.notes:
        payload["notes"] = scenario.notes
    return payload


def plan_generate_v2_request(
    *,
    scenario_request_path: Path,
    simulator_runs_path: Path,
    output_path: Path,
    max_parallel_tasks: int | None = None,
) -> Path:
    payload = _build_simulation_plan_payload(
        scenario_request_path=scenario_request_path,
        simulator_runs_path=simulator_runs_path,
        max_parallel_tasks=max_parallel_tasks,
    )
    validate_simulation_plan_payload(payload, base_dir=output_path.resolve().parent)
    _write_json(output_path, payload)
    return output_path
