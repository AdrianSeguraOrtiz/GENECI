"""Run inference tool smoketests from a single unified script.

By default, runs every tool in the packaged catalog (`geneci/inference_catalog/tools/*`)
that has a `toolspec.json`.
You can filter with one or multiple --tool flags.

Each tool can customize the smoke behavior via:
  components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json

Exit codes:
- 0: every selected smoketest passed
- 1: one or more smoketests failed
- 2: usage/runtime error (unknown tool ids, invalid root, etc.)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from shared.param_profiles import DEFAULT_PARAM_OVERRIDES_DIR, resolve_dev_params

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES_DIR = INFERENCE_TOOLS_ROOT / "tests" / "fixtures"
DEFAULT_SMOKETEST_CONFIGS_DIR = INFERENCE_TOOLS_ROOT / "tests" / "smoketest_configs"
DEFAULT_BUILD_SCRIPT = INFERENCE_TOOLS_ROOT / "scripts" / "build_tool_images.py"
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "geneci" / "inference_catalog"
DEFAULT_CATALOG_TOOLS_ROOT = CATALOG_ROOT / "tools"
DEFAULT_TOOL_SOURCES_ROOT = INFERENCE_TOOLS_ROOT / "tools"

REQUIRED_NETWORK_COLUMNS = ["source", "target", "score", "sign", "evidence", "context"]
ALLOWED_CONFIG_ROOT_KEYS = {"extra_files", "require_progress", "checks"}
ALLOWED_CONFIG_CHECK_KEYS = {
    "require_cluster_context",
    "require_unique_unordered_pairs",
    "forbid_self_loops",
}


@dataclass(frozen=True)
class SmokeConfig:
    extra_files: list[str]
    require_progress: bool
    require_cluster_context: bool
    require_unique_unordered_pairs: bool
    forbid_self_loops: bool


@dataclass(frozen=True)
class AuxArtifactSpec:
    path_pattern: str
    kind: str
    require_non_empty: bool


@dataclass(frozen=True)
class SmokeIOPaths:
    io_dir: Path
    out_dir: Path
    progress_file: Path


DEFAULT_CONFIG = SmokeConfig(
    extra_files=[],
    require_progress=True,
    require_cluster_context=False,
    require_unique_unordered_pairs=False,
    forbid_self_loops=False,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tool smoketests for selected or all tools."
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory (toolspec.json files). Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--tool-sources-root",
        type=Path,
        default=DEFAULT_TOOL_SOURCES_ROOT,
        help=(
            "Path to tool source directories (Dockerfile/wrappers) used for image builds. "
            f"Default: {DEFAULT_TOOL_SOURCES_ROOT}"
        ),
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help=f"Path to shared fixtures directory. Default: {DEFAULT_FIXTURES_DIR}",
    )
    parser.add_argument(
        "--smoketest-configs-dir",
        type=Path,
        default=DEFAULT_SMOKETEST_CONFIGS_DIR,
        help=f"Path to per-tool smoketest config files. Default: {DEFAULT_SMOKETEST_CONFIGS_DIR}",
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
        help="Tool id to run (repeatable). If omitted, runs all discovered tools.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=int(os.environ.get("THREADS", "2")),
        help="Threads passed to wrapper. Default: env THREADS or 2.",
    )
    parser.add_argument(
        "--skip-image-build",
        action="store_true",
        default=os.environ.get("SKIP_IMAGE_BUILD", "0") == "1",
        help="Skip image build (or set SKIP_IMAGE_BUILD=1).",
    )
    parser.add_argument(
        "--image-tag",
        action="append",
        default=[],
        help=(
            "Per-tool image tag override, format TOOL_ID=IMAGE_TAG. "
            "Default for each tool: <tool>-smoketest:local"
        ),
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Progress polling interval in seconds. Default: 0.5",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered tools/config and exit.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after first failure.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Per-tool timeout in seconds (0 = no timeout).",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print output files content (progress.json and network.csv) for each tool run.",
    )
    parser.add_argument(
        "--show-output-lines",
        type=int,
        default=60,
        help="Maximum lines to print per output file when --show-output is enabled (<=0 = full file).",
    )
    return parser.parse_args(argv)


def run_cmd(
    cmd: Sequence[str], *, cwd: Path, timeout_s: int = 0
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd),
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
        timeout=None if timeout_s <= 0 else timeout_s,
    )


def remaining_timeout(started_at: float, timeout_s: int) -> int:
    if timeout_s <= 0:
        return 0
    elapsed = time.perf_counter() - started_at
    remaining = int(timeout_s - elapsed)
    if remaining <= 0:
        return 1
    return remaining


def discover_catalog_tools(catalog_tools_root: Path) -> list[tuple[str, Path]]:
    if not catalog_tools_root.exists() or not catalog_tools_root.is_dir():
        raise RuntimeError(f"Invalid catalog tools root: {catalog_tools_root}")

    discovered: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in catalog_tools_root.iterdir() if path.is_dir()
    ):
        if (tool_dir / "toolspec.json").exists():
            discovered.append((tool_dir.name, tool_dir))

    if not discovered:
        raise RuntimeError(
            f"No tools with toolspec.json found under: {catalog_tools_root}"
        )
    return discovered


def select_tools(
    discovered: list[tuple[str, Path]], filters: list[str]
) -> list[tuple[str, Path]]:
    by_tool_id = {tool_id: tool_dir for tool_id, tool_dir in discovered}
    if not filters:
        return discovered

    unknown = sorted(tool_id for tool_id in filters if tool_id not in by_tool_id)
    if unknown:
        raise RuntimeError(f"Unknown tool id(s): {unknown}")
    return [(tool_id, by_tool_id[tool_id]) for tool_id in filters]


def parse_image_tag_overrides(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise RuntimeError(
                f"Invalid --image-tag '{item}'. Expected format: TOOL_ID=IMAGE_TAG"
            )
        tool_id, tag = item.split("=", 1)
        tool_id = tool_id.strip()
        tag = tag.strip()
        if not tool_id or not tag:
            raise RuntimeError(
                f"Invalid --image-tag '{item}'. Expected format: TOOL_ID=IMAGE_TAG"
            )
        out[tool_id] = tag
    return out


def default_image_tag(tool_id: str) -> str:
    return f"{tool_id}-smoketest:local"


def validate_cli_args(args: argparse.Namespace) -> None:
    if args.threads <= 0:
        raise RuntimeError("--threads must be a positive integer.")


def validate_image_tag_overrides(
    selected: list[tuple[str, Path]],
    image_tags: dict[str, str],
) -> None:
    """Ensure --image-tag overrides only reference selected tools."""
    selected_ids = {tool_id for tool_id, _ in selected}
    unknown_tag_overrides = sorted(
        tool_id for tool_id in image_tags if tool_id not in selected_ids
    )
    if unknown_tag_overrides:
        raise RuntimeError(
            f"--image-tag contains tools not selected for run: {unknown_tag_overrides}"
        )


def prepare_smoke_io(
    *,
    tool_id: str,
    catalog_tools_root: Path,
    fixtures_dir: Path,
    param_overrides_dir: Path,
    config: SmokeConfig,
) -> tuple[tempfile.TemporaryDirectory[str], SmokeIOPaths]:
    """Create a temporary /io workspace and copy required smoketest inputs."""
    tmp_ctx = tempfile.TemporaryDirectory(prefix=f"smoke_{tool_id}_")
    tmp_dir = Path(tmp_ctx.name)
    io_dir = tmp_dir / "io"
    extra_dir = io_dir / "extra"
    out_dir = io_dir / "out"
    extra_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved_params, _profile = resolve_dev_params(
        tool_id=tool_id,
        catalog_tools_root=catalog_tools_root,
        param_overrides_dir=param_overrides_dir,
    )

    expression_src = resolve_path(
        fixtures_dir,
        tool_id,
        "expression.tsv",
    )
    shutil.copy2(expression_src, io_dir / "expression.tsv")
    with (io_dir / "params.json").open("w", encoding="utf-8") as fh:
        json.dump(resolved_params, fh, indent=2, ensure_ascii=True)
        fh.write("\n")

    for extra_name in config.extra_files:
        src = resolve_path(
            fixtures_dir,
            tool_id,
            extra_name,
        )
        shutil.copy2(src, extra_dir / extra_name)

    return tmp_ctx, SmokeIOPaths(
        io_dir=io_dir,
        out_dir=out_dir,
        progress_file=out_dir / "progress.json",
    )


def run_container_lifecycle(
    *,
    image_tag: str,
    io_dir: Path,
    threads: int,
    progress_file: Path,
    poll_interval_s: float,
    started_at: float,
    timeout_s: int,
) -> tuple[int, bool, str]:
    """Start, monitor and cleanup one smoketest container."""
    container_id = start_container(image_tag=image_tag, io_dir=io_dir, threads=threads)
    try:
        exit_code, saw_progress = wait_container(
            container_id=container_id,
            progress_file=progress_file,
            poll_interval_s=poll_interval_s,
            started_at=started_at,
            timeout_s=timeout_s,
        )
    finally:
        logs = cleanup_container(container_id)
    return exit_code, saw_progress, logs


def resolve_path(
    fixtures_dir: Path,
    tool_id: str,
    filename: str,
) -> Path:
    tool_fixture = fixtures_dir / tool_id / filename
    shared_fixture = fixtures_dir / filename

    candidates = [tool_fixture, shared_fixture]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"Required smoketest file not found: {filename} (looked in {tool_fixture} and {shared_fixture})"
    )


def load_config(*, tool_id: str, configs_dir: Path) -> SmokeConfig:
    config_path = configs_dir / f"{tool_id}.json"
    if not config_path.exists():
        return DEFAULT_CONFIG

    with config_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid config in {config_path}: expected JSON object.")

    unknown_root = sorted(set(raw.keys()).difference(ALLOWED_CONFIG_ROOT_KEYS))
    if unknown_root:
        raise ValueError(
            f"Invalid config in {config_path}: unknown keys {unknown_root}. "
            f"Allowed keys: {sorted(ALLOWED_CONFIG_ROOT_KEYS)}"
        )

    checks = raw.get("checks", {})
    if checks is None:
        checks = {}
    if not isinstance(checks, dict):
        raise ValueError(
            f"Invalid config in {config_path}: 'checks' must be an object."
        )

    unknown_checks = sorted(set(checks.keys()).difference(ALLOWED_CONFIG_CHECK_KEYS))
    if unknown_checks:
        raise ValueError(
            f"Invalid config in {config_path}: unknown checks keys {unknown_checks}. "
            f"Allowed checks keys: {sorted(ALLOWED_CONFIG_CHECK_KEYS)}"
        )

    extra_files = raw.get("extra_files", [])
    if not isinstance(extra_files, list) or not all(
        isinstance(x, str) for x in extra_files
    ):
        raise ValueError(
            f"Invalid config in {config_path}: 'extra_files' must be list[str]."
        )

    require_progress = bool(raw.get("require_progress", True))

    require_cluster_context = bool(checks.get("require_cluster_context", False))
    require_unique_unordered_pairs = bool(
        checks.get("require_unique_unordered_pairs", False)
    )
    forbid_self_loops = bool(checks.get("forbid_self_loops", False))

    return SmokeConfig(
        extra_files=extra_files,
        require_progress=require_progress,
        require_cluster_context=require_cluster_context,
        require_unique_unordered_pairs=require_unique_unordered_pairs,
        forbid_self_loops=forbid_self_loops,
    )


def load_aux_artifacts(catalog_tool_dir: Path) -> list[AuxArtifactSpec]:
    toolspec_path = catalog_tool_dir / "toolspec.json"
    with toolspec_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid toolspec in {toolspec_path}: expected JSON object.")

    entries = raw.get("artifacts_aux", [])
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise ValueError(
            f"Invalid toolspec in {toolspec_path}: 'artifacts_aux' must be an array."
        )

    out: list[AuxArtifactSpec] = []
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Invalid toolspec in {toolspec_path}: artifacts_aux[{idx}] must be an object."
            )
        path_pattern = entry.get("path_pattern")
        kind = entry.get("kind")
        require_non_empty = entry.get("require_non_empty", True)

        if not isinstance(path_pattern, str) or not path_pattern:
            raise ValueError(
                f"Invalid toolspec in {toolspec_path}: artifacts_aux[{idx}].path_pattern "
                f"must be a non-empty string."
            )
        if kind not in {"file", "dir"}:
            raise ValueError(
                f"Invalid toolspec in {toolspec_path}: artifacts_aux[{idx}].kind "
                f"must be 'file' or 'dir'."
            )
        if not isinstance(require_non_empty, bool):
            raise ValueError(
                f"Invalid toolspec in {toolspec_path}: artifacts_aux[{idx}].require_non_empty "
                f"must be boolean."
            )

        out.append(
            AuxArtifactSpec(
                path_pattern=path_pattern,
                kind=kind,
                require_non_empty=require_non_empty,
            )
        )

    return out


def build_image(
    *,
    tool_id: str,
    image_tag: str,
    catalog_tools_root: Path,
    tool_sources_root: Path,
    timeout_s: int,
) -> None:
    print(f"[1/5] Building Docker image: {image_tag}")
    cmd = [
        sys.executable,
        str(DEFAULT_BUILD_SCRIPT),
        "--catalog-tools-root",
        str(catalog_tools_root),
        "--tool-sources-root",
        str(tool_sources_root),
        "--tool",
        tool_id,
        "--image-tag",
        f"{tool_id}={image_tag}",
    ]
    result = run_cmd(cmd, cwd=REPO_ROOT, timeout_s=timeout_s)
    if result.returncode != 0:
        raise RuntimeError(
            f"Image build failed for {tool_id} (exit {result.returncode}).\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )


def start_container(image_tag: str, io_dir: Path, threads: int) -> str:
    cmd = [
        "docker",
        "run",
        "-d",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
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
    result = run_cmd(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(
            f"docker run failed (exit {result.returncode}).\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )

    container_id = (result.stdout or "").strip()
    if not container_id:
        raise RuntimeError("docker run returned empty container id.")
    return container_id


def inspect_status(container_id: str) -> str:
    result = run_cmd(
        ["docker", "inspect", "-f", "{{.State.Status}}", container_id],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        return "unknown"
    return (result.stdout or "").strip().lower()


def parse_progress(path: Path) -> tuple[int, str, str, str]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    percent = int(data.get("percent", 0))
    status = str(data.get("status", "unknown"))
    phase = str(data.get("phase", "unknown"))
    message = str(data.get("message", ""))
    return percent, status, phase, message


def wait_container(
    *,
    container_id: str,
    progress_file: Path,
    poll_interval_s: float,
    started_at: float,
    timeout_s: int,
) -> tuple[int, bool]:
    saw_progress = False
    last_snapshot: tuple[int, str, str, str] | None = None

    print("[3/5] Monitoring progress.json during execution")
    while True:
        if timeout_s > 0 and (time.perf_counter() - started_at) >= timeout_s:
            raise TimeoutError(f"Smoketest timeout reached ({timeout_s}s).")

        status = inspect_status(container_id)

        if progress_file.exists():
            saw_progress = True
            snapshot = parse_progress(progress_file)
            if snapshot != last_snapshot:
                percent, prog_status, phase, message = snapshot
                print(f"[progress] {percent}% | {prog_status} | {phase} | {message}")
                last_snapshot = snapshot

        if status in {"exited", "dead"}:
            break

        time.sleep(max(0.05, poll_interval_s))

    wait_result = run_cmd(["docker", "wait", container_id], cwd=REPO_ROOT)
    if wait_result.returncode != 0:
        raise RuntimeError(
            f"docker wait failed for {container_id} (exit {wait_result.returncode}).\n"
            f"stdout:\n{wait_result.stdout}\n\nstderr:\n{wait_result.stderr}"
        )

    exit_code_text = (wait_result.stdout or "").strip().splitlines()[-1]
    exit_code = int(exit_code_text)
    return exit_code, saw_progress


def cleanup_container(container_id: str) -> str:
    logs_result = run_cmd(["docker", "logs", container_id], cwd=REPO_ROOT)
    logs = logs_result.stdout or ""
    if logs_result.stderr:
        logs += ("\n" if logs else "") + logs_result.stderr

    _ = run_cmd(["docker", "rm", "-f", container_id], cwd=REPO_ROOT)
    return logs.strip()


def validate_progress(path: Path) -> None:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if data.get("status") != "completed":
        raise RuntimeError(
            f"Expected final status='completed', got: {data.get('status')!r}"
        )
    if int(data.get("percent", -1)) != 100:
        raise RuntimeError(f"Expected final percent=100, got: {data.get('percent')!r}")


def validate_network(path: Path, config: SmokeConfig) -> int:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(
            "Smoke test failed: /io/out/network.csv was not generated or is empty."
        )

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        missing = [c for c in REQUIRED_NETWORK_COLUMNS if c not in cols]
        if missing:
            raise RuntimeError(f"Missing columns in network.csv: {missing}")

        rows = list(reader)
        if not rows:
            raise RuntimeError("network.csv has header but no rows.")

    if config.require_cluster_context:
        if not any(str(row.get("context", "")).startswith("cluster:") for row in rows):
            raise RuntimeError("Expected at least one row with context='cluster:*'.")

    if config.forbid_self_loops:
        for row in rows:
            if str(row.get("source", "")) == str(row.get("target", "")):
                raise RuntimeError(
                    "Expected network.csv to exclude self-loops, but at least one row has source == target."
                )

    if config.require_unique_unordered_pairs:
        seen_pairs: set[tuple[str, str]] = set()
        for row in rows:
            pair = tuple(sorted((str(row.get("source", "")), str(row.get("target", "")))))
            if pair in seen_pairs:
                raise RuntimeError(
                    "Expected at most one row per unordered source/target pair, "
                    f"but found a duplicate pair: {pair!r}."
                )
            seen_pairs.add(pair)

    return len(rows)


def directory_has_nonempty_file(path: Path) -> bool:
    for candidate in path.rglob("*"):
        if candidate.is_file() and candidate.stat().st_size > 0:
            return True
    return False


def validate_aux_artifacts(out_dir: Path, specs: list[AuxArtifactSpec]) -> int:
    checked = 0
    for spec in specs:
        matches = sorted(out_dir.glob(spec.path_pattern))
        if not matches:
            raise RuntimeError(
                f"Missing auxiliary artifact for pattern '{spec.path_pattern}' in {out_dir}"
            )

        for match in matches:
            if spec.kind == "file":
                if not match.is_file():
                    raise RuntimeError(
                        f"Auxiliary artifact '{match.relative_to(out_dir)}' is not a file."
                    )
                if spec.require_non_empty and match.stat().st_size <= 0:
                    raise RuntimeError(
                        f"Auxiliary artifact '{match.relative_to(out_dir)}' is empty."
                    )
            else:
                if not match.is_dir():
                    raise RuntimeError(
                        f"Auxiliary artifact '{match.relative_to(out_dir)}' is not a directory."
                    )
                if spec.require_non_empty and not directory_has_nonempty_file(match):
                    raise RuntimeError(
                        f"Auxiliary artifact directory '{match.relative_to(out_dir)}' has no non-empty files."
                    )
            checked += 1

    return checked


def file_preview(path: Path, max_lines: int) -> str:
    if not path.exists():
        return "<missing>"

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if max_lines <= 0 or len(lines) <= max_lines:
        return "\n".join(lines) if lines else "<empty>"

    head = lines[:max_lines]
    omitted = len(lines) - max_lines
    return "\n".join(head + [f"... ({omitted} more lines omitted)"])


def directory_preview(path: Path, max_lines: int) -> str:
    if not path.exists():
        return "<missing>"
    if not path.is_dir():
        return "<not a directory>"

    entries: list[str] = []
    for candidate in sorted(path.rglob("*")):
        rel = candidate.relative_to(path)
        if candidate.is_dir():
            entries.append(f"{rel}/")
            continue
        if candidate.is_file():
            entries.append(f"{rel} ({candidate.stat().st_size} bytes)")
            continue
        entries.append(str(rel))

    if not entries:
        return "<empty directory>"

    if max_lines <= 0 or len(entries) <= max_lines:
        return "\n".join(entries)

    head = entries[:max_lines]
    omitted = len(entries) - max_lines
    return "\n".join(head + [f"... ({omitted} more entries omitted)"])


def print_output_files(
    out_dir: Path, max_lines: int, aux_specs: list[AuxArtifactSpec]
) -> None:
    progress_path = out_dir / "progress.json"
    network_path = out_dir / "network.csv"

    print("[output] progress.json")
    print(file_preview(progress_path, max_lines))
    print("[output] network.csv")
    print(file_preview(network_path, max_lines))

    if not aux_specs:
        return

    seen: set[Path] = set()
    for spec in aux_specs:
        matches = sorted(out_dir.glob(spec.path_pattern))
        if not matches:
            print(f"[output] {spec.path_pattern}")
            print("<missing>")
            continue

        for match in matches:
            rel = match.relative_to(out_dir)
            if rel in seen:
                continue
            seen.add(rel)
            print(f"[output] {rel}")
            if match.is_file():
                print(file_preview(match, max_lines))
            elif match.is_dir():
                print(directory_preview(match, max_lines))
            else:
                print("<unsupported filesystem type>")


def run_tool_smoketest(
    *,
    tool_id: str,
    catalog_tool_dir: Path,
    fixtures_dir: Path,
    smoketest_configs_dir: Path,
    catalog_tools_root: Path,
    param_overrides_dir: Path,
    tool_sources_root: Path,
    image_tag: str,
    threads: int,
    skip_image_build: bool,
    poll_interval_s: float,
    timeout_s: int,
    show_output: bool,
    show_output_lines: int,
) -> int:
    started_at = time.perf_counter()
    config = load_config(tool_id=tool_id, configs_dir=smoketest_configs_dir)
    aux_artifacts = load_aux_artifacts(catalog_tool_dir)
    tmp_ctx, io_paths = prepare_smoke_io(
        tool_id=tool_id,
        catalog_tools_root=catalog_tools_root,
        fixtures_dir=fixtures_dir,
        param_overrides_dir=param_overrides_dir,
        config=config,
    )

    try:
        if skip_image_build:
            print(
                f"[1/5] Skipping Docker image build (SKIP_IMAGE_BUILD=1): {image_tag}"
            )
        else:
            build_image(
                tool_id=tool_id,
                image_tag=image_tag,
                catalog_tools_root=catalog_tools_root,
                tool_sources_root=tool_sources_root,
                timeout_s=remaining_timeout(started_at, timeout_s),
            )

        print("[2/5] Running wrapper in container (detached)")
        exit_code, saw_progress, logs = run_container_lifecycle(
            image_tag=image_tag,
            io_dir=io_paths.io_dir,
            threads=threads,
            progress_file=io_paths.progress_file,
            poll_interval_s=poll_interval_s,
            started_at=started_at,
            timeout_s=timeout_s,
        )

        if logs:
            print("[container logs]")
            print(logs)

        if exit_code != 0:
            raise RuntimeError(
                f"Smoke test failed: container exited with code {exit_code}."
            )

        if config.require_progress and not saw_progress:
            raise RuntimeError("Smoke test failed: progress.json was never observed.")

        if io_paths.progress_file.exists():
            validate_progress(io_paths.progress_file)

        print("[4/5] Validating output file")
        row_count = validate_network(io_paths.out_dir / "network.csv", config)
        print(f"Validated network.csv with {row_count} rows")
        aux_count = validate_aux_artifacts(io_paths.out_dir, aux_artifacts)
        if aux_count > 0:
            print(f"Validated {aux_count} auxiliary artifact(s)")
    finally:
        try:
            if show_output:
                print_output_files(io_paths.out_dir, show_output_lines, aux_artifacts)
        finally:
            tmp_ctx.cleanup()

    print("[5/5] Smoke test passed")
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validate_cli_args(args)

    discovered = discover_catalog_tools(args.catalog_tools_root)
    selected = select_tools(discovered, args.tool)

    if args.list:
        print("Discovered tools for smoketests:")
        for tool_id, _catalog_tool_dir in selected:
            config_path = args.smoketest_configs_dir / f"{tool_id}.json"
            config_state = "config" if config_path.exists() else "default"
            params_path = args.param_overrides_dir / f"{tool_id}.json"
            params_state = "override" if params_path.exists() else "toolspec-defaults"
            print(f"  - {tool_id}: {config_state}, params={params_state}")
        return 0

    image_tags = parse_image_tag_overrides(args.image_tag)
    validate_image_tag_overrides(selected, image_tags)

    passed = 0
    failed = 0

    for tool_id, catalog_tool_dir in selected:
        tool_source_dir = args.tool_sources_root / tool_id
        if not tool_source_dir.exists() or not tool_source_dir.is_dir():
            print(
                f"[{tool_id}] FAILED (missing tool source directory: {tool_source_dir})"
            )
            failed += 1
            if args.fail_fast:
                break
            continue

        image_tag = image_tags.get(tool_id, default_image_tag(tool_id))

        print()
        print(f"[{tool_id}] running smoketest")
        started = time.perf_counter()
        try:
            run_tool_smoketest(
                tool_id=tool_id,
                catalog_tool_dir=catalog_tool_dir,
                fixtures_dir=args.fixtures_dir,
                smoketest_configs_dir=args.smoketest_configs_dir,
                catalog_tools_root=args.catalog_tools_root,
                param_overrides_dir=args.param_overrides_dir,
                tool_sources_root=args.tool_sources_root,
                image_tag=image_tag,
                threads=args.threads,
                skip_image_build=args.skip_image_build,
                poll_interval_s=max(0.05, args.poll_interval),
                timeout_s=args.timeout,
                show_output=args.show_output,
                show_output_lines=args.show_output_lines,
            )
        except TimeoutError:
            elapsed = time.perf_counter() - started
            print(f"[{tool_id}] FAILED (timeout after {elapsed:.1f}s)")
            failed += 1
            if args.fail_fast:
                break
            continue
        except Exception as exc:
            elapsed = time.perf_counter() - started
            print(f"[{tool_id}] FAILED ({elapsed:.1f}s): {exc}")
            failed += 1
            if args.fail_fast:
                break
            continue

        elapsed = time.perf_counter() - started
        print(f"[{tool_id}] PASSED ({elapsed:.1f}s)")
        passed += 1

    print()
    print(f"Summary: passed={passed} failed={failed}")
    return 0 if failed == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
