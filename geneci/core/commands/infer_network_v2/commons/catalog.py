"""Catalog and schema constraint resolution helpers."""

from __future__ import annotations

import re
from pathlib import Path

from .shared import CATALOG_ROOT, SchemaConstraints, _load_json_object


def _has_toolspecs(tools_root: Path) -> bool:
    return any(tools_root.glob("*/toolspec.json"))


def _validate_catalog_layout(catalog_root: Path, *, source: str) -> tuple[Path, Path]:
    catalog_root = catalog_root.resolve()
    tools_root = (catalog_root / "tools").resolve()
    schemas_dir = (catalog_root / "schemas").resolve()

    if not catalog_root.exists() or not catalog_root.is_dir():
        raise ValueError(
            f"Inference tools catalog root not found ({source}): {catalog_root}"
        )
    if not tools_root.exists() or not tools_root.is_dir():
        raise ValueError(f"Inference tools catalog not found ({source}): {tools_root}")
    if not _has_toolspecs(tools_root):
        raise ValueError(
            f"Inference tools catalog has no tool specs ({source}): {tools_root}"
        )
    if not schemas_dir.exists() or not schemas_dir.is_dir():
        raise ValueError(
            f"Inference schemas directory not found ({source}): {schemas_dir}"
        )

    return tools_root, schemas_dir


def _resolve_catalog_paths() -> tuple[Path, Path]:
    return _validate_catalog_layout(CATALOG_ROOT, source="geneci package catalog")


def _extract_extension_from_pattern(pattern: str) -> str:
    match = re.search(r"\\\.([A-Za-z0-9]+)\$", pattern)
    if match:
        return match.group(1).lower()
    return "tsv"


def _load_schema_constraints(schemas_dir: Path) -> SchemaConstraints:
    dataset_manifest_schema = _load_json_object(
        schemas_dir / "dataset-manifest.schema.json",
        "dataset-manifest.schema",
    )
    toolspec_schema = _load_json_object(
        schemas_dir / "toolspec.schema.json",
        "toolspec.schema",
    )

    spec_expr_props = (
        dataset_manifest_schema.get("properties", {})
        .get("dataset", {})
        .get("properties", {})
        .get("spec", {})
        .get("properties", {})
        .get("expression", {})
        .get("properties", {})
    )
    raw_column_kinds = spec_expr_props.get("column_kind", {}).get("enum", [])
    raw_expression_profiles = spec_expr_props.get("expression_profile", {}).get(
        "enum", []
    )

    column_kinds = {x for x in raw_column_kinds if isinstance(x, str)}
    expression_profiles = {x for x in raw_expression_profiles if isinstance(x, str)}
    if not column_kinds:
        raise ValueError(
            "dataset-manifest.schema: dataset.spec.expression.column_kind.enum is missing or empty"
        )
    if not expression_profiles:
        raise ValueError(
            "dataset-manifest.schema: dataset.spec.expression.expression_profile.enum is missing or empty"
        )

    raw_assumptions = (
        toolspec_schema.get("properties", {}).get("assumes", {}).get("enum", [])
    )
    assumptions = {x for x in raw_assumptions if isinstance(x, str)}
    if not assumptions:
        raise ValueError("toolspec.schema: assumes.enum is missing or empty")

    extras_props = (
        dataset_manifest_schema.get("properties", {})
        .get("extras", {})
        .get("properties", {})
    )
    if not isinstance(extras_props, dict) or not extras_props:
        raise ValueError(
            "dataset-manifest.schema: extras.properties is missing or empty"
        )

    extra_input_keys = {key for key in extras_props if isinstance(key, str)}
    extra_input_filenames: dict[str, str] = {}
    for key, prop in extras_props.items():
        if not isinstance(prop, dict):
            extra_input_filenames[key] = f"{key}.tsv"
            continue
        pattern = str(prop.get("pattern", ""))
        extension = _extract_extension_from_pattern(pattern)
        extra_input_filenames[key] = f"{key}.{extension}"

    return SchemaConstraints(
        column_kinds=column_kinds,
        expression_profiles=expression_profiles,
        assumptions=assumptions,
        extra_input_keys=extra_input_keys,
        extra_input_filenames=extra_input_filenames,
    )
