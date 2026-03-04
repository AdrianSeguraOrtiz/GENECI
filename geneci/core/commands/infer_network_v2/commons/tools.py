"""Tool request parsing, compatibility checks, and parameter resolution."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .shared import (
    DatasetContext,
    ParamValidationError,
    SchemaConstraints,
    _load_json_object,
)


def _load_tools_params(tools_params_path: Path) -> dict[str, dict[str, Any]]:
    raw = _load_json_object(tools_params_path, "tools-params")
    if not raw:
        raise ValueError("tools-params JSON must include at least one tool request")

    parsed: dict[str, dict[str, Any]] = {}
    # Required format:
    # {"runs": [{"run_id": "...", "tool_id": "...", "params": {...}}, ...]}
    runs = raw.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError(
            "tools-params must be an object with non-empty array field: runs"
        )
    extra_keys = sorted(k for k in raw.keys() if k != "runs")
    if extra_keys:
        raise ValueError(
            "tools-params with 'runs' format must not include extra top-level keys: "
            f"{extra_keys}"
        )

    for idx, item in enumerate(runs, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"tools-params.runs[{idx}] must be an object")

        tool_id_raw = item.get("tool_id")
        if not isinstance(tool_id_raw, str) or not tool_id_raw.strip():
            raise ValueError(
                f"tools-params.runs[{idx}].tool_id must be a non-empty string"
            )
        tool_id = tool_id_raw.strip()

        params = item.get("params", {})
        if not isinstance(params, dict):
            raise ValueError(f"tools-params.runs[{idx}].params must be an object")

        run_id_raw = item.get("run_id")
        if run_id_raw is None or (
            isinstance(run_id_raw, str) and not run_id_raw.strip()
        ):
            run_id = f"{tool_id}__{idx:02d}"
        elif isinstance(run_id_raw, str):
            run_id = run_id_raw.strip()
        else:
            raise ValueError(
                f"tools-params.runs[{idx}].run_id must be string when provided"
            )

        if run_id in parsed:
            raise ValueError(f"Duplicate run_id in tools-params: {run_id}")
        parsed[run_id] = {"tool_id": tool_id, "params": params}
    return parsed


def _load_toolspec(tools_root: Path, tool_id: str) -> dict[str, Any]:
    toolspec_path = tools_root / tool_id / "toolspec.json"
    if not toolspec_path.exists():
        raise ValueError(
            f"Tool '{tool_id}' requested in tools-params but toolspec not found: {toolspec_path}"
        )
    return _load_json_object(toolspec_path, f"toolspec[{tool_id}]")


def _check_tool_compatibility(
    *,
    tool_id: str,
    toolspec: dict[str, Any],
    dataset: DatasetContext,
    constraints: SchemaConstraints,
    strict: bool,
    warnings: list[str],
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    accepts = toolspec.get("accepts")
    if not isinstance(accepts, list) or not all(isinstance(x, str) for x in accepts):
        errors.append("invalid toolspec.accepts")
    elif dataset.column_kind not in set(accepts):
        errors.append(
            f"dataset column_kind '{dataset.column_kind}' is not accepted by tool ({accepts})"
        )

    assumes = str(toolspec.get("assumes", "")).strip()
    if assumes not in constraints.assumptions:
        errors.append("invalid toolspec.assumes")
    else:
        if assumes == "scrna_specific" and dataset.expression_profile not in {
            "scrna",
            "mixed",
        }:
            errors.append(
                f"tool assumes scrna_specific but dataset expression_profile is '{dataset.expression_profile}'"
            )
        if assumes == "bulk_specific" and dataset.expression_profile not in {
            "bulk",
            "mixed",
        }:
            errors.append(
                f"tool assumes bulk_specific but dataset expression_profile is '{dataset.expression_profile}'"
            )

    extra_inputs = toolspec.get("extra_inputs", {})
    required_extras = []
    optional_extras = []
    if isinstance(extra_inputs, dict):
        req = extra_inputs.get("required", [])
        opt = extra_inputs.get("optional", [])
        if isinstance(req, list):
            required_extras = [x for x in req if isinstance(x, str)]
        if isinstance(opt, list):
            optional_extras = [x for x in opt if isinstance(x, str)]
    else:
        errors.append("invalid toolspec.extra_inputs")

    for extra_key in required_extras:
        if dataset.extras.get(extra_key) is None:
            errors.append(f"required extra input missing in manifest: {extra_key}")

    for extra_key in optional_extras:
        if dataset.extras.get(extra_key) is None:
            warnings.append(f"[{tool_id}] optional extra not provided: {extra_key}")

    if errors:
        message = "; ".join(errors)
        if strict:
            raise ValueError(f"[{tool_id}] incompatible with dataset: {message}")
        warnings.append(f"[{tool_id}] skipped due to incompatibility: {message}")
        return False, errors

    return True, []


def _validate_numeric_range(
    value: float,
    param_def: dict[str, Any],
    path: str,
) -> None:
    min_value = param_def.get("min")
    max_value = param_def.get("max")
    if isinstance(min_value, (int, float)) and value < float(min_value):
        raise ParamValidationError(f"{path} must be >= {min_value}")
    if isinstance(max_value, (int, float)) and value > float(max_value):
        raise ParamValidationError(f"{path} must be <= {max_value}")


def _validate_param_value(
    *,
    value: Any,
    param_def: dict[str, Any],
    path: str,
    warnings: list[str],
) -> Any:
    param_type = param_def.get("type")

    if param_type == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ParamValidationError(f"{path} must be int")
        _validate_numeric_range(float(value), param_def, path)
        return int(value)

    if param_type == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ParamValidationError(f"{path} must be float")
        out = float(value)
        _validate_numeric_range(out, param_def, path)
        return out

    if param_type == "bool":
        if not isinstance(value, bool):
            raise ParamValidationError(f"{path} must be bool")
        return value

    if param_type == "string":
        if not isinstance(value, str):
            raise ParamValidationError(f"{path} must be string")
        return value

    if param_type == "enum":
        if not isinstance(value, str):
            raise ParamValidationError(f"{path} must be enum string")
        choices = param_def.get("enum", [])
        if value not in choices:
            raise ParamValidationError(f"{path} must be one of {choices}")
        return value

    if param_type == "object":
        if not isinstance(value, dict):
            raise ParamValidationError(f"{path} must be object")
        properties = param_def.get("properties", {})
        if not isinstance(properties, dict):
            return value

        unknown = sorted(set(value.keys()).difference(properties.keys()))
        for key in unknown:
            warnings.append(
                f"{path}.{key} is not defined in toolspec and will be ignored"
            )

        resolved: dict[str, Any] = {}
        for key, sub_def in properties.items():
            if not isinstance(sub_def, dict):
                continue
            sub_path = f"{path}.{key}"
            if key in value:
                raw_sub = value[key]
            else:
                raw_sub = copy.deepcopy(sub_def.get("default"))

            if raw_sub is None:
                if bool(sub_def.get("required")) and sub_def.get("default") is None:
                    raise ParamValidationError(
                        f"missing required parameter: {sub_path}"
                    )
                resolved[key] = None
                continue

            resolved[key] = _validate_param_value(
                value=raw_sub,
                param_def=sub_def,
                path=sub_path,
                warnings=warnings,
            )
        return resolved

    if param_type == "array":
        if not isinstance(value, list):
            raise ParamValidationError(f"{path} must be array")
        item_def = param_def.get("items")
        if not isinstance(item_def, dict):
            return value
        out = []
        for idx, item in enumerate(value):
            out.append(
                _validate_param_value(
                    value=item,
                    param_def=item_def,
                    path=f"{path}[{idx}]",
                    warnings=warnings,
                )
            )
        return out

    if param_type == "union":
        options = param_def.get("oneOf", [])
        if not isinstance(options, list) or not options:
            raise ParamValidationError(f"{path} has invalid union definition")
        errors: list[str] = []
        for option in options:
            if not isinstance(option, dict):
                continue
            try:
                return _validate_param_value(
                    value=value,
                    param_def=option,
                    path=path,
                    warnings=warnings,
                )
            except ParamValidationError as exc:
                errors.append(str(exc))
        raise ParamValidationError(f"{path} does not match union options: {errors}")

    raise ParamValidationError(
        f"{path} has unsupported param type in toolspec: {param_type!r}"
    )


def _resolve_tool_params(
    *,
    tool_id: str,
    user_params: dict[str, Any],
    toolspec_params: dict[str, Any],
    strict: bool,
    warnings: list[str],
) -> tuple[bool, dict[str, Any], list[str]]:
    errors: list[str] = []
    unknown_keys = sorted(set(user_params.keys()).difference(toolspec_params.keys()))
    for key in unknown_keys:
        warnings.append(f"[{tool_id}] unknown parameter key ignored: {key}")

    resolved: dict[str, Any] = {}
    for param_name, param_def_any in toolspec_params.items():
        if not isinstance(param_def_any, dict):
            errors.append(f"invalid toolspec.params definition for '{param_name}'")
            continue

        if param_name in user_params:
            raw_value = user_params[param_name]
        else:
            raw_value = copy.deepcopy(param_def_any.get("default"))

        if raw_value is None:
            if (
                bool(param_def_any.get("required"))
                and param_def_any.get("default") is None
            ):
                errors.append(f"missing required parameter: {param_name}")
            resolved[param_name] = None
            continue

        try:
            resolved[param_name] = _validate_param_value(
                value=raw_value,
                param_def=param_def_any,
                path=f"{tool_id}.{param_name}",
                warnings=warnings,
            )
        except ParamValidationError as exc:
            errors.append(str(exc))

    if errors:
        if strict:
            raise ValueError(f"[{tool_id}] invalid parameter set: {'; '.join(errors)}")
        warnings.append(
            f"[{tool_id}] skipped due to invalid params: {'; '.join(errors)}"
        )
        return False, {}, errors

    return True, resolved, []


def _scan_catalog_compatibility(
    *,
    tools_root: Path,
    dataset: DatasetContext,
    constraints: SchemaConstraints,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for toolspec_path in sorted(tools_root.glob("*/toolspec.json")):
        tool_id = toolspec_path.parent.name
        try:
            toolspec = _load_json_object(toolspec_path, f"toolspec[{tool_id}]")
        except ValueError as exc:
            entries.append(
                {
                    "tool_id": tool_id,
                    "status": "blocked",
                    "reasons": [f"invalid toolspec: {exc}"],
                    "warnings": [],
                }
            )
            continue

        local_warnings: list[str] = []
        compatible, reasons = _check_tool_compatibility(
            tool_id=tool_id,
            toolspec=toolspec,
            dataset=dataset,
            constraints=constraints,
            strict=False,
            warnings=local_warnings,
        )

        status = "eligible"
        if not compatible:
            status = "blocked"
        elif local_warnings:
            status = "warning"

        entries.append(
            {
                "tool_id": tool_id,
                "status": status,
                "reasons": reasons,
                "warnings": local_warnings,
            }
        )

    eligible = [item for item in entries if item["status"] == "eligible"]
    warning = [item for item in entries if item["status"] == "warning"]
    blocked = [item for item in entries if item["status"] == "blocked"]
    return {
        "tools_total": len(entries),
        "eligible": eligible,
        "warning": warning,
        "blocked": blocked,
    }
