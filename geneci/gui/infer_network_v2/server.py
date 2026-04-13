"""Local web GUI for infer-network-v2."""

from __future__ import annotations

import copy
import csv
import json
import tempfile
import threading
import traceback
import uuid
import webbrowser
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from geneci.core.commands.infer_network_v2 import (
    _inspect_expression_tsv,
    _load_input_specs,
    _load_schema_constraints,
    _resolve_catalog_paths,
    plan_infer_network_new,
    preflight_infer_network_new,
    run_infer_network_new_plan,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
GUI_TMP_ROOT = Path(tempfile.gettempdir()) / "geneci_gui" / "infer_network_v2"
MAX_TEXT_PREVIEW_BYTES = 256 * 1024
MAX_TABLE_PREVIEW_ROWS = 400


@dataclass
class GuiJob:
    job_id: str
    created_at: str
    status: str
    request_dir: str
    output_dir: str
    stage: str = "draft"
    run_dir: Optional[str] = None
    dataset_manifest_path: Optional[str] = None
    tools_params_path: Optional[str] = None
    preflight_report_path: Optional[str] = None
    run_report_path: Optional[str] = None
    plan_path: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class GuiState:
    jobs: dict[str, GuiJob] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)


STATE = GuiState()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_tools_bootstrap() -> dict[str, Any]:
    tools_root, schemas_dir = _resolve_catalog_paths()
    constraints = _load_schema_constraints(schemas_dir)
    input_specs = _load_input_specs()
    expr_spec = input_specs.get("expression_matrix", {})

    extra_examples = {
        "groups": "sample\tcluster\nS1\tA\nS2\tB",
        "lineage_tree": "child\tparent\tgain_rate\tloss_rate\nC2\tC1\t0.2\t0.1",
        "tf_list": "SOX2\nMYC\nTP53",
        "prior_grn_by_group": "group\tsource\ttarget\tscore\nA\tG1\tG2\t0.82\nB\tG1\tG3\t0.41",
    }

    tools: list[dict[str, Any]] = []
    for toolspec_path in sorted(tools_root.glob("*/toolspec.json")):
        tool_dir = toolspec_path.parent
        tool_id = tool_dir.name
        with toolspec_path.open("r", encoding="utf-8") as fh:
            toolspec = json.load(fh)

        raw_params = toolspec.get("params", {})
        params_schema = raw_params if isinstance(raw_params, dict) else {}
        defaults = {
            key: _default_for_param(param_def)
            for key, param_def in params_schema.items()
            if isinstance(param_def, dict)
        }

        extra_inputs = toolspec.get("extra_inputs", {})
        required_extras = []
        optional_extras = []
        conditional_required_extras = []
        if isinstance(extra_inputs, dict):
            req = extra_inputs.get("required", [])
            opt = extra_inputs.get("optional", [])
            cond = extra_inputs.get("conditional_required", [])
            if isinstance(req, list):
                required_extras = [x for x in req if isinstance(x, str)]
            if isinstance(opt, list):
                optional_extras = [x for x in opt if isinstance(x, str)]
            if isinstance(cond, list):
                conditional_required_extras = [
                    item for item in cond if isinstance(item, dict)
                ]

        tools.append(
            {
                "tool_id": tool_id,
                "name": str(toolspec.get("name", tool_id)),
                "assumes": str(toolspec.get("assumes", "")),
                "accepts": [
                    x for x in toolspec.get("accepts", []) if isinstance(x, str)
                ],
                "required_extras": required_extras,
                "optional_extras": optional_extras,
                "conditional_required_extras": conditional_required_extras,
                "publication": (
                    [
                        str(x)
                        for x in toolspec.get("publication", [])
                        if isinstance(x, str)
                    ]
                    if isinstance(toolspec.get("publication"), list)
                    else (
                        [str(toolspec.get("publication"))]
                        if toolspec.get("publication")
                        else []
                    )
                ),
                "first_author": str(toolspec.get("first_author", "")),
                "implementation_url": str(toolspec.get("implementation_url", "")),
                "docker_image": str(toolspec.get("docker_image", "")),
                "outputs": toolspec.get("outputs", {}),
                "progress": toolspec.get("progress", {}),
                "params_schema": params_schema,
                "default_params": defaults,
            }
        )

    return {
        "column_kinds": sorted(constraints.column_kinds),
        "expression_profiles": sorted(constraints.expression_profiles),
        "dataset_input_help": {
            "expression_matrix": {
                "description": str(expr_spec.get("description", "")),
                "example": str(
                    expr_spec.get(
                        "example",
                        "gene\tcell_1\tcell_2\nG1\t0.12\t0.20\nG2\t1.30\t0.95",
                    )
                ),
                "file_kind": str(expr_spec.get("file_kind", "tsv")),
                "delimiter": str(expr_spec.get("delimiter", "\t")),
                "header": bool(expr_spec.get("header", True)),
                "min_rows": int(expr_spec.get("min_rows", 1) or 1),
                "min_columns": int(expr_spec.get("min_columns", 2) or 2),
                "required_columns": [
                    str(col)
                    for col in expr_spec.get("required_columns", [])
                    if isinstance(col, str)
                ],
                "column_types": (
                    expr_spec.get("column_types", {})
                    if isinstance(expr_spec.get("column_types", {}), dict)
                    else {}
                ),
                "first_column_role": str(expr_spec.get("first_column_role", "none")),
                "first_column_disallowed_names": [
                    str(x)
                    for x in expr_spec.get("first_column_disallowed_names", [])
                    if isinstance(x, str)
                ],
                "unique_first_column": bool(
                    expr_spec.get("unique_first_column", False)
                ),
                "data_columns_type": str(expr_spec.get("data_columns_type", "any")),
                "data_numeric_min_fraction": float(
                    expr_spec.get("data_numeric_min_fraction", 1.0) or 1.0
                ),
            }
        },
        "extra_inputs": [
            {
                "key": key,
                "default_filename": constraints.extra_input_filenames.get(
                    key, f"{key}.tsv"
                ),
                "description": str(input_specs.get(key, {}).get("description", "")),
                "example": str(
                    input_specs.get(key, {}).get("example", extra_examples.get(key, ""))
                ),
                "file_kind": str(input_specs.get(key, {}).get("file_kind", "tsv")),
                "delimiter": str(input_specs.get(key, {}).get("delimiter", "\t")),
                "header": bool(input_specs.get(key, {}).get("header", True)),
                "min_rows": int(input_specs.get(key, {}).get("min_rows", 0) or 0),
                "min_columns": int(input_specs.get(key, {}).get("min_columns", 1) or 1),
                "required_columns": [
                    str(col)
                    for col in input_specs.get(key, {}).get("required_columns", [])
                    if isinstance(col, str)
                ],
                "column_types": (
                    input_specs.get(key, {}).get("column_types", {})
                    if isinstance(
                        input_specs.get(key, {}).get("column_types", {}), dict
                    )
                    else {}
                ),
                "first_column_role": str(
                    input_specs.get(key, {}).get("first_column_role", "none")
                ),
                "first_column_disallowed_names": [
                    str(x)
                    for x in input_specs.get(key, {}).get(
                        "first_column_disallowed_names", []
                    )
                    if isinstance(x, str)
                ],
                "unique_first_column": bool(
                    input_specs.get(key, {}).get("unique_first_column", False)
                ),
                "data_columns_type": str(
                    input_specs.get(key, {}).get("data_columns_type", "any")
                ),
                "data_numeric_min_fraction": float(
                    input_specs.get(key, {}).get("data_numeric_min_fraction", 1.0)
                    or 1.0
                ),
            }
            for key in sorted(constraints.extra_input_keys)
        ],
        "tools": tools,
    }


def _default_for_param(param_def: dict[str, Any]) -> Any:
    if "default" in param_def:
        return copy.deepcopy(param_def.get("default"))

    param_type = param_def.get("type")
    if param_type == "object":
        properties = param_def.get("properties", {})
        if not isinstance(properties, dict):
            return {}
        out: dict[str, Any] = {}
        for key, sub_def in properties.items():
            if not isinstance(sub_def, dict):
                continue
            has_default = "default" in sub_def
            is_required = bool(sub_def.get("required"))
            if has_default or is_required:
                out[key] = _default_for_param(sub_def)
        return out

    if param_type == "array":
        return []

    return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return float(value)


def _safe_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return int(value)


def _save_upload(upload: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    upload.file.seek(0)
    with destination.open("wb") as fh:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)


def _normalize_runs(raw_runs: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_runs, list) or not raw_runs:
        raise ValueError("runs must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for idx, raw in enumerate(raw_runs, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"runs[{idx}] must be an object")

        tool_id = str(raw.get("tool_id", "")).strip()
        if not tool_id:
            raise ValueError(f"runs[{idx}].tool_id is required")

        run_id_raw = raw.get("run_id")
        if run_id_raw is None or (
            isinstance(run_id_raw, str) and not run_id_raw.strip()
        ):
            run_id = f"{tool_id}__{idx:02d}"
        elif isinstance(run_id_raw, str):
            run_id = run_id_raw.strip()
        else:
            raise ValueError(f"runs[{idx}].run_id must be string when provided")

        if run_id in seen_ids:
            raise ValueError(f"Duplicate run_id: {run_id}")
        seen_ids.add(run_id)

        params = raw.get("params", {})
        if not isinstance(params, dict):
            raise ValueError(f"runs[{idx}].params must be an object")

        normalized.append(
            {
                "run_id": run_id,
                "tool_id": tool_id,
                "params": params,
            }
        )

    return normalized


def _build_dataset_manifest_file(
    *,
    config: dict[str, Any],
    form: Any,
    request_dir: Path,
    bootstrap: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any]]:
    dataset_cfg = config.get("dataset")
    if not isinstance(dataset_cfg, dict):
        raise ValueError("config.dataset must be an object")

    options_cfg = config.get("options")
    if options_cfg is None:
        options_cfg = {}
    if not isinstance(options_cfg, dict):
        raise ValueError("config.options must be an object when provided")

    dataset_id = str(dataset_cfg.get("id", "")).strip()
    if not dataset_id:
        raise ValueError("config.dataset.id is required")

    column_kind = str(dataset_cfg.get("column_kind", "")).strip()
    if column_kind not in set(bootstrap["column_kinds"]):
        raise ValueError(
            f"config.dataset.column_kind must be one of {bootstrap['column_kinds']}"
        )

    expression_profile = str(dataset_cfg.get("expression_profile", "")).strip()
    if expression_profile not in set(bootstrap["expression_profiles"]):
        raise ValueError(
            "config.dataset.expression_profile must be one of "
            f"{bootstrap['expression_profiles']}"
        )

    expression_upload = form.get("expression_file")
    if expression_upload is None or not getattr(expression_upload, "filename", ""):
        raise ValueError("expression_file is required")

    inputs_dir = request_dir / "inputs"
    extras_dir = inputs_dir / "extra"
    expression_path = inputs_dir / "expression.tsv"
    _save_upload(expression_upload, expression_path)

    observed_genes, observed_columns = _inspect_expression_tsv(expression_path)
    genes = _safe_int(dataset_cfg.get("genes"), default=observed_genes)
    columns = _safe_int(dataset_cfg.get("columns"), default=observed_columns)

    if genes != observed_genes or columns != observed_columns:
        raise ValueError(
            "The provided genes/columns do not match the uploaded expression matrix: "
            f"provided={genes}x{columns}, observed={observed_genes}x{observed_columns}"
        )

    extras_payload: dict[str, Optional[str]] = {}
    extra_keys = [item["key"] for item in bootstrap["extra_inputs"]]
    extra_default_filenames = {
        item["key"]: item["default_filename"] for item in bootstrap["extra_inputs"]
    }
    for key in extra_keys:
        upload = form.get(f"extra__{key}")
        if upload is None or not getattr(upload, "filename", ""):
            extras_payload[key] = None
            continue
        filename = extra_default_filenames.get(key, f"{key}.tsv")
        destination = extras_dir / filename
        _save_upload(upload, destination)
        extras_payload[key] = str(Path("inputs") / "extra" / filename)

    dataset_manifest = {
        "schema_version": "1.0",
        "id": dataset_id,
        "dataset": {
            "spec": {
                "schema_version": "1.0",
                "id": dataset_id,
                "name": dataset_id,
                "expression": {
                    "column_kind": column_kind,
                    "expression_profile": expression_profile,
                    "genes": genes,
                    "columns": columns,
                },
                "organism": {"tax_id": 9606},
            },
            "expression_matrix": str(Path("inputs") / "expression.tsv"),
        },
        "extras": extras_payload,
    }

    dataset_manifest_path = request_dir / "dataset-manifest.json"

    dataset_manifest_path.write_text(
        json.dumps(dataset_manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return dataset_manifest_path, expression_path, options_cfg


def _write_tools_params_file(
    *,
    request_dir: Path,
    runs_raw: Any,
) -> Path:
    runs = _normalize_runs(runs_raw)
    tools_params = {"runs": runs}
    tools_params_path = request_dir / "tools_params.json"
    tools_params_path.write_text(
        json.dumps(tools_params, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return tools_params_path


def _job_payload(job: GuiJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "created_at": job.created_at,
        "status": job.status,
        "stage": job.stage,
        "request_dir": job.request_dir,
        "output_dir": job.output_dir,
        "run_dir": job.run_dir,
        "dataset_manifest_path": job.dataset_manifest_path,
        "tools_params_path": job.tools_params_path,
        "preflight_report_path": job.preflight_report_path,
        "run_report_path": job.run_report_path,
        "plan_path": job.plan_path,
        "error": job.error,
        "traceback": job.traceback,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


def _read_json_if_exists(path: Optional[str]) -> Optional[dict[str, Any]]:
    if not path:
        return None
    json_path = Path(path)
    if not json_path.exists() or not json_path.is_file():
        return None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    return data


def _collect_runtime_progress(*, run_dir: Optional[Path]) -> dict[str, Any]:
    if run_dir is None or not run_dir.exists() or not run_dir.is_dir():
        return {
            "tools": [],
            "summary": {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "running": 0,
                "pending": 0,
            },
        }

    status_by_tool: dict[str, str] = {}
    run_report = _read_json_if_exists(str(run_dir / "run_report.json"))
    if isinstance(run_report, dict):
        tools_payload = run_report.get("tools")
        if isinstance(tools_payload, dict):
            status_payload = tools_payload.get("status_by_tool")
            if isinstance(status_payload, dict):
                status_by_tool = {
                    str(tool_id): str(status)
                    for tool_id, status in status_payload.items()
                    if isinstance(tool_id, str)
                }

    tools_root = run_dir / "tools"
    tool_entries: list[dict[str, Any]] = []
    if tools_root.exists() and tools_root.is_dir():
        for tool_dir in sorted(tools_root.iterdir()):
            if not tool_dir.is_dir():
                continue
            run_id = tool_dir.name
            progress_file = tool_dir / "io" / "out" / "progress.json"
            percent = 0
            status = status_by_tool.get(run_id, "pending")
            phase = "pending"
            message = ""
            updated_at: Optional[str] = None

            if progress_file.exists() and progress_file.is_file():
                try:
                    payload = json.loads(progress_file.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    payload = {}
                percent = int(payload.get("percent", percent))
                status = str(payload.get("status", status))
                phase = str(payload.get("phase", phase))
                message = str(payload.get("message", ""))
                updated_at = (
                    datetime.fromtimestamp(
                        progress_file.stat().st_mtime, tz=timezone.utc
                    )
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            elif status in {"completed", "failed"}:
                percent = 100
                phase = "done" if status == "completed" else "failed"

            percent = max(0, min(100, int(percent)))
            normalized_status = status.lower().strip()
            if normalized_status not in {"pending", "running", "completed", "failed"}:
                normalized_status = "running" if percent > 0 else "pending"
            tool_entries.append(
                {
                    "run_id": run_id,
                    "percent": percent,
                    "status": normalized_status,
                    "phase": phase,
                    "message": message,
                    "updated_at": updated_at,
                }
            )

    summary = {
        "total": len(tool_entries),
        "completed": sum(1 for item in tool_entries if item["status"] == "completed"),
        "failed": sum(1 for item in tool_entries if item["status"] == "failed"),
        "running": sum(1 for item in tool_entries if item["status"] == "running"),
        "pending": sum(1 for item in tool_entries if item["status"] == "pending"),
    }
    return {"tools": tool_entries, "summary": summary}


def _bundle_sources(
    *,
    request_dir: Path,
    run_dir: Optional[Path],
    mode: str,
) -> list[tuple[str, Path]]:
    if mode not in {"light", "full"}:
        raise ValueError("mode must be one of: light, full")

    sources: list[tuple[str, Path]] = []

    request_candidates = [
        request_dir / "dataset-manifest.json",
        request_dir / "tools_params.json",
        request_dir / "preflight_report.json",
    ]
    for path in request_candidates:
        if path.exists() and path.is_file():
            sources.append((f"input/{path.name}", path))

    inputs_dir = request_dir / "inputs"
    if inputs_dir.exists() and inputs_dir.is_dir():
        for path in sorted(inputs_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(request_dir)
            sources.append((f"input/{rel.as_posix()}", path))

    if run_dir is None or not run_dir.exists() or not run_dir.is_dir():
        return sources

    if mode == "full":
        for path in sorted(run_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(run_dir)
            sources.append((f"run/{rel.as_posix()}", path))
    else:
        run_candidates = [
            run_dir / "plan.json",
            run_dir / "run_report.json",
            run_dir / "merged_network_raw.csv",
            run_dir / "merged_network_normalized.csv",
        ]
        for path in run_candidates:
            if path.exists() and path.is_file():
                rel = path.relative_to(run_dir)
                sources.append((f"run/{rel.as_posix()}", path))

        for path in sorted(run_dir.glob("tools/*/resolved_params.json")):
            if not path.is_file():
                continue
            rel = path.relative_to(run_dir)
            sources.append((f"run/{rel.as_posix()}", path))

    unique: dict[str, Path] = {}
    for virtual_path, source_path in sources:
        unique[virtual_path] = source_path
    return sorted(unique.items(), key=lambda item: item[0])


def _viewer_for_virtual_path(path: str) -> str:
    normalized = path.lower()
    basename = Path(normalized).name
    if normalized == "run/plan.json":
        return "plan"
    if normalized.endswith(".json"):
        return "json"
    if normalized.endswith(".csv"):
        return "table_csv"
    if normalized.endswith(".tsv"):
        return "table_tsv"
    if (
        normalized.endswith(".txt")
        or normalized.endswith(".log")
        or basename.endswith(".out")
        or basename.endswith(".err")
        or basename.endswith(".stderr")
        or basename.endswith(".stdout")
        or "log" in basename
    ):
        return "text"
    return "none"


def _build_bundle_entries(sources: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for virtual_path, source in sources:
        parts = virtual_path.split("/")
        for idx in range(1, len(parts)):
            dir_path = "/".join(parts[:idx])
            entries.setdefault(
                dir_path,
                {
                    "path": dir_path,
                    "kind": "dir",
                    "size_bytes": None,
                    "viewer": "none",
                    "visualizable": False,
                    "depth": max(0, len(parts[:idx]) - 1),
                },
            )

        viewer = _viewer_for_virtual_path(virtual_path)
        entries[virtual_path] = {
            "path": virtual_path,
            "kind": "file",
            "size_bytes": source.stat().st_size if source.exists() else None,
            "viewer": viewer,
            "visualizable": viewer != "none",
            "depth": max(0, len(parts) - 1),
        }

    return sorted(
        entries.values(),
        key=lambda item: (item["kind"] != "dir", item["path"]),
    )


def _resolve_virtual_source(
    *,
    sources: list[tuple[str, Path]],
    virtual_path: str,
) -> Optional[Path]:
    for candidate_path, source in sources:
        if candidate_path == virtual_path:
            return source
    return None


def _preview_table(
    *,
    source: Path,
    delimiter: str,
    max_rows: int,
) -> dict[str, Any]:
    headers: list[str] = []
    rows: list[list[str]] = []
    total_rows = 0

    with source.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        first = next(reader, None)
        if first is None:
            return {"headers": [], "rows": [], "total_rows": 0, "truncated": False}
        headers = [str(x) for x in first]
        for row in reader:
            total_rows += 1
            if len(rows) < max_rows:
                rows.append([str(x) for x in row])

    return {
        "headers": headers,
        "rows": rows,
        "total_rows": total_rows,
        "truncated": total_rows > len(rows),
    }


def _preview_text(source: Path, max_bytes: int) -> dict[str, Any]:
    with source.open("rb") as fh:
        raw = fh.read(max_bytes + 1)
    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    return {"text": text, "truncated": truncated, "size_bytes": source.stat().st_size}


def _is_probably_text(source: Path, sample_bytes: int = 4096) -> bool:
    try:
        with source.open("rb") as fh:
            raw = fh.read(sample_bytes)
    except Exception:  # noqa: BLE001
        return False
    if not raw:
        return True
    if b"\x00" in raw:
        return False
    return True


def _build_zip_bundle(
    *,
    zip_path: Path,
    sources: list[tuple[str, Path]],
) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for virtual_path, source in sources:
            if source.exists() and source.is_file():
                zf.write(source, arcname=virtual_path)
    return zip_path


def _run_job(
    *,
    job_id: str,
    action: str,
    options: dict[str, Any],
) -> None:
    with STATE.lock:
        job = STATE.jobs[job_id]
        job.status = "running"
        job.started_at = _utc_now()

    try:
        with STATE.lock:
            job = STATE.jobs[job_id]
            dataset_manifest_path = (
                Path(job.dataset_manifest_path) if job.dataset_manifest_path else None
            )
            tools_params_path = (
                Path(job.tools_params_path) if job.tools_params_path else None
            )
            output_dir = Path(job.output_dir)
            run_dir_existing = Path(job.run_dir) if job.run_dir else None

        if action == "preflight":
            if dataset_manifest_path is None:
                raise ValueError("Job is missing dataset_manifest_path")
            preflight_report = preflight_infer_network_new(
                dataset_manifest_path=dataset_manifest_path,
                tools_params_path=tools_params_path,
                strict=bool(options.get("strict", False)),
            )
            preflight_path = Path(job.request_dir) / "preflight_report.json"
            preflight_path.write_text(
                json.dumps(preflight_report, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "preflight_ok"
                job.preflight_report_path = str(preflight_path)
                job.finished_at = _utc_now()
            return

        if action == "plan":
            if dataset_manifest_path is None or tools_params_path is None:
                raise ValueError("Job is missing dataset/tools paths for planning")
            preflight_path = Path(job.request_dir) / "preflight_report.json"
            preflight_report = _read_json_if_exists(str(preflight_path))
            run_dir = plan_infer_network_new(
                dataset_manifest_path=dataset_manifest_path,
                tools_params_path=tools_params_path,
                output_dir=output_dir,
                max_cores=_safe_int(options.get("max_cores"), default=4),
                max_ram_gb=_safe_float(options.get("max_ram_gb")),
                planner=str(options.get("planner", "auto") or "auto"),
                planner_time_limit_seconds=float(
                    options.get("planner_time_limit_seconds", 10.0)
                ),
                strict=bool(options.get("strict", False)),
                preflight_report=preflight_report,
            )
            run_dir_resolved = run_dir.resolve()
            run_report_path = run_dir_resolved / "run_report.json"
            plan_path = run_dir_resolved / "plan.json"

            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "planned"
                job.run_dir = str(run_dir_resolved)
                job.run_report_path = (
                    str(run_report_path) if run_report_path.exists() else None
                )
                job.plan_path = str(plan_path) if plan_path.exists() else None
                job.finished_at = _utc_now()
            return

        if action == "run":
            if run_dir_existing is None:
                raise ValueError("Job has no planned run_dir to execute")
            run_dir = run_infer_network_new_plan(
                run_dir=run_dir_existing,
                progress_poll_seconds=float(options.get("progress_poll_seconds", 0.5)),
                strict=bool(options.get("strict", False)),
            )
            run_dir_resolved = run_dir.resolve()
            run_report_path = run_dir_resolved / "run_report.json"
            plan_path = run_dir_resolved / "plan.json"
            with STATE.lock:
                job = STATE.jobs[job_id]
                job.status = "completed"
                job.stage = "executed"
                job.run_dir = str(run_dir_resolved)
                job.run_report_path = (
                    str(run_report_path) if run_report_path.exists() else None
                )
                job.plan_path = str(plan_path) if plan_path.exists() else None
                job.finished_at = _utc_now()
            return

        raise ValueError(f"Unsupported job action: {action}")
    except Exception as exc:  # noqa: BLE001
        with STATE.lock:
            job = STATE.jobs[job_id]
            job.status = "failed"
            job.error = str(exc)
            job.traceback = traceback.format_exc(limit=30)
            job.finished_at = _utc_now()


def create_app() -> FastAPI:
    app = FastAPI(title="GENECI GUI - infer-network-v2")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    bootstrap = _load_tools_bootstrap()

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/infer-network-v2/bootstrap")
    async def api_bootstrap() -> JSONResponse:
        return JSONResponse(bootstrap)

    @app.get("/api/infer-network-v2/jobs")
    async def api_jobs() -> JSONResponse:
        with STATE.lock:
            jobs = [_job_payload(job) for job in STATE.jobs.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return JSONResponse({"jobs": jobs})

    @app.get("/api/infer-network-v2/jobs/{job_id}")
    async def api_job(job_id: str) -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            payload = _job_payload(job)

        run_report = _read_json_if_exists(payload.get("run_report_path"))
        preflight_report = _read_json_if_exists(payload.get("preflight_report_path"))
        run_dir = Path(payload["run_dir"]) if payload.get("run_dir") else None
        runtime_progress = _collect_runtime_progress(run_dir=run_dir)

        return JSONResponse(
            {
                "job": payload,
                "run_report": run_report,
                "preflight_report": preflight_report,
                "runtime_progress": runtime_progress,
            }
        )

    @app.get("/api/infer-network-v2/jobs/{job_id}/plan")
    async def api_job_plan(job_id: str) -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            plan_path = job.plan_path
            status = job.status

        plan = _read_json_if_exists(plan_path)
        if plan is None:
            return JSONResponse({"status": status, "plan": None})
        return JSONResponse({"status": status, "plan": plan, "plan_path": plan_path})

    @app.get("/api/infer-network-v2/jobs/{job_id}/files")
    async def api_job_files(
        job_id: str,
        mode: str = "light",
    ) -> JSONResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            run_dir = Path(job.run_dir) if job.run_dir else None
            status = job.status

        try:
            sources = _bundle_sources(
                request_dir=request_dir, run_dir=run_dir, mode=mode
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        entries = _build_bundle_entries(sources)
        return JSONResponse(
            {
                "status": status,
                "mode": mode,
                "entries": entries,
            }
        )

    @app.get("/api/infer-network-v2/jobs/{job_id}/file-content")
    async def api_job_file_content(
        job_id: str,
        path: str,
        mode: str = "light",
        max_rows: int = MAX_TABLE_PREVIEW_ROWS,
    ) -> JSONResponse:
        requested_path = str(path or "").strip().lstrip("/")
        if not requested_path:
            raise HTTPException(status_code=400, detail="path is required")

        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            run_dir = Path(job.run_dir) if job.run_dir else None

        try:
            sources = _bundle_sources(
                request_dir=request_dir, run_dir=run_dir, mode=mode
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        source = _resolve_virtual_source(sources=sources, virtual_path=requested_path)
        if source is None or not source.exists() or not source.is_file():
            raise HTTPException(
                status_code=404, detail=f"File not found in bundle: {requested_path}"
            )

        viewer = _viewer_for_virtual_path(requested_path)
        if viewer == "plan":
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": viewer,
                    "note": "Use the dedicated plan viewer panel.",
                }
            )
        if viewer == "json":
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
                text = json.dumps(payload, indent=2, ensure_ascii=True)
            except Exception:
                text = source.read_text(encoding="utf-8", errors="replace")
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "json",
                    "text": text,
                    "truncated": False,
                }
            )

        if viewer == "table_csv":
            table = _preview_table(
                source=source,
                delimiter=",",
                max_rows=max(1, min(int(max_rows), MAX_TABLE_PREVIEW_ROWS)),
            )
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "table_csv",
                    **table,
                }
            )

        if viewer == "table_tsv":
            table = _preview_table(
                source=source,
                delimiter="\t",
                max_rows=max(1, min(int(max_rows), MAX_TABLE_PREVIEW_ROWS)),
            )
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "table_tsv",
                    **table,
                }
            )

        if viewer == "text":
            text_preview = _preview_text(
                source=source, max_bytes=MAX_TEXT_PREVIEW_BYTES
            )
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "text",
                    **text_preview,
                }
            )

        # Fallback for unknown extensions that are plain text-like files.
        if _is_probably_text(source):
            text_preview = _preview_text(
                source=source, max_bytes=MAX_TEXT_PREVIEW_BYTES
            )
            return JSONResponse(
                {
                    "path": requested_path,
                    "viewer": "text",
                    **text_preview,
                }
            )

        raise HTTPException(
            status_code=400,
            detail=f"Preview is not available for this file type: {requested_path}",
        )

    @app.get("/api/infer-network-v2/jobs/{job_id}/bundle")
    async def api_job_bundle(
        job_id: str,
        mode: str = "light",
    ) -> FileResponse:
        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            request_dir = Path(job.request_dir)
            run_dir = Path(job.run_dir) if job.run_dir else None

        try:
            sources = _bundle_sources(
                request_dir=request_dir, run_dir=run_dir, mode=mode
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        zip_path = request_dir / f"{job_id}_bundle_{mode}.zip"
        _build_zip_bundle(zip_path=zip_path, sources=sources)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"geneci_{job_id}_{mode}.zip",
        )

    @app.post("/api/infer-network-v2/preflight")
    async def api_preflight(request: Request) -> JSONResponse:
        form = await request.form()
        config_raw = form.get("config")
        if not isinstance(config_raw, str) or not config_raw.strip():
            raise HTTPException(status_code=400, detail="config JSON is required")
        try:
            config = json.loads(config_raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    "config JSON is malformed at line "
                    f"{exc.lineno}, column {exc.colno}: {exc.msg}"
                ),
            ) from exc
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="config must be a JSON object")

        options = config.get("options")
        if options is None:
            options = {}
        if not isinstance(options, dict):
            raise HTTPException(
                status_code=400, detail="config.options must be an object"
            )

        output_dir_raw = str(
            options.get("output_dir", "./inferred_networks_v2")
        ).strip()
        if not output_dir_raw:
            output_dir_raw = "./inferred_networks_v2"
        output_dir = Path(output_dir_raw).resolve()

        job_id = uuid.uuid4().hex[:12]
        request_dir = (GUI_TMP_ROOT / job_id).resolve()
        request_dir.mkdir(parents=True, exist_ok=True)

        try:
            dataset_manifest_path, _expression_path, options_cfg = (
                _build_dataset_manifest_file(
                    config=config,
                    form=form,
                    request_dir=request_dir,
                    bootstrap=bootstrap,
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        job = GuiJob(
            job_id=job_id,
            created_at=_utc_now(),
            status="queued",
            stage="draft",
            request_dir=str(request_dir),
            output_dir=str(output_dir),
            dataset_manifest_path=str(dataset_manifest_path),
            tools_params_path=None,
            preflight_report_path=None,
        )
        with STATE.lock:
            STATE.jobs[job_id] = job

        worker = threading.Thread(
            target=_run_job,
            kwargs={
                "job_id": job_id,
                "action": "preflight",
                "options": options_cfg,
            },
            daemon=True,
        )
        worker.start()
        return JSONResponse(
            {
                "job_id": job_id,
                "status": "queued",
                "stage": "draft",
                "request_dir": str(request_dir),
                "dataset_manifest_path": str(dataset_manifest_path),
            }
        )

    @app.post("/api/infer-network-v2/plan")
    async def api_plan(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Request body must be a JSON object"
            )
        job_id = str(payload.get("job_id", "")).strip()
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        runs_raw = payload.get("runs")
        options = payload.get("options")
        if options is None:
            options = {}
        if not isinstance(options, dict):
            raise HTTPException(status_code=400, detail="options must be an object")

        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if job.status == "running":
                raise HTTPException(status_code=409, detail="Job is already running")
            if job.dataset_manifest_path is None:
                raise HTTPException(
                    status_code=400, detail="Job has no dataset manifest"
                )
            if job.stage not in {"preflight_ok", "planned", "executed"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job is not ready for planning (stage={job.stage})",
                )
            request_dir = Path(job.request_dir)
            output_dir = Path(job.output_dir)

        try:
            tools_params_path = _write_tools_params_file(
                request_dir=request_dir,
                runs_raw=runs_raw,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        with STATE.lock:
            job = STATE.jobs[job_id]
            job.status = "queued"
            job.stage = "preflight_ok"
            job.tools_params_path = str(tools_params_path)
            job.error = None
            job.traceback = None
            job.run_dir = None
            job.plan_path = None
            job.run_report_path = None

        options_cfg = dict(options)
        options_cfg.setdefault("output_dir", str(output_dir))
        worker = threading.Thread(
            target=_run_job,
            kwargs={
                "job_id": job_id,
                "action": "plan",
                "options": options_cfg,
            },
            daemon=True,
        )
        worker.start()
        return JSONResponse(
            {
                "job_id": job_id,
                "status": "queued",
                "stage": "preflight_ok",
                "tools_params_path": str(tools_params_path),
            }
        )

    @app.post("/api/infer-network-v2/run")
    async def api_run(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Request body must be a JSON object"
            )
        job_id = str(payload.get("job_id", "")).strip()
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        options = payload.get("options")
        if options is None:
            options = {}
        if not isinstance(options, dict):
            raise HTTPException(status_code=400, detail="options must be an object")

        with STATE.lock:
            job = STATE.jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            if job.status == "running":
                raise HTTPException(status_code=409, detail="Job is already running")
            if not job.run_dir or not job.plan_path:
                raise HTTPException(
                    status_code=400, detail="No planned run found for this job"
                )
            if job.stage not in {"planned", "executed"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job is not in planned state (stage={job.stage})",
                )
            job.status = "queued"
            job.error = None
            job.traceback = None

        worker = threading.Thread(
            target=_run_job,
            kwargs={
                "job_id": job_id,
                "action": "run",
                "options": options,
            },
            daemon=True,
        )
        worker.start()
        return JSONResponse({"job_id": job_id, "status": "queued", "stage": "planned"})

    return app


def run_server(*, host: str, port: int, open_browser: bool) -> None:
    app = create_app()

    if open_browser:
        url = f"http://{host}:{port}/"
        timer = threading.Timer(
            0.8, lambda: webbrowser.open(url, new=2, autoraise=True)
        )
        timer.daemon = True
        timer.start()

    uvicorn.run(app, host=host, port=port, log_level="info")
