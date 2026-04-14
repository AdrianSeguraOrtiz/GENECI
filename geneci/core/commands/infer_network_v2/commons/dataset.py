"""Dataset parsing and declarative input validation helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Optional

from .shared import (
    INPUT_SPECS_DIR,
    DatasetContext,
    SchemaConstraints,
    _load_json_object,
    _resolve_path,
)


def _inspect_expression_tsv(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader, None)
        if header is None or len(header) < 2:
            raise ValueError(
                f"Expression matrix must have header with at least 2 columns: {path}"
            )
        expected_cols = len(header)
        genes = 0
        for line_idx, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != expected_cols:
                raise ValueError(
                    f"Expression matrix has inconsistent number of columns at line {line_idx}: "
                    f"expected {expected_cols}, got {len(row)} ({path})"
                )
            genes += 1

    columns = expected_cols - 1
    if genes <= 0:
        raise ValueError(f"Expression matrix has no gene rows: {path}")
    return genes, columns


def _parse_dataset_context(
    *,
    dataset_manifest_path: Path,
    constraints: SchemaConstraints,
) -> DatasetContext:
    manifest = _load_json_object(dataset_manifest_path, "dataset-manifest")

    manifest_dataset = manifest.get("dataset")
    if not isinstance(manifest_dataset, dict):
        raise ValueError("dataset-manifest must include object field: dataset")

    spec = manifest_dataset.get("spec")
    expr_raw = manifest_dataset.get("expression_matrix")
    if not isinstance(spec, dict):
        raise ValueError("dataset-manifest.dataset.spec must be an embedded object")
    if not isinstance(expr_raw, str) or not expr_raw:
        raise ValueError(
            "dataset-manifest.dataset.expression_matrix must be a non-empty string path"
        )

    manifest_base = dataset_manifest_path.parent.resolve()
    expression_path = _resolve_path(manifest_base, expr_raw)

    if not expression_path.exists():
        raise ValueError(f"Expression matrix file not found: {expression_path}")

    spec_expression = spec.get("expression")
    if not isinstance(spec_expression, dict):
        raise ValueError(
            "dataset-manifest.dataset.spec must include object field: expression"
        )

    dataset_id = str(spec.get("id", "")).strip()
    if not dataset_id:
        raise ValueError("dataset-manifest.dataset.spec.id is required")

    column_kind = str(spec_expression.get("column_kind", "")).strip()
    if column_kind not in constraints.column_kinds:
        raise ValueError(
            "dataset-manifest.dataset.spec.expression.column_kind must be one of "
            f"{sorted(constraints.column_kinds)}"
        )

    expression_profile = str(spec_expression.get("expression_profile", "")).strip()
    if expression_profile not in constraints.expression_profiles:
        raise ValueError(
            "dataset-manifest.dataset.spec.expression.expression_profile must be one of "
            f"{sorted(constraints.expression_profiles)}"
        )

    try:
        genes_expected = int(spec_expression.get("genes"))
        cols_expected = int(spec_expression.get("columns"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            "dataset-manifest.dataset.spec.expression.genes and columns must be integers >= 1"
        ) from exc
    if genes_expected < 1 or cols_expected < 1:
        raise ValueError(
            "dataset-manifest.dataset.spec.expression.genes and columns must be >= 1"
        )

    genes_observed, cols_observed = _inspect_expression_tsv(expression_path)
    if genes_observed != genes_expected or cols_observed != cols_expected:
        raise ValueError(
            "dataset-manifest.dataset.spec expression dimensions do not match the expression matrix: "
            f"spec={genes_expected}x{cols_expected}, observed={genes_observed}x{cols_observed}"
        )

    raw_extras = manifest.get("extras", {})
    if raw_extras is None:
        raw_extras = {}
    if not isinstance(raw_extras, dict):
        raise ValueError("dataset-manifest.extras must be an object when provided")

    extras: dict[str, Optional[Path]] = {}
    for key in sorted(constraints.extra_input_keys):
        value = raw_extras.get(key)
        if value is None:
            extras[key] = None
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"dataset-manifest.extras.{key} must be string or null")
        extra_path = _resolve_path(manifest_base, value)
        if not extra_path.exists():
            raise ValueError(
                f"Extra input declared but file not found: extras.{key} -> {extra_path}"
            )
        extras[key] = extra_path

    return DatasetContext(
        dataset_id=dataset_id,
        column_kind=column_kind,
        expression_profile=expression_profile,
        genes=genes_observed,
        columns=cols_observed,
        expression_matrix_path=expression_path,
        extras=extras,
    )


def _load_input_specs() -> dict[str, dict[str, Any]]:
    if not INPUT_SPECS_DIR.exists() or not INPUT_SPECS_DIR.is_dir():
        raise ValueError(f"Input specs directory not found: {INPUT_SPECS_DIR}")

    specs: dict[str, dict[str, Any]] = {}
    for spec_path in sorted(INPUT_SPECS_DIR.glob("*.json")):
        spec = _load_json_object(spec_path, f"input-spec[{spec_path.name}]")
        key = str(spec.get("key", "")).strip()
        if not key:
            raise ValueError(f"input spec is missing key: {spec_path}")
        if key in specs:
            raise ValueError(f"Duplicate input spec key '{key}': {spec_path}")
        specs[key] = spec

    if "expression_matrix" not in specs:
        raise ValueError(
            f"Missing required input spec 'expression_matrix' in {INPUT_SPECS_DIR}"
        )
    return specs


def _read_expression_axes(path: Path) -> tuple[list[str], list[str]]:
    genes: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader, None)
        if header is None or len(header) < 2:
            raise ValueError(
                f"Expression matrix must have header with at least 2 columns: {path}"
            )
        columns = [str(x).strip() for x in header[1:]]
        expected_cols = len(header)
        for line_idx, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != expected_cols:
                raise ValueError(
                    f"Expression matrix has inconsistent number of columns at line {line_idx}: "
                    f"expected {expected_cols}, got {len(row)} ({path})"
                )
            gene_id = str(row[0]).strip()
            if not gene_id:
                raise ValueError(
                    f"Expression matrix has empty gene identifier at line {line_idx}: {path}"
                )
            genes.append(gene_id)
    if not genes:
        raise ValueError(f"Expression matrix has no gene rows: {path}")
    return genes, columns


def _load_groups_by_column(
    *,
    groups_path: Path,
    expression_columns: list[str],
) -> tuple[list[str], dict[str, list[str]]]:
    sample_to_group: dict[str, str] = {}
    header_markers = {"sample", "cell", "column", "observation", "id"}
    group_markers = {"group", "cluster", "cell_type", "label"}

    with groups_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        for line_idx, row in enumerate(reader, start=1):
            if not row or not any(str(cell).strip() for cell in row):
                continue
            if len(row) < 2:
                raise ValueError(
                    f"{groups_path}: line {line_idx} must have at least 2 columns: sample and group"
                )

            sample = str(row[0]).strip()
            group = str(row[1]).strip()
            if (
                line_idx == 1
                and sample.lower() in header_markers
                and group.lower() in group_markers
            ):
                continue
            if not sample or not group:
                raise ValueError(
                    f"{groups_path}: line {line_idx} must have non-empty sample and group values"
                )
            if sample in sample_to_group:
                raise ValueError(
                    f"{groups_path}: duplicate sample assignment found: {sample}"
                )
            sample_to_group[sample] = group

    missing = [column for column in expression_columns if column not in sample_to_group]
    if missing:
        preview = ", ".join(missing[:8])
        raise ValueError(
            f"{groups_path}: missing group assignments for expression columns: {preview}"
        )

    extra = [sample for sample in sample_to_group if sample not in set(expression_columns)]
    if extra:
        preview = ", ".join(extra[:8])
        raise ValueError(
            f"{groups_path}: contains samples not present in expression matrix: {preview}"
        )

    group_order: list[str] = []
    group_to_columns: dict[str, list[str]] = {}
    for column in expression_columns:
        group = sample_to_group[column]
        if group not in group_to_columns:
            group_to_columns[group] = []
            group_order.append(group)
        group_to_columns[group].append(column)

    return group_order, group_to_columns


def _coerce_cell_type(
    *,
    value: str,
    type_name: str,
    field_name: str,
    file_path: Path,
    line_idx: int,
) -> Optional[str]:
    if value is None:
        value = ""
    stripped = str(value).strip()
    if stripped == "":
        return None

    if type_name == "string":
        return stripped
    if type_name == "int":
        try:
            int(stripped)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                f"{file_path}: line {line_idx}, field '{field_name}' must be int"
            ) from exc
        return stripped
    if type_name == "float":
        try:
            float(stripped)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                f"{file_path}: line {line_idx}, field '{field_name}' must be float"
            ) from exc
        return stripped
    if type_name == "bool":
        normalized = stripped.lower()
        if normalized not in {"true", "false", "0", "1"}:
            raise ValueError(
                f"{file_path}: line {line_idx}, field '{field_name}' must be bool"
            )
        return stripped

    raise ValueError(
        f"Unsupported input spec type '{type_name}' for field '{field_name}'"
    )


def _read_tsv_column_values(path: Path, spec: dict[str, Any], column: str) -> set[str]:
    delimiter = str(spec.get("delimiter", "\t"))
    has_header = bool(spec.get("header", True))
    if not has_header:
        raise ValueError("referenced input does not define a header row")

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        header_row = next(reader, None)
        fieldnames = [str(x).strip() for x in header_row] if header_row else []
        if not fieldnames:
            raise ValueError("referenced input is missing a header row")
        try:
            column_index = fieldnames.index(column)
        except ValueError as exc:
            raise ValueError(
                f"referenced input is missing required column '{column}'"
            ) from exc

        values: set[str] = set()
        expected_cols = len(fieldnames)
        for row in reader:
            if not row or len(row) != expected_cols:
                continue
            raw_value = str(row[column_index]).strip()
            if raw_value:
                values.add(raw_value)
    return values


def _validate_tsv_file_with_spec(
    *,
    key: str,
    path: Path,
    spec: dict[str, Any],
    expression_genes: set[str],
    expression_columns: set[str],
    expression_columns_count: int,
    extra_column_lookup: Any = None,
) -> dict[str, Any]:
    delimiter = str(spec.get("delimiter", "\t"))
    has_header = bool(spec.get("header", True))
    min_rows = int(spec.get("min_rows", 0) or 0)
    min_columns = int(spec.get("min_columns", 1) or 1)
    required_columns = [
        c for c in spec.get("required_columns", []) if isinstance(c, str)
    ]
    column_types = spec.get("column_types", {})
    if not isinstance(column_types, dict):
        column_types = {}
    first_column_role = str(spec.get("first_column_role", "none") or "none").strip()
    unique_first_column = bool(spec.get("unique_first_column", False))
    first_column_disallowed_names = {
        str(x).strip().lower()
        for x in spec.get("first_column_disallowed_names", [])
        if isinstance(x, str) and str(x).strip()
    }
    if first_column_role == "gene_id" and not first_column_disallowed_names:
        first_column_disallowed_names = {
            "cell",
            "cells",
            "sample",
            "samples",
            "timepoint",
            "timepoints",
            "perturbation",
            "perturbations",
            "cluster",
            "pseudotime",
        }
    data_columns_type = str(spec.get("data_columns_type", "any") or "any").strip()
    if data_columns_type not in {"any", "float"}:
        data_columns_type = "any"
    data_numeric_min_fraction = float(spec.get("data_numeric_min_fraction", 1.0) or 1.0)
    if data_numeric_min_fraction < 0.0:
        data_numeric_min_fraction = 0.0
    if data_numeric_min_fraction > 1.0:
        data_numeric_min_fraction = 1.0
    cross_checks = spec.get("cross_checks", [])
    if not isinstance(cross_checks, list):
        cross_checks = []

    errors: list[str] = []
    warnings: list[str] = []
    row_count = 0
    columns_count = 0
    values_by_column: dict[str, set[str]] = {}
    first_column_seen: set[str] = set()
    first_column_values: set[str] = set()
    data_cells_total = 0
    data_cells_numeric = 0
    data_non_numeric_samples: list[str] = []

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader_raw = csv.reader(fh, delimiter=delimiter)
        if has_header:
            header_row = next(reader_raw, None)
            fieldnames = [str(x).strip() for x in header_row] if header_row else []
            columns_count = len(fieldnames)
            if not fieldnames:
                errors.append(f"{path}: expected header row with column names")
            if columns_count and columns_count < min_columns:
                errors.append(
                    f"{path}: expected at least {min_columns} column(s) for '{key}', got {columns_count}"
                )
            if any(not name for name in fieldnames):
                errors.append(f"{path}: header contains empty column names")
            if first_column_role == "gene_id" and fieldnames:
                first_header = str(fieldnames[0]).strip().lower()
                if first_header in first_column_disallowed_names:
                    errors.append(
                        f"{path}: first column header '{fieldnames[0]}' is not valid for expression genes"
                    )
            missing_required = [c for c in required_columns if c not in fieldnames]
            if missing_required:
                errors.append(
                    f"{path}: missing required columns for '{key}': {missing_required}"
                )
            tracked_columns = {
                str(col).strip()
                for col in list(column_types.keys())
                + [
                    str(rule.get("column", "")).strip()
                    for rule in cross_checks
                    if isinstance(rule, dict)
                ]
                if isinstance(col, str) and str(col).strip()
            }
            index_by_name = {name: idx for idx, name in enumerate(fieldnames)}

            for line_idx, row in enumerate(reader_raw, start=2):
                if not row:
                    continue
                if len(row) != columns_count:
                    errors.append(
                        f"{path}: inconsistent number of columns at line {line_idx} "
                        f"(expected {columns_count}, got {len(row)})"
                    )
                    continue
                row_count += 1

                if first_column_role == "gene_id":
                    first_value = str(row[0]).strip() if columns_count >= 1 else ""
                    if not first_value:
                        errors.append(
                            f"{path}: line {line_idx} has empty gene identifier in first column"
                        )
                    elif unique_first_column:
                        if first_value in first_column_seen:
                            errors.append(
                                f"{path}: duplicated gene identifier '{first_value}' in first column"
                            )
                        else:
                            first_column_seen.add(first_value)
                elif first_column_role == "expression_column_id":
                    first_value = str(row[0]).strip() if columns_count >= 1 else ""
                    if not first_value:
                        errors.append(
                            f"{path}: line {line_idx} has empty expression-column identifier in first column"
                        )
                    else:
                        first_column_values.add(first_value)
                        if unique_first_column:
                            if first_value in first_column_seen:
                                errors.append(
                                    f"{path}: duplicated expression-column identifier '{first_value}' in first column"
                                )
                            else:
                                first_column_seen.add(first_value)

                if data_columns_type == "float" and columns_count > 1:
                    for col_idx, raw_value in enumerate(row[1:], start=2):
                        value = str(raw_value).strip()
                        data_cells_total += 1
                        if value == "":
                            if len(data_non_numeric_samples) < 5:
                                data_non_numeric_samples.append(
                                    f"line {line_idx}, col {col_idx}: <empty>"
                                )
                            continue
                        try:
                            float(value)
                            data_cells_numeric += 1
                        except Exception:  # noqa: BLE001
                            if len(data_non_numeric_samples) < 5:
                                data_non_numeric_samples.append(
                                    f"line {line_idx}, col {col_idx}: {value!r}"
                                )

                for col, type_name in column_types.items():
                    idx = index_by_name.get(str(col))
                    if idx is None:
                        continue
                    value = row[idx]
                    coerced = _coerce_cell_type(
                        value=value if value is not None else "",
                        type_name=str(type_name),
                        field_name=col,
                        file_path=path,
                        line_idx=line_idx,
                    )
                    if coerced is not None:
                        values_by_column.setdefault(col, set()).add(coerced)
                for col in tracked_columns:
                    idx = index_by_name.get(col)
                    if idx is None:
                        continue
                    raw_value = str(row[idx]).strip()
                    if raw_value:
                        values_by_column.setdefault(col, set()).add(raw_value)
        else:
            expected_cols: Optional[int] = None
            columns_count = 0
            for line_idx, row in enumerate(reader_raw, start=1):
                if not row:
                    continue
                if expected_cols is None:
                    expected_cols = len(row)
                    columns_count = len(row)
                    if columns_count < min_columns:
                        errors.append(
                            f"{path}: expected at least {min_columns} column(s) for '{key}', got {columns_count}"
                        )
                elif len(row) != expected_cols:
                    errors.append(
                        f"{path}: inconsistent number of columns at line {line_idx} "
                        f"(expected {expected_cols}, got {len(row)})"
                    )
                    continue
                row_count += 1
                if first_column_role == "gene_id":
                    first_value = str(row[0]).strip() if columns_count >= 1 else ""
                    if not first_value:
                        errors.append(
                            f"{path}: line {line_idx} has empty gene identifier in first column"
                        )
                    elif unique_first_column:
                        if first_value in first_column_seen:
                            errors.append(
                                f"{path}: duplicated gene identifier '{first_value}' in first column"
                            )
                        else:
                            first_column_seen.add(first_value)
                elif first_column_role == "expression_column_id":
                    first_value = str(row[0]).strip() if columns_count >= 1 else ""
                    if not first_value:
                        errors.append(
                            f"{path}: line {line_idx} has empty expression-column identifier in first column"
                        )
                    else:
                        first_column_values.add(first_value)
                        if unique_first_column:
                            if first_value in first_column_seen:
                                errors.append(
                                    f"{path}: duplicated expression-column identifier '{first_value}' in first column"
                                )
                            else:
                                first_column_seen.add(first_value)
                if data_columns_type == "float" and columns_count > 1:
                    for col_idx, raw_value in enumerate(row[1:], start=2):
                        value = str(raw_value).strip()
                        data_cells_total += 1
                        if value == "":
                            if len(data_non_numeric_samples) < 5:
                                data_non_numeric_samples.append(
                                    f"line {line_idx}, col {col_idx}: <empty>"
                                )
                            continue
                        try:
                            float(value)
                            data_cells_numeric += 1
                        except Exception:  # noqa: BLE001
                            if len(data_non_numeric_samples) < 5:
                                data_non_numeric_samples.append(
                                    f"line {line_idx}, col {col_idx}: {value!r}"
                                )
            if expected_cols is None:
                columns_count = 0

    if row_count < min_rows:
        errors.append(
            f"{path}: expected at least {min_rows} row(s) for '{key}', got {row_count}"
        )
    if columns_count and columns_count < min_columns:
        errors.append(
            f"{path}: expected at least {min_columns} column(s) for '{key}', got {columns_count}"
        )
    if data_columns_type == "float" and columns_count > 1:
        if data_cells_total <= 0:
            errors.append(
                f"{path}: expected numeric values in data columns for '{key}', but found none"
            )
        else:
            numeric_fraction = data_cells_numeric / data_cells_total
            if numeric_fraction < data_numeric_min_fraction:
                errors.append(
                    f"{path}: only {numeric_fraction:.3f} of data cells are numeric for '{key}' "
                    f"(required >= {data_numeric_min_fraction:.3f}); "
                    f"examples: {data_non_numeric_samples[:5]}"
                )

    for rule in cross_checks:
        if not isinstance(rule, dict):
            continue
        kind = str(rule.get("kind", "")).strip()
        column = str(rule.get("column", "")).strip()
        if kind == "column_subset_expression_genes":
            present = values_by_column.get(column, set())
            unknown = sorted(present.difference(expression_genes))
            if unknown:
                sample = unknown[:5]
                errors.append(
                    f"{path}: column '{column}' contains identifiers not present in expression genes: {sample}"
                )
        elif kind == "column_subset_expression_columns":
            present = values_by_column.get(column, set())
            unknown = sorted(present.difference(expression_columns))
            if unknown:
                sample = unknown[:5]
                errors.append(
                    f"{path}: column '{column}' contains identifiers not present in expression columns: {sample}"
                )
        elif kind == "first_column_subset_expression_columns":
            unknown = sorted(first_column_values.difference(expression_columns))
            if unknown:
                sample = unknown[:5]
                errors.append(
                    f"{path}: first column contains identifiers not present in expression columns: {sample}"
                )
        elif kind == "column_subset_extra_column":
            other_input = str(rule.get("other_input", "")).strip()
            other_column = str(rule.get("other_column", "")).strip()
            if callable(extra_column_lookup):
                reference_values, lookup_warning = extra_column_lookup(
                    other_input,
                    other_column,
                )
            else:
                reference_values, lookup_warning = None, "cross-check lookup unavailable"
            if lookup_warning:
                warnings.append(
                    f"{path}: skipped cross-check for column '{column}' against "
                    f"extra '{other_input}.{other_column}': {lookup_warning}"
                )
                continue
            if reference_values is None:
                continue
            present = values_by_column.get(column, set())
            unknown = sorted(present.difference(reference_values))
            if unknown:
                sample = unknown[:5]
                errors.append(
                    f"{path}: column '{column}' contains identifiers not present in "
                    f"extra '{other_input}.{other_column}': {sample}"
                )
        elif kind == "row_count_matches_expression_columns":
            if row_count != expression_columns_count:
                errors.append(
                    f"{path}: row count ({row_count}) must match expression columns ({expression_columns_count})"
                )
        elif kind:
            warnings.append(f"[{key}] unknown cross-check ignored: {kind}")

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "rows": row_count,
            "columns": columns_count,
        },
    }


def _validate_text_list_with_spec(
    *,
    key: str,
    path: Path,
    spec: dict[str, Any],
    expression_genes: set[str],
) -> dict[str, Any]:
    min_rows = int(spec.get("min_rows", 0) or 0)
    cross_checks = spec.get("cross_checks", [])
    if not isinstance(cross_checks, list):
        cross_checks = []

    values: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            v = raw.strip()
            if v:
                values.append(v)

    errors: list[str] = []
    warnings: list[str] = []
    if len(values) < min_rows:
        errors.append(
            f"{path}: expected at least {min_rows} line(s) for '{key}', got {len(values)}"
        )

    for rule in cross_checks:
        if not isinstance(rule, dict):
            continue
        kind = str(rule.get("kind", "")).strip()
        if kind == "line_subset_expression_genes":
            unknown = sorted(set(values).difference(expression_genes))
            if unknown:
                errors.append(
                    f"{path}: contains identifiers not present in expression genes: {unknown[:5]}"
                )
        elif kind:
            warnings.append(f"[{key}] unknown cross-check ignored: {kind}")

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "rows": len(values),
            "columns": 1,
        },
    }


def _validate_dataset_inputs_by_specs(
    *,
    dataset: DatasetContext,
    input_specs: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str], list[str]]:
    expr_genes, expr_columns = _read_expression_axes(dataset.expression_matrix_path)
    expression_genes = set(expr_genes)
    expression_columns = set(expr_columns)
    results: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    extra_column_cache: dict[tuple[str, str], tuple[Optional[set[str]], Optional[str]]] = {}

    def lookup_extra_column_values(
        other_input: str,
        other_column: str,
    ) -> tuple[Optional[set[str]], Optional[str]]:
        cache_key = (other_input, other_column)
        if cache_key in extra_column_cache:
            return extra_column_cache[cache_key]

        if not other_input or not other_column:
            result = (
                None,
                "invalid cross-check reference (other_input/other_column required)",
            )
            extra_column_cache[cache_key] = result
            return result

        other_path = dataset.extras.get(other_input)
        if other_path is None:
            result = (None, f"extra '{other_input}' was not provided")
            extra_column_cache[cache_key] = result
            return result

        other_spec = input_specs.get(other_input, {})
        file_kind = (
            str(other_spec.get("file_kind", "tsv"))
            if isinstance(other_spec, dict)
            else "tsv"
        )
        if file_kind != "tsv":
            result = (
                None,
                f"extra '{other_input}' is not a TSV input and cannot be referenced by column",
            )
            extra_column_cache[cache_key] = result
            return result

        try:
            values = _read_tsv_column_values(
                other_path,
                other_spec if isinstance(other_spec, dict) else {},
                other_column,
            )
        except ValueError as exc:
            result = (None, str(exc))
        else:
            result = (values, None)
        extra_column_cache[cache_key] = result
        return result

    expr_spec = input_specs.get("expression_matrix", {})
    expr_result = _validate_tsv_file_with_spec(
        key="expression_matrix",
        path=dataset.expression_matrix_path,
        spec=expr_spec if isinstance(expr_spec, dict) else {},
        expression_genes=expression_genes,
        expression_columns=expression_columns,
        expression_columns_count=len(expr_columns),
        extra_column_lookup=lookup_extra_column_values,
    )
    results["expression_matrix"] = expr_result
    errors.extend(expr_result["errors"])
    warnings.extend(expr_result["warnings"])

    extras_results: dict[str, Any] = {}
    for key, extra_path in sorted(dataset.extras.items()):
        spec = input_specs.get(key, {})
        if extra_path is None:
            extras_results[key] = {
                "status": "missing",
                "errors": [],
                "warnings": [],
                "summary": None,
            }
            continue

        file_kind = (
            str(spec.get("file_kind", "tsv")) if isinstance(spec, dict) else "tsv"
        )
        if file_kind == "txt_list":
            res = _validate_text_list_with_spec(
                key=key,
                path=extra_path,
                spec=spec if isinstance(spec, dict) else {},
                expression_genes=expression_genes,
            )
        else:
            res = _validate_tsv_file_with_spec(
                key=key,
                path=extra_path,
                spec=spec if isinstance(spec, dict) else {},
                expression_genes=expression_genes,
                expression_columns=expression_columns,
                expression_columns_count=len(expr_columns),
                extra_column_lookup=lookup_extra_column_values,
            )
        extras_results[key] = res
        errors.extend(res["errors"])
        warnings.extend(res["warnings"])

    results["extras"] = extras_results
    return results, errors, warnings
