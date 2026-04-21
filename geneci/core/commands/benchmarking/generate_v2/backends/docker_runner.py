"""Docker backend runner for generate-v2."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..shared import REPO_ROOT, ResolvedBenchmarkRequest, _write_json

_BUILT_IMAGES: set[str] = set()
_PULLED_IMAGES: set[str] = set()


def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=True,
    )


def _ensure_docker_cli() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI is not available in PATH")
    result = _run_cmd(["docker", "info"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Docker daemon is not available. Details: {details}")


def _docker_image_exists(image: str) -> bool:
    result = _run_cmd(["docker", "image", "inspect", image])
    return result.returncode == 0


def _resolve_wrapper_dir(simulator_id: str) -> Path:
    return (
        REPO_ROOT
        / "components"
        / "generate_data_dev"
        / "generators"
        / simulator_id
    ).resolve()


def _build_local_image(*, simulator_id: str, image: str) -> str:
    wrapper_dir = _resolve_wrapper_dir(simulator_id)
    dockerfile = wrapper_dir / "Dockerfile"
    if not dockerfile.exists():
        raise RuntimeError(
            f"Dockerfile not found for simulator '{simulator_id}': {dockerfile}"
        )
    if image in _BUILT_IMAGES and _docker_image_exists(image):
        return "built_local"

    result = _run_cmd(
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
        raise RuntimeError(
            f"Failed to build local docker image '{image}' for simulator '{simulator_id}': {details}"
        )
    _BUILT_IMAGES.add(image)
    return "built_local"


def _pull_image(*, image: str) -> str:
    if image in _PULLED_IMAGES and _docker_image_exists(image):
        return "pulled"
    result = _run_cmd(["docker", "pull", image])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Failed to pull docker image '{image}': {details}")
    _PULLED_IMAGES.add(image)
    return "pulled"


def _ensure_docker_image(*, simulator_id: str, image: str) -> str:
    wrapper_dir = _resolve_wrapper_dir(simulator_id)
    dockerfile = wrapper_dir / "Dockerfile"
    if dockerfile.exists():
        try:
            return _build_local_image(simulator_id=simulator_id, image=image)
        except RuntimeError as exc:
            build_error = str(exc)
    elif _docker_image_exists(image):
        return "local"
    else:
        build_error = None

    try:
        return _pull_image(image=image)
    except RuntimeError as exc:
        pull_error = str(exc)

    message = [f"Could not prepare docker image '{image}' for '{simulator_id}'."]
    if build_error:
        message.append(build_error)
    message.append(pull_error)
    raise RuntimeError(" ".join(message))


def run_docker_simulator(
    *,
    request: ResolvedBenchmarkRequest,
    seed: int,
    stage_dir: Path,
) -> Path:
    image = str(request.simulator_spec.get("docker_image", "")).strip()
    if not image:
        raise RuntimeError(
            f"Simulator '{request.simulator_id}' has no docker_image"
        )

    _ensure_docker_cli()
    image_origin = _ensure_docker_image(simulator_id=request.simulator_id, image=image)

    stage_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = stage_dir / "provenance" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"geneci_generate_v2_{request.simulator_id}_") as tmp:
        request_dir = Path(tmp) / "request"
        inputs_dir = Path(tmp) / "inputs"
        request_dir.mkdir(parents=True, exist_ok=True)
        inputs_dir.mkdir(parents=True, exist_ok=True)
        container_input_files: dict[str, str] = {}
        for input_id, source_path in request.resolved_input_files.items():
            staged_path = inputs_dir / input_id
            if source_path.is_dir():
                shutil.copytree(source_path, staged_path)
            else:
                shutil.copy2(source_path, staged_path)
            container_input_files[input_id] = f"/work/inputs/{input_id}"

        request_payload = {
            "schema_version": "1.0",
            "simulator_id": request.simulator_id,
            "profile": request.profile,
            "seed": int(seed),
            "effective_extras": list(request.effective_extras),
            "input_files": container_input_files,
            "params": dict(request.simulator_params),
            "output_dir_in_container": "/work/out",
        }
        request_path = request_dir / "simulator-run-request.json"
        _write_json(request_path, request_payload)

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
                f"{stage_dir}:/work/out",
                image,
            ]
        )

        completed = _run_cmd(cmd)
        (raw_dir / "docker_wrapper.stdout.log").write_text(
            completed.stdout, encoding="utf-8"
        )
        (raw_dir / "docker_wrapper.stderr.log").write_text(
            completed.stderr, encoding="utf-8"
        )
        (raw_dir / "docker_wrapper.request.json").write_text(
            request_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (raw_dir / "docker_wrapper.image.txt").write_text(
            image + "\n", encoding="utf-8"
        )
        (raw_dir / "docker_wrapper.image_origin.txt").write_text(
            image_origin + "\n", encoding="utf-8"
        )
        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                f"Docker simulator '{request.simulator_id}' failed with exit code "
                f"{completed.returncode}: {details}"
            )

    manifest_path = stage_dir / "simulator-output-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(
            f"Docker simulator '{request.simulator_id}' did not produce simulator-output-manifest.json"
        )
    return manifest_path
