"""Run simulator smoketests for selected or all catalog simulators."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator

from shared.catalog_simulators import (
    CATALOG_ROOT,
    DEFAULT_CATALOG_SIMULATORS_ROOT,
    DEFAULT_SMOKETEST_CONFIGS_ROOT,
    DEFAULT_SMOKETEST_SCHEMA_PATH,
    DEFAULT_WRAPPERS_ROOT,
    REPO_ROOT,
    discover_catalog_simulator_dirs,
    load_json,
    load_simulatorspec,
    select_simulators,
)

SIMULATOR_OUTPUT_SCHEMA_PATH = (
    CATALOG_ROOT / "schemas" / "simulator-output-manifest.schema.json"
)
_BUILT_IMAGES: set[str] = set()


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def _ensure_docker() -> None:
    result = _run(["docker", "info"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Docker is not available: {details}")


def _schema_errors(
    *,
    validator: Draft202012Validator,
    payload: dict[str, Any],
) -> list[str]:
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    return [".".join(str(x) for x in err.path) + f" -> {err.message}" for err in errors]


def _load_smoketest_configs(
    *,
    simulator_id: str,
    configs_root: Path,
    schema_validator: Draft202012Validator,
) -> list[tuple[Path, dict[str, Any]]]:
    configs: list[tuple[Path, dict[str, Any]]] = []
    for config_path in sorted(configs_root.glob("*.json")):
        config = load_json(config_path)
        if not isinstance(config, dict):
            raise RuntimeError(
                f"Invalid smoketest config {config_path}: expected object"
            )
        if config.get("simulator_id") != simulator_id:
            continue
        errors = _schema_errors(validator=schema_validator, payload=config)
        if errors:
            raise RuntimeError(
                f"Invalid smoketest config {config_path.name}: " + "; ".join(errors)
            )
        configs.append((config_path, config))
    if not configs:
        raise RuntimeError(f"Missing smoketest configs for: {simulator_id}")
    return configs


def _build_image(
    *,
    simulator_id: str,
    image: str,
    wrappers_root: Path,
) -> None:
    dockerfile = wrappers_root / simulator_id / "Dockerfile"
    if not dockerfile.exists():
        raise RuntimeError(f"Missing Dockerfile for {simulator_id}: {dockerfile}")
    if image in _BUILT_IMAGES:
        return
    result = subprocess.run(
        [
            "docker",
            "build",
            "-f",
            str(dockerfile),
            "-t",
            image,
            str(REPO_ROOT),
        ],
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"[{simulator_id}] docker build failed with exit code {result.returncode}"
        )
    _BUILT_IMAGES.add(image)


def _validate_manifest(simulator_id: str, out_dir: Path) -> None:
    manifest_path = out_dir / "simulator-output-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"[{simulator_id}] missing simulator-output-manifest.json")
    manifest = load_json(manifest_path)
    validator = Draft202012Validator(load_json(SIMULATOR_OUTPUT_SCHEMA_PATH))
    errors = _schema_errors(validator=validator, payload=manifest)
    if errors:
        raise RuntimeError(
            f"[{simulator_id}] invalid simulator-output-manifest.json: "
            + "; ".join(errors)
        )


def _assert_required_files(
    simulator_id: str,
    out_dir: Path,
    required_files: list[str],
) -> None:
    for rel_path in required_files:
        path = out_dir / rel_path
        if not path.exists():
            raise RuntimeError(
                f"[{simulator_id}] missing required smoketest artifact: {rel_path}"
            )
        if path.is_file() and path.stat().st_size == 0:
            raise RuntimeError(
                f"[{simulator_id}] empty required smoketest artifact: {rel_path}"
            )


def _stage_input_files(
    *,
    config_path: Path,
    config: dict[str, Any],
    inputs_dir: Path,
) -> dict[str, str]:
    container_input_files: dict[str, str] = {}
    raw_input_files = dict(config["request"].get("input_files", {}))
    for input_id, raw_path in raw_input_files.items():
        source_path = Path(str(raw_path)).expanduser()
        if not source_path.is_absolute():
            source_path = (config_path.parent / source_path).resolve()
        if not source_path.exists():
            raise RuntimeError(
                f"[{config['simulator_id']}:{config_path.stem}] input file not found: {source_path}"
            )
        staged_path = inputs_dir / input_id
        if source_path.is_dir():
            shutil.copytree(source_path, staged_path)
        else:
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, staged_path)
        container_input_files[input_id] = f"/work/inputs/{input_id}"
    return container_input_files


def _run_one_config(
    *,
    simulator_id: str,
    image: str,
    config_path: Path,
    config: dict[str, Any],
    show_output: bool,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"geneci_smoketest_{simulator_id}_") as tmp:
        tmp_path = Path(tmp)
        request_dir = tmp_path / "request"
        inputs_dir = tmp_path / "inputs"
        out_dir = tmp_path / "out"
        request_dir.mkdir(parents=True, exist_ok=True)
        inputs_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        container_input_files = _stage_input_files(
            config_path=config_path,
            config=config,
            inputs_dir=inputs_dir,
        )
        request_payload = {
            "schema_version": "1.0",
            "simulator_id": simulator_id,
            "profile": config["request"]["profile"],
            "seed": int(config["request"].get("seed", 1)),
            "effective_extras": list(config["request"]["effective_extras"]),
            "input_files": container_input_files,
            "params": dict(config["request"]["params"]),
            "output_dir_in_container": "/work/out",
        }
        request_path = request_dir / "simulator-run-request.json"
        request_path.write_text(
            json.dumps(request_payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

        cmd = ["docker", "run", "--rm"]
        if hasattr(os, "getuid") and hasattr(os, "getgid"):
            cmd.extend(["--user", f"{os.getuid()}:{os.getgid()}"])
        cmd.extend(
            [
                "-v",
                f"{request_dir}:/work/request:ro",
                "-v",
                f"{inputs_dir}:/work/inputs:ro",
                "-v",
                f"{out_dir}:/work/out",
                image,
            ]
        )

        proc = subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        progress_seen = False
        progress_path = out_dir / "progress.json"
        while proc.poll() is None:
            if progress_path.exists():
                progress_seen = True
            time.sleep(0.5)
        stdout, stderr = proc.communicate()
        if progress_path.exists():
            progress_seen = True

        if proc.returncode != 0:
            details = (stderr or stdout or "").strip()
            raise RuntimeError(
                f"[{simulator_id}:{config_path.stem}] docker run failed: {details}"
            )
        if config["expect_progress"] and not progress_seen:
            raise RuntimeError(
                f"[{simulator_id}:{config_path.stem}] progress.json was never observed"
            )

        _validate_manifest(simulator_id, out_dir)
        _assert_required_files(
            simulator_id,
            out_dir,
            list(config["required_files"]),
        )

        if show_output:
            print(f"[{simulator_id}:{config_path.stem}] progress.json")
            print(progress_path.read_text(encoding="utf-8"))
            print(f"[{simulator_id}:{config_path.stem}] simulator-output-manifest.json")
            print(
                (out_dir / "simulator-output-manifest.json").read_text(encoding="utf-8")
            )


def _run_smoketest(
    *,
    simulator_id: str,
    catalog_simulators_root: Path,
    configs_root: Path,
    wrappers_root: Path,
    schema_validator: Draft202012Validator,
    skip_build: bool,
    show_output: bool,
) -> None:
    spec = load_simulatorspec(catalog_simulators_root, simulator_id)
    image = str(spec["docker_image"])
    if not skip_build:
        _build_image(
            simulator_id=simulator_id, image=image, wrappers_root=wrappers_root
        )
    for config_path, config in _load_smoketest_configs(
        simulator_id=simulator_id,
        configs_root=configs_root,
        schema_validator=schema_validator,
    ):
        _run_one_config(
            simulator_id=simulator_id,
            image=image,
            config_path=config_path,
            config=config,
            show_output=show_output,
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run generate-v2 simulator smoketests."
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--configs-root",
        type=Path,
        default=DEFAULT_SMOKETEST_CONFIGS_ROOT,
        help=f"Path to smoketest config directory. Default: {DEFAULT_SMOKETEST_CONFIGS_ROOT}",
    )
    parser.add_argument(
        "--wrappers-root",
        type=Path,
        default=DEFAULT_WRAPPERS_ROOT,
        help=f"Path to simulator wrapper directories. Default: {DEFAULT_WRAPPERS_ROOT}",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SMOKETEST_SCHEMA_PATH,
        help=f"Path to smoketest config schema. Default: {DEFAULT_SMOKETEST_SCHEMA_PATH}",
    )
    parser.add_argument(
        "--simulator",
        dest="simulators",
        action="append",
        help="Simulator id to test. Repeatable. Defaults to all catalog simulators.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not build images before running containers.",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print progress.json and simulator-output-manifest.json after successful runs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _ensure_docker()
        discovered = discover_catalog_simulator_dirs(args.catalog_simulators_root)
        selected = select_simulators(discovered, args.simulators or [])
        schema_validator = Draft202012Validator(load_json(args.schema))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    for simulator_id, _simulator_dir in selected:
        print(f"[{simulator_id}] running smoketest", flush=True)
        try:
            _run_smoketest(
                simulator_id=simulator_id,
                catalog_simulators_root=args.catalog_simulators_root,
                configs_root=args.configs_root,
                wrappers_root=args.wrappers_root,
                schema_validator=schema_validator,
                skip_build=args.skip_build,
                show_output=args.show_output,
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{simulator_id}: {exc}")
            print(f"[{simulator_id}] FAILED: {exc}", file=sys.stderr, flush=True)
        else:
            print(f"[{simulator_id}] passed", flush=True)

    if failures:
        print("Simulator smoketests failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
