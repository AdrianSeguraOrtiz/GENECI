"""Shared types, constants, and low-level IO helpers for infer-network-v2."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

DEFAULT_OUTPUT_DIR = Path("./inferred_networks_v2")
CATALOG_ROOT = Path(__file__).resolve().parents[4] / "inference_catalog"
INPUT_SPECS_DIR = CATALOG_ROOT / "input_specs"
NETWORK_REQUIRED_COLUMNS = ["source", "target", "score", "sign", "evidence", "context"]
PREFLIGHT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class DatasetContext:
    dataset_id: str
    column_kind: str
    expression_profile: str
    genes: int
    columns: int
    expression_matrix_path: Path
    extras: dict[str, Optional[Path]]


@dataclass(frozen=True)
class SchemaConstraints:
    column_kinds: set[str]
    expression_profiles: set[str]
    assumptions: set[str]
    extra_input_keys: set[str]
    extra_input_filenames: dict[str, str]


@dataclass(frozen=True)
class ToolPlanItem:
    tool_id: str
    run_id: str
    image: str
    threads: int
    ram_gb: float
    eta_seconds: float
    eta_source: str
    output_dir: str
    group_label: Optional[str] = None


@dataclass(frozen=True)
class PlanWave:
    index: int
    threads_used: int
    ram_gb_used: float
    eta_seconds: float
    tasks: list[ToolPlanItem]


@dataclass(frozen=True)
class ToolRuntimeIO:
    tool_id: str
    run_id: str
    tool_dir: Path
    io_dir: Path
    out_dir: Path
    progress_file: Path
    params_file: Path


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_id: str
    status: str
    exit_code: int
    duration_seconds: float
    network_path: Optional[str]
    progress_path: Optional[str]
    logs_path: Optional[str]
    error: Optional[str]


@dataclass
class RunningTool:
    tool_id: str
    container_id: str
    started_at: float
    progress_file: Path
    last_snapshot: Optional[tuple[int, str, str, str]] = None


class ParamValidationError(ValueError):
    """Raised when a tool parameter value does not match its ToolSpec definition."""


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


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    return path


def _detect_host_ram_gb() -> float:
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    kib = int(parts[1])
                    return kib / (1024 * 1024)
    return 8.0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=True)
        fh.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task_eta_note(eta_source: str) -> Optional[str]:
    if eta_source == "fallback_no_cost":
        return "No cost profile was found; ETA is a conservative fallback estimate."
    if eta_source == "fallback_invalid_cost":
        return "Cost profile was invalid or unusable; ETA is a conservative fallback estimate."
    return None


def _slugify_token(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    slug = slug.strip("_")
    return slug or "group"
