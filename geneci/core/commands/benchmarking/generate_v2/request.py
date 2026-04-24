"""Request parsing and validation for generate-v2."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from geneci.core.commands.infer_network_v2.commons.shared import ParamValidationError
from geneci.core.commands.infer_network_v2.commons.tools import _validate_param_value

from .catalog import _load_simulator_catalog, get_profile_capability
from .shared import (
    KNOWN_EXTRAS,
    PROFILE_SPECS,
    ResolvedSimulationPlan,
    ResolvedSimulatorRun,
    _load_json_object,
    _validate_json_instance,
)


def _supported_requested_artifacts(
    profile_capability: dict[str, Any],
) -> tuple[set[str], set[str]]:
    native = set(profile_capability.get("native_extras", []))
    derivable = set(profile_capability.get("derivable_extras", []))
    truth_outputs = profile_capability.get("truth_outputs", {})
    if isinstance(truth_outputs, dict):
        native.update(
            key
            for key, mode in truth_outputs.items()
            if key in KNOWN_EXTRAS and mode == "native"
        )
        derivable.update(
            key
            for key, mode in truth_outputs.items()
            if key in KNOWN_EXTRAS and mode == "derivable"
        )
    return native, derivable


def _supported_native_outputs(
    profile_capability: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    supported: dict[str, dict[str, Any]] = {}
    for item in profile_capability.get("native_outputs", []):
        if not isinstance(item, dict):
            continue
        output_id = str(item.get("id", "")).strip()
        if output_id:
            supported[output_id] = item
    return supported


def _resolve_native_outputs(
    *,
    simulator_id: str,
    profile: str,
    profile_capability: dict[str, Any],
    raw_native_outputs: Any,
    label: str,
) -> list[str]:
    supported = _supported_native_outputs(profile_capability)
    if raw_native_outputs is None:
        return []
    if not isinstance(raw_native_outputs, list):
        raise ValueError(f"{label}.native_outputs must be an array when provided")

    resolved: list[str] = []
    seen: set[str] = set()
    for item in raw_native_outputs:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"{label}.native_outputs must contain non-empty string identifiers"
            )
        output_id = item.strip()
        if output_id in seen:
            continue
        seen.add(output_id)
        resolved.append(output_id)

    unsupported = sorted(set(resolved).difference(supported))
    if unsupported:
        raise ValueError(
            f"Simulator '{simulator_id}' does not support native outputs for profile '{profile}': "
            f"{unsupported}"
        )
    return resolved


def _resolve_simulator_params(
    *,
    simulator_id: str,
    user_params: dict[str, Any],
    spec_params: dict[str, Any],
) -> dict[str, Any]:
    warnings: list[str] = []
    resolved: dict[str, Any] = {}
    errors: list[str] = []

    unknown_keys = sorted(set(user_params.keys()).difference(spec_params.keys()))
    if unknown_keys:
        raise ValueError(
            f"[{simulator_id}] unknown simulator_params keys: {', '.join(unknown_keys)}"
        )

    for param_name, param_def in spec_params.items():
        if not isinstance(param_def, dict):
            errors.append(f"invalid param definition for '{param_name}'")
            continue
        if param_name in user_params:
            raw_value = user_params[param_name]
        else:
            raw_value = copy.deepcopy(param_def.get("default"))

        if raw_value is None:
            if bool(param_def.get("required")) and param_def.get("default") is None:
                errors.append(f"missing required simulator param: {param_name}")
            resolved[param_name] = None
            continue
        try:
            resolved[param_name] = _validate_param_value(
                value=raw_value,
                param_def=param_def,
                path=f"{simulator_id}.{param_name}",
                warnings=warnings,
            )
        except ParamValidationError as exc:
            errors.append(str(exc))

    if errors:
        raise ValueError(
            f"[{simulator_id}] invalid simulator_params: {'; '.join(errors)}"
        )
    return resolved


def _resolve_input_files(
    raw_inputs: Any,
    *,
    base_dir: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, Path]]:
    if raw_inputs is None:
        return {}, {}, {}
    if not isinstance(raw_inputs, dict):
        raise ValueError("inputs must be an object mapping input id to input metadata")

    inputs: dict[str, dict[str, Any]] = {}
    input_files: dict[str, str] = {}
    resolved: dict[str, Path] = {}
    for input_id, raw_input in raw_inputs.items():
        if not isinstance(input_id, str) or not input_id:
            raise ValueError("inputs keys must be non-empty strings")
        if isinstance(raw_input, str):
            input_payload: dict[str, Any] = {"path": raw_input}
        elif isinstance(raw_input, dict):
            input_payload = dict(raw_input)
        else:
            raise ValueError(f"inputs.{input_id} must be an object with a path")
        raw_path = input_payload.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"inputs.{input_id}.path must be a non-empty path string")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        else:
            path = path.resolve()
        if not path.exists():
            raise ValueError(f"inputs.{input_id}.path does not exist: {path}")
        input_payload["path"] = raw_path
        inputs[input_id] = input_payload
        input_files[input_id] = raw_path
        resolved[input_id] = path
    return inputs, input_files, resolved


def _param_lookup(params: dict[str, Any], path: str) -> Any:
    current: Any = params
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _conditional_input_matches(
    requirement: dict[str, Any],
    *,
    profile: str,
    requested_extras: set[str],
    simulator_params: dict[str, Any],
) -> bool:
    if requirement.get("profile") not in (None, profile):
        return False
    requested_extra = requirement.get("requested_extra")
    if requested_extra is not None and requested_extra not in requested_extras:
        return False
    param = requirement.get("param")
    if param is None:
        return True
    actual = _param_lookup(simulator_params, str(param))
    op = str(requirement.get("op", "=="))
    expected = requirement.get("value")
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op == "in":
        return isinstance(expected, list) and actual in expected
    if op == "not_in":
        return isinstance(expected, list) and actual not in expected
    return False


def validate_simulator_input_files(
    *,
    simulator_id: str,
    simulator_spec: dict[str, Any],
    profile: str,
    requested_extras: list[str],
    simulator_params: dict[str, Any],
    input_files: dict[str, str],
) -> list[str]:
    simulator_inputs = simulator_spec.get("simulator_inputs", {})
    required = simulator_inputs.get("required", [])
    optional = simulator_inputs.get("optional", [])
    conditional_required = simulator_inputs.get("conditional_required", [])

    declared_ids = {
        str(item.get("id"))
        for item in required + optional
        if isinstance(item, dict) and item.get("id")
    }
    declared_ids.update(
        str(item.get("input"))
        for item in conditional_required
        if isinstance(item, dict) and item.get("input")
    )

    errors: list[str] = []
    unknown_inputs = sorted(set(input_files).difference(declared_ids))
    if unknown_inputs:
        errors.append(
            f"unknown input_files for simulator '{simulator_id}': {', '.join(unknown_inputs)}"
        )

    for item in required:
        if isinstance(item, dict):
            input_id = str(item.get("id", ""))
            if input_id and input_id not in input_files:
                errors.append(f"missing required input file '{input_id}'")

    requested_extra_set = set(requested_extras)
    for requirement in conditional_required:
        if not isinstance(requirement, dict):
            continue
        input_id = str(requirement.get("input", ""))
        if not input_id:
            continue
        if (
            _conditional_input_matches(
                requirement,
                profile=profile,
                requested_extras=requested_extra_set,
                simulator_params=simulator_params,
            )
            and input_id not in input_files
        ):
            errors.append(
                str(
                    requirement.get(
                        "message",
                        f"missing conditionally required input file '{input_id}'",
                    )
                )
            )
    return errors


def _validate_organism(payload: dict[str, Any]) -> None:
    kind = str(payload.get("kind", "biological")).strip() or "biological"
    tax_id = payload.get("tax_id")
    if kind == "biological":
        if not isinstance(tax_id, int) or tax_id < 1:
            raise ValueError(
                "organism.tax_id must be integer >= 1 when organism.kind=biological"
            )
    elif kind in {"synthetic", "unknown"}:
        if tax_id is not None and (not isinstance(tax_id, int) or tax_id < 1):
            raise ValueError(
                "organism.tax_id must be null or integer >= 1 when organism.kind is synthetic/unknown"
            )
    else:
        raise ValueError("organism.kind must be one of: biological, synthetic, unknown")


def _validate_common_plan_fields(
    payload: dict[str, Any],
    *,
    label: str,
) -> tuple[str, dict[str, Any], list[str], list[str], int | None]:
    profile = str(payload.get("profile", "")).strip()
    if profile not in PROFILE_SPECS:
        raise ValueError(f"Unknown benchmark profile: {profile}")

    requested_extras = list(payload.get("requested_extras", []))
    if any(extra not in KNOWN_EXTRAS for extra in requested_extras):
        unsupported = sorted(set(requested_extras).difference(KNOWN_EXTRAS))
        raise ValueError(f"Unknown requested_extras: {unsupported}")

    profile_required = set(PROFILE_SPECS[profile].required_extras)
    effective_extras = sorted(set(requested_extras).union(profile_required))

    organism = payload.get("organism", {"kind": "synthetic", "tax_id": None})
    if not isinstance(organism, dict):
        raise ValueError(f"{label}.organism must be an object")
    _validate_organism(organism)

    base_seed = payload.get("base_seed")
    if base_seed is not None and (not isinstance(base_seed, int)):
        raise ValueError(f"{label}.base_seed must be integer when provided")
    if base_seed is not None and int(base_seed) < 1:
        raise ValueError(f"{label}.base_seed must be >= 1")

    return profile, organism, requested_extras, effective_extras, base_seed


def _resolve_simulator_run(
    *,
    request_id: str,
    profile: str,
    run_id: str,
    organism: dict[str, Any],
    requested_extras: list[str],
    effective_extras: list[str],
    inputs: dict[str, dict[str, Any]],
    input_files: dict[str, str],
    resolved_input_files: dict[str, Path],
    run_payload: dict[str, Any],
    notes: str | None,
    catalog: dict[str, dict[str, Any]],
) -> ResolvedSimulatorRun:
    simulator_id = str(run_payload.get("simulator_id", "")).strip()
    if simulator_id not in catalog:
        raise ValueError(f"Unknown simulator_id in simulation-plan: {simulator_id}")
    simulator_spec = catalog[simulator_id]

    profile_capability = get_profile_capability(simulator_spec, profile)
    if profile_capability is None:
        raise ValueError(
            f"Simulator '{simulator_id}' does not support profile '{profile}'"
        )

    native, derivable = _supported_requested_artifacts(profile_capability)
    supported_extras = native.union(derivable)
    unsupported_requested = sorted(set(requested_extras).difference(supported_extras))
    if unsupported_requested:
        raise ValueError(
            f"Simulator '{simulator_id}' does not support requested extras for profile '{profile}': "
            f"{unsupported_requested}"
        )

    profile_required = set(PROFILE_SPECS[profile].required_extras)
    missing_profile_support = sorted(profile_required.difference(supported_extras))
    if missing_profile_support:
        raise ValueError(
            f"Simulator '{simulator_id}' cannot satisfy required extras for profile '{profile}': "
            f"{missing_profile_support}"
        )

    raw_simulator_params = run_payload.get("simulator_params", {})
    if not isinstance(raw_simulator_params, dict):
        raise ValueError(
            f"simulation-plan.runs[{run_id}].simulator_params must be an object"
        )
    resolved_params = _resolve_simulator_params(
        simulator_id=simulator_id,
        user_params=raw_simulator_params,
        spec_params=simulator_spec.get("params", {}),
    )
    native_outputs = _resolve_native_outputs(
        simulator_id=simulator_id,
        profile=profile,
        profile_capability=profile_capability,
        raw_native_outputs=run_payload.get("native_outputs"),
        label=f"simulation-plan.runs[{run_id}]",
    )

    input_errors = validate_simulator_input_files(
        simulator_id=simulator_id,
        simulator_spec=simulator_spec,
        profile=profile,
        requested_extras=requested_extras,
        simulator_params=resolved_params,
        input_files=input_files,
    )
    if input_errors:
        raise ValueError(
            f"[{simulator_id}] invalid input_files: {'; '.join(input_errors)}"
        )

    simulator_seed_base = run_payload.get("base_seed")
    if simulator_seed_base is None:
        raise ValueError(f"simulation-plan.runs[{run_id}].base_seed is required")
    if simulator_seed_base is not None and not isinstance(simulator_seed_base, int):
        raise ValueError(
            f"simulation-plan.runs[{run_id}].base_seed must be integer when provided"
        )
    if int(simulator_seed_base) < 1:
        raise ValueError(f"simulation-plan.runs[{run_id}].base_seed must be >= 1")

    replicates = int(run_payload.get("replicates", 0))
    if replicates < 1:
        raise ValueError(f"simulation-plan.runs[{run_id}].replicates must be >= 1")

    replicate_seeds = run_payload.get("replicate_seeds", [])
    if not isinstance(replicate_seeds, list) or not replicate_seeds:
        raise ValueError(
            f"simulation-plan.runs[{run_id}].replicate_seeds must be a non-empty array"
        )
    if any(not isinstance(seed, int) or seed < 1 for seed in replicate_seeds):
        raise ValueError(
            f"simulation-plan.runs[{run_id}].replicate_seeds must contain integers >= 1"
        )
    if len(replicate_seeds) != replicates:
        raise ValueError(
            f"simulation-plan.runs[{run_id}].replicate_seeds must contain "
            f"{replicates} seed(s)"
        )

    return ResolvedSimulatorRun(
        request_id=request_id,
        profile=profile,
        run_id=run_id,
        simulator_id=simulator_id,
        organism=organism,
        requested_extras=requested_extras,
        effective_extras=effective_extras,
        inputs=inputs,
        input_files=input_files,
        resolved_input_files=resolved_input_files,
        simulator_params=resolved_params,
        native_outputs=native_outputs,
        replicates=replicates,
        base_seed=int(simulator_seed_base),
        replicate_seeds=[int(seed) for seed in replicate_seeds],
        notes=run_payload.get("notes") or notes,
        simulator_spec=simulator_spec,
    )


def validate_simulation_plan_payload(
    plan_payload: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> ResolvedSimulationPlan:
    schemas, catalog = _load_simulator_catalog()
    _validate_json_instance(
        instance=plan_payload,
        schema=schemas["simulation_plan"],
        label="simulation-plan",
    )

    profile, organism, requested_extras, effective_extras, base_seed = (
        _validate_common_plan_fields(plan_payload, label="simulation-plan")
    )
    raw_inputs = plan_payload.get("inputs", plan_payload.get("input_files", {}))
    inputs, input_files, resolved_input_files = _resolve_input_files(
        raw_inputs,
        base_dir=base_dir or Path.cwd(),
    )

    run_payloads = plan_payload.get("runs", [])
    simulator_runs = [
        _resolve_simulator_run(
            request_id=str(plan_payload["id"]),
            profile=profile,
            run_id=str(run_payload["run_id"]),
            organism=organism,
            requested_extras=requested_extras,
            effective_extras=effective_extras,
            inputs=inputs,
            input_files=input_files,
            resolved_input_files=resolved_input_files,
            run_payload=run_payload,
            notes=plan_payload.get("notes"),
            catalog=catalog,
        )
        for run_payload in run_payloads
    ]

    seen_runs: set[str] = set()
    duplicate_runs: set[str] = set()
    for run in simulator_runs:
        if run.run_id in seen_runs:
            duplicate_runs.add(run.run_id)
        seen_runs.add(run.run_id)
    if duplicate_runs:
        raise ValueError(
            "simulation-plan.runs must not contain duplicate run_id values: "
            + ", ".join(sorted(duplicate_runs))
        )

    tasks = list(plan_payload.get("tasks", []))
    task_run_ids = {str(task.get("run_id")) for task in tasks if isinstance(task, dict)}
    unknown_task_runs = sorted(task_run_ids.difference(seen_runs))
    if unknown_task_runs:
        raise ValueError(
            "simulation-plan.tasks reference unknown run_id values: "
            + ", ".join(unknown_task_runs)
        )
    expected_task_count = sum(run.replicates for run in simulator_runs)
    if len(tasks) != expected_task_count:
        raise ValueError(
            f"simulation-plan.tasks must contain {expected_task_count} tasks "
            f"(sum of per-run replicates across {len(simulator_runs)} runs)"
        )
    task_ids = [str(task.get("task_id")) for task in tasks if isinstance(task, dict)]
    duplicate_tasks = sorted(
        {task_id for task_id in task_ids if task_ids.count(task_id) > 1}
    )
    if duplicate_tasks:
        raise ValueError(
            "simulation-plan.tasks must not contain duplicate task_id values: "
            + ", ".join(duplicate_tasks)
        )

    runs_by_id = {run.run_id: run for run in simulator_runs}
    seen_replicates_by_run: dict[str, set[int]] = {
        run.run_id: set() for run in simulator_runs
    }
    for task in tasks:
        run_id = str(task.get("run_id"))
        run = runs_by_id[run_id]
        replicate_index = int(task.get("replicate_index", 0))
        if replicate_index < 1 or replicate_index > run.replicates:
            raise ValueError(
                f"simulation-plan.tasks[{task.get('task_id')}].replicate_index "
                f"must be between 1 and {run.replicates}"
            )
        expected_seed = run.replicate_seeds[replicate_index - 1]
        if int(task.get("seed", 0)) != expected_seed:
            raise ValueError(
                f"simulation-plan.tasks[{task.get('task_id')}].seed must match "
                f"runs[{run_id}].replicate_seeds[{replicate_index - 1}]"
            )
        seen_replicates_by_run[run_id].add(replicate_index)
    missing_replicates = {
        run_id: sorted(set(range(1, run.replicates + 1)).difference(indices))
        for run_id, indices in seen_replicates_by_run.items()
        for run in [runs_by_id[run_id]]
        if len(indices) != run.replicates
    }
    if missing_replicates:
        details = "; ".join(
            f"{run_id}: {indices}"
            for run_id, indices in sorted(missing_replicates.items())
        )
        raise ValueError(f"simulation-plan.tasks missing replicate indexes: {details}")

    execution = dict(plan_payload.get("execution", {}))

    return ResolvedSimulationPlan(
        request_id=str(plan_payload["id"]),
        profile=profile,
        organism=organism,
        requested_extras=requested_extras,
        effective_extras=effective_extras,
        inputs=inputs,
        input_files=input_files,
        resolved_input_files=resolved_input_files,
        base_seed=base_seed,
        notes=plan_payload.get("notes"),
        simulator_runs=simulator_runs,
        tasks=tasks,
        execution=execution,
        plan_payload=plan_payload,
    )


def validate_simulation_plan(plan_path: Path) -> ResolvedSimulationPlan:
    plan_payload = _load_json_object(plan_path, "simulation-plan")
    return validate_simulation_plan_payload(
        plan_payload,
        base_dir=plan_path.resolve().parent,
    )
