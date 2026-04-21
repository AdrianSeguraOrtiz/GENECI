"""Request parsing and validation for generate-v2."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from geneci.core.commands.infer_network_v2.commons.shared import ParamValidationError
from geneci.core.commands.infer_network_v2.commons.tools import _validate_param_value

from .catalog import _load_simulator_catalog, get_profile_capability
from .shared import (
    MAX_SEED_32BIT,
    KNOWN_EXTRAS,
    PROFILE_SPECS,
    ResolvedBenchmarkRequest,
    _load_json_object,
    _stable_seed_base,
    _validate_json_instance,
)


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
        raise ValueError(f"[{simulator_id}] invalid simulator_params: {'; '.join(errors)}")
    return resolved


def _resolve_input_files(
    raw_input_files: Any,
    *,
    base_dir: Path,
) -> tuple[dict[str, str], dict[str, Path]]:
    if raw_input_files is None:
        return {}, {}
    if not isinstance(raw_input_files, dict):
        raise ValueError("input_files must be an object mapping input id to path")

    input_files: dict[str, str] = {}
    resolved: dict[str, Path] = {}
    for input_id, raw_path in raw_input_files.items():
        if not isinstance(input_id, str) or not input_id:
            raise ValueError("input_files keys must be non-empty strings")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"input_files.{input_id} must be a non-empty path string")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        else:
            path = path.resolve()
        if not path.exists():
            raise ValueError(f"input_files.{input_id} path does not exist: {path}")
        input_files[input_id] = raw_path
        resolved[input_id] = path
    return input_files, resolved


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
        if _conditional_input_matches(
            requirement,
            profile=profile,
            requested_extras=requested_extra_set,
            simulator_params=simulator_params,
        ) and input_id not in input_files:
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
            raise ValueError("organism.tax_id must be integer >= 1 when organism.kind=biological")
    elif kind in {"synthetic", "unknown"}:
        if tax_id is not None and (not isinstance(tax_id, int) or tax_id < 1):
            raise ValueError(
                "organism.tax_id must be null or integer >= 1 when organism.kind is synthetic/unknown"
            )
    else:
        raise ValueError("organism.kind must be one of: biological, synthetic, unknown")


def validate_benchmark_request_payload(
    request_payload: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> ResolvedBenchmarkRequest:
    schemas, catalog = _load_simulator_catalog()
    _validate_json_instance(
        instance=request_payload,
        schema=schemas["benchmark_request"],
        label="benchmark-request",
    )

    simulator_id = str(request_payload.get("simulator_id", "")).strip()
    if simulator_id not in catalog:
        raise ValueError(f"Unknown simulator_id in request: {simulator_id}")
    simulator_spec = catalog[simulator_id]

    profile = str(request_payload.get("profile", "")).strip()
    if profile not in PROFILE_SPECS:
        raise ValueError(f"Unknown benchmark profile: {profile}")
    profile_capability = get_profile_capability(simulator_spec, profile)
    if profile_capability is None:
        raise ValueError(
            f"Simulator '{simulator_id}' does not support profile '{profile}'"
        )

    requested_extras = list(request_payload.get("requested_extras", []))
    if any(extra not in KNOWN_EXTRAS for extra in requested_extras):
        unsupported = sorted(set(requested_extras).difference(KNOWN_EXTRAS))
        raise ValueError(f"Unknown requested_extras: {unsupported}")

    native = set(profile_capability.get("native_extras", []))
    derivable = set(profile_capability.get("derivable_extras", []))
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

    organism = request_payload.get("organism")
    if not isinstance(organism, dict):
        raise ValueError("benchmark-request.organism must be an object")
    _validate_organism(organism)

    replicates = int(request_payload.get("replicates", 0))
    if replicates < 1:
        raise ValueError("benchmark-request.replicates must be >= 1")

    raw_simulator_params = request_payload.get("simulator_params", {})
    if not isinstance(raw_simulator_params, dict):
        raise ValueError("benchmark-request.simulator_params must be an object")
    resolved_params = _resolve_simulator_params(
        simulator_id=simulator_id,
        user_params=raw_simulator_params,
        spec_params=simulator_spec.get("params", {}),
    )

    input_files, resolved_input_files = _resolve_input_files(
        request_payload.get("input_files", {}),
        base_dir=base_dir or Path.cwd(),
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
        raise ValueError(f"[{simulator_id}] invalid input_files: {'; '.join(input_errors)}")

    base_seed = request_payload.get("base_seed")
    if base_seed is not None and (not isinstance(base_seed, int)):
        raise ValueError("benchmark-request.base_seed must be integer when provided")
    if base_seed is None:
        base_seed = _stable_seed_base(
            request_id=str(request_payload["id"]),
            profile=profile,
            simulator_id=simulator_id,
        )
    if int(base_seed) < 1:
        raise ValueError("benchmark-request.base_seed must be >= 1")

    effective_extras = sorted(set(requested_extras).union(profile_required))
    replicate_seeds = [
        ((int(base_seed) - 1 + idx) % MAX_SEED_32BIT) + 1
        for idx in range(replicates)
    ]

    return ResolvedBenchmarkRequest(
        request_id=str(request_payload["id"]),
        profile=profile,
        simulator_id=simulator_id,
        replicates=replicates,
        organism=organism,
        requested_extras=requested_extras,
        effective_extras=effective_extras,
        input_files=input_files,
        resolved_input_files=resolved_input_files,
        simulator_params=resolved_params,
        base_seed=int(base_seed),
        replicate_seeds=replicate_seeds,
        notes=request_payload.get("notes"),
        simulator_spec=simulator_spec,
        request_payload=request_payload,
    )


def validate_benchmark_request(request_path: Path) -> ResolvedBenchmarkRequest:
    request_payload = _load_json_object(request_path, "benchmark-request")
    return validate_benchmark_request_payload(
        request_payload,
        base_dir=request_path.resolve().parent,
    )
