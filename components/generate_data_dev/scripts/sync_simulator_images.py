"""List, pull, or push simulator images defined in SimulatorSpecs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_simulators import (
    DEFAULT_CATALOG_SIMULATORS_ROOT,
    discover_catalog_simulator_dirs,
    load_required_simulatorspec_string,
    select_simulators,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List, pull, or push Docker images referenced by SimulatorSpecs."
    )
    parser.add_argument(
        "action",
        choices=("list", "pull", "push"),
        help="Action to perform on simulator images.",
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        help="Simulator id to operate on (repeatable). If omitted, uses all catalog simulators.",
    )
    parser.add_argument(
        "--image-tag",
        action="append",
        default=[],
        help="Per-simulator image tag override, format: SIMULATOR_ID=IMAGE_TAG.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first docker pull/push failure.",
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


def docker_sync(action: str, image: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["docker", action, image],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "").strip()


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
        except RuntimeError as exc:
            failures.append(f"{simulator_id}: {exc}")
            print(f"[{simulator_id}] FAILED: {exc}", file=sys.stderr)
            if args.fail_fast:
                break
            continue

        if args.action == "list":
            print(f"{simulator_id}\t{image}")
            continue

        print(f"[{simulator_id}] docker {args.action} {image}")
        ok, details = docker_sync(args.action, image)
        if ok:
            print(f"[{simulator_id}] {args.action}ed")
            continue

        failures.append(f"{simulator_id}: {details}")
        print(f"[{simulator_id}] FAILED: {details}", file=sys.stderr)
        if args.fail_fast:
            break

    if failures:
        print("Simulator image sync failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
