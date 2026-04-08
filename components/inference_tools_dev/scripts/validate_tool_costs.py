"""Validate tool cost.json files against the tool cost JSON Schema.

Usage examples:
1) Validate every cost profile:
   python validate_tool_costs.py

2) Validate only selected tools:
   python validate_tool_costs.py --tool genie3 --tool scmtni

Exit codes:
- 0: all selected cost profiles are valid
- 1: one or more cost profiles are invalid / unreadable
- 2: usage/runtime error (missing schema, unknown tool ids, etc.)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from shared.catalog_tools import (
    CATALOG_ROOT,
    DEFAULT_CATALOG_TOOLS_ROOT,
    discover_catalog_tool_dirs,
    load_json,
    load_toolspec,
    select_tools,
)

DEFAULT_SCHEMA_PATH = CATALOG_ROOT / "schemas" / "toolcost.schema.json"


@dataclass(frozen=True)
class ValidationCounters:
    valid: int = 0
    invalid: int = 0

    @property
    def checked(self) -> int:
        return self.valid + self.invalid


def to_json_pointer(error: ValidationError) -> str:
    if not error.path:
        return "(root)"
    return "/" + "/".join(str(part) for part in error.path)


def build_validator(schema: Any) -> Draft202012Validator:
    try:
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimeError(f"Invalid JSON Schema: {exc.message}") from exc
    return validator


def validate_instance(
    validator: Draft202012Validator,
    instance: Any,
) -> list[ValidationError]:
    return sorted(validator.iter_errors(instance), key=lambda err: list(err.path))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate every catalog cost.json against toolcost.schema.json."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to tool cost schema. Default: {DEFAULT_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory. Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to validate (repeatable). If omitted, validates all cost.json files.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first invalid cost profile.",
    )
    return parser.parse_args(argv)


def discover_cost_files(catalog_tools_root: Path) -> list[tuple[str, Path]]:
    return [
        (tool_id, tool_dir / "cost.json")
        for tool_id, tool_dir in discover_catalog_tool_dirs(
            catalog_tools_root, required_filename="cost.json"
        )
    ]


def _check_param_key_compatibility(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    unknown = sorted(set(payload.keys()).difference(schema.keys()))
    for key in unknown:
        errors.append(
            f"params_profile.resolved_params{path}/{key} does not exist in toolspec.params."
        )

    for key, value in payload.items():
        param_def = schema.get(key)
        if not isinstance(param_def, dict):
            continue
        if param_def.get("type") != "object" or not isinstance(value, dict):
            continue
        properties = param_def.get("properties", {})
        if not isinstance(properties, dict):
            continue
        _check_param_key_compatibility(
            payload=value,
            schema=properties,
            path=f"{path}/{key}",
            errors=errors,
        )


def semantic_errors_for_cost(
    *,
    tool_id: str,
    instance: Any,
    catalog_tools_root: Path,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(instance, dict):
        errors.append("Cost profile root must be a JSON object.")
        return errors

    benchmark_config = instance.get("benchmark_config")
    if not isinstance(benchmark_config, dict):
        return errors

    params_profile = benchmark_config.get("params_profile")
    if not isinstance(params_profile, dict):
        return errors

    source = params_profile.get("source")
    override_file = params_profile.get("override_file")
    if source == "toolspec_defaults" and override_file is not None:
        errors.append(
            "benchmark_config.params_profile.override_file must be null when source='toolspec_defaults'."
        )
    if source == "toolspec_defaults_plus_override" and (
        not isinstance(override_file, str) or not override_file.strip()
    ):
        errors.append(
            "benchmark_config.params_profile.override_file must be a non-empty string when source='toolspec_defaults_plus_override'."
        )

    resolved_params = params_profile.get("resolved_params")
    if not isinstance(resolved_params, dict):
        return errors

    toolspec = load_toolspec(catalog_tools_root, tool_id)
    raw_params = toolspec.get("params", {})
    params_schema = raw_params if isinstance(raw_params, dict) else {}
    _check_param_key_compatibility(
        payload=resolved_params,
        schema=params_schema,
        path="",
        errors=errors,
    )
    return errors


def run(
    schema_path: Path,
    catalog_tools_root: Path,
    tool_filters: list[str],
    fail_fast: bool,
) -> int:
    all_costs = discover_cost_files(catalog_tools_root)
    if not all_costs:
        raise RuntimeError(f"No cost.json files found under: {catalog_tools_root}")

    selected = select_tools(all_costs, tool_filters)
    schema = load_json(schema_path)
    validator = build_validator(schema)

    counters = ValidationCounters()

    for tool_id, cost_path in selected:
        print(f"[{tool_id}] validating {cost_path}")
        try:
            instance = load_json(cost_path)
            schema_errors = validate_instance(validator, instance)
            semantic_errors = semantic_errors_for_cost(
                tool_id=tool_id,
                instance=instance,
                catalog_tools_root=catalog_tools_root,
            )
        except RuntimeError as exc:
            counters = ValidationCounters(
                valid=counters.valid, invalid=counters.invalid + 1
            )
            print(f"  ERROR: {exc}")
            if fail_fast:
                break
            continue

        if not schema_errors and not semantic_errors:
            counters = ValidationCounters(
                valid=counters.valid + 1, invalid=counters.invalid
            )
            print("  VALID")
            continue

        counters = ValidationCounters(
            valid=counters.valid, invalid=counters.invalid + 1
        )
        print(
            "  INVALID: {count} issue(s)".format(
                count=len(schema_errors) + len(semantic_errors)
            )
        )
        for idx, err in enumerate(schema_errors, start=1):
            print(f"    {idx}. {to_json_pointer(err)} -> {err.message}")
        base = len(schema_errors)
        for rel_idx, message in enumerate(semantic_errors, start=1):
            print(f"    {base + rel_idx}. (semantic) {message}")
        if fail_fast:
            break

    print()
    print(
        f"Summary: checked={counters.checked} valid={counters.valid} invalid={counters.invalid}"
    )
    return 0 if counters.invalid == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(
            schema_path=args.schema,
            catalog_tools_root=args.catalog_tools_root,
            tool_filters=args.tool,
            fail_fast=args.fail_fast,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
