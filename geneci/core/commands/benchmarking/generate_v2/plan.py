"""Scenario-first planning helpers for generate-v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import _load_simulator_catalog
from .request import validate_benchmark_request_payload, _resolve_simulator_params
from .scenario import validate_scenario_request
from .selection import evaluate_simulator_for_scenario
from .shared import _write_json


def _build_benchmark_request_payload(
    *,
    scenario_request_path: Path,
    simulator_id: str,
    simulator_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scenario = validate_scenario_request(scenario_request_path)
    _schemas, catalog = _load_simulator_catalog()
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
            f"Simulator '{simulator_id}' is blocked for scenario '{scenario.request_id}': "
            + "; ".join(entry["blocking_reasons"])
        )

    resolved_params = _resolve_simulator_params(
        simulator_id=simulator_id,
        user_params=simulator_params or {},
        spec_params=simulator_spec.get("params", {}),
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "id": scenario.request_id,
        "profile": scenario.profile,
        "simulator_id": simulator_id,
        "replicates": scenario.replicates,
        "organism": dict(scenario.organism),
        "requested_extras": list(scenario.requested_extras),
        "input_files": {
            key: str(path)
            for key, path in sorted(scenario.resolved_input_files.items())
        },
        "simulator_params": resolved_params,
        "base_seed": scenario.base_seed,
    }
    if scenario.notes:
        payload["notes"] = scenario.notes
    return payload


def plan_generate_v2_request(
    *,
    scenario_request_path: Path,
    output_path: Path,
    simulator_id: str,
    simulator_params: dict[str, Any] | None = None,
) -> Path:
    payload = _build_benchmark_request_payload(
        scenario_request_path=scenario_request_path,
        simulator_id=simulator_id,
        simulator_params=simulator_params,
    )
    validate_benchmark_request_payload(payload, base_dir=output_path.resolve().parent)
    _write_json(output_path, payload)
    return output_path
