"""Run simulator smoketests for selected or all configured simulators."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIGS_DIR = REPO_ROOT / "components" / "generate_data_dev" / "tests" / "smoketest_configs"
SCHEMA_PATH = (
    REPO_ROOT
    / "components"
    / "generate_data_dev"
    / "tests"
    / "schemas"
    / "smoketest.config.schema.json"
)
SIMULATOR_SCHEMA_PATH = (
    REPO_ROOT
    / "geneci"
    / "generation_catalog"
    / "schemas"
    / "simulator-output-manifest.schema.json"
)
GENERATORS_ROOT = REPO_ROOT / "geneci" / "generation_catalog" / "simulators"
WRAPPERS_ROOT = REPO_ROOT / "components" / "generate_data_dev" / "generators"
_BUILT_IMAGES: set[str] = set()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def _ensure_docker() -> None:
    result = _run(["docker", "info"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Docker is not available: {details}")


def _load_smoketest_configs(simulator_id: str) -> list[tuple[Path, dict[str, Any]]]:
    config_paths = sorted(CONFIGS_DIR.glob(f"{simulator_id}*.json"))
    if not config_paths:
        raise RuntimeError(f"Missing smoketest configs for: {simulator_id}")

    validator = Draft202012Validator(_load_json(SCHEMA_PATH))
    configs: list[tuple[Path, dict[str, Any]]] = []
    for config_path in config_paths:
        config = _load_json(config_path)
        errors = sorted(validator.iter_errors(config), key=lambda err: list(err.path))
        if errors:
            joined = "; ".join(f"{list(err.path)} -> {err.message}" for err in errors)
            raise RuntimeError(f"Invalid smoketest config {config_path.name}: {joined}")
        if config["simulator_id"] != simulator_id:
            raise RuntimeError(
                f"Smoketest config {config_path.name} declares simulator_id={config['simulator_id']!r}, "
                f"expected {simulator_id!r}"
            )
        configs.append((config_path, config))
    return configs


def _load_simulator_spec(simulator_id: str) -> dict[str, Any]:
    spec_path = GENERATORS_ROOT / simulator_id / "simulatorspec.json"
    if not spec_path.exists():
        raise RuntimeError(f"Missing SimulatorSpec: {spec_path}")
    return _load_json(spec_path)


def _build_image(simulator_id: str, image: str) -> None:
    dockerfile = WRAPPERS_ROOT / simulator_id / "Dockerfile"
    if not dockerfile.exists():
        raise RuntimeError(f"Missing Dockerfile for {simulator_id}: {dockerfile}")
    if image in _BUILT_IMAGES:
        return
    result = _run(
        [
          "docker",
          "build",
          "-f",
          str(dockerfile),
          "-t",
          image,
          str(REPO_ROOT),
        ]
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"[{simulator_id}] docker build failed: {details}")
    _BUILT_IMAGES.add(image)


def _validate_manifest(simulator_id: str, out_dir: Path) -> None:
    manifest_path = out_dir / "simulator-output-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"[{simulator_id}] missing simulator-output-manifest.json")
    manifest = _load_json(manifest_path)
    validator = Draft202012Validator(_load_json(SIMULATOR_SCHEMA_PATH))
    errors = sorted(validator.iter_errors(manifest), key=lambda err: list(err.path))
    if errors:
        joined = "; ".join(f"{list(err.path)} -> {err.message}" for err in errors)
        raise RuntimeError(f"[{simulator_id}] invalid simulator-output-manifest.json: {joined}")


def _assert_required_files(simulator_id: str, out_dir: Path, required_files: list[str]) -> None:
    for rel_path in required_files:
        path = out_dir / rel_path
        if not path.exists():
            raise RuntimeError(f"[{simulator_id}] missing required smoketest artifact: {rel_path}")
        if path.is_file() and path.stat().st_size == 0:
            raise RuntimeError(f"[{simulator_id}] empty required smoketest artifact: {rel_path}")


def _run_smoketest(simulator_id: str, show_output: bool) -> None:
    spec = _load_simulator_spec(simulator_id)
    image = str(spec["docker_image"])
    _build_image(simulator_id, image)
    for config_path, config in _load_smoketest_configs(simulator_id):
        with tempfile.TemporaryDirectory(prefix=f"geneci_smoketest_{simulator_id}_") as tmp:
            tmp_path = Path(tmp)
            request_dir = tmp_path / "request"
            out_dir = tmp_path / "out"
            request_dir.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)

            request_payload = {
                "schema_version": "1.0",
                "simulator_id": simulator_id,
                "profile": config["request"]["profile"],
                "seed": int(config["request"].get("seed", 1)),
                "effective_extras": list(config["request"]["effective_extras"]),
                "input_files": dict(config["request"].get("input_files", {})),
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
                raise RuntimeError(f"[{simulator_id}:{config_path.stem}] docker run failed: {details}")
            if config["expect_progress"] and not progress_seen:
                raise RuntimeError(f"[{simulator_id}:{config_path.stem}] progress.json was never observed")

            _validate_manifest(simulator_id, out_dir)
            _assert_required_files(simulator_id, out_dir, list(config["required_files"]))

            if show_output:
                print(f"[{simulator_id}:{config_path.stem}] progress.json")
                print(progress_path.read_text(encoding="utf-8"))
                print(f"[{simulator_id}:{config_path.stem}] simulator-output-manifest.json")
                print((out_dir / "simulator-output-manifest.json").read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run generate-data docker smoketests.")
    parser.add_argument(
        "--simulator",
        dest="simulators",
        action="append",
        help="Simulator id to test. Repeatable. Defaults to all configured simulators.",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print progress.json and simulator-output-manifest.json after successful runs.",
    )
    args = parser.parse_args(argv)

    _ensure_docker()
    available = sorted(
        {
            path.name.split("_", 1)[0]
            for path in CONFIGS_DIR.glob("*.json")
        }
    )
    simulators = args.simulators or available

    failures: list[str] = []
    for simulator_id in simulators:
      print(f"[{simulator_id}] running smoketest")
      try:
        _run_smoketest(simulator_id, args.show_output)
      except Exception as exc:  # noqa: BLE001
        failures.append(f"{simulator_id}: {exc}")
        print(f"[{simulator_id}] FAILED: {exc}", file=sys.stderr)
      else:
        print(f"[{simulator_id}] passed")

    if failures:
      print("Simulator smoketests failed:", file=sys.stderr)
      for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
      return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
