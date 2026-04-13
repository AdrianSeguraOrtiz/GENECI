"""Validate smoketest config JSON files against schema and local fixture semantics.

Usage examples:
1) Validate every smoketest config:
   python validate_smoketest_configs.py

2) Validate only selected tools:
   python validate_smoketest_configs.py --tool genie3 --tool scmtni

Exit codes:
- 0: all selected smoketest configs are valid
- 1: one or more smoketest configs are invalid / unreadable
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
    DEFAULT_CATALOG_TOOLS_ROOT,
    INFERENCE_TOOLS_ROOT,
    discover_catalog_tool_dirs,
    load_json,
    select_tools,
)

DEFAULT_SMOKETEST_CONFIGS_ROOT = INFERENCE_TOOLS_ROOT / "tests" / "smoketest_configs"
DEFAULT_FIXTURES_DIR = INFERENCE_TOOLS_ROOT / "tests" / "fixtures"
DEFAULT_SCHEMA_PATH = (
    INFERENCE_TOOLS_ROOT / "tests" / "schemas" / "smoketest.config.schema.json"
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


def validate_instance(
    validator: Draft202012Validator,
    instance: Any,
) -> list[ValidationError]:
    return sorted(validator.iter_errors(instance), key=lambda err: list(err.path))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate per-tool smoketest configs against smoketest.config.schema.json."
        )
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to smoketest config schema. Default: {DEFAULT_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory. Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--configs-root",
        type=Path,
        default=DEFAULT_SMOKETEST_CONFIGS_ROOT,
        help=(
            "Path to smoketest config directory. "
            f"Default: {DEFAULT_SMOKETEST_CONFIGS_ROOT}"
        ),
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help=f"Path to smoketest fixtures directory. Default: {DEFAULT_FIXTURES_DIR}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to validate (repeatable). If omitted, validates all configs.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first invalid smoketest config.",
    )
    return parser.parse_args(argv)


def discover_config_files(configs_root: Path) -> list[tuple[str, Path]]:
    if not configs_root.exists() or not configs_root.is_dir():
        raise RuntimeError(f"Invalid smoketest configs root: {configs_root}")

    discovered: list[tuple[str, Path]] = []
    for config_path in sorted(configs_root.glob("*.json")):
        discovered.append((config_path.stem, config_path))
    return discovered


def resolve_fixture_path(fixtures_dir: Path, tool_id: str, filename: str) -> Path | None:
    tool_fixture = fixtures_dir / tool_id / filename
    if tool_fixture.exists():
        return tool_fixture

    shared_fixture = fixtures_dir / filename
    if shared_fixture.exists():
        return shared_fixture

    return None


def semantic_errors_for_config(
    *,
    tool_id: str,
    config_path: Path,
    instance: Any,
    catalog_tool_ids: set[str],
    fixtures_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if tool_id not in catalog_tool_ids:
        errors.append(
            f"Config filename '{config_path.name}' does not match any catalog tool id."
        )

    if not isinstance(instance, dict):
        errors.append("Smoketest config root must be a JSON object.")
        return errors

    extra_files = instance.get("extra_files", [])
    if not isinstance(extra_files, list):
        return errors

    for extra_name in extra_files:
        if not isinstance(extra_name, str):
            continue
        resolved = resolve_fixture_path(fixtures_dir, tool_id, extra_name)
        if resolved is None:
            errors.append(
                "extra_files entry does not resolve to an existing fixture: "
                f"{extra_name!r} (looked in {fixtures_dir / tool_id / extra_name} "
                f"and {fixtures_dir / extra_name})"
            )

    return errors


def run(
    *,
    schema_path: Path,
    catalog_tools_root: Path,
    configs_root: Path,
    fixtures_dir: Path,
    tool_filters: list[str],
    fail_fast: bool,
) -> int:
    catalog_tools = discover_catalog_tool_dirs(catalog_tools_root, required_filename="toolspec.json")
    if not catalog_tools:
        raise RuntimeError(f"No catalog tools found under: {catalog_tools_root}")
    catalog_tool_ids = {tool_id for tool_id, _ in catalog_tools}

    all_configs = discover_config_files(configs_root)
    if not all_configs:
        raise RuntimeError(f"No smoketest configs found under: {configs_root}")

    selected = select_tools(all_configs, tool_filters)
    schema = load_json(schema_path)
    validator = build_validator(schema)

    counters = ValidationCounters()

    for tool_id, config_path in selected:
        print(f"[{tool_id}] validating {config_path}")
        try:
            instance = load_json(config_path)
            schema_errors = validate_instance(validator, instance)
            semantic_errors = semantic_errors_for_config(
                tool_id=tool_id,
                config_path=config_path,
                instance=instance,
                catalog_tool_ids=catalog_tool_ids,
                fixtures_dir=fixtures_dir,
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

        counters = ValidationCounters(valid=counters.valid, invalid=counters.invalid + 1)
        for error in schema_errors:
            print(f"  ERROR {to_json_pointer(error)}: {error.message}")
        for error in semantic_errors:
            print(f"  ERROR: {error}")
        if fail_fast:
            break

    print(
        f"\nSummary: checked={counters.checked} valid={counters.valid} invalid={counters.invalid}"
    )
    return 0 if counters.invalid == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(
            schema_path=args.schema,
            catalog_tools_root=args.catalog_tools_root,
            configs_root=args.configs_root,
            fixtures_dir=args.fixtures_dir,
            tool_filters=args.tool,
            fail_fast=args.fail_fast,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
