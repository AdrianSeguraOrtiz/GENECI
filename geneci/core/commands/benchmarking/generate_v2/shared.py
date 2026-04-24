"""Shared constants, dataclasses, and IO helpers for generate-v2."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from jsonschema import Draft202012Validator

DEFAULT_OUTPUT_DIR = Path("./benchmarks_v2")
CATALOG_ROOT = Path(__file__).resolve().parents[4] / "generation_catalog"
REPO_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_VERSION = "1.0"
KNOWN_EXTRAS = {
    "groups",
    "lineage_tree",
    "tf_list",
    "prior_grn_by_group",
    "group_networks",
}
MAX_SEED_32BIT = 2_147_483_646


@dataclass(frozen=True)
class ProfileSpec:
    profile: str
    column_kind: str
    expression_profile: str
    required_extras: frozenset[str]


PROFILE_SPECS: dict[str, ProfileSpec] = {
    "bulk_steady_state": ProfileSpec(
        profile="bulk_steady_state",
        column_kind="samples",
        expression_profile="bulk",
        required_extras=frozenset(),
    ),
    "bulk_time_series": ProfileSpec(
        profile="bulk_time_series",
        column_kind="timepoints",
        expression_profile="bulk",
        required_extras=frozenset(),
    ),
    "bulk_perturbational": ProfileSpec(
        profile="bulk_perturbational",
        column_kind="perturbations",
        expression_profile="bulk",
        required_extras=frozenset(),
    ),
    "scrna_global": ProfileSpec(
        profile="scrna_global",
        column_kind="cells",
        expression_profile="scrna",
        required_extras=frozenset(),
    ),
    "scrna_grouped": ProfileSpec(
        profile="scrna_grouped",
        column_kind="cells",
        expression_profile="scrna",
        required_extras=frozenset({"groups"}),
    ),
}


@dataclass(frozen=True)
class ResolvedSimulatorRun:
    request_id: str
    profile: str
    run_id: str
    simulator_id: str
    organism: dict[str, Any]
    requested_extras: list[str]
    effective_extras: list[str]
    inputs: dict[str, dict[str, Any]]
    input_files: dict[str, str]
    resolved_input_files: dict[str, Path]
    simulator_params: dict[str, Any]
    native_outputs: list[str]
    replicates: int
    base_seed: Optional[int]
    replicate_seeds: list[int]
    notes: Optional[str]
    simulator_spec: dict[str, Any]


@dataclass(frozen=True)
class ResolvedSimulationPlan:
    request_id: str
    profile: str
    organism: dict[str, Any]
    requested_extras: list[str]
    effective_extras: list[str]
    inputs: dict[str, dict[str, Any]]
    input_files: dict[str, str]
    resolved_input_files: dict[str, Path]
    base_seed: Optional[int]
    notes: Optional[str]
    simulator_runs: list[ResolvedSimulatorRun]
    tasks: list[dict[str, Any]]
    execution: dict[str, Any]
    plan_payload: dict[str, Any]


@dataclass(frozen=True)
class ResolvedScenarioRequest:
    request_id: str
    profile: str
    organism: dict[str, Any]
    requested_extras: list[str]
    effective_extras: list[str]
    inputs: dict[str, dict[str, Any]]
    input_files: dict[str, str]
    resolved_input_files: dict[str, Path]
    base_seed: Optional[int]
    notes: Optional[str]
    request_payload: dict[str, Any]


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise ValueError(f"{label} file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{label} is malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _validate_json_instance(
    *,
    instance: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.path))
    if not errors:
        return
    first = errors[0]
    dotted = ".".join(str(x) for x in first.absolute_path)
    if dotted:
        raise ValueError(
            f"{label} failed schema validation at {dotted}: {first.message}"
        )
    raise ValueError(f"{label} failed schema validation: {first.message}")


def _relative_posix(path: Path, start: Path) -> str:
    return path.relative_to(start).as_posix()


def _stable_seed_base(*, request_id: str, profile: str, simulator_id: str) -> int:
    digest = hashlib.sha256(
        f"{request_id}|{profile}|{simulator_id}".encode("utf-8")
    ).hexdigest()
    return (int(digest[:8], 16) % MAX_SEED_32BIT) + 1
