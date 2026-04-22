"""Shared catalog and simulator source helpers for generate-data dev scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GENERATE_DEV_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_ROOT = REPO_ROOT / "geneci" / "generation_catalog"
DEFAULT_CATALOG_SIMULATORS_ROOT = CATALOG_ROOT / "simulators"
DEFAULT_SCHEMA_PATH = CATALOG_ROOT / "schemas" / "simulatorspec.schema.json"
DEFAULT_WRAPPERS_ROOT = GENERATE_DEV_ROOT / "generators"
DEFAULT_SMOKETEST_CONFIGS_ROOT = GENERATE_DEV_ROOT / "tests" / "smoketest_configs"
DEFAULT_SMOKETEST_SCHEMA_PATH = (
    GENERATE_DEV_ROOT / "tests" / "schemas" / "smoketest.config.schema.json"
)
DEFAULT_SIMULATOR_EVIDENCE_ROOT = REPO_ROOT / "components" / "generate_data"


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


def discover_catalog_simulator_dirs(
    catalog_simulators_root: Path,
    *,
    required_filename: str = "simulatorspec.json",
) -> list[tuple[str, Path]]:
    if not catalog_simulators_root.exists() or not catalog_simulators_root.is_dir():
        raise RuntimeError(
            f"Invalid catalog simulators root: {catalog_simulators_root}"
        )

    discovered: list[tuple[str, Path]] = []
    for simulator_dir in sorted(
        path for path in catalog_simulators_root.iterdir() if path.is_dir()
    ):
        if (simulator_dir / required_filename).exists():
            discovered.append((simulator_dir.name, simulator_dir))
    return discovered


def discover_wrapper_dirs(wrappers_root: Path) -> list[tuple[str, Path]]:
    if not wrappers_root.exists() or not wrappers_root.is_dir():
        raise RuntimeError(f"Invalid simulator wrappers root: {wrappers_root}")

    return sorted(
        (wrapper_dir.name, wrapper_dir)
        for wrapper_dir in wrappers_root.iterdir()
        if wrapper_dir.is_dir()
    )


def discover_evidence_dirs(evidence_root: Path) -> list[tuple[str, Path]]:
    if not evidence_root.exists() or not evidence_root.is_dir():
        raise RuntimeError(f"Invalid simulator evidence root: {evidence_root}")

    return sorted(
        (source_dir.name, source_dir)
        for source_dir in evidence_root.iterdir()
        if source_dir.is_dir()
    )


def select_simulators(
    discovered: list[tuple[str, Path]],
    filters: list[str],
) -> list[tuple[str, Path]]:
    by_id = {simulator_id: path for simulator_id, path in discovered}
    if not filters:
        return discovered

    unknown = sorted(
        simulator_id for simulator_id in filters if simulator_id not in by_id
    )
    if unknown:
        raise RuntimeError(f"Unknown simulator id(s): {unknown}")
    return [(simulator_id, by_id[simulator_id]) for simulator_id in filters]


def load_simulatorspec(
    catalog_simulators_root: Path,
    simulator_id: str,
) -> dict[str, Any]:
    spec_path = catalog_simulators_root / simulator_id / "simulatorspec.json"
    payload = load_json(spec_path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in: {spec_path}")
    return payload


def load_required_simulatorspec_string(
    *,
    simulator_id: str,
    catalog_simulators_root: Path,
    field_name: str,
) -> str:
    spec = load_simulatorspec(catalog_simulators_root, simulator_id)
    value = spec.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"[{simulator_id}] simulatorspec.{field_name} must be a non-empty string."
        )
    return value.strip()


def load_simulatorspec_publications(
    *,
    simulator_id: str,
    catalog_simulators_root: Path,
) -> list[str]:
    spec = load_simulatorspec(catalog_simulators_root, simulator_id)
    value = spec.get("publication")
    if not isinstance(value, list) or not value:
        raise RuntimeError(
            f"[{simulator_id}] simulatorspec.publication must be a non-empty array."
        )

    publications: list[str] = []
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(
                f"[{simulator_id}] simulatorspec.publication[{idx}] must be a non-empty string."
            )
        publications.append(item.strip())
    return publications


def expected_docker_image(simulator_id: str) -> str:
    return f"adriansegura99/simulator_{simulator_id}:1.0.0"
