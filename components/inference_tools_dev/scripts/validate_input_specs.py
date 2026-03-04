"""Validate InputSpec files against the InputSpec JSON Schema.

Usage examples:
1) Validate every input spec:
   python validate_input_specs.py

2) Validate only selected specs:
   python validate_input_specs.py --spec expression_matrix --spec tf_list

Exit codes:
- 0: all selected InputSpecs are valid
- 1: one or more InputSpecs are invalid / unreadable
- 2: usage/runtime error (missing schema, unknown spec ids, etc.)
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
DEFAULT_SCHEMA_PATH = CATALOG_ROOT / "schemas" / "input-spec.schema.json"
DEFAULT_INPUT_SPECS_ROOT = CATALOG_ROOT / "input_specs"

REQUIRES_COLUMN_KINDS = {
    "column_subset_expression_genes",
    "column_subset_expression_columns",
}


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
        description="Validate every input spec JSON against input-spec.schema.json."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to InputSpec schema. Default: {DEFAULT_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--input-specs-root",
        type=Path,
        default=DEFAULT_INPUT_SPECS_ROOT,
        help=f"Path to input_specs directory. Default: {DEFAULT_INPUT_SPECS_ROOT}",
    )
    parser.add_argument(
        "--spec",
        action="append",
        default=[],
        help="Input spec id / filename stem to validate (repeatable). If omitted, validates all specs.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first invalid InputSpec.",
    )
    return parser.parse_args(argv)


def discover_input_specs(input_specs_root: Path) -> list[tuple[str, Path]]:
    if not input_specs_root.exists() or not input_specs_root.is_dir():
        raise RuntimeError(f"Invalid input_specs root: {input_specs_root}")

    discovered: list[tuple[str, Path]] = []
    for spec_path in sorted(input_specs_root.glob("*.json")):
        discovered.append((spec_path.stem, spec_path))
    return discovered


def select_input_specs(
    all_specs: list[tuple[str, Path]],
    filters: list[str],
) -> list[tuple[str, Path]]:
    by_id = {spec_id: path for spec_id, path in all_specs}
    if not filters:
        return all_specs

    unknown = sorted(spec_id for spec_id in filters if spec_id not in by_id)
    if unknown:
        raise RuntimeError(f"Unknown input spec id(s): {unknown}")
    return [(spec_id, by_id[spec_id]) for spec_id in filters]


def semantic_errors_for_input_spec(
    *,
    spec_id: str,
    spec_path: Path,
    instance: Any,
    seen_keys: dict[str, Path],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(instance, dict):
        errors.append("InputSpec root must be a JSON object.")
        return errors

    key_raw = instance.get("key")
    if not isinstance(key_raw, str) or not key_raw.strip():
        errors.append("InputSpec 'key' must be a non-empty string.")
        return errors

    key = key_raw.strip()
    if key != spec_id:
        errors.append(
            f"InputSpec key must match filename stem. expected='{spec_id}' got='{key}'."
        )

    previous = seen_keys.get(key)
    if previous is not None and previous != spec_path:
        errors.append(
            f"Duplicate InputSpec key '{key}' found in {spec_path} and {previous}."
        )
    seen_keys[key] = spec_path

    cross_checks = instance.get("cross_checks", [])
    if isinstance(cross_checks, list):
        for idx, check in enumerate(cross_checks):
            if not isinstance(check, dict):
                continue
            kind = check.get("kind")
            column = check.get("column")
            if kind in REQUIRES_COLUMN_KINDS and (
                not isinstance(column, str) or not column.strip()
            ):
                errors.append(
                    "cross_checks[{idx}] requires non-empty 'column' for kind '{kind}'.".format(
                        idx=idx, kind=kind
                    )
                )

    return errors


def run(
    schema_path: Path,
    input_specs_root: Path,
    spec_filters: list[str],
    fail_fast: bool,
) -> int:
    all_specs = discover_input_specs(input_specs_root)
    if not all_specs:
        raise RuntimeError(f"No input spec .json files found under: {input_specs_root}")

    selected = select_input_specs(all_specs, spec_filters)
    schema = load_json(schema_path)
    validator = build_validator(schema)

    counters = ValidationCounters()
    seen_keys: dict[str, Path] = {}

    for spec_id, spec_path in selected:
        print(f"[{spec_id}] validating {spec_path}")
        try:
            instance = load_json(spec_path)
            schema_errors = validate_instance(validator, instance)
            semantic_errors = semantic_errors_for_input_spec(
                spec_id=spec_id,
                spec_path=spec_path,
                instance=instance,
                seen_keys=seen_keys,
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
            input_specs_root=args.input_specs_root,
            spec_filters=args.spec,
            fail_fast=args.fail_fast,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
