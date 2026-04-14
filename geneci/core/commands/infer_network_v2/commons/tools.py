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


def _parse_extra_inputs_spec(
    *,
    tool_id: str,
    toolspec: dict[str, Any],
    known_params: set[str] | None = None,
) -> tuple[list[str], list[str], list[dict[str, Any]], list[str]]:
    extra_inputs = toolspec.get("extra_inputs", {})
    if not isinstance(extra_inputs, dict):
        return [], [], [], ["invalid toolspec.extra_inputs"]

    errors: list[str] = []
    required_extras: list[str] = []
    optional_extras: list[str] = []
    conditional_required: list[dict[str, Any]] = []

    req = extra_inputs.get("required", [])
    opt = extra_inputs.get("optional", [])
    cond = extra_inputs.get("conditional_required", [])

    if isinstance(req, list):
        required_extras = [x for x in req if isinstance(x, str)]
    else:
        errors.append("toolspec.extra_inputs.required must be an array")

    if isinstance(opt, list):
        optional_extras = [x for x in opt if isinstance(x, str)]
    else:
        errors.append("toolspec.extra_inputs.optional must be an array")

    overlap = sorted(set(required_extras).intersection(optional_extras))
    if overlap:
        errors.append(
            f"toolspec.extra_inputs.required/optional overlap: {overlap}"
        )

    if cond is None:
        cond = []
    if not isinstance(cond, list):
        errors.append("toolspec.extra_inputs.conditional_required must be an array")
        cond = []

    for idx, raw_rule in enumerate(cond, start=1):
        if not isinstance(raw_rule, dict):
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}] must be an object"
            )
            continue

        input_key = str(raw_rule.get("input", "")).strip()
        param_name = str(raw_rule.get("param", "")).strip()
        op = str(raw_rule.get("op", "")).strip()
        message = str(raw_rule.get("message", "")).strip()
        value = raw_rule.get("value")

        if not input_key:
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}].input is required"
            )
            continue
        if not param_name:
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}].param is required"
            )
            continue
        if op not in {"eq", "ne", "gt", "gte", "lt", "lte"}:
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}].op is invalid"
            )
            continue
        if not message:
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}].message is required"
            )
            continue
        if known_params is not None and param_name not in known_params:
            errors.append(
                f"toolspec.extra_inputs.conditional_required[{idx}] references unknown parameter '{param_name}'"
            )
            continue

        conditional_required.append(
            {
                "input": input_key,
                "param": param_name,
                "op": op,
                "value": value,
                "message": message,
            }
        )

    return required_extras, optional_extras, conditional_required, errors


def _load_tools_params(tools_params_path: Path) -> dict[str, dict[str, Any]]:
    raw = _load_json_object(tools_params_path, "tools-params")
    if not raw:
        raise ValueError("tools-params JSON must include at least one tool request")

    parsed: dict[str, dict[str, Any]] = {}
    # Required format:
    # {"runs": [{"run_id": "...", "tool_id": "...", "params": {...}, "execution": {...}}, ...]}
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

        execution = item.get("execution", {})
        if execution is None:
            execution = {}
        if not isinstance(execution, dict):
            raise ValueError(
                f"tools-params.runs[{idx}].execution must be an object when provided"
            )

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
        parsed[run_id] = {
            "tool_id": tool_id,
            "params": params,
            "execution": execution,
        }
    return parsed


def _load_toolspec(tools_root: Path, tool_id: str) -> dict[str, Any]:
    toolspec_path = tools_root / tool_id / "toolspec.json"
    if not toolspec_path.exists():
        raise ValueError(
            f"Tool '{tool_id}' requested in tools-params but toolspec not found: {toolspec_path}"
        )
    return _load_json_object(toolspec_path, f"toolspec[{tool_id}]")


def _parse_execution_scope(*, tool_id: str, toolspec: dict[str, Any]) -> str:
    execution_scope = str(toolspec.get("execution_scope", "")).strip()
    if execution_scope not in {"global", "group"}:
        raise ValueError(
            f"[{tool_id}] toolspec.execution_scope must be one of: global, group"
        )
    return execution_scope


def _resolve_run_execution(
    *,
    run_id: str,
    toolspec: dict[str, Any],
    user_execution: dict[str, Any],
    strict: bool,
    warnings: list[str],
) -> tuple[bool, dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        execution_scope = _parse_execution_scope(tool_id=run_id, toolspec=toolspec)
    except ValueError as exc:
        errors.append(str(exc))
        execution_scope = "global"

    unknown_keys = sorted(set(user_execution.keys()).difference({"group_mode"}))
    for key in unknown_keys:
        warnings.append(f"[{run_id}] unknown execution key ignored: {key}")

    group_mode_raw = user_execution.get("group_mode")
    if group_mode_raw is None:
        group_mode = "per_group" if execution_scope == "group" else "global"
    elif not isinstance(group_mode_raw, str):
        errors.append("execution.group_mode must be string when provided")
        group_mode = "global"
    else:
        group_mode = group_mode_raw.strip()
        if group_mode not in {"global", "per_group"}:
            errors.append("execution.group_mode must be one of: global, per_group")

    if execution_scope == "group" and group_mode == "global":
        errors.append(
            "execution.group_mode=global is not allowed because toolspec.execution_scope=group"
        )

    if errors:
        if strict:
            raise ValueError(f"[{run_id}] invalid execution config: {'; '.join(errors)}")
        warnings.append(
            f"[{run_id}] skipped due to invalid execution config: {'; '.join(errors)}"
        )
        return False, {}, errors

    return True, {"group_mode": group_mode}, []


def _check_tool_compatibility(
    *,
    tool_id: str,
    toolspec: dict[str, Any],
    dataset: DatasetContext,
    constraints: SchemaConstraints,
    strict: bool,
    warnings: list[str],
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    pending_conditions: list[str] = []

    try:
        _parse_execution_scope(tool_id=tool_id, toolspec=toolspec)
    except ValueError as exc:
        errors.append(str(exc))

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

    toolspec_params = toolspec.get("params", {})
    known_params = set(toolspec_params.keys()) if isinstance(toolspec_params, dict) else None
    required_extras, optional_extras, conditional_required, extra_errors = (
        _parse_extra_inputs_spec(
            tool_id=tool_id,
            toolspec=toolspec,
            known_params=known_params,
        )
    )
    errors.extend(extra_errors)

    for extra_key in required_extras:
        if dataset.extras.get(extra_key) is None:
            errors.append(f"required extra input missing in manifest: {extra_key}")

    conditional_inputs = {
        str(rule.get("input", "")).strip()
        for rule in conditional_required
        if str(rule.get("input", "")).strip()
    }
    for extra_key in optional_extras:
        if extra_key in conditional_inputs:
            continue
        if dataset.extras.get(extra_key) is None:
            warnings.append(f"[{tool_id}] optional extra not provided: {extra_key}")

    for rule in conditional_required:
        input_key = str(rule.get("input", "")).strip()
        message = str(rule.get("message", "")).strip()
        if input_key and dataset.extras.get(input_key) is None and message:
            pending_conditions.append(message)

    if errors:
        message = "; ".join(errors)
        if strict:
            raise ValueError(f"[{tool_id}] incompatible with dataset: {message}")
        warnings.append(f"[{tool_id}] skipped due to incompatibility: {message}")
        return False, errors, []

    return True, [], pending_conditions


def _validate_numeric_range(
    value: float,
    param_def: dict[str, Any],
    path: str,
) -> None:
    min_value = param_def.get("min")
    max_value = param_def.get("max")
    if isinstance(min_value, (int, float)):
        min_bound = float(min_value)
        if bool(param_def.get("exclusive_min")):
            if value <= min_bound:
                raise ParamValidationError(f"{path} must be > {min_value}")
        elif value < min_bound:
            raise ParamValidationError(f"{path} must be >= {min_value}")
    if isinstance(max_value, (int, float)):
        max_bound = float(max_value)
        if bool(param_def.get("exclusive_max")):
            if value >= max_bound:
                raise ParamValidationError(f"{path} must be < {max_value}")
        elif value > max_bound:
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


def _conditional_rule_matches(
    *,
    resolved_params: dict[str, Any],
    rule: dict[str, Any],
) -> bool:
    param_name = str(rule.get("param", "")).strip()
    op = str(rule.get("op", "")).strip()
    expected = rule.get("value")

    if param_name not in resolved_params:
        return False
    actual = resolved_params.get(param_name)

    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected

    if (
        isinstance(actual, bool)
        or isinstance(expected, bool)
        or not isinstance(actual, (int, float))
        or not isinstance(expected, (int, float))
    ):
        return False

    actual_num = float(actual)
    expected_num = float(expected)
    if op == "gt":
        return actual_num > expected_num
    if op == "gte":
        return actual_num >= expected_num
    if op == "lt":
        return actual_num < expected_num
    if op == "lte":
        return actual_num <= expected_num
    return False


def _collect_requirement_issues(
    *,
    tool_id: str,
    toolspec: dict[str, Any],
    dataset: DatasetContext,
    resolved_params: dict[str, Any],
    resolved_execution: dict[str, Any],
) -> list[str]:
    toolspec_params = toolspec.get("params", {})
    known_params = (
        set(toolspec_params.keys()) if isinstance(toolspec_params, dict) else None
    )
    _required, _optional, conditional_required, extra_errors = _parse_extra_inputs_spec(
        tool_id=tool_id,
        toolspec=toolspec,
        known_params=known_params,
    )
    if extra_errors:
        return [f"invalid toolspec extra-input rules: {msg}" for msg in extra_errors]

    issues: list[str] = []
    group_mode = str(resolved_execution.get("group_mode", "")).strip()
    if group_mode == "per_group" and dataset.extras.get("groups") is None:
        issues.append("groups is required when execution.group_mode=per_group.")
    for rule in conditional_required:
        input_key = str(rule.get("input", "")).strip()
        message = str(rule.get("message", "")).strip()
        if dataset.extras.get(input_key) is not None:
            continue
        if _conditional_rule_matches(resolved_params=resolved_params, rule=rule):
            issues.append(message)
    return issues


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
        compatible, reasons, pending_conditions = _check_tool_compatibility(
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
        elif local_warnings or pending_conditions:
            status = "warning"

        entries.append(
            {
                "tool_id": tool_id,
                "status": status,
                "reasons": reasons,
                "warnings": local_warnings,
                "pending_conditions": pending_conditions,
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
