"""Shared helpers for dev-only parameter profiles derived from ToolSpecs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARAM_OVERRIDES_DIR = INFERENCE_TOOLS_ROOT / "param_overrides"


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{label} is malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return data


def _default_for_param(param_def: dict[str, Any]) -> Any:
    if "default" in param_def:
        return copy.deepcopy(param_def.get("default"))

    param_type = param_def.get("type")
    if param_type == "object":
        properties = param_def.get("properties", {})
        if not isinstance(properties, dict):
            return {}
        out: dict[str, Any] = {}
        for key, sub_def in properties.items():
            if not isinstance(sub_def, dict):
                continue
            has_default = "default" in sub_def
            is_required = bool(sub_def.get("required"))
            if has_default or is_required:
                out[key] = _default_for_param(sub_def)
        return out

    if param_type == "array":
        return []

    return None


def _build_default_params(params_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _default_for_param(param_def)
        for key, param_def in params_schema.items()
        if isinstance(param_def, dict)
    }


def _validate_override_keys(
    *,
    override: dict[str, Any],
    params_schema: dict[str, Any],
    label: str,
) -> None:
    unknown = sorted(set(override.keys()).difference(params_schema.keys()))
    if unknown:
        raise ValueError(f"{label} contains unknown parameter keys: {unknown}")

    for key, value in override.items():
        param_def = params_schema.get(key)
        if not isinstance(param_def, dict):
            continue
        if param_def.get("type") != "object" or not isinstance(value, dict):
            continue
        properties = param_def.get("properties", {})
        if not isinstance(properties, dict):
            continue
        _validate_override_keys(
            override=value,
            params_schema=properties,
            label=f"{label}.{key}",
        )


def _deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in override.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    return copy.deepcopy(override)


def resolve_dev_params(
    *,
    tool_id: str,
    catalog_tools_root: Path,
    param_overrides_dir: Path = DEFAULT_PARAM_OVERRIDES_DIR,
) -> tuple[dict[str, Any], dict[str, Any]]:
    toolspec_path = catalog_tools_root / tool_id / "toolspec.json"
    toolspec = _load_json_object(toolspec_path, f"toolspec[{tool_id}]")
    raw_params = toolspec.get("params", {})
    params_schema = raw_params if isinstance(raw_params, dict) else {}
    defaults = _build_default_params(params_schema)

    override_path = param_overrides_dir / f"{tool_id}.json"
    override_payload: dict[str, Any] = {}
    if override_path.exists():
        override_payload = _load_json_object(
            override_path, f"param_override[{tool_id}]"
        )
        _validate_override_keys(
            override=override_payload,
            params_schema=params_schema,
            label=override_path.name,
        )

    resolved = _deep_merge(defaults, override_payload)
    profile = {
        "source": (
            "toolspec_defaults_plus_override"
            if override_payload
            else "toolspec_defaults"
        ),
        "override_file": override_path.name if override_payload else None,
        "resolved_params": resolved,
    }
    return resolved, profile
