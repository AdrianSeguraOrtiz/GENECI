"""Validate simulator SimulatorSpec files against the SimulatorSpec JSON Schema.

Usage examples:
1) Validate every simulator:
   python validate_simulatorspecs.py

2) Validate only selected simulators:
   python validate_simulatorspecs.py --simulator dyngen
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
    DEFAULT_SCHEMA_PATH,
    DEFAULT_WRAPPERS_ROOT,
    discover_catalog_simulator_dirs,
    expected_docker_image,
    load_json,
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


def semantic_errors(
    *,
    simulator_id: str,
    spec: dict[str, Any],
    wrappers_root: Path,
) -> list[str]:
    errors: list[str] = []
    if spec.get("id") != simulator_id:
        errors.append(f"id must match catalog directory name '{simulator_id}'")

    expected_image = expected_docker_image(simulator_id)
    if spec.get("docker_image") != expected_image:
        errors.append(f"docker_image must be '{expected_image}'")

    publications = spec.get("publication", [])
    if not all(
        isinstance(item, str) and item.startswith(("http://", "https://"))
        for item in publications
    ):
        errors.append("publication entries must be complete http(s) URLs")

    first_author = str(spec.get("first_author", "")).strip()
    if len(first_author.split()) < 2:
        errors.append("first_author must include at least given name and surname")

    wrapper_dir = wrappers_root / simulator_id
    if not wrapper_dir.exists():
        errors.append(f"missing wrapper directory: {wrapper_dir}")
    elif not (wrapper_dir / "Dockerfile").exists():
        errors.append(f"missing wrapper Dockerfile: {wrapper_dir / 'Dockerfile'}")

    for profile, capability in spec.get("profile_capabilities", {}).items():
        native = set(capability.get("native_extras", []))
        derivable = set(capability.get("derivable_extras", []))
        overlap = sorted(native.intersection(derivable))
        if overlap:
            errors.append(
                f"profile_capabilities.{profile}: native_extras and derivable_extras overlap: {overlap}"
            )
        truth_derivable = {
            key
            for key, value in capability.get("truth_outputs", {}).items()
            if value == "derivable"
        }
        expected_derivations = derivable.union(truth_derivable)
        derivation_entries = capability.get("derivations", [])
        derivation_artifacts = [
            str(item.get("artifact"))
            for item in derivation_entries
            if isinstance(item, dict)
        ]
        duplicate_derivations = sorted(
            artifact
            for artifact in set(derivation_artifacts)
            if derivation_artifacts.count(artifact) > 1
        )
        if duplicate_derivations:
            errors.append(
                f"profile_capabilities.{profile}: duplicate derivation entries: {duplicate_derivations}"
            )
        documented_derivations = set(derivation_artifacts)
        missing_derivations = sorted(expected_derivations.difference(documented_derivations))
        if missing_derivations:
            errors.append(
                f"profile_capabilities.{profile}: missing derivation explanations for: {missing_derivations}"
            )
        unexpected_derivations = sorted(documented_derivations.difference(expected_derivations))
        if unexpected_derivations:
            errors.append(
                f"profile_capabilities.{profile}: derivation explanations declared for non-derived artifacts: {unexpected_derivations}"
            )
    return errors


def validate_one(
    *,
    simulator_id: str,
    simulator_dir: Path,
    validator: Draft202012Validator,
    wrappers_root: Path,
) -> list[str]:
    spec_path = simulator_dir / "simulatorspec.json"
    spec = load_json(spec_path)
    if not isinstance(spec, dict):
        return [f"{spec_path}: expected JSON object"]

    errors = [
        f"{to_json_pointer(err)} -> {err.message}"
        for err in sorted(validator.iter_errors(spec), key=lambda err: list(err.path))
    ]
    errors.extend(
        semantic_errors(
            simulator_id=simulator_id,
            spec=spec,
            wrappers_root=wrappers_root,
        )
    )
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate every catalog simulatorspec.json against simulatorspec.schema.json."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"Path to SimulatorSpec schema. Default: {DEFAULT_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--wrappers-root",
        type=Path,
        default=DEFAULT_WRAPPERS_ROOT,
        help=f"Path to simulator wrapper directories. Default: {DEFAULT_WRAPPERS_ROOT}",
    )
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        help="Simulator id to validate (repeatable). If omitted, validates every simulator.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first invalid simulator.",
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

    counters = ValidationCounters()
    for simulator_id, simulator_dir in selected:
        try:
            errors = validate_one(
                simulator_id=simulator_id,
                simulator_dir=simulator_dir,
                validator=validator,
                wrappers_root=args.wrappers_root,
            )
        except RuntimeError as exc:
            errors = [str(exc)]

        if errors:
            counters = ValidationCounters(counters.valid, counters.invalid + 1)
            print(f"[INVALID] {simulator_id}", file=sys.stderr)
            for message in errors:
                print(f"  - {message}", file=sys.stderr)
            if args.fail_fast:
                break
        else:
            counters = ValidationCounters(counters.valid + 1, counters.invalid)
            print(f"[valid] {simulator_id}")

    print(
        f"Checked {counters.checked} simulator spec(s): "
        f"{counters.valid} valid, {counters.invalid} invalid"
    )
    return 1 if counters.invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
