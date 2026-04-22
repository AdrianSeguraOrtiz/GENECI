"""Build simulator Docker images from generate-data wrapper directories."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_simulators import (
    DEFAULT_CATALOG_SIMULATORS_ROOT,
    DEFAULT_WRAPPERS_ROOT,
    REPO_ROOT,
    discover_catalog_simulator_dirs,
    load_required_simulatorspec_string,
    select_simulators,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Docker images referenced by catalog SimulatorSpecs."
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--wrappers-root",
        type=Path,
        default=DEFAULT_WRAPPERS_ROOT,
        help=f"Path to simulator wrapper directories. Default: {DEFAULT_WRAPPERS_ROOT}",
    )
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        help="Simulator id to build (repeatable). If omitted, builds every catalog simulator.",
    )
    parser.add_argument(
        "--image-tag",
        action="append",
        default=[],
        help="Per-simulator image tag override, format: SIMULATOR_ID=IMAGE_TAG.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass --no-cache to docker build.",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pass --pull to docker build.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print docker build commands without executing them.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed build.",
    )
    return parser.parse_args(argv)


def parse_tag_overrides(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise RuntimeError(
                f"Invalid --image-tag '{item}'. Expected format: SIMULATOR_ID=IMAGE_TAG"
            )
        simulator_id, tag = item.split("=", 1)
        simulator_id = simulator_id.strip()
        tag = tag.strip()
        if not simulator_id or not tag:
            raise RuntimeError(
                f"Invalid --image-tag '{item}'. Expected format: SIMULATOR_ID=IMAGE_TAG"
            )
        out[simulator_id] = tag
    return out


def build_command(
    *,
    dockerfile: Path,
    image: str,
    no_cache: bool,
    pull: bool,
) -> list[str]:
    cmd = ["docker", "build"]
    if no_cache:
        cmd.append("--no-cache")
    if pull:
        cmd.append("--pull")
    cmd.extend(["-f", str(dockerfile), "-t", image, str(REPO_ROOT)])
    return cmd


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        tag_overrides = parse_tag_overrides(args.image_tag)
        discovered = discover_catalog_simulator_dirs(args.catalog_simulators_root)
        selected = select_simulators(discovered, args.simulator)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    for simulator_id, _simulator_dir in selected:
        try:
            image = tag_overrides.get(
                simulator_id,
                load_required_simulatorspec_string(
                    simulator_id=simulator_id,
                    catalog_simulators_root=args.catalog_simulators_root,
                    field_name="docker_image",
                ),
            )
            dockerfile = args.wrappers_root / simulator_id / "Dockerfile"
            if not dockerfile.exists():
                raise RuntimeError(f"missing Dockerfile: {dockerfile}")

            cmd = build_command(
                dockerfile=dockerfile,
                image=image,
                no_cache=args.no_cache,
                pull=args.pull,
            )
            print(f"[{simulator_id}] {' '.join(cmd)}", flush=True)
            if not args.dry_run:
                result = subprocess.run(cmd, text=True, check=False)
                if result.returncode != 0:
                    raise RuntimeError(
                        f"docker build failed with exit code {result.returncode}"
                    )
        except RuntimeError as exc:
            message = f"{simulator_id}: {exc}"
            failures.append(message)
            print(f"[{simulator_id}] FAILED: {exc}", file=sys.stderr)
            if args.fail_fast:
                break
        else:
            print(f"[{simulator_id}] built", flush=True)

    if failures:
        print("Simulator image builds failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
