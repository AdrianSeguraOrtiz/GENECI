"""Catalog loading and schema validation for generate-v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .shared import CATALOG_ROOT, _load_json_object, _validate_json_instance


def get_profile_capability(spec: dict[str, Any], profile: str) -> dict[str, Any] | None:
    profile_capabilities = spec.get("profile_capabilities", {})
    if not isinstance(profile_capabilities, dict):
        return None
    capability = profile_capabilities.get(profile)
    if not isinstance(capability, dict):
        return None
    return capability


def _resolve_catalog_paths() -> tuple[Path, Path]:
    catalog_root = CATALOG_ROOT.resolve()
    schemas_dir = (catalog_root / "schemas").resolve()
    simulators_dir = (catalog_root / "simulators").resolve()

    if not catalog_root.exists() or not catalog_root.is_dir():
        raise ValueError(f"Generation catalog root not found: {catalog_root}")
    if not schemas_dir.exists() or not schemas_dir.is_dir():
        raise ValueError(f"Generation schemas directory not found: {schemas_dir}")
    if not simulators_dir.exists() or not simulators_dir.is_dir():
        raise ValueError(f"Generation simulators directory not found: {simulators_dir}")
    if not any(simulators_dir.glob("*/simulatorspec.json")):
        raise ValueError(f"Generation catalog has no simulator specs: {simulators_dir}")
    return schemas_dir, simulators_dir


def _load_schema(schemas_dir: Path, filename: str) -> dict[str, Any]:
    return _load_json_object(schemas_dir / filename, filename)


def _load_all_schemas(schemas_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        "simulatorspec": _load_schema(schemas_dir, "simulatorspec.schema.json"),
        "scenario_request": _load_schema(schemas_dir, "scenario-request.schema.json"),
        "simulator_runs": _load_schema(schemas_dir, "simulator-runs.schema.json"),
        "simulation_plan": _load_schema(schemas_dir, "simulation-plan.schema.json"),
        "simulator_output_manifest": _load_schema(
            schemas_dir, "simulator-output-manifest.schema.json"
        ),
        "ground_truth_manifest": _load_schema(
            schemas_dir, "ground-truth-manifest.schema.json"
        ),
        "benchmark_manifest": _load_schema(
            schemas_dir, "benchmark-manifest.schema.json"
        ),
        "preflight_report": _load_schema(schemas_dir, "preflight-report.schema.json"),
    }


def _load_simulator_spec(
    *,
    simulators_dir: Path,
    simulator_id: str,
    simulator_spec_schema: dict[str, Any],
) -> dict[str, Any]:
    spec_path = simulators_dir / simulator_id / "simulatorspec.json"
    if not spec_path.exists():
        raise ValueError(
            f"Simulator '{simulator_id}' not found in catalog: {spec_path}"
        )
    spec = _load_json_object(spec_path, f"simulatorspec[{simulator_id}]")
    _validate_json_instance(
        instance=spec,
        schema=simulator_spec_schema,
        label=f"simulatorspec[{simulator_id}]",
    )
    return spec


def _load_simulator_catalog() -> (
    tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]
):
    schemas_dir, simulators_dir = _resolve_catalog_paths()
    schemas = _load_all_schemas(schemas_dir)
    simulator_spec_schema = schemas["simulatorspec"]

    catalog: dict[str, dict[str, Any]] = {}
    for spec_path in sorted(simulators_dir.glob("*/simulatorspec.json")):
        simulator_id = spec_path.parent.name
        catalog[simulator_id] = _load_simulator_spec(
            simulators_dir=simulators_dir,
            simulator_id=simulator_id,
            simulator_spec_schema=simulator_spec_schema,
        )
    return schemas, catalog
