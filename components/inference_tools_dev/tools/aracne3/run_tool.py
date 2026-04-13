"""
ARACNe3 wrapper for the inference_tools execution contract.

This wrapper assumes params.json is already resolved/validated by the orchestrator.
It only enforces minimal runtime checks (paths, basic param presence/types).
"""

import argparse
import csv
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from _run_tool_common import load_params as _load_params
from _run_tool_common import require_param_keys
from _run_tool_common import tail_text as _tail_text
from _run_tool_common import validate_runtime_inputs, warn_unknown_params
from _run_tool_common import write_progress as _write_progress

ARACNE_BIN = Path("/app/bin/ARACNe3_app_release")


def _resolve_params(raw_params: Dict[str, Any]) -> Dict[str, Any]:
    expected_keys = {
        "alpha",
        "x",
        "adaptive",
        "min_subnets",
        "method",
        "subsample",
        "no_alpha",
        "no_maxent",
        "seed",
    }
    require_param_keys(raw_params, expected_keys)
    warn_unknown_params(raw_params, expected_keys)

    alpha = raw_params["alpha"]
    x_value = raw_params["x"]
    adaptive = raw_params["adaptive"]
    min_subnets = raw_params["min_subnets"]
    method = raw_params["method"]
    subsample = raw_params["subsample"]
    no_alpha = raw_params["no_alpha"]
    no_maxent = raw_params["no_maxent"]
    seed = raw_params["seed"]

    if not isinstance(alpha, (int, float)):
        raise ValueError("alpha must be numeric.")
    alpha = float(alpha)
    if alpha <= 0 or alpha > 1:
        raise ValueError("alpha must be in (0, 1].")

    if not isinstance(x_value, int) or x_value < 1:
        raise ValueError("x must be an integer >= 1.")

    if not isinstance(adaptive, bool):
        raise ValueError("adaptive must be a boolean.")

    if not isinstance(min_subnets, int) or min_subnets < 0:
        raise ValueError("min_subnets must be an integer >= 0.")

    if not isinstance(method, str):
        raise ValueError("method must be a string.")
    method = method.upper()
    if method not in {"FDR", "FWER", "FPR"}:
        raise ValueError("method must be one of: FDR, FWER, FPR.")

    if not isinstance(subsample, (int, float)):
        raise ValueError("subsample must be numeric.")
    subsample = float(subsample)
    if subsample <= 0 or subsample > 1:
        raise ValueError("subsample must be in (0, 1].")

    if not isinstance(no_alpha, bool):
        raise ValueError("no_alpha must be a boolean.")
    if not isinstance(no_maxent, bool):
        raise ValueError("no_maxent must be a boolean.")

    if seed is not None:
        if not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be null or an integer >= 0.")

    return {
        "alpha": alpha,
        "x": x_value,
        "adaptive": adaptive,
        "min_subnets": min_subnets,
        "method": method,
        "subsample": subsample,
        "no_alpha": no_alpha,
        "no_maxent": no_maxent,
        "seed": seed,
    }


def _validate_inputs(
    input_path: Path, params_path: Path, extra_dir: Path, threads: int
) -> None:
    validate_runtime_inputs(
        input_path=input_path,
        params_path=params_path,
        extra_dir=extra_dir,
        threads=threads,
        required_paths=[ARACNE_BIN],
    )


def _count_subnets(subnets_dir: Path, runid: str) -> int:
    if not subnets_dir.exists():
        return 0
    return sum(1 for _ in subnets_dir.glob(f"subnet*_{runid}.tsv"))


def _build_aracne_cmd(
    *,
    input_path: Path,
    tf_path: Path,
    output_dir: Path,
    threads: int,
    runid: str,
    params: Dict[str, Any],
) -> list[str]:
    cmd = [
        str(ARACNE_BIN),
        "-e",
        str(input_path),
        "-r",
        str(tf_path),
        "-o",
        str(output_dir),
        "-x",
        str(params["x"]),
        "--threads",
        str(threads),
        "--runid",
        runid,
        "--alpha",
        str(params["alpha"]),
        "--subsample",
        str(params["subsample"]),
        "--min-subnets",
        str(params["min_subnets"]),
    ]

    method = params["method"]
    if method == "FWER":
        cmd.append("--FWER")
    elif method == "FPR":
        cmd.append("--FPR")

    if params["adaptive"]:
        cmd.append("--adaptive")
    if params["no_alpha"]:
        cmd.append("--noalpha")
    if params["no_maxent"]:
        cmd.append("--noMaxEnt")

    if params["seed"] is not None:
        cmd.extend(["--seed", str(params["seed"])])

    return cmd


def _run_aracne(
    *,
    input_path: Path,
    tf_path: Path,
    output_dir: Path,
    threads: int,
    params: Dict[str, Any],
    progress_path: Path,
) -> Path:
    runid = f"geneci_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    cmd = _build_aracne_cmd(
        input_path=input_path,
        tf_path=tf_path,
        output_dir=output_dir,
        threads=threads,
        runid=runid,
        params=params,
    )

    stdout_path = output_dir / "aracne3.stdout.log"
    stderr_path = output_dir / "aracne3.stderr.log"

    total_subnets = params["x"] if not params["adaptive"] else None
    last_completed = -1
    saw_consolidation = False

    with (
        stdout_path.open("w", encoding="utf-8") as stdout_fh,
        stderr_path.open("w", encoding="utf-8") as stderr_fh,
    ):
        process = subprocess.Popen(
            cmd,
            cwd=str(output_dir),
            stdout=stdout_fh,
            stderr=stderr_fh,
            text=True,
        )

        while True:
            return_code = process.poll()

            if total_subnets is not None:
                completed = _count_subnets(output_dir / "subnets", runid)
                if completed != last_completed:
                    pct = 10 + int(
                        (min(completed, total_subnets) / max(1, total_subnets)) * 80
                    )
                    _write_progress(
                        progress_path,
                        status="running",
                        percent=min(90, pct),
                        phase="inference",
                        message=f"Generated subnetworks: {completed}/{total_subnets}",
                        completed=completed,
                        total=total_subnets,
                    )
                    last_completed = completed
            elif last_completed < 0:
                _write_progress(
                    progress_path,
                    status="running",
                    percent=50,
                    phase="inference",
                    message="Inferring network (adaptive mode, unknown total iterations)",
                )
                last_completed = 0

            consolidated_tsv = output_dir / f"consolidated-net_{runid}.tsv"
            if consolidated_tsv.exists() and not saw_consolidation:
                _write_progress(
                    progress_path,
                    status="running",
                    percent=92,
                    phase="consolidate",
                    message="Consolidating subnetworks",
                )
                saw_consolidation = True

            if return_code is not None:
                break
            time.sleep(0.5)

    if process.returncode != 0:
        stdout_tail = _tail_text(stdout_path)
        stderr_tail = _tail_text(stderr_path)
        details = []
        if stdout_tail:
            details.append(f"stdout tail:\n{stdout_tail}")
        if stderr_tail:
            details.append(f"stderr tail:\n{stderr_tail}")
        details_text = "\n\n".join(details)
        if details_text:
            raise RuntimeError(
                f"ARACNe3 failed with exit code {process.returncode}.\n\n{details_text}"
            )
        raise RuntimeError(f"ARACNe3 failed with exit code {process.returncode}.")

    consolidated_tsv = output_dir / f"consolidated-net_{runid}.tsv"
    if not consolidated_tsv.exists():
        raise FileNotFoundError(
            f"Expected consolidated network not found: {consolidated_tsv}"
        )

    return consolidated_tsv


def _convert_consolidated_to_network(consolidated_tsv: Path, network_csv: Path) -> int:
    required_columns = {"regulator.values", "target.values", "mi.values"}

    with consolidated_tsv.open("r", encoding="utf-8", newline="") as in_fh:
        reader = csv.DictReader(in_fh, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("Consolidated output is empty or missing header.")

        missing = sorted(required_columns.difference(reader.fieldnames))
        if missing:
            raise ValueError(
                "Unexpected consolidated output columns. "
                f"Missing required columns: {missing}. "
                f"Found: {reader.fieldnames}"
            )

        with network_csv.open("w", encoding="utf-8", newline="") as out_fh:
            writer = csv.DictWriter(
                out_fh,
                fieldnames=["source", "target", "score", "sign", "evidence", "context"],
            )
            writer.writeheader()

            rows_written = 0
            for idx, row in enumerate(reader, start=2):
                source = (row.get("regulator.values") or "").strip()
                target = (row.get("target.values") or "").strip()
                score_raw = (row.get("mi.values") or "").strip()

                if not source or not target:
                    continue

                try:
                    score = float(score_raw)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid mi.values at line {idx} in {consolidated_tsv.name}: {score_raw!r}"
                    ) from exc

                if score == 0.0:
                    continue

                writer.writerow(
                    {
                        "source": source,
                        "target": target,
                        "score": score,
                        "sign": "?",
                        "evidence": "association",
                        "context": "global",
                    }
                )
                rows_written += 1

    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--extra", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    _validate_inputs(args.input, args.params, args.extra, args.threads)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    progress_path = args.output_dir / "progress.json"
    _write_progress(
        progress_path,
        status="running",
        percent=0,
        phase="init",
        message="Initializing",
    )

    try:
        raw_params = _load_params(args.params)
        params = _resolve_params(raw_params)

        tf_path = args.extra / "tf_list.txt"
        if not tf_path.exists():
            raise FileNotFoundError(f"Required extra input not found: {tf_path}")

        _write_progress(
            progress_path,
            status="running",
            percent=5,
            phase="load_input",
            message="Loading expression and extra inputs",
        )

        _write_progress(
            progress_path,
            status="running",
            percent=10,
            phase="inference",
            message="Starting ARACNe3 inference",
        )
        consolidated_tsv = _run_aracne(
            input_path=args.input,
            tf_path=tf_path,
            output_dir=args.output_dir,
            threads=args.threads,
            params=params,
            progress_path=progress_path,
        )

        _write_progress(
            progress_path,
            status="running",
            percent=96,
            phase="write_output",
            message="Writing network.csv",
        )
        rows_written = _convert_consolidated_to_network(
            consolidated_tsv=consolidated_tsv,
            network_csv=args.output_dir / "network.csv",
        )

        _write_progress(
            progress_path,
            status="completed",
            percent=100,
            phase="done",
            message="Inference finished",
            completed=rows_written,
            total=rows_written,
        )
    except Exception as exc:
        _write_progress(
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
