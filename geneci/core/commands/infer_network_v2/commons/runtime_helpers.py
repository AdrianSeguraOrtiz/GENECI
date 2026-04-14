"""Docker runtime and per-wave execution helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

from rich import print
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .shared import (
    DatasetContext,
    PlanWave,
    RunningTool,
    SchemaConstraints,
    ToolExecutionResult,
    ToolRuntimeIO,
    _write_json,
    _write_text,
)


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=True,
    )


def _tail_lines(text: str, max_lines: int = 40) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def _ensure_docker_cli() -> None:
    result = _run_cmd(["docker", "--version"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Docker CLI is not available. Details: {details}")


def _docker_image_exists(image: str) -> bool:
    result = _run_cmd(["docker", "image", "inspect", image])
    return result.returncode == 0


def _ensure_docker_image(
    *,
    image: str,
    pulled_images: set[str],
) -> str:
    if _docker_image_exists(image):
        return "local"

    if image in pulled_images:
        if _docker_image_exists(image):
            return "pulled"
        raise RuntimeError(
            f"Docker image marked as pulled but missing locally: {image}"
        )

    pull = _run_cmd(["docker", "pull", image])
    if pull.returncode != 0:
        details = (pull.stderr or pull.stdout or "").strip()
        raise RuntimeError(f"Failed to pull docker image '{image}': {details}")
    pulled_images.add(image)
    return "pulled"


def _docker_run_detached(
    *,
    image: str,
    io_dir: Path,
    threads: int,
    ram_gb: float,
) -> str:
    cmd = ["docker", "run", "-d"]

    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        cmd.extend(["--user", f"{os.getuid()}:{os.getgid()}"])

    cmd.extend(
        [
            "--cpus",
            str(max(1, int(threads))),
            "--memory",
            f"{max(0.5, float(ram_gb)):.3g}g",
            "-v",
            f"{io_dir}:/io",
            image,
            "--input",
            "/io/expression.tsv",
            "--params",
            "/io/params.json",
            "--extra",
            "/io/extra",
            "--output-dir",
            "/io/out",
            "--threads",
            str(max(1, int(threads))),
        ]
    )

    result = _run_cmd(cmd)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"docker run failed for image '{image}': {details}")

    container_id = (result.stdout or "").strip()
    if not container_id:
        raise RuntimeError(
            f"docker run returned empty container id for image '{image}'"
        )
    return container_id


def _docker_inspect_status(container_id: str) -> str:
    result = _run_cmd(["docker", "inspect", "-f", "{{.State.Status}}", container_id])
    if result.returncode != 0:
        return "unknown"
    return (result.stdout or "").strip().lower()


def _docker_wait_exit_code(container_id: str) -> int:
    result = _run_cmd(["docker", "wait", container_id])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"docker wait failed for {container_id}: {details}")
    tail = (result.stdout or "").strip().splitlines()
    if not tail:
        raise RuntimeError(f"docker wait returned empty output for {container_id}")
    return int(tail[-1].strip())


def _docker_logs(container_id: str) -> str:
    result = _run_cmd(["docker", "logs", container_id])
    logs = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if err:
        if logs:
            logs = f"{logs}\n{err}"
        else:
            logs = err
    return logs


def _docker_rm(container_id: str) -> None:
    _ = _run_cmd(["docker", "rm", "-f", container_id])


def _parse_progress_snapshot(path: Path) -> tuple[int, str, str, str]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    percent = int(data.get("percent", 0))
    status = str(data.get("status", "unknown"))
    phase = str(data.get("phase", "unknown"))
    message = str(data.get("message", ""))
    return percent, status, phase, message


def _short_progress_message(message: str, *, max_len: int = 64) -> str:
    compact = " ".join(message.strip().split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3]}..."


def _link_or_copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _prepare_shared_inputs(
    *,
    run_dir: Path,
    dataset: DatasetContext,
    constraints: SchemaConstraints,
) -> tuple[Path, dict[str, Path]]:
    shared_dir = run_dir / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)

    shared_expression = shared_dir / "expression.tsv"
    shutil.copy2(dataset.expression_matrix_path, shared_expression)

    extras_dir = shared_dir / "extra"
    extras_dir.mkdir(parents=True, exist_ok=True)
    shared_extras: dict[str, Path] = {}

    for key, source in dataset.extras.items():
        if source is None:
            continue
        filename = constraints.extra_input_filenames.get(key, key)
        dest = extras_dir / filename
        _link_or_copy_file(source, dest)
        shared_extras[key] = dest

    return shared_expression, shared_extras


def _prepare_tool_runtime_io(
    *,
    run_dir: Path,
    tool_id: str,
    run_id: str,
    output_dir: str,
    resolved_params: dict[str, Any],
    shared_expression: Path,
    shared_extras: dict[str, Path],
    expression_source: Optional[Path] = None,
) -> ToolRuntimeIO:
    tool_dir = run_dir / output_dir
    io_dir = tool_dir / "io"
    extra_dir = io_dir / "extra"
    out_dir = io_dir / "out"
    io_dir.mkdir(parents=True, exist_ok=True)
    extra_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    expression_dst = io_dir / "expression.tsv"
    _link_or_copy_file(expression_source or shared_expression, expression_dst)

    params_file = io_dir / "params.json"
    _write_json(params_file, resolved_params)

    for extra_path in shared_extras.values():
        dest = extra_dir / extra_path.name
        _link_or_copy_file(extra_path, dest)

    return ToolRuntimeIO(
        tool_id=tool_id,
        run_id=run_id,
        tool_dir=tool_dir,
        io_dir=io_dir,
        out_dir=out_dir,
        progress_file=out_dir / "progress.json",
        params_file=params_file,
    )


def _run_wave(
    *,
    wave: PlanWave,
    runtime_io_by_tool: dict[str, ToolRuntimeIO],
    pulled_images: set[str],
    poll_interval_s: float,
    warnings: list[str],
) -> dict[str, ToolExecutionResult]:
    results: dict[str, ToolExecutionResult] = {}
    running: dict[str, RunningTool] = {}
    progress_task_id: dict[str, int] = {}
    use_live_progress = bool(sys.stdout.isatty())
    progress: Optional[Progress] = None
    if use_live_progress:
        progress = Progress(
            TextColumn("{task.fields[tool]:<28}"),
            BarColumn(bar_width=24),
            TaskProgressColumn(),
            TextColumn("{task.fields[status]:<9}"),
            TextColumn("{task.fields[phase]:<12}"),
            TextColumn("{task.fields[msg]}"),
            TimeElapsedColumn(),
            transient=False,
        )
        progress.start()

    try:
        print(
            f"wave {wave.index}: starting {len(wave.tasks)} tool(s), "
            f"planned cores={wave.threads_used}, planned ram={wave.ram_gb_used}GB"
        )

        for task in wave.tasks:
            tool_io = runtime_io_by_tool[task.tool_id]
            logs_path = tool_io.tool_dir / "container.log"
            try:
                image_source = _ensure_docker_image(
                    image=task.image, pulled_images=pulled_images
                )
                if image_source == "pulled":
                    warnings.append(
                        f"[{task.tool_id}] docker image was not local and was pulled: {task.image}"
                    )

                container_id = _docker_run_detached(
                    image=task.image,
                    io_dir=tool_io.io_dir,
                    threads=task.threads,
                    ram_gb=task.ram_gb,
                )
                running[task.tool_id] = RunningTool(
                    tool_id=task.tool_id,
                    container_id=container_id,
                    started_at=time.perf_counter(),
                    progress_file=tool_io.progress_file,
                )

                if progress is not None:
                    progress_task_id[task.tool_id] = progress.add_task(
                        "",
                        total=100,
                        completed=0,
                        tool=task.tool_id,
                        status="running",
                        phase="starting",
                        msg="Container started",
                    )
                else:
                    print(
                        f"tool {task.tool_id}: container started "
                        f"(threads={task.threads}, ram={task.ram_gb}GB)"
                    )
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                _write_text(logs_path, f"{error}\n")
                warnings.append(f"[{task.tool_id}] failed before execution: {error}")
                results[task.tool_id] = ToolExecutionResult(
                    tool_id=task.tool_id,
                    status="failed",
                    exit_code=127,
                    duration_seconds=0.0,
                    network_path=None,
                    progress_path=None,
                    logs_path=str(logs_path.resolve()),
                    error=error,
                )
                if progress is not None:
                    progress_task_id[task.tool_id] = progress.add_task(
                        "",
                        total=100,
                        completed=100,
                        tool=task.tool_id,
                        status="failed",
                        phase="startup",
                        msg=_short_progress_message(error),
                    )

        while running:
            for tool_id in list(running.keys()):
                state = running[tool_id]
                tool_io = runtime_io_by_tool[tool_id]

                if state.progress_file.exists():
                    try:
                        snapshot = _parse_progress_snapshot(state.progress_file)
                    except Exception:  # noqa: BLE001
                        snapshot = None
                    if snapshot is not None and snapshot != state.last_snapshot:
                        percent, status, phase, message = snapshot
                        percent = max(0, min(100, int(percent)))
                        if progress is not None:
                            task_id = progress_task_id.get(tool_id)
                            if task_id is None:
                                task_id = progress.add_task(
                                    "",
                                    total=100,
                                    completed=0,
                                    tool=tool_id,
                                    status="running",
                                    phase="unknown",
                                    msg="",
                                )
                                progress_task_id[tool_id] = task_id
                            progress.update(
                                task_id,
                                completed=percent,
                                status=status,
                                phase=phase,
                                msg=_short_progress_message(message),
                            )
                        else:
                            print(
                                f"tool {tool_id} progress: {percent}% | {status} | {phase} | {message}"
                            )
                        state.last_snapshot = snapshot

                status = _docker_inspect_status(state.container_id)
                if status not in {"exited", "dead"}:
                    continue

                logs_path = tool_io.tool_dir / "container.log"
                exit_code = -1
                logs = ""
                error: Optional[str] = None
                network_path: Optional[str] = None

                try:
                    exit_code = _docker_wait_exit_code(state.container_id)
                    logs = _docker_logs(state.container_id)
                    _write_text(logs_path, f"{logs}\n" if logs else "")
                except Exception as exc:  # noqa: BLE001
                    error = f"Failed while collecting container outputs: {exc}"
                    _write_text(logs_path, f"{error}\n")
                finally:
                    _docker_rm(state.container_id)

                duration = round(time.perf_counter() - state.started_at, 3)
                network_file = tool_io.out_dir / "network.csv"

                if error is None and exit_code == 0 and network_file.exists():
                    network_path = str(network_file.resolve())
                    final_status = "completed"
                else:
                    final_status = "failed"
                    if error is None:
                        if exit_code != 0:
                            error = (
                                f"Container exited with non-zero status ({exit_code})."
                            )
                        else:
                            error = "Container exited successfully but network.csv is missing."
                    if logs:
                        logs_tail = _tail_lines(logs, max_lines=20)
                        if logs_tail:
                            error = f"{error}\nContainer logs tail:\n{logs_tail}"
                    warnings.append(f"[{tool_id}] execution failed: {error}")

                results[tool_id] = ToolExecutionResult(
                    tool_id=tool_id,
                    status=final_status,
                    exit_code=exit_code,
                    duration_seconds=duration,
                    network_path=network_path,
                    progress_path=(
                        str(tool_io.progress_file.resolve())
                        if tool_io.progress_file.exists()
                        else None
                    ),
                    logs_path=str(logs_path.resolve()),
                    error=error,
                )

                if progress is not None:
                    task_id = progress_task_id.get(tool_id)
                    if task_id is None:
                        task_id = progress.add_task(
                            "",
                            total=100,
                            completed=0,
                            tool=tool_id,
                            status="running",
                            phase="unknown",
                            msg="",
                        )
                        progress_task_id[tool_id] = task_id
                    progress.update(
                        task_id,
                        completed=100,
                        status=(
                            "completed" if final_status == "completed" else "failed"
                        ),
                        phase=("done" if final_status == "completed" else "failed"),
                        msg=(
                            f"finished in {duration:.2f}s"
                            if final_status == "completed"
                            else _short_progress_message(error or "Execution failed")
                        ),
                    )
                else:
                    if final_status == "completed":
                        print(f"tool {tool_id}: completed in {duration:.2f}s")
                    else:
                        print(f"tool {tool_id}: failed in {duration:.2f}s")

                del running[tool_id]

            if running:
                time.sleep(max(0.05, float(poll_interval_s)))
    finally:
        if progress is not None:
            progress.stop()

    return results


# ============================================================================
# Phase: Output Merge And Score Normalization
