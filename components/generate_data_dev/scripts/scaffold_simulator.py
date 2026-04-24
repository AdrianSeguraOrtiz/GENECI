"""Scaffold files for a new generate-v2 simulator integration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_simulators import (
    DEFAULT_CATALOG_SIMULATORS_ROOT,
    DEFAULT_SMOKETEST_CONFIGS_ROOT,
    DEFAULT_WRAPPERS_ROOT,
    expected_docker_image,
)

SIMULATOR_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
WRAPPER_RE = re.compile(r"^[a-z0-9][a-z0-9_.+-]*$")
WRAPPER_EXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

WRAPPER_EXTENSION_MAP = {
    "python": "py",
    "r": "R",
    "bash": "sh",
    "sh": "sh",
    "shell": "sh",
}

RUNTIME_ENTRYPOINTS = {
    "python": ("python", "/app/run_simulator.py"),
    "r": ("Rscript", "/app/run_simulator.R"),
    "bash": ("bash", "/app/run_simulator.sh"),
    "sh": ("bash", "/app/run_simulator.sh"),
    "shell": ("bash", "/app/run_simulator.sh"),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create scaffold files for a new simulator integration."
    )
    parser.add_argument(
        "--simulator",
        required=True,
        help="Stable simulator id (lowercase, digits, underscore, hyphen).",
    )
    parser.add_argument(
        "--wrapper",
        default="python",
        help="Initial wrapper language scaffold. Known templates: python, r, bash.",
    )
    parser.add_argument(
        "--wrapper-ext",
        default=None,
        help="Override wrapper script extension.",
    )
    parser.add_argument(
        "--wrappers-root",
        type=Path,
        default=DEFAULT_WRAPPERS_ROOT,
        help=f"Path to simulator wrapper directories. Default: {DEFAULT_WRAPPERS_ROOT}",
    )
    parser.add_argument(
        "--catalog-simulators-root",
        type=Path,
        default=DEFAULT_CATALOG_SIMULATORS_ROOT,
        help=f"Path to catalog simulators directory. Default: {DEFAULT_CATALOG_SIMULATORS_ROOT}",
    )
    parser.add_argument(
        "--smoketest-configs-root",
        type=Path,
        default=DEFAULT_SMOKETEST_CONFIGS_ROOT,
        help=f"Path to smoketest config directory. Default: {DEFAULT_SMOKETEST_CONFIGS_ROOT}",
    )
    parser.add_argument(
        "--activate-catalog",
        action="store_true",
        help="Write an active catalog simulatorspec.json. By default only a draft is created in the wrapper dir.",
    )
    parser.add_argument(
        "--activate-smoketest",
        action="store_true",
        help="Write an active smoketest config. By default only a draft is created in the wrapper dir.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files created by this scaffold.",
    )
    return parser.parse_args(argv)


def write_file(path: Path, content: str, *, force: bool) -> str:
    if path.exists() and not force:
        return "exists"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "written"


def write_json(path: Path, payload: dict[str, object], *, force: bool) -> str:
    return write_file(
        path,
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        force=force,
    )


def dockerfile_template(wrapper: str, script_name: str) -> str:
    runtime_bin, app_script = RUNTIME_ENTRYPOINTS.get(
        wrapper,
        ("bash", f"/app/{script_name}"),
    )
    return f"""FROM ubuntu:24.04

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates python3 r-base \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY components/generate_data_dev/generators/{{simulator_id}}/{script_name} /app/{script_name}

ENTRYPOINT ["{runtime_bin}", "{app_script}", "--request", "/work/request/simulator-run-request.json", "--output-dir", "/work/out"]
"""


def wrapper_template(wrapper: str) -> str:
    if wrapper == "python":
        return '''"""TODO: implement simulator wrapper.

The wrapper must read --request and --output-dir, then write:
- expression.tsv
- truth/global_network.csv
- truth/legacy/global_gs.csv
- simulator-output-manifest.json
- progress.json
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-dir", required=True)
    _args = parser.parse_args()
    raise NotImplementedError("Implement simulator wrapper")


if __name__ == "__main__":
    raise SystemExit(main())
'''
    if wrapper == "r":
        return """#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
stop("TODO: implement simulator wrapper")
"""
    return """#!/usr/bin/env bash
set -euo pipefail
echo "TODO: implement simulator wrapper" >&2
exit 1
"""


def spec_payload(simulator_id: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "id": simulator_id,
        "name": simulator_id,
        "publication": ["TODO_PUBLICATION_URL"],
        "first_author": "TODO",
        "year": 2026,
        "simulation_summary": "TODO: describe simulator scope and assumptions.",
        "simulation_keywords": ["todo"],
        "implementation_url": "TODO_IMPLEMENTATION_URL",
        "docker_image": expected_docker_image(simulator_id),
        "simulator_inputs": {"required": [], "optional": []},
        "profile_capabilities": {
            "scrna_global": {
                "native_extras": [],
                "derivable_extras": [],
                "truth_outputs": {
                    "global_network": "native",
                    "legacy_binary_matrix": "derivable",
                    "group_networks": "none",
                },
                "derivations": [
                    {
                        "artifact": "legacy_binary_matrix",
                        "source_artifacts": ["truth/global_network.csv"],
                        "method": "TODO: describe how this derived artifact is computed.",
                        "assumptions": ["TODO: describe derivation assumptions."],
                        "limitations": ["TODO: describe information loss or caveats."],
                        "implemented_in": f"components/generate_data_dev/generators/{simulator_id}/run_simulator",
                    }
                ],
                "artifacts_aux": [],
                "notes": "TODO: replace with the real supported profile capabilities.",
            }
        },
        "params": {},
        "notes": "Draft scaffold. Do not activate until reviewed against paper and implementation.",
    }


def smoketest_payload(simulator_id: str) -> dict[str, object]:
    return {
        "simulator_id": simulator_id,
        "request": {
            "profile": "scrna_global",
            "seed": 1,
            "effective_extras": [],
            "input_files": {},
            "params": {},
        },
        "expect_progress": True,
        "required_files": [
            "expression.tsv",
            "truth/global_network.csv",
            "truth/legacy/global_gs.csv",
            "simulator-output-manifest.json",
            "progress.json",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    simulator_id = args.simulator.strip()
    wrapper = args.wrapper.strip().lower()
    wrapper_ext = args.wrapper_ext or WRAPPER_EXTENSION_MAP.get(wrapper, wrapper)

    if not SIMULATOR_ID_RE.match(simulator_id):
        print(f"ERROR: invalid simulator id: {simulator_id}", file=sys.stderr)
        return 2
    if not WRAPPER_RE.match(wrapper):
        print(f"ERROR: invalid wrapper name: {wrapper}", file=sys.stderr)
        return 2
    if not WRAPPER_EXT_RE.match(wrapper_ext):
        print(f"ERROR: invalid wrapper extension: {wrapper_ext}", file=sys.stderr)
        return 2

    wrapper_dir = args.wrappers_root / simulator_id
    script_name = f"run_simulator.{wrapper_ext}"

    outputs: list[tuple[Path, str]] = []
    dockerfile = dockerfile_template(wrapper, script_name).replace(
        "{simulator_id}", simulator_id
    )
    outputs.append(
        (
            wrapper_dir / "Dockerfile",
            write_file(wrapper_dir / "Dockerfile", dockerfile, force=args.force),
        )
    )
    outputs.append(
        (
            wrapper_dir / script_name,
            write_file(
                wrapper_dir / script_name, wrapper_template(wrapper), force=args.force
            ),
        )
    )
    outputs.append(
        (
            wrapper_dir / "README.md",
            write_file(
                wrapper_dir / "README.md",
                f"# {simulator_id}\\n\\nTODO: document installation, wrapper behavior, and smoke tests.\\n",
                force=args.force,
            ),
        )
    )
    outputs.append(
        (
            wrapper_dir / "integration_decisions.md",
            write_file(
                wrapper_dir / "integration_decisions.md",
                f"# {simulator_id} Integration Decisions\\n\\nTODO: record paper/repo review and wrapper decisions.\\n",
                force=args.force,
            ),
        )
    )

    draft_spec = wrapper_dir / "simulatorspec.draft.json"
    active_spec = args.catalog_simulators_root / simulator_id / "simulatorspec.json"
    outputs.append(
        (
            active_spec if args.activate_catalog else draft_spec,
            write_json(
                active_spec if args.activate_catalog else draft_spec,
                spec_payload(simulator_id),
                force=args.force,
            ),
        )
    )

    draft_smoke = wrapper_dir / "smoketest.config.draft.json"
    active_smoke = args.smoketest_configs_root / f"{simulator_id}_basic.json"
    outputs.append(
        (
            active_smoke if args.activate_smoketest else draft_smoke,
            write_json(
                active_smoke if args.activate_smoketest else draft_smoke,
                smoketest_payload(simulator_id),
                force=args.force,
            ),
        )
    )

    for path, status in outputs:
        print(f"[{status}] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
