"""List, push, or pull tool images defined in ToolSpecs.

Usage examples:
1) List image tags:
   python sync_tool_images.py list

2) Push all tool images:
   python sync_tool_images.py push

3) Pull selected tool images:
   python sync_tool_images.py pull --tool genie3 --tool tigress

Exit codes:
- 0: requested action completed for all selected tools
- 1: one or more docker push/pull operations failed
- 2: usage/runtime error (unknown tool ids, invalid catalog, etc.)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_tools import (
    DEFAULT_CATALOG_TOOLS_ROOT,
    discover_catalog_tool_dirs,
    load_required_toolspec_string,
    select_tools,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List, push, or pull Docker images referenced by catalog ToolSpecs."
    )
    parser.add_argument(
        "action",
        choices=("list", "push", "pull"),
        help="Action to perform on tool images.",
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory. Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to operate on (repeatable). If omitted, uses all catalog tools.",
    )
    parser.add_argument(
        "--image-tag",
        action="append",
        default=[],
        help="Per-tool image tag override, format: TOOL_ID=IMAGE_TAG (repeatable).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first docker push/pull failure.",
    )
    return parser.parse_args(argv)


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


def resolve_image_tag(
    *,
    tool_id: str,
    catalog_tools_root: Path,
    tag_overrides: dict[str, str],
) -> str:
    if tool_id in tag_overrides:
        return tag_overrides[tool_id]
    return load_required_toolspec_string(
        tool_id=tool_id,
        catalog_tools_root=catalog_tools_root,
        field_name="docker_image",
    )


def run_docker_action(*, action: str, tool_id: str, image_tag: str) -> bool:
    print(f"[{tool_id}] {action} {image_tag}")
    result = subprocess.run(
        ["docker", action, image_tag],
        text=True,
        check=False,
    )
    if result.returncode == 0:
        print("  OK")
        return True
    print(f"  FAILED (exit code {result.returncode})")
    return False


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    discovered = discover_catalog_tool_dirs(args.catalog_tools_root)
    if not discovered:
        raise RuntimeError(f"No toolspec.json files found under: {args.catalog_tools_root}")

    selected = select_tools(discovered, args.tool)
    tag_overrides = parse_tag_overrides(args.image_tag)

    unknown_tag_overrides = sorted(
        tool_id for tool_id in tag_overrides if tool_id not in {tool_id for tool_id, _ in selected}
    )
    if unknown_tag_overrides:
        raise RuntimeError(
            f"--image-tag contains tools not selected for action: {unknown_tag_overrides}"
        )

    if args.action == "list":
        for tool_id, _tool_dir in selected:
            image_tag = resolve_image_tag(
                tool_id=tool_id,
                catalog_tools_root=args.catalog_tools_root,
                tag_overrides=tag_overrides,
            )
            print(f"- {tool_id}: image_tag={image_tag}")
        return 0

    failures = 0
    for tool_id, _tool_dir in selected:
        image_tag = resolve_image_tag(
            tool_id=tool_id,
            catalog_tools_root=args.catalog_tools_root,
            tag_overrides=tag_overrides,
        )
        ok = run_docker_action(action=args.action, tool_id=tool_id, image_tag=image_tag)
        if ok:
            continue
        failures += 1
        if args.fail_fast:
            break

    print()
    print(
        "Summary: selected={selected} succeeded={succeeded} failed={failed}".format(
            selected=len(selected),
            succeeded=len(selected) - failures,
            failed=failures,
        )
    )
    return 0 if failures == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
