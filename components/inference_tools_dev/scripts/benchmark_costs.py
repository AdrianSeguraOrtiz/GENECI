"""Benchmark inference tools and write per-tool cost profiles (`cost.json`).

This script runs each tool wrapper in Docker for multiple input sizes and
resource configurations (threads + memory limit), measures runtime, and writes:
1) `geneci/inference_catalog/tools/<tool_id>/cost.json` files.

Usage examples:
1) Benchmark all tools with defaults (up to host cap, max 8 CPU / 64 GB):
   python benchmark_costs.py

2) Benchmark selected tools:
   python benchmark_costs.py --tool genie3 --tool grnboost2

3) Customize matrix:
   python benchmark_costs.py \
     --size 50x20 --size 100x40 --size 200x80 \
     --threads 1,2,4,8 \
     --ram-gb 8,16,32,64

Exit codes:
- 0: script completed (even if some runs failed; inspect report summary)
- 2: usage/runtime error (invalid args, missing paths, etc.)

Cost model written to cost.json:
- runtime_points: aggregated per (genes, columns, threads, ram_gb), including
  status/failure information, ok_rate, failure_breakdown, and p50/p90 runtime estimates.
- benchmark_config: benchmark matrix metadata (sizes/resources/repeats/timeout)
  plus the resolved parameter profile used for the benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

from shared.param_profiles import DEFAULT_PARAM_OVERRIDES_DIR, resolve_dev_params

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "geneci" / "inference_catalog"
DEFAULT_CATALOG_TOOLS_ROOT = CATALOG_ROOT / "tools"
DEFAULT_TOOL_SOURCES_ROOT = INFERENCE_TOOLS_ROOT / "tools"
DEFAULT_SIZES = ("50x20", "100x40", "200x80")
DEFAULT_THREADS = "1,2,4,8"
DEFAULT_RAM_GB = "8,16,32,64"


@dataclass(frozen=True)
class SizePoint:
    genes: int
    columns: int


@dataclass(frozen=True)
class RunPlanItem:
    size: SizePoint
    threads: int
    ram_gb: int
    repeat: int


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark tool source wrappers (components/inference_tools_dev/tools/*) "
            "under different sizes/resources and "
            "write cost.json profiles in the runtime catalog."
        )
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=(
            "Path to catalog tools directory containing toolspec.json files. "
            f"Default: {DEFAULT_CATALOG_TOOLS_ROOT}"
        ),
    )
    parser.add_argument(
        "--tool-sources-root",
        type=Path,
        default=DEFAULT_TOOL_SOURCES_ROOT,
        help=(
            "Path to tool source directories containing Dockerfile/wrappers. "
            f"Default: {DEFAULT_TOOL_SOURCES_ROOT}"
        ),
    )
    parser.add_argument(
        "--param-overrides-dir",
        type=Path,
        default=DEFAULT_PARAM_OVERRIDES_DIR,
        help=(
            "Path to optional per-tool dev parameter overrides merged onto ToolSpec defaults. "
            f"Default: {DEFAULT_PARAM_OVERRIDES_DIR}"
        ),
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to benchmark (repeatable). If omitted, benchmarks all discovered tools.",
    )
    parser.add_argument(
        "--size",
        action="append",
        default=[],
        help=(
            "Benchmark size point as GENESxCOLUMNS (repeatable). "
            f"Default: {', '.join(DEFAULT_SIZES)}"
        ),
    )
    parser.add_argument(
        "--threads",
        default=DEFAULT_THREADS,
        help=f"Comma-separated thread counts to test. Default: {DEFAULT_THREADS}",
    )
    parser.add_argument(
        "--ram-gb",
        default=DEFAULT_RAM_GB,
        help=f"Comma-separated memory limits (GB) to test. Default: {DEFAULT_RAM_GB}",
    )
    parser.add_argument(
        "--max-cpu",
        type=int,
        default=8,
        help="Upper CPU cap for this machine. Default: 8",
    )
    parser.add_argument(
        "--max-ram-gb",
        type=int,
        default=64,
        help="Upper RAM cap (GB) for this machine. Default: 64",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeats per (size, threads, ram) run. Default: 1",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds per run (0 = no timeout). Default: 1800",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip Docker image build step and assume images already exist.",
    )
    parser.add_argument(
        "--no-write-cost",
        action="store_true",
        help="Do not write cost.json; run benchmarks without persisting cost profiles.",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep temporary benchmark IO directories for debugging.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed used for synthetic data generation. Default: 12345",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after first failed run.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=True)
        fh.write("\n")


def parse_size(value: str) -> SizePoint:
    token = value.strip().lower()
    if "x" not in token:
        raise ValueError(f"Invalid size '{value}'. Expected format: GENESxCOLUMNS")
    left, right = token.split("x", 1)
    genes = int(left)
    columns = int(right)
    if genes < 1 or columns < 1:
        raise ValueError(f"Invalid size '{value}'. Both dimensions must be >= 1.")
    return SizePoint(genes=genes, columns=columns)


def parse_int_csv(value: str, label: str) -> list[int]:
    items = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        parsed = int(token)
        if parsed < 1:
            raise ValueError(f"{label} values must be >= 1. Got: {parsed}")
        items.append(parsed)
    if not items:
        raise ValueError(f"{label} list is empty.")
    return sorted(set(items))


def detect_host_ram_gb() -> float:
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    kib = int(parts[1])
                    return kib / (1024 * 1024)
    # Fallback: conservative default if /proc/meminfo is unavailable.
    return 8.0


def discover_catalog_tools(catalog_tools_root: Path) -> list[tuple[str, Path]]:
    if not catalog_tools_root.exists() or not catalog_tools_root.is_dir():
        raise RuntimeError(f"Invalid catalog tools root: {catalog_tools_root}")
    out: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in catalog_tools_root.iterdir() if path.is_dir()
    ):
        if (tool_dir / "toolspec.json").exists():
            out.append((tool_dir.name, tool_dir))
    if not out:
        raise RuntimeError(f"No toolspec.json found under: {catalog_tools_root}")
    return out


def select_tools(
    discovered: list[tuple[str, Path]], filters: list[str]
) -> list[tuple[str, Path]]:
    by_id = {tool_id: path for tool_id, path in discovered}
    if not filters:
        return discovered
    unknown = sorted(tool_id for tool_id in filters if tool_id not in by_id)
    if unknown:
        raise RuntimeError(f"Unknown tool id(s): {unknown}")
    return [(tool_id, by_id[tool_id]) for tool_id in filters]


def docker_image_tag(tool_id: str) -> str:
    return f"inference-tools-{tool_id}:benchmark-local"


def run_cmd(
    cmd: Sequence[str],
    *,
    cwd: Path,
    timeout_s: int,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd),
        cwd=str(cwd),
        text=True,
        check=False,
        capture_output=capture_output,
        timeout=None if timeout_s <= 0 else timeout_s,
    )


def build_image(
    tool_id: str,
    *,
    catalog_tools_root: Path,
    tool_sources_root: Path,
    image_tag: str,
) -> None:
    print(f"[{tool_id}] building image {image_tag}")
    build_script = INFERENCE_TOOLS_ROOT / "scripts" / "build_tool_images.py"
    result = run_cmd(
        [
            sys.executable,
            str(build_script),
            "--catalog-tools-root",
            str(catalog_tools_root),
            "--tool-sources-root",
            str(tool_sources_root),
            "--tool",
            tool_id,
            "--image-tag",
            f"{tool_id}={image_tag}",
        ],
        cwd=REPO_ROOT,
        timeout_s=0,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Docker build failed for {tool_id} (exit {result.returncode}).\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )


def write_expression_tsv(
    path: Path, genes: int, columns: int, rng: random.Random
) -> list[str]:
    gene_names = [f"G{i + 1}" for i in range(genes)]
    sample_names = [f"S{i + 1}" for i in range(columns)]

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["gene"] + sample_names)
        for gene in gene_names:
            row = [f"{rng.uniform(-2.0, 2.0):.6f}" for _ in range(columns)]
            writer.writerow([gene] + row)

    return gene_names


def write_tf_list(path: Path, genes: Sequence[str]) -> None:
    n_tf = max(1, min(len(genes), max(3, len(genes) // 5)))
    with path.open("w", encoding="utf-8") as fh:
        for gene in genes[:n_tf]:
            fh.write(f"{gene}\n")


def write_groups(path: Path, columns: int) -> list[str]:
    clusters = ["cluster_root", "cluster_child"] if columns > 1 else ["cluster_root"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["sample", "cluster"])
        for idx in range(columns):
            sample = f"S{idx + 1}"
            cluster = clusters[idx % len(clusters)]
            writer.writerow([sample, cluster])
    return clusters


def write_lineage_tree(path: Path, clusters: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["child", "parent", "gain_rate", "loss_rate"])
        if len(clusters) == 1:
            writer.writerow([clusters[0], clusters[0], "0.2", "0.8"])
            return
        for idx in range(1, len(clusters)):
            writer.writerow([clusters[idx], clusters[idx - 1], "0.2", "0.8"])


def write_prior_grn(path: Path, genes: Sequence[str], rng: random.Random) -> None:
    n_tf = max(1, min(len(genes), max(3, len(genes) // 5)))
    tfs = list(genes[:n_tf])
    targets = list(genes)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        for tf in tfs:
            k = min(5, len(targets))
            chosen = rng.sample(targets, k=k) if k > 0 else []
            for target in chosen:
                score = rng.uniform(0.01, 1.0)
                writer.writerow([tf, target, f"{score:.6f}"])


def prepare_io_dir(
    io_dir: Path,
    size: SizePoint,
    *,
    resolved_params: dict[str, Any],
    seed: int,
    run_offset: int,
) -> None:
    io_dir.mkdir(parents=True, exist_ok=True)
    (io_dir / "extra").mkdir(parents=True, exist_ok=True)
    (io_dir / "out").mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed + run_offset)
    genes = write_expression_tsv(
        io_dir / "expression.tsv", size.genes, size.columns, rng
    )
    save_json(io_dir / "params.json", resolved_params)

    write_tf_list(io_dir / "extra" / "tf_list.txt", genes)
    clusters = write_groups(io_dir / "extra" / "groups.tsv", size.columns)
    write_lineage_tree(io_dir / "extra" / "lineage_tree.tsv", clusters)
    write_prior_grn(io_dir / "extra" / "prior_grn.tsv", genes, rng)


def run_container_once(
    *,
    image_tag: str,
    io_dir: Path,
    threads: int,
    ram_gb: int,
    timeout_s: int,
) -> tuple[str, float, str]:
    uid_gid = f"{os.getuid()}:{os.getgid()}"
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        uid_gid,
        "--cpus",
        str(threads),
        "--memory",
        f"{ram_gb}g",
        "-v",
        f"{io_dir}:/io",
        image_tag,
        "--input",
        "/io/expression.tsv",
        "--params",
        "/io/params.json",
        "--extra",
        "/io/extra",
        "--output-dir",
        "/io/out",
        "--threads",
        str(threads),
    ]

    started = time.perf_counter()
    try:
        result = run_cmd(cmd, cwd=REPO_ROOT, timeout_s=timeout_s, capture_output=True)
        elapsed = time.perf_counter() - started
        logs = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        if result.returncode != 0:
            return (classify_failure(logs), elapsed, logs.strip())
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - started
        return ("timeout", elapsed, f"Run exceeded timeout of {timeout_s} seconds.")

    network_path = io_dir / "out" / "network.csv"
    if not network_path.exists() or network_path.stat().st_size <= 0:
        return (
            "error",
            elapsed,
            "Container finished but /io/out/network.csv is missing or empty.",
        )
    return ("ok", elapsed, "")


def classify_failure(logs: str) -> str:
    text = logs.lower()
    oom_markers = [
        "oom",
        "out of memory",
        "cannot allocate memory",
        "oomkilled",
        "killed process",
    ]
    if any(marker in text for marker in oom_markers):
        return "oom"
    return "error"


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot compute percentile of empty sequence.")
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]

    position = (q / 100.0) * (len(ordered) - 1)
    lower_idx = int(math.floor(position))
    upper_idx = int(math.ceil(position))
    if lower_idx == upper_idx:
        return ordered[lower_idx]

    weight = position - lower_idx
    return ordered[lower_idx] * (1.0 - weight) + ordered[upper_idx] * weight


def aggregate_runtime_points(all_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for run in all_runs:
        key = (
            int(run["genes"]),
            int(run["columns"]),
            int(run["threads"]),
            int(run["ram_gb"]),
        )
        grouped[key].append(run)

    points: list[dict[str, Any]] = []
    for (genes, columns, threads, ram_gb), runs in sorted(grouped.items()):
        total = len(runs)
        ok_runs = [r for r in runs if r["status"] == "ok"]
        ok_count = len(ok_runs)
        ok_secs = [float(r["seconds"]) for r in ok_runs]
        failed_count = total - ok_count

        run_status_counts: dict[str, int] = defaultdict(int)
        for run in runs:
            run_status_counts[str(run.get("status", "error"))] += 1

        # Keep a minimal, fixed failure taxonomy for planner use.
        oom_failures = int(run_status_counts.get("oom", 0))
        timeout_failures = int(run_status_counts.get("timeout", 0))
        error_failures = int(run_status_counts.get("error", 0))
        unknown_failures = int(
            sum(
                count
                for status, count in run_status_counts.items()
                if status not in {"ok", "oom", "timeout", "error"}
            )
        )
        error_failures += unknown_failures

        failure_breakdown = {
            "oom": oom_failures,
            "timeout": timeout_failures,
            "error": error_failures,
        }

        if ok_count == total:
            status = "ok"
        elif ok_count > 0:
            status = "partial"
        else:
            if oom_failures > 0:
                status = "oom"
            elif timeout_failures > 0:
                status = "timeout"
            else:
                status = "error"

        point = {
            "genes": genes,
            "columns": columns,
            "threads": threads,
            "ram_gb": ram_gb,
            "status": status,
            "repeats_total": total,
            "repeats_ok": ok_count,
            "repeats_failed": failed_count,
            "ok_rate": round((ok_count / total), 6),
            "failure_breakdown": failure_breakdown,
            "seconds_p50": None,
            "seconds_p90": None,
        }

        if ok_secs:
            point["seconds_p50"] = round(percentile(ok_secs, 50), 6)
            point["seconds_p90"] = round(percentile(ok_secs, 90), 6)

        points.append(point)
    return points


def write_tool_cost_profile(
    *,
    cost_path: Path,
    cost_payload: dict[str, Any],
) -> None:
    save_json(cost_path, cost_payload)


def validate_runtime_args(args: argparse.Namespace) -> None:
    """Validate global CLI limits before running any benchmark."""
    if args.repeats < 1:
        raise RuntimeError("--repeats must be >= 1.")
    if args.max_cpu < 1:
        raise RuntimeError("--max-cpu must be >= 1.")
    if args.max_ram_gb < 1:
        raise RuntimeError("--max-ram-gb must be >= 1.")


def resolve_benchmark_dimensions(
    args: argparse.Namespace,
) -> tuple[list[SizePoint], list[int], list[int], int, float]:
    """Resolve and cap benchmark sizes/resources against host limits."""
    sizes_raw = args.size or list(DEFAULT_SIZES)
    sizes = [parse_size(token) for token in sizes_raw]
    threads_requested = parse_int_csv(args.threads, "threads")
    ram_requested = parse_int_csv(args.ram_gb, "ram-gb")

    host_cores = os.cpu_count() or 1
    host_ram_gb = detect_host_ram_gb()
    effective_cores = min(host_cores, args.max_cpu)
    effective_ram_gb = min(host_ram_gb, float(args.max_ram_gb))

    threads = [value for value in threads_requested if value <= effective_cores]
    ram_gb = [value for value in ram_requested if value <= int(effective_ram_gb)]
    if not threads:
        raise RuntimeError(
            f"No thread values <= effective core cap ({effective_cores}). Requested: {threads_requested}"
        )
    if not ram_gb:
        raise RuntimeError(
            f"No RAM values <= effective RAM cap ({int(effective_ram_gb)} GB). Requested: {ram_requested}"
        )

    return sizes, threads, ram_gb, int(effective_cores), float(effective_ram_gb)


def build_benchmark_config(
    *,
    sizes: list[SizePoint],
    threads: list[int],
    ram_gb: list[int],
    params_profile: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Build the benchmark_config block stored in cost.json."""
    return {
        "sizes": [{"genes": s.genes, "columns": s.columns} for s in sizes],
        "threads_tested": [int(t) for t in threads],
        "ram_gb_tested": [float(r) for r in ram_gb],
        "repeats": int(args.repeats),
        "timeout_seconds": int(args.timeout),
        "params_profile": params_profile,
    }


def iter_run_plan(
    *, sizes: list[SizePoint], threads: list[int], ram_gb: list[int], repeats: int
) -> Iterator[RunPlanItem]:
    """Yield the cartesian run plan in a deterministic order."""
    for size in sizes:
        for thread_count in threads:
            for ram_limit in ram_gb:
                for repeat_idx in range(1, repeats + 1):
                    yield RunPlanItem(
                        size=size,
                        threads=thread_count,
                        ram_gb=ram_limit,
                        repeat=repeat_idx,
                    )


def allocate_tool_workdir(
    tool_id: str, keep_workdir: bool
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    """Create a per-tool working directory (ephemeral by default)."""
    if keep_workdir:
        preserved = tempfile.mkdtemp(prefix=f"benchmark_{tool_id}_")
        print(f"[{tool_id}] keeping benchmark workdir: {preserved}")
        return Path(preserved), None
    context = tempfile.TemporaryDirectory(prefix=f"benchmark_{tool_id}_")
    return Path(context.name), context


def summarize_tool_runs(tool_runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate run-level status counters for tool-level reporting."""
    successful = [r for r in tool_runs if r["status"] == "ok"]
    failed = [r for r in tool_runs if r["status"] != "ok"]
    status_counts: dict[str, int] = defaultdict(int)
    for run_item in tool_runs:
        status_counts[str(run_item["status"])] += 1

    return {
        "total_runs": len(tool_runs),
        "successful_runs": len(successful),
        "failed_runs": len(failed),
        "status_counts": dict(sorted(status_counts.items())),
    }


def make_cost_payload(
    *,
    runtime_points: list[dict[str, Any]],
    benchmark_config: dict[str, Any],
) -> dict[str, Any]:
    """Build the final cost payload written into cost.json."""
    return {
        "benchmark_config": benchmark_config,
        "runtime_points": runtime_points,
    }


def execute_tool_benchmarks(
    *,
    tool_id: str,
    image_tag: str,
    workdir: Path,
    sizes: list[SizePoint],
    threads: list[int],
    ram_gb: list[int],
    repeats: int,
    resolved_params: dict[str, Any],
    seed: int,
    timeout: int,
    fail_fast: bool,
    run_index: int,
    total_runs: int,
) -> tuple[list[dict[str, Any]], int, bool]:
    """Execute all planned runs for one tool; returns runs, updated index, and fail-fast flag."""
    tool_runs: list[dict[str, Any]] = []
    run_offset = 0

    for plan in iter_run_plan(
        sizes=sizes, threads=threads, ram_gb=ram_gb, repeats=repeats
    ):
        run_index += 1
        print(
            f"[{run_index}/{total_runs}] {tool_id} "
            f"{plan.size.genes}x{plan.size.columns} "
            f"threads={plan.threads} ram={plan.ram_gb}GB repeat={plan.repeat}"
        )

        run_key = (
            f"g{plan.size.genes}_c{plan.size.columns}_t{plan.threads}"
            f"_m{plan.ram_gb}_r{plan.repeat}"
        )
        io_dir = workdir / run_key / "io"
        prepare_io_dir(
            io_dir,
            plan.size,
            resolved_params=resolved_params,
            seed=seed,
            run_offset=run_offset,
        )
        run_offset += 1

        status, elapsed, error_or_empty = run_container_once(
            image_tag=image_tag,
            io_dir=io_dir,
            threads=plan.threads,
            ram_gb=plan.ram_gb,
            timeout_s=timeout,
        )

        run_payload: dict[str, Any] = {
            "genes": plan.size.genes,
            "columns": plan.size.columns,
            "threads": plan.threads,
            "ram_gb": plan.ram_gb,
            "repeat": plan.repeat,
            "seconds": round(elapsed, 6),
            "status": status,
        }
        if error_or_empty:
            run_payload["error"] = error_or_empty
        tool_runs.append(run_payload)

        if status != "ok":
            print(f"  -> {status} ({elapsed:.3f}s)")
            if fail_fast:
                return tool_runs, run_index, True
        else:
            print(f"  -> ok ({elapsed:.3f}s)")

    return tool_runs, run_index, False


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validate_runtime_args(args)
    sizes, threads, ram_gb, _effective_cores, _effective_ram_gb = (
        resolve_benchmark_dimensions(args)
    )

    discovered = discover_catalog_tools(args.catalog_tools_root)
    selected = select_tools(discovered, args.tool)

    total_runs = len(selected) * len(sizes) * len(threads) * len(ram_gb) * args.repeats
    run_index = 0
    fail_fast_triggered = False
    global_success = 0
    global_fail = 0

    for tool_id, catalog_tool_dir in selected:
        image_tag = docker_image_tag(tool_id)
        tool_source_dir = args.tool_sources_root / tool_id
        if not tool_source_dir.exists() or not tool_source_dir.is_dir():
            print(
                f"[{tool_id}] ERROR: missing tool source directory: {tool_source_dir}",
                file=sys.stderr,
            )
            if args.fail_fast:
                break
            continue

        cost_path = catalog_tool_dir / "cost.json"
        wrote_cost = False
        workdir_context: tempfile.TemporaryDirectory[str] | None = None

        try:
            if not args.skip_build:
                build_image(
                    tool_id,
                    catalog_tools_root=args.catalog_tools_root,
                    tool_sources_root=args.tool_sources_root,
                    image_tag=image_tag,
                )

            workdir, workdir_context = allocate_tool_workdir(
                tool_id=tool_id,
                keep_workdir=args.keep_workdir,
            )
            resolved_params, params_profile = resolve_dev_params(
                tool_id=tool_id,
                catalog_tools_root=args.catalog_tools_root,
                param_overrides_dir=args.param_overrides_dir,
            )
            benchmark_config = build_benchmark_config(
                sizes=sizes,
                threads=threads,
                ram_gb=ram_gb,
                params_profile=params_profile,
                args=args,
            )
            tool_runs, run_index, fail_fast_triggered = execute_tool_benchmarks(
                tool_id=tool_id,
                image_tag=image_tag,
                workdir=workdir,
                sizes=sizes,
                threads=threads,
                ram_gb=ram_gb,
                repeats=args.repeats,
                resolved_params=resolved_params,
                seed=args.seed,
                timeout=args.timeout,
                fail_fast=args.fail_fast,
                run_index=run_index,
                total_runs=total_runs,
            )

            tool_summary = summarize_tool_runs(tool_runs)
            global_success += tool_summary["successful_runs"]
            global_fail += tool_summary["failed_runs"]

            runtime_points = aggregate_runtime_points(tool_runs)

            has_success = any(
                int(point.get("repeats_ok", 0)) > 0 for point in runtime_points
            )
            if has_success:
                cost_payload = make_cost_payload(
                    runtime_points=runtime_points,
                    benchmark_config=benchmark_config,
                )

                if not args.no_write_cost:
                    write_tool_cost_profile(
                        cost_path=cost_path,
                        cost_payload=cost_payload,
                    )
                    wrote_cost = True
            else:
                print(
                    f"[{tool_id}] warning: no successful runs were observed; "
                    "cost.json was not written."
                )

            print(
                f"[{tool_id}] summary: total={tool_summary['total_runs']} "
                f"ok={tool_summary['successful_runs']} failed={tool_summary['failed_runs']} "
                f"wrote_cost={wrote_cost}"
            )

        except Exception as exc:  # noqa: BLE001
            print(f"[{tool_id}] ERROR: {exc}", file=sys.stderr)
            if args.fail_fast:
                break
        finally:
            if workdir_context is not None:
                workdir_context.cleanup()

        if fail_fast_triggered:
            break

    print()
    print(
        f"Benchmark finished. successful_runs={global_success} "
        f"failed_runs={global_fail}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
