"""GENIE3 wrapper for the inference_tools execution contract.

This wrapper assumes params.json is already resolved/validated by the orchestrator.
It only enforces minimal runtime checks (paths, basic param presence/types).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _arboreto_common import (
    infer_arboreto_local,
    load_tf_list,
    read_expression_tsv,
    to_standard_network,
    validate_inferred_columns,
)
from _run_tool_common import (
    load_params,
    require_param_keys,
    validate_runtime_inputs,
    write_progress,
)


def _resolve_params(
    raw_params: dict[str, Any]
) -> tuple[str, dict[str, Any], int | None, int | None]:
    required_keys = {"regressor_type", "regressor_kwargs", "limit", "seed"}
    require_param_keys(raw_params, required_keys)

    regressor_type = raw_params["regressor_type"]
    regressor_kwargs = raw_params["regressor_kwargs"]
    limit = raw_params["limit"]
    seed = raw_params["seed"]

    if not isinstance(regressor_type, str):
        raise ValueError("regressor_type must be a string.")
    regressor_type = regressor_type.upper()
    if regressor_type not in {"RF", "ET"}:
        raise ValueError("regressor_type must be one of: RF, ET.")

    if not isinstance(regressor_kwargs, dict):
        raise ValueError("regressor_kwargs must be an object/dict.")
    if limit is not None and not isinstance(limit, int):
        raise ValueError("limit must be an integer or null.")
    if seed is not None and not isinstance(seed, int):
        raise ValueError("seed must be an integer or null.")

    return regressor_type, regressor_kwargs, limit, seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--extra", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    validate_runtime_inputs(
        input_path=args.input,
        params_path=args.params,
        extra_dir=args.extra,
        threads=args.threads,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    progress_path = args.output_dir / "progress.json"
    write_progress(
        progress_path,
        status="running",
        percent=0,
        phase="init",
        message="Initializing",
    )

    try:
        raw_params = load_params(args.params)
        regressor_type, regressor_kwargs, limit, seed = _resolve_params(raw_params)

        write_progress(
            progress_path,
            status="running",
            percent=5,
            phase="load_input",
            message="Loading expression and extra inputs",
        )
        expression_data = read_expression_tsv(args.input)
        tf_names = load_tf_list(args.extra) or "all"

        write_progress(
            progress_path,
            status="running",
            percent=10,
            phase="inference",
            message="Starting inference",
        )

        def _on_partition_complete(completed: int, total: int) -> None:
            pct = 10 + int((completed / max(1, total)) * 85)
            write_progress(
                progress_path,
                status="running",
                percent=pct,
                phase="inference",
                message="Inferring network",
                completed=completed,
                total=total,
            )

        inferred = infer_arboreto_local(
            expression_data=expression_data,
            tf_names=tf_names,
            regressor_type=regressor_type,
            regressor_kwargs=regressor_kwargs,
            limit=limit,
            seed=seed,
            threads=args.threads,
            on_partition_complete=_on_partition_complete,
        )
        validate_inferred_columns(inferred)

        write_progress(
            progress_path,
            status="running",
            percent=96,
            phase="write_output",
            message="Writing network.csv",
        )

        out_df = to_standard_network(inferred)
        out_df.to_csv(args.output_dir / "network.csv", index=False)

        write_progress(
            progress_path,
            status="completed",
            percent=100,
            phase="done",
            message="Inference finished",
            completed=len(out_df),
            total=len(out_df),
        )
    except Exception as exc:
        write_progress(
            progress_path,
            status="failed",
            percent=100,
            phase="failed",
            message="Inference failed",
            error=str(exc),
        )
        raise


if __name__ == "__main__":
    main()
