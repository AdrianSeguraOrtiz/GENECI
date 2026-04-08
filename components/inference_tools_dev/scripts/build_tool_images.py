"""Build inference tool Docker images using temporary, template-enriched contexts.

This script is the single build pipeline for tool source directories under
`components/inference_tools_dev/tools/*`:
1) copies each tool source directory to a temporary context,
2) injects generated run_tool.sh and mapped shared templates,
3) runs docker build,
4) removes temporary files (unless --keep-context).
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "geneci" / "inference_catalog"
DEFAULT_CATALOG_TOOLS_ROOT = CATALOG_ROOT / "tools"
DEFAULT_TOOL_SOURCES_ROOT = INFERENCE_TOOLS_ROOT / "tools"
DEFAULT_TEMPLATE_MAP = Path(__file__).resolve().parent / "template_map.json"
TEMPLATES_ROOT = Path(__file__).resolve().parent / "templates"

RUNTIME_ENTRYPOINTS = {
    "python": ("python", "/app/run_tool.py"),
    "r": ("Rscript", "/app/run_tool.R"),
}


@dataclass(frozen=True)
class ToolTemplateConfig:
    runtime: str
    templates: list[str]


ENTRYPOINT_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail

INPUT=""
PARAMS=""
EXTRA=""
OUTPUT_DIR=""
THREADS=""

RUNTIME_BIN="{runtime_bin}"
APP_SCRIPT="{app_script}"

usage() {{
  echo "Usage: /app/run_tool.sh --input /io/expression.tsv --params /io/params.json --extra /io/extra --output-dir /io/out --threads 8"
}}

die() {{
  echo "Error: $*" >&2
  usage >&2
  exit 1
}}

require_value() {{
  local arg="$1"
  local value="${{2-}}"
  if [[ -z "${{value}}" || "${{value}}" == --* ]]; then
    die "Missing value for ${{arg}}"
  fi
}}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      require_value "$1" "${{2-}}"
      INPUT="$2"
      shift 2
      ;;
    --params)
      require_value "$1" "${{2-}}"
      PARAMS="$2"
      shift 2
      ;;
    --extra)
      require_value "$1" "${{2-}}"
      EXTRA="$2"
      shift 2
      ;;
    --output-dir)
      require_value "$1" "${{2-}}"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --threads)
      require_value "$1" "${{2-}}"
      THREADS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

if [[ -z "${{INPUT}}" || -z "${{PARAMS}}" || -z "${{EXTRA}}" || -z "${{OUTPUT_DIR}}" || -z "${{THREADS}}" ]]; then
  die "Missing required arguments."
fi

if ! [[ "${{THREADS}}" =~ ^[1-9][0-9]*$ ]]; then
  die "--threads must be a positive integer."
fi

command -v "${{RUNTIME_BIN}}" >/dev/null 2>&1 || die "'${{RUNTIME_BIN}}' is not available in PATH."
[[ -f "${{APP_SCRIPT}}" ]] || die "Internal error: ${{APP_SCRIPT}} not found."

mkdir -p "${{OUTPUT_DIR}}"

exec "${{RUNTIME_BIN}}" "${{APP_SCRIPT}}" \\
  --input "${{INPUT}}" \\
  --params "${{PARAMS}}" \\
  --extra "${{EXTRA}}" \\
  --output-dir "${{OUTPUT_DIR}}" \\
  --threads "${{THREADS}}"
"""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build selected tool images from temporary contexts generated from template_map.json."
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
        "--template-map",
        type=Path,
        default=DEFAULT_TEMPLATE_MAP,
        help=f"Template map JSON file. Default: {DEFAULT_TEMPLATE_MAP}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to build (repeatable). If omitted, builds all mapped tools.",
    )
    parser.add_argument(
        "--tag-pattern",
        default=None,
        help=(
            "Fallback image tag pattern when toolspec.docker_image is missing. "
            "Supports {tool_id}. Ignored for tools with --image-tag override."
        ),
    )
    parser.add_argument(
        "--image-tag",
        action="append",
        default=[],
        help="Per-tool tag override, format: TOOL_ID=IMAGE_TAG (repeatable).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass --no-cache to docker build.",
    )
    parser.add_argument(
        "--keep-context",
        action="store_true",
        help="Keep temporary build contexts for debugging.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List selected tools and planned templates without building.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object in: {path}")
    return data


def discover_tool_sources(tool_sources_root: Path) -> list[tuple[str, Path]]:
    if not tool_sources_root.exists() or not tool_sources_root.is_dir():
        raise RuntimeError(f"Invalid tool sources root: {tool_sources_root}")

    tools: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in tool_sources_root.iterdir() if path.is_dir()
    ):
        if (tool_dir / "Dockerfile").exists():
            tools.append((tool_dir.name, tool_dir))

    if not tools:
        raise RuntimeError(
            f"No buildable tools found under tool sources root: {tool_sources_root}"
        )
    return tools


def parse_tag_overrides(items: list[str]) -> dict[str, str]:
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


def load_toolspec_docker_image(tool_id: str, catalog_tools_root: Path) -> str | None:
    toolspec_path = catalog_tools_root / tool_id / "toolspec.json"
    toolspec = load_json(toolspec_path)
    docker_image = toolspec.get("docker_image")
    if docker_image is None:
        return None
    if not isinstance(docker_image, str):
        raise RuntimeError(
            f"[{tool_id}] toolspec.docker_image must be a string when present."
        )
    normalized = docker_image.strip()
    return normalized or None


def validate_template_map(
    template_map: dict[str, Any], discovered: dict[str, Path]
) -> dict[str, ToolTemplateConfig]:
    bundle_templates = template_map.get("bundle_templates")
    tools_cfg = template_map.get("tools")

    if not isinstance(bundle_templates, dict):
        raise RuntimeError("template_map.json: 'bundle_templates' must be an object.")
    if not isinstance(tools_cfg, dict):
        raise RuntimeError("template_map.json: 'tools' must be an object.")

    normalized: dict[str, ToolTemplateConfig] = {}

    for tool_id, cfg in tools_cfg.items():
        if tool_id not in discovered:
            raise RuntimeError(f"template_map.json references unknown tool: {tool_id}")
        if not isinstance(cfg, dict):
            raise RuntimeError(f"template_map.json tool '{tool_id}' must be an object.")

        runtime = cfg.get("runtime")
        bundles = cfg.get("bundles")

        if runtime not in RUNTIME_ENTRYPOINTS:
            raise RuntimeError(
                f"template_map.json tool '{tool_id}' has unsupported runtime: {runtime!r}"
            )
        if not isinstance(bundles, list) or not all(
            isinstance(x, str) for x in bundles
        ):
            raise RuntimeError(
                f"template_map.json tool '{tool_id}' bundles must be a list of strings."
            )

        template_relpaths: list[str] = []
        for bundle in bundles:
            bundle_items = bundle_templates.get(bundle)
            if not isinstance(bundle_items, list) or not all(
                isinstance(x, str) for x in bundle_items
            ):
                raise RuntimeError(
                    f"template_map.json bundle '{bundle}' must map to a list of strings."
                )
            template_relpaths.extend(bundle_items)

        deduped = list(dict.fromkeys(template_relpaths))
        normalized[tool_id] = ToolTemplateConfig(
            runtime=runtime,
            templates=deduped,
        )

    return normalized


def select_tools(
    discovered: dict[str, Path],
    mapped_tools: dict[str, ToolTemplateConfig],
    filters: list[str],
) -> list[str]:
    if not filters:
        missing_map = sorted(
            tool_id for tool_id in discovered if tool_id not in mapped_tools
        )
        if missing_map:
            raise RuntimeError(
                f"Tool(s) missing in template_map.json: {missing_map}. "
                "Add them or build with explicit --tool filters."
            )
        return sorted(mapped_tools.keys())

    unknown = sorted(tool_id for tool_id in filters if tool_id not in discovered)
    if unknown:
        raise RuntimeError(f"Unknown tool id(s): {unknown}")

    unmapped = sorted(tool_id for tool_id in filters if tool_id not in mapped_tools)
    if unmapped:
        raise RuntimeError(
            f"Selected tool(s) not present in template_map.json: {unmapped}"
        )

    return filters


def render_entrypoint(runtime: str) -> str:
    runtime_bin, app_script = RUNTIME_ENTRYPOINTS[runtime]
    return ENTRYPOINT_TEMPLATE.format(runtime_bin=runtime_bin, app_script=app_script)


def runtime_script_name(runtime: str) -> str:
    if runtime == "python":
        return "run_tool.py"
    if runtime == "r":
        return "run_tool.R"
    raise RuntimeError(f"Unsupported runtime: {runtime!r}")


def resolve_image_tag(
    *,
    tool_id: str,
    toolspec_tag: str | None,
    tag_pattern: str | None,
    tag_overrides: dict[str, str],
) -> str:
    if tool_id in tag_overrides:
        return tag_overrides[tool_id]
    if toolspec_tag:
        return toolspec_tag
    if tag_pattern:
        return tag_pattern.format(tool_id=tool_id)
    raise RuntimeError(
        f"[{tool_id}] toolspec.docker_image is missing; provide --tag-pattern or --image-tag."
    )


def allocate_temp_root(
    keep_context: bool,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    """Create temp root for build contexts. Persistent only when keep_context=true."""
    if keep_context:
        temp_root = Path(tempfile.mkdtemp(prefix="inference-tools-build-"))
        print(f"Temporary contexts kept at: {temp_root}")
        return temp_root, None

    temp_root_ctx = tempfile.TemporaryDirectory(prefix="inference-tools-build-")
    return Path(temp_root_ctx.name), temp_root_ctx


def prepare_context(
    *,
    tool_id: str,
    tool_source_dir: Path,
    runtime: str,
    template_relpaths: list[str],
    context_dir: Path,
) -> None:
    shutil.copytree(tool_source_dir, context_dir)

    script_name = runtime_script_name(runtime)
    runtime_script_path = context_dir / script_name
    if not runtime_script_path.exists():
        raise RuntimeError(
            f"[{tool_id}] Expected runtime script not found in tool source directory: {script_name}"
        )

    entrypoint_path = context_dir / "run_tool.sh"
    entrypoint_path.write_text(render_entrypoint(runtime), encoding="utf-8")
    mode = entrypoint_path.stat().st_mode
    entrypoint_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    for relpath in template_relpaths:
        src = TEMPLATES_ROOT / relpath
        if not src.exists() or not src.is_file():
            raise RuntimeError(f"[{tool_id}] Template file not found: {src}")
        dst = context_dir / src.name
        shutil.copy2(src, dst)


def build_image(
    *,
    tool_id: str,
    context_dir: Path,
    image_tag: str,
    no_cache: bool,
) -> None:
    cmd = ["docker", "build", "-t", image_tag]
    if no_cache:
        cmd.append("--no-cache")
    cmd.append(str(context_dir))

    print(f"[{tool_id}] building image: {image_tag}")
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"[{tool_id}] docker build failed (exit code {result.returncode})."
        )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    discovered_pairs = discover_tool_sources(args.tool_sources_root)
    discovered = {tool_id: path for tool_id, path in discovered_pairs}

    template_map = load_json(args.template_map)
    mapped_tools = validate_template_map(template_map, discovered)

    selected_tool_ids = select_tools(discovered, mapped_tools, args.tool)
    tag_overrides = parse_tag_overrides(args.image_tag)
    toolspec_image_tags = {
        tool_id: load_toolspec_docker_image(tool_id, args.catalog_tools_root)
        for tool_id in selected_tool_ids
    }

    unknown_tag_overrides = sorted(
        tool_id for tool_id in tag_overrides if tool_id not in selected_tool_ids
    )
    if unknown_tag_overrides:
        raise RuntimeError(
            f"--image-tag contains tools not selected for build: {unknown_tag_overrides}"
        )

    if args.list:
        for tool_id in selected_tool_ids:
            cfg = mapped_tools[tool_id]
            image_tag = resolve_image_tag(
                tool_id=tool_id,
                toolspec_tag=toolspec_image_tags[tool_id],
                tag_pattern=args.tag_pattern,
                tag_overrides=tag_overrides,
            )
            print(
                f"- {tool_id}: runtime={cfg.runtime} templates={cfg.templates} image_tag={image_tag}"
            )
        return 0

    temp_root, temp_root_ctx = allocate_temp_root(args.keep_context)

    try:
        for tool_id in selected_tool_ids:
            cfg = mapped_tools[tool_id]
            tool_source_dir = discovered[tool_id]
            image_tag = resolve_image_tag(
                tool_id=tool_id,
                toolspec_tag=toolspec_image_tags[tool_id],
                tag_pattern=args.tag_pattern,
                tag_overrides=tag_overrides,
            )

            context_dir = temp_root / tool_id
            prepare_context(
                tool_id=tool_id,
                tool_source_dir=tool_source_dir,
                runtime=cfg.runtime,
                template_relpaths=cfg.templates,
                context_dir=context_dir,
            )
            build_image(
                tool_id=tool_id,
                context_dir=context_dir,
                image_tag=image_tag,
                no_cache=args.no_cache,
            )
    finally:
        if temp_root_ctx is not None:
            temp_root_ctx.cleanup()

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
