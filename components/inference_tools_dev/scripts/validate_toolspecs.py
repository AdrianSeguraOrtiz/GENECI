"""Validate tool ToolSpec files against the ToolSpec JSON Schema.

Usage examples:
1) Validate every tool:
   python validate_toolspecs.py

2) Validate only selected tools:
   python validate_toolspecs.py --tool genie3 --tool scmtni

Exit codes:
- 0: all selected ToolSpecs are valid
- 1: one or more ToolSpecs are invalid / unreadable
- 2: usage/runtime error (missing schema, unknown tool ids, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "geneci" / "inference_catalog"
DEFAULT_SCHEMA_PATH = CATALOG_ROOT / "schemas" / "toolspec.schema.json"
DEFAULT_CATALOG_TOOLS_ROOT = CATALOG_ROOT / "tools"


@dataclass(frozen=True)
class ValidationCounters:
    valid: int = 0
    invalid: int = 0

    @property
    def checked(self) -> int:
        return self.valid + self.invalid


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"File not found: {path}") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not read file: {path} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Malformed JSON in {path} (line {exc.lineno}, column {exc.colno}): {exc.msg}"
        ) from exc


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
        description="Validate every catalog toolspec.json against toolspec.schema.json."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to ToolSpec schema. Default: {DEFAULT_SCHEMA_PATH}",
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
        help="Tool id to validate (repeatable). If omitted, validates all tools.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first invalid ToolSpec.",
    )
    return parser.parse_args(argv)


def discover_toolspecs(catalog_tools_root: Path) -> list[tuple[str, Path]]:
    if not catalog_tools_root.exists() or not catalog_tools_root.is_dir():
        raise RuntimeError(f"Invalid catalog tools root: {catalog_tools_root}")

    discovered: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in catalog_tools_root.iterdir() if path.is_dir()
    ):
        spec_path = tool_dir / "toolspec.json"
        if spec_path.exists():
            discovered.append((tool_dir.name, spec_path))
    return discovered


def select_toolspecs(
    all_toolspecs: list[tuple[str, Path]],
    tool_filters: list[str],
) -> list[tuple[str, Path]]:
    by_tool_id = {tool_id: path for tool_id, path in all_toolspecs}
    if not tool_filters:
        return all_toolspecs

    unknown = sorted(tool_id for tool_id in tool_filters if tool_id not in by_tool_id)
    if unknown:
        raise RuntimeError(f"Unknown tool id(s): {unknown}")
    return [(tool_id, by_tool_id[tool_id]) for tool_id in tool_filters]


def validate_one_toolspec(
    *,
    spec_path: Path,
    validator: Draft202012Validator,
) -> list[ValidationError]:
    instance = load_json(spec_path)
    return validate_instance(validator, instance)


def run(
    schema_path: Path,
    catalog_tools_root: Path,
    tool_filters: list[str],
    fail_fast: bool,
) -> int:
    all_toolspecs = discover_toolspecs(catalog_tools_root)
    if not all_toolspecs:
        raise RuntimeError(f"No toolspec.json files found under: {catalog_tools_root}")

    selected = select_toolspecs(all_toolspecs, tool_filters)

    schema = load_json(schema_path)
    validator = build_validator(schema)

    counters = ValidationCounters()

    for tool_id, spec_path in selected:
        print(f"[{tool_id}] validating {spec_path}")
        try:
            errors = validate_one_toolspec(
                spec_path=spec_path,
                validator=validator,
            )
        except RuntimeError as exc:
            counters = ValidationCounters(
                valid=counters.valid, invalid=counters.invalid + 1
            )
            print(f"  ERROR: {exc}")
            if fail_fast:
                break
            continue

        if not errors:
            counters = ValidationCounters(
                valid=counters.valid + 1, invalid=counters.invalid
            )
            print("  VALID")
            continue

        counters = ValidationCounters(
            valid=counters.valid, invalid=counters.invalid + 1
        )
        print(f"  INVALID: {len(errors)} error(s)")
        for idx, err in enumerate(errors, start=1):
            print(f"    {idx}. {to_json_pointer(err)} -> {err.message}")
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
