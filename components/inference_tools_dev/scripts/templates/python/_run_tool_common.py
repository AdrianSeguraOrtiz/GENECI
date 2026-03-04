"""Common runtime-contract helpers for Python inference tool wrappers."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional, Sequence


def load_params(params_path: Path) -> dict[str, Any]:
    with params_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("params.json must be a JSON object.")
    return data


def require_param_keys(raw_params: dict[str, Any], required_keys: set[str]) -> None:
    missing = sorted(required_keys.difference(raw_params.keys()))
    if missing:
        raise ValueError(f"Missing required params in params.json: {missing}")


def warn_unknown_params(raw_params: dict[str, Any], expected_keys: set[str]) -> None:
    unknown = sorted(set(raw_params.keys()).difference(expected_keys))
    if unknown:
        print(f"Warning: ignoring unknown params keys: {unknown}", file=sys.stderr)


def write_progress(
    progress_path: Path,
    *,
    status: str,
    percent: int,
    phase: str,
    message: str,
    completed: Optional[int] = None,
    total: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    payload: dict[str, Any] = {
        "status": status,
        "phase": phase,
        "percent": max(0, min(100, int(percent))),
        "message": message,
        "timestamp": time.time(),
    }
    if completed is not None:
        payload["completed"] = int(completed)
    if total is not None:
        payload["total"] = int(total)
    if error is not None:
        payload["error"] = error

    tmp_path = progress_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True)
    tmp_path.replace(progress_path)


def validate_runtime_inputs(
    *,
    input_path: Path,
    params_path: Path,
    extra_dir: Path,
    threads: int,
    required_paths: Optional[Sequence[Path]] = None,
) -> None:
    if threads <= 0:
        raise ValueError("--threads must be a positive integer.")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not params_path.exists():
        raise FileNotFoundError(f"Params file not found: {params_path}")
    if not extra_dir.exists():
        raise FileNotFoundError(f"Extra directory not found: {extra_dir}")

    for path in required_paths or ():
        if not path.exists():
            raise FileNotFoundError(f"Required runtime file not found: {path}")


def optional_extra_file(extra_dir: Path, filename: str) -> Optional[Path]:
    path = extra_dir / filename
    return path if path.exists() else None


def require_extra_file(extra_dir: Path, filename: str, label: str) -> Path:
    path = extra_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required extra input '{label}' not found in {extra_dir}. "
            f"Expected file: {filename}"
        )
    return path


def tail_text(path: Path, max_lines: int = 40) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])
