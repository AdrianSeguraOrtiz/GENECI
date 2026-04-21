"""Scenario-to-simulator capability evaluation for generate-v2."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from .catalog import _load_simulator_catalog, get_profile_capability
from .request import _resolve_simulator_params, validate_simulator_input_files
from .scenario import validate_scenario_request
from .shared import ResolvedScenarioRequest, _validate_json_instance


def _evaluate_runtime_requirements(_simulator_id: str) -> list[str]:
    if shutil.which("docker") is None:
        return ["missing runtime command: docker"]
    result = subprocess.run(
        ["docker", "info"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        return [f"docker daemon is not available: {details}"]
    return []


def evaluate_simulator_for_scenario(
    *,
    simulator_id: str,
    spec: dict[str, Any],
    scenario: ResolvedScenarioRequest,
) -> dict[str, Any]:
    profile_capability = get_profile_capability(spec, scenario.profile)
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if profile_capability is None:
        blocking_reasons.append(
            f"profile '{scenario.profile}' is not supported"
        )
        native = set()
        derivable = set()
        truth_outputs = {
            "global_network": "none",
            "legacy_binary_matrix": "none",
            "group_networks": "none",
        }
        supported_effective_extras: list[str] = []
    else:
        resolved_params = _resolve_simulator_params(
            simulator_id=simulator_id,
            user_params={},
            spec_params=spec.get("params", {}),
        )
        native = set(profile_capability.get("native_extras", []))
        derivable = set(profile_capability.get("derivable_extras", []))
        truth_outputs = dict(profile_capability.get("truth_outputs", {}))
        supported_effective_extras = sorted(
            set(scenario.effective_extras).intersection(native.union(derivable))
        )
        unsupported_requested = sorted(
            set(scenario.effective_extras).difference(native.union(derivable))
        )
        if unsupported_requested:
            blocking_reasons.append(
                "unsupported extras for this profile: "
                + ", ".join(unsupported_requested)
            )
        blocking_reasons.extend(
            validate_simulator_input_files(
                simulator_id=simulator_id,
                simulator_spec=spec,
                profile=scenario.profile,
                requested_extras=scenario.requested_extras,
                simulator_params=resolved_params,
                input_files=scenario.input_files,
            )
        )
        blocking_reasons.extend(_evaluate_runtime_requirements(simulator_id))

        derived_extras_used = sorted(set(supported_effective_extras).intersection(derivable))
        if derived_extras_used:
            warnings.append(
                "derived extras required: " + ", ".join(derived_extras_used)
            )

    if blocking_reasons:
        status = "blocked"
    elif warnings:
        status = "warning"
    else:
        status = "eligible"

    native_used = sorted(set(supported_effective_extras).intersection(native))
    derived_used = sorted(set(supported_effective_extras).intersection(derivable))
    return {
        "simulator_id": simulator_id,
        "name": spec["name"],
        "requested_profile": scenario.profile,
        "requested_extras": list(scenario.requested_extras),
        "effective_extras": list(scenario.effective_extras),
        "input_files_used": sorted(scenario.input_files),
        "native_extras_used": native_used,
        "derived_extras_used": derived_used,
        "truth_outputs": truth_outputs,
        "status": status,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
    }


def preflight_generate_v2_scenario(scenario_path: Path) -> dict[str, Any]:
    scenario = validate_scenario_request(scenario_path)
    schemas, catalog = _load_simulator_catalog()

    entries = [
        evaluate_simulator_for_scenario(
            simulator_id=simulator_id,
            spec=spec,
            scenario=scenario,
        )
        for simulator_id, spec in sorted(catalog.items())
    ]
    eligible = [entry for entry in entries if entry["status"] == "eligible"]
    warning = [entry for entry in entries if entry["status"] == "warning"]
    blocked = [entry for entry in entries if entry["status"] == "blocked"]

    report = {
        "schema_version": "1.0",
        "scenario": {
            "id": scenario.request_id,
            "profile": scenario.profile,
            "replicates": scenario.replicates,
            "organism": scenario.organism,
            "requested_extras": scenario.requested_extras,
            "effective_extras": scenario.effective_extras,
            "input_files": scenario.input_files,
            "base_seed": scenario.base_seed,
            "replicate_seeds": scenario.replicate_seeds,
        },
        "catalog_summary": {
            "total": len(entries),
            "eligible": len(eligible),
            "warning": len(warning),
            "blocked": len(blocked),
        },
        "eligible": eligible,
        "warning": warning,
        "blocked": blocked,
    }
    _validate_json_instance(
        instance=report,
        schema=schemas["preflight_report"],
        label=f"preflight-report[{scenario.request_id}]",
    )
    return report
