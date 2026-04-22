"""Validate simulator smoketest config JSON files.

Usage examples:
1) Validate every simulator smoketest config:
   python validate_smoketest_configs.py

2) Validate only selected simulators:
   python validate_smoketest_configs.py --simulator dyngen
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from shared.catalog_simulators import (
    DEFAULT_CATALOG_SIMULATORS_ROOT,
    DEFAULT_SMOKETEST_CONFIGS_ROOT,
    DEFAULT_SMOKETEST_SCHEMA_PATH,
    discover_catalog_simulator_dirs,
    load_json,
    load_simulatorspec,
    select_simulators,
)


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


def declared_input_ids(spec: dict[str, Any]) -> set[str]:
    simulator_inputs = spec.get("simulator_inputs", {})
    declared: set[str] = set()
    for key in ("required", "optional"):
        for item in simulator_inputs.get(key, []):
            if isinstance(item, dict) and item.get("id"):
                declared.add(str(item["id"]))
    for item in simulator_inputs.get("conditional_required", []):
        if isinstance(item, dict) and item.get("input"):
            declared.add(str(item["input"]))
    return declared


def semantic_errors(
    *,
    config_path: Path,
    config: dict[str, Any],
    catalog_simulators_root: Path,
    known_simulator_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    simulator_id = str(config.get("simulator_id", ""))
    if simulator_id not in known_simulator_ids:
        return [f"unknown simulator_id '{simulator_id}'"]

    spec = load_simulatorspec(catalog_simulators_root, simulator_id)
    request = config.get("request", {})
    profile = str(request.get("profile", ""))
    capabilities = spec.get("profile_capabilities", {})
    capability = capabilities.get(profile)
    if not isinstance(capability, dict):
        errors.append(f"request.profile '{profile}' is not supported by {simulator_id}")
    else:
        supported_extras = set(capability.get("native_extras", [])).union(
            capability.get("derivable_extras", [])
        )
        extras = set(request.get("effective_extras", []))
        unsupported = sorted(extras.difference(supported_extras))
        if unsupported:
            errors.append(
                f"request.effective_extras not supported for profile '{profile}': {unsupported}"
            )

    unknown_inputs = sorted(
        set(request.get("input_files", {})).difference(declared_input_ids(spec))
    )
    if unknown_inputs:
        errors.append(f"request.input_files contains unknown ids: {unknown_inputs}")

    if not config_path.name.startswith(f"{simulator_id}_") and config_path.name != (
        f"{simulator_id}.json"
    ):
        errors.append(
            f"filename should start with '{simulator_id}_' or be '{simulator_id}.json'"
        )
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate simulator smoketest configs against schema and catalog semantics."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SMOKETEST_SCHEMA_PATH,
        help=f"Path to smoketest config schema. Default: {DEFAULT_SMOKETEST_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--configs-root",
        type=Path,
        default=DEFAULT_SMOKETEST_CONFIGS_ROOT,
        help=f"Path to smoketest config directory. Default: {DEFAULT_SMOKETEST_CONFIGS_ROOT}",
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        help="Simulator id to validate (repeatable). If omitted, validates every config.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first invalid config.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validator = build_validator(load_json(args.schema))
        discovered = discover_catalog_simulator_dirs(args.catalog_simulators_root)
        selected = select_simulators(discovered, args.simulator)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    selected_ids = {simulator_id for simulator_id, _path in selected}
    known_ids = {simulator_id for simulator_id, _path in discovered}
    seen_ids: set[str] = set()
    counters = ValidationCounters()

    config_paths = sorted(args.configs_root.glob("*.json"))
    if not config_paths:
        print(
            f"ERROR: no smoketest configs found in {args.configs_root}", file=sys.stderr
        )
        return 2

    for config_path in config_paths:
        try:
            config = load_json(config_path)
            simulator_id = str(config.get("simulator_id", ""))
            if args.simulator and simulator_id not in selected_ids:
                continue
            schema_errors = [
                f"{to_json_pointer(err)} -> {err.message}"
                for err in sorted(
                    validator.iter_errors(config), key=lambda err: list(err.path)
                )
            ]
            if simulator_id in selected_ids:
                seen_ids.add(simulator_id)
            semantic = (
                []
                if schema_errors
                else semantic_errors(
                    config_path=config_path,
                    config=config,
                    catalog_simulators_root=args.catalog_simulators_root,
                    known_simulator_ids=known_ids,
                )
            )
            errors = schema_errors + semantic
        except RuntimeError as exc:
            simulator_id = "(unknown)"
            errors = [str(exc)]

        if errors:
            counters = ValidationCounters(counters.valid, counters.invalid + 1)
            print(f"[INVALID] {config_path.name}", file=sys.stderr)
            for message in errors:
                print(f"  - {message}", file=sys.stderr)
            if args.fail_fast:
                break
        else:
            counters = ValidationCounters(counters.valid + 1, counters.invalid)
            print(f"[valid] {config_path.name}")

    missing = sorted(selected_ids.difference(seen_ids))
    for simulator_id in missing:
        counters = ValidationCounters(counters.valid, counters.invalid + 1)
        print(
            f"[INVALID] {simulator_id}: missing smoketest config",
            file=sys.stderr,
        )

    print(
        f"Checked {counters.checked} smoketest config(s): "
        f"{counters.valid} valid, {counters.invalid} invalid"
    )
    return 1 if counters.invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
