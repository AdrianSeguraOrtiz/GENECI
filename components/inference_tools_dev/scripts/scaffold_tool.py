"""Scaffold files for a new infer-network-v2 tool integration.

Usage examples:
1) Create a Python-wrapper scaffold:
   python scaffold_tool.py --tool mytool

2) Create an R-wrapper scaffold:
   python scaffold_tool.py --tool mytool --wrapper r

3) Create a generic scaffold for another language:
   python scaffold_tool.py --tool mytool --wrapper matlab

4) Override the file extension for a generic scaffold:
   python scaffold_tool.py --tool mytool --wrapper matlab --wrapper-ext m

5) Overwrite existing scaffold files:
   python scaffold_tool.py --tool mytool --force
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
INFERENCE_DEV_ROOT = REPO_ROOT / "components" / "inference_tools_dev"
TOOLS_DEV_ROOT = INFERENCE_DEV_ROOT / "tools"
CATALOG_TOOLS_ROOT = REPO_ROOT / "geneci" / "inference_catalog" / "tools"
SMOKETEST_CONFIGS_ROOT = INFERENCE_DEV_ROOT / "tests" / "smoketest_configs"

TOOL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
WRAPPER_RE = re.compile(r"^[a-z0-9][a-z0-9_.+-]*$")
WRAPPER_EXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")

WRAPPER_EXTENSION_MAP = {
    "python": "py",
    "r": "R",
    "java": "java",
    "julia": "jl",
    "matlab": "m",
    "octave": "m",
    "bash": "sh",
    "sh": "sh",
    "shell": "sh",
}

WRAPPER_COMMENT_PREFIX_MAP = {
    "python": "#",
    "r": "#",
    "java": "//",
    "julia": "#",
    "matlab": "%",
    "octave": "%",
    "bash": "#",
    "sh": "#",
    "shell": "#",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create scaffold files for a new inference tool integration."
    )
    parser.add_argument(
        "--tool",
        required=True,
        help="Stable tool identifier (lowercase, digits, underscore, hyphen).",
    )
    parser.add_argument(
        "--wrapper",
        default="python",
        help=(
            "Initial wrapper language scaffold. "
            "Known tailored templates: python, r. "
            "Any other value creates a generic placeholder scaffold."
        ),
    )
    parser.add_argument(
        "--wrapper-ext",
        help=(
            "Optional file extension override for generic wrapper languages. "
            "Example: --wrapper matlab --wrapper-ext m"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files.",
    )
    return parser.parse_args(argv)


def ensure_tool_id(tool_id: str) -> str:
    normalized = tool_id.strip()
    if not normalized or TOOL_ID_RE.fullmatch(normalized) is None:
        raise RuntimeError(
            "Invalid --tool value. Expected pattern: ^[a-z0-9][a-z0-9_-]*$"
        )
    return normalized


def ensure_wrapper(wrapper: str) -> str:
    normalized = wrapper.strip().lower()
    if not normalized or WRAPPER_RE.fullmatch(normalized) is None:
        raise RuntimeError(
            "Invalid --wrapper value. Expected pattern: ^[a-z0-9][a-z0-9_.+-]*$"
        )
    return normalized


def resolve_wrapper_extension(wrapper: str, wrapper_ext: str | None) -> str:
    if wrapper_ext is not None:
        normalized = wrapper_ext.strip().lstrip(".")
        if not normalized or WRAPPER_EXT_RE.fullmatch(normalized) is None:
            raise RuntimeError(
                "Invalid --wrapper-ext value. Expected pattern: "
                "^[A-Za-z0-9][A-Za-z0-9_.+-]*$"
            )
        return normalized

    mapped = WRAPPER_EXTENSION_MAP.get(wrapper)
    if mapped is not None:
        return mapped

    fallback = re.sub(r"[^A-Za-z0-9]+", "_", wrapper).strip("_")
    return fallback or "txt"


def _write_text_file(path: Path, content: str, *, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed_before = path.exists()
    if existed_before and not force:
        return "skipped"
    path.write_text(content, encoding="utf-8")
    return "updated" if existed_before else "created"


def toolspec_template(tool_id: str) -> str:
    payload = {
        "schema_version": "1.0",
        "id": tool_id,
        "name": tool_id,
        "publication": ["https://doi.org/TODO"],
        "first_author": "TODO",
        "year": 2000,
        "method_summary": "TODO: replace with a short 1-2 sentence summary of the method core.",
        "method_keywords": ["todo_keyword"],
        "implementation_url": "https://example.org/TODO",
        "docker_image": f"TODO/{tool_id}:latest",
        "accepts": ["samples"],
        "assumes": "generic",
        "extra_inputs": {
            "required": [],
            "optional": [],
            "conditional_required": [],
        },
        "outputs": {
            "directed": False,
            "sign": "none",
            "evidence": "association",
        },
        "progress": {
            "kind": "none",
            "note": "TODO: replace with actual progress semantics if the wrapper exposes progress.json updates.",
        },
        "params": {},
        "artifacts_aux": [],
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def integration_decisions_template(tool_id: str) -> str:
    return f"""# {tool_id} Integration Decisions

## Sources Reviewed

- Upstream repo: `components/inference_tools_dev/tools/{tool_id}/repo/`
- Local papers: `components/inference_tools_dev/tools/{tool_id}/papers/`

## Paper Preparation

- PDF inputs found:
  - TODO
- Extracted text files used for analysis:
  - TODO
- Extraction quality / problems:
  - TODO

## Method Summary

TODO

## ToolSpec Evidence Ledger

For each field below record:
- chosen value
- evidence
- rationale
- confidence / ambiguity

### `schema_version`

TODO

### `id`

TODO

### `name`

TODO

### `publication`

TODO

### `first_author`

TODO

### `year`

TODO

### `method_summary`

TODO

### `method_keywords`

TODO

### `implementation_url`

TODO

### `docker_image`

TODO

### `accepts`

TODO

### `assumes`

TODO

### `extra_inputs`

TODO

### `outputs`

TODO

### `progress`

TODO

### `params`

TODO

### `artifacts_aux`

TODO

## Upstream Interface

### Required inputs

TODO

### Optional or conditional inputs

TODO

### Parameters and defaults

TODO

### Primary outputs

TODO

## Normalized Input Mapping

### Reused input specs

TODO

### New input specs required

TODO

## Output Mapping to `network.csv`

TODO

## Installation Strategy

Preferred public installation source:

TODO

Fallback pinned source if needed:

TODO

## Wrapper Notes

TODO

## Smoketest Plan

TODO

## Known Limitations / Open Questions

TODO
"""


def smoketest_config_template() -> str:
    payload = {
        "extra_files": [],
        "checks": {},
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def run_tool_python_template(tool_id: str) -> str:
    return f'''"""
Scaffold wrapper for {tool_id}.

TODO:
- resolve and validate runtime params
- load normalized inputs from /io/expression.tsv and /io/extra/*
- run the upstream method
- write /io/out/network.csv and /io/out/progress.json
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--extra", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True, type=int)
    _args = parser.parse_args()
    raise NotImplementedError("TODO: implement the wrapper for {tool_id}")


if __name__ == "__main__":
    main()
'''


def run_tool_r_template(tool_id: str) -> str:
    return f"""# Scaffold wrapper for {tool_id}
#
# TODO:
# - parse commandArgs()
# - load normalized inputs from /io/expression.tsv and /io/extra/*
# - run the upstream method
# - write /io/out/network.csv and /io/out/progress.json

stop(\"TODO: implement the wrapper for {tool_id}\", call. = FALSE)
"""


def run_tool_generic_template(tool_id: str, wrapper: str) -> str:
    comment_prefix = WRAPPER_COMMENT_PREFIX_MAP.get(wrapper, "#")
    lines = [
        f"Scaffold wrapper for {tool_id} ({wrapper}).",
        "",
        "TODO:",
        "- decide the real public installation/runtime strategy",
        "- parse GENECI runtime arguments",
        "- load normalized inputs from /io/expression.tsv and /io/extra/*",
        "- run the upstream method",
        "- write /io/out/network.csv and /io/out/progress.json",
        "",
        "This generic stub exists because scaffold_tool.py currently ships",
        "language-specific templates only for Python and R.",
    ]
    rendered = []
    for line in lines:
        if line:
            rendered.append(f"{comment_prefix} {line}")
        else:
            rendered.append(comment_prefix)
    return "\n".join(rendered) + "\n"


def dockerfile_template(tool_id: str, wrapper: str, wrapper_name: str) -> str:
    if wrapper == "r":
        return f"""FROM rocker/r-ver:4.4.1

WORKDIR /app

# TODO: install public runtime dependencies for {tool_id}
COPY {wrapper_name} /app/{wrapper_name}

ENTRYPOINT ["Rscript", "/app/{wrapper_name}"]
"""

    if wrapper == "python":
        return f"""FROM python:3.13-slim

WORKDIR /app

# TODO: install public runtime dependencies for {tool_id}
COPY {wrapper_name} /app/{wrapper_name}

ENTRYPOINT ["python", "/app/{wrapper_name}"]
"""

    return f"""FROM debian:bookworm-slim

WORKDIR /app

# TODO: install public runtime dependencies for {tool_id} ({wrapper})
COPY {wrapper_name} /app/{wrapper_name}

CMD ["/bin/sh", "-lc", "echo 'TODO: replace the generic scaffold ENTRYPOINT for {tool_id} ({wrapper})' >&2; exit 1"]
"""


def scaffold(
    tool_id: str,
    wrapper: str,
    wrapper_ext: str,
    *,
    force: bool,
) -> list[tuple[Path, str]]:
    tool_root = TOOLS_DEV_ROOT / tool_id
    catalog_root = CATALOG_TOOLS_ROOT / tool_id
    smoketest_path = SMOKETEST_CONFIGS_ROOT / f"{tool_id}.json"
    wrapper_name = f"run_tool.{wrapper_ext}"
    if wrapper == "r":
        wrapper_content = run_tool_r_template(tool_id)
    elif wrapper == "python":
        wrapper_content = run_tool_python_template(tool_id)
    else:
        wrapper_content = run_tool_generic_template(tool_id, wrapper)

    created: list[tuple[Path, str]] = []
    for directory in (
        tool_root,
        tool_root / "repo",
        tool_root / "papers",
        catalog_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    file_specs = [
        (
            catalog_root / "toolspec.json",
            toolspec_template(tool_id),
        ),
        (
            tool_root / "integration_decisions.md",
            integration_decisions_template(tool_id),
        ),
        (
            tool_root / "Dockerfile",
            dockerfile_template(tool_id, wrapper, wrapper_name),
        ),
        (
            tool_root / wrapper_name,
            wrapper_content,
        ),
        (
            smoketest_path,
            smoketest_config_template(),
        ),
    ]

    for path, content in file_specs:
        status = _write_text_file(path, content, force=force)
        created.append((path, status))

    return created


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        tool_id = ensure_tool_id(args.tool)
        wrapper = ensure_wrapper(args.wrapper)
        wrapper_ext = resolve_wrapper_extension(wrapper, args.wrapper_ext)
        created = scaffold(tool_id, wrapper, wrapper_ext, force=args.force)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"[{tool_id}] scaffold ready")
    for path, status in created:
        print(f"  {status.upper():7s} {path}")
    print()
    print("Next steps:")
    print(
        f"  1. Place upstream evidence in {TOOLS_DEV_ROOT / tool_id / 'repo'} and {TOOLS_DEV_ROOT / tool_id / 'papers'}"
    )
    print(
        f"  2. Extract local PDFs when available: make prepare-tool-papers TOOL={tool_id}"
    )
    print(
        f"  3. Follow {INFERENCE_DEV_ROOT / 'TOOL_INTEGRATION_PLAYBOOK.md'}"
    )
    print(f"  4. When implementation is ready, verify with: make verify-tool TOOL={tool_id}")
    if wrapper not in {"python", "r"}:
        print()
        print(
            f"Note: {wrapper!r} currently uses a generic scaffold placeholder "
            f"({TOOLS_DEV_ROOT / tool_id / f'run_tool.{wrapper_ext}'})."
        )
        print(
            "Replace the generic wrapper and Dockerfile during integration with "
            "the real runtime strategy for that language."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
