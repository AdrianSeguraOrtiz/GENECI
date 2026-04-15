"""Network output merging and normalization helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Optional

from .shared import NETWORK_REQUIRED_COLUMNS, ToolExecutionResult


def _format_score(value: float) -> str:
    return format(float(value), ".12g")


def _read_network_rows(path: Path, tool_id: str) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size <= 0:
        raise ValueError(
            f"[{tool_id}] network.csv was not generated or is empty: {path}"
        )

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        missing = [col for col in NETWORK_REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(
                f"[{tool_id}] network.csv is missing required columns: {missing}"
            )

        for idx, row in enumerate(reader, start=2):
            try:
                score = float(row["score"])
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    f"[{tool_id}] invalid numeric score at network.csv line {idx}: {row.get('score')!r}"
                ) from exc

            if score == 0.0:
                continue

            rows.append(
                {
                    "source": str(row["source"]),
                    "target": str(row["target"]),
                    "score": score,
                    "sign": str(row["sign"]),
                    "evidence": str(row["evidence"]),
                    "context": str(row["context"]),
                }
            )

    return rows


def _write_network_rows(
    *,
    path: Path,
    rows: list[dict[str, Any]],
    include_tool_id: bool,
) -> None:
    fieldnames = list(NETWORK_REQUIRED_COLUMNS)
    if include_tool_id:
        fieldnames.append("tool_id")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out_row = {
                "source": row["source"],
                "target": row["target"],
                "score": _format_score(float(row["score"])),
                "sign": row["sign"],
                "evidence": row["evidence"],
                "context": row["context"],
            }
            if include_tool_id:
                out_row["tool_id"] = row["tool_id"]
            writer.writerow(out_row)


def _merge_network_outputs(
    *,
    run_dir: Path,
    execution_results: dict[str, ToolExecutionResult],
    warnings: list[str],
) -> tuple[
    dict[str, ToolExecutionResult], dict[str, int], Optional[Path], Optional[Path]
]:
    updated = dict(execution_results)
    merged_raw_rows: list[dict[str, Any]] = []
    merged_norm_rows: list[dict[str, Any]] = []
    per_tool_rows: dict[str, int] = {}
    had_completed_network_output = False

    for tool_id in sorted(updated.keys()):
        result = updated[tool_id]
        if result.status != "completed" or not result.network_path:
            continue
        had_completed_network_output = True

        network_path = Path(result.network_path)
        try:
            rows = _read_network_rows(network_path, tool_id=tool_id)
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"[{tool_id}] invalid network output, tool marked as failed: {exc}"
            )
            updated[tool_id] = ToolExecutionResult(
                tool_id=result.tool_id,
                status="failed",
                exit_code=result.exit_code,
                duration_seconds=result.duration_seconds,
                network_path=result.network_path,
                progress_path=result.progress_path,
                logs_path=result.logs_path,
                error=str(exc),
            )
            continue

        if not rows:
            warnings.append(
                f"[{tool_id}] network output contains no non-zero edges; empty network kept as a valid result."
            )
            per_tool_rows[tool_id] = 0
            continue

        scores = [float(row["score"]) for row in rows]
        min_score = min(scores)
        max_score = max(scores)
        if max_score > min_score:
            norm_scores = [
                (score - min_score) / (max_score - min_score) for score in scores
            ]
        else:
            norm_scores = [1.0 for _ in scores]

        tool_norm_rows: list[dict[str, Any]] = []
        for row, normalized in zip(rows, norm_scores):
            raw_row = dict(row)
            raw_row["tool_id"] = tool_id
            merged_raw_rows.append(raw_row)

            norm_row = dict(row)
            norm_row["score"] = float(normalized)
            norm_row["tool_id"] = tool_id
            merged_norm_rows.append(norm_row)

            tool_norm_rows.append(
                {
                    "source": row["source"],
                    "target": row["target"],
                    "score": float(normalized),
                    "sign": row["sign"],
                    "evidence": row["evidence"],
                    "context": row["context"],
                }
            )

        tool_norm_path = network_path.parent / "network.normalized.csv"
        _write_network_rows(
            path=tool_norm_path, rows=tool_norm_rows, include_tool_id=False
        )
        per_tool_rows[tool_id] = len(rows)

    merged_raw_path: Optional[Path] = None
    merged_norm_path: Optional[Path] = None

    if merged_raw_rows or had_completed_network_output:
        merged_raw_path = run_dir / "merged_network_raw.csv"
        _write_network_rows(
            path=merged_raw_path, rows=merged_raw_rows, include_tool_id=True
        )

    if merged_norm_rows or had_completed_network_output:
        merged_norm_path = run_dir / "merged_network_normalized.csv"
        _write_network_rows(
            path=merged_norm_path, rows=merged_norm_rows, include_tool_id=True
        )

    return updated, per_tool_rows, merged_raw_path, merged_norm_path
