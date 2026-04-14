"""Phase A: Input preflight for infer-network-v2.

Phase dependencies:
1. Catalog + schema constraints resolution.
2. Dataset manifest parsing + declarative input validation.
3. Tool request compatibility + parameter validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .commons.artifacts import _serialize_dataset_context
from .commons.catalog import _load_schema_constraints, _resolve_catalog_paths
from .commons.dataset import (
    _load_input_specs,
    _parse_dataset_context,
    _validate_dataset_inputs_by_specs,
)
from .commons.shared import INPUT_SPECS_DIR, PREFLIGHT_SCHEMA_VERSION
from .commons.tools import (
    _check_tool_compatibility,
    _collect_requirement_issues,
    _load_tools_params,
    _load_toolspec,
    _resolve_run_execution,
    _resolve_tool_params,
    _scan_catalog_compatibility,
)


def preflight_infer_network_new(
    *,
    dataset_manifest_path: Path,
    tools_params_path: Optional[Path] = None,
    strict: bool = False,
) -> dict[str, Any]:
    tools_root, schemas_dir = _resolve_catalog_paths()
    constraints = _load_schema_constraints(schemas_dir)
    dataset = _parse_dataset_context(
        dataset_manifest_path=dataset_manifest_path,
        constraints=constraints,
    )
    input_specs = _load_input_specs()
    input_validation, validation_errors, validation_warnings = (
        _validate_dataset_inputs_by_specs(
            dataset=dataset,
            input_specs=input_specs,
        )
    )
    if validation_errors:
        raise ValueError("Input validation failed: " + "; ".join(validation_errors))

    warnings: list[str] = list(validation_warnings)
    catalog = _scan_catalog_compatibility(
        tools_root=tools_root,
        dataset=dataset,
        constraints=constraints,
    )

    selected_tools: list[str] = []
    selected_tool_catalog_ids: dict[str, str] = {}
    skipped_tools: dict[str, str] = {}
    resolved_params_by_tool: dict[str, dict[str, Any]] = {}
    resolved_execution_by_tool: dict[str, dict[str, Any]] = {}
    requirement_issues: dict[str, list[str]] = {}
    requested_total = 0

    if tools_params_path is not None:
        tools_params = _load_tools_params(tools_params_path)
        requested_total = len(tools_params)
        for run_id, run_spec in tools_params.items():
            catalog_tool_id = str(run_spec.get("tool_id", "")).strip()
            user_params = run_spec.get("params", {})
            user_execution = run_spec.get("execution", {})
            if not catalog_tool_id:
                if strict:
                    raise ValueError(
                        f"[{run_id}] invalid tool request: missing tool_id"
                    )
                warnings.append(
                    f"[{run_id}] skipped: invalid tool request (missing tool_id)"
                )
                skipped_tools[run_id] = "invalid tool request: missing tool_id"
                continue
            if not isinstance(user_params, dict):
                if strict:
                    raise ValueError(
                        f"[{run_id}] invalid tool request: params must be object"
                    )
                warnings.append(
                    f"[{run_id}] skipped: invalid tool request (params must be object)"
                )
                skipped_tools[run_id] = "invalid tool request: params must be object"
                continue
            if not isinstance(user_execution, dict):
                if strict:
                    raise ValueError(
                        f"[{run_id}] invalid tool request: execution must be object"
                    )
                warnings.append(
                    f"[{run_id}] skipped: invalid tool request (execution must be object)"
                )
                skipped_tools[run_id] = "invalid tool request: execution must be object"
                continue

            toolspec = _load_toolspec(tools_root, catalog_tool_id)
            compatible, compat_errors, _pending_conditions = _check_tool_compatibility(
                tool_id=run_id,
                toolspec=toolspec,
                dataset=dataset,
                constraints=constraints,
                strict=strict,
                warnings=warnings,
            )
            if not compatible:
                skipped_tools[run_id] = "; ".join(compat_errors)
                continue

            toolspec_params = toolspec.get("params", {})
            if not isinstance(toolspec_params, dict):
                if strict:
                    raise ValueError(f"[{run_id}] toolspec.params must be an object")
                warnings.append(f"[{run_id}] skipped: toolspec.params is not an object")
                skipped_tools[run_id] = "invalid toolspec.params"
                continue

            valid_params, resolved_params, param_errors = _resolve_tool_params(
                tool_id=run_id,
                user_params=user_params,
                toolspec_params=toolspec_params,
                strict=strict,
                warnings=warnings,
            )
            if not valid_params:
                skipped_tools[run_id] = "; ".join(param_errors)
                continue

            valid_execution, resolved_execution, execution_errors = _resolve_run_execution(
                run_id=run_id,
                toolspec=toolspec,
                user_execution=user_execution,
                strict=strict,
                warnings=warnings,
            )
            if not valid_execution:
                skipped_tools[run_id] = "; ".join(execution_errors)
                continue

            selected_tools.append(run_id)
            selected_tool_catalog_ids[run_id] = catalog_tool_id
            resolved_params_by_tool[run_id] = resolved_params
            resolved_execution_by_tool[run_id] = resolved_execution
            issues = _collect_requirement_issues(
                tool_id=run_id,
                toolspec=toolspec,
                dataset=dataset,
                resolved_params=resolved_params,
                resolved_execution=resolved_execution,
            )
            if issues:
                requirement_issues[run_id] = issues

    return {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "inputs": {
            "dataset_manifest_path": str(dataset_manifest_path.resolve()),
            "tools_params_path": (
                str(tools_params_path.resolve()) if tools_params_path else None
            ),
            "tools_root": str(tools_root.resolve()),
            "schemas_dir": str(schemas_dir.resolve()),
            "input_specs_dir": str(INPUT_SPECS_DIR.resolve()),
        },
        "dataset": _serialize_dataset_context(dataset),
        "input_validation": input_validation,
        "catalog": catalog,
        "runs": {
            "requested_total": requested_total,
            "selected": selected_tools,
            "catalog_tool_ids": selected_tool_catalog_ids,
            "resolved_params": resolved_params_by_tool,
            "resolved_execution": resolved_execution_by_tool,
            "requirement_issues": requirement_issues,
            "skipped": skipped_tools,
        },
        "warnings": warnings,
    }
