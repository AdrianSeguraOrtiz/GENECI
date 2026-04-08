"""Clone or clean upstream implementation repositories for tool sources.

Usage examples:
1) List clone targets:
   python sync_tool_repos.py list

2) Clone all upstream repos under tools/<tool_id>/repo:
   python sync_tool_repos.py clone

3) Remove selected cloned repos:
   python sync_tool_repos.py clean --tool tigress --tool genie3

Exit codes:
- 0: requested action completed for all selected tools
- 1: one or more clone/clean operations failed
- 2: usage/runtime error (unknown tool ids, invalid paths, etc.)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_tools import (
    DEFAULT_CATALOG_TOOLS_ROOT,
    DEFAULT_TOOL_SOURCES_ROOT,
    discover_tool_source_dirs,
    load_required_toolspec_string,
    select_tools,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List, clone, or clean upstream implementation repos under "
            "components/inference_tools_dev/tools/<tool_id>/repo."
        )
    )
    parser.add_argument(
        "action",
        choices=("list", "clone", "clean"),
        help="Action to perform on per-tool repo directories.",
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory. Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--tool-sources-root",
        type=Path,
        default=DEFAULT_TOOL_SOURCES_ROOT,
        help=f"Path to tool source directories. Default: {DEFAULT_TOOL_SOURCES_ROOT}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to operate on (repeatable). If omitted, uses all tool source dirs.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed clone/clean action.",
    )
    return parser.parse_args(argv)


def repo_dir_for(tool_source_dir: Path) -> Path:
    return tool_source_dir / "repo"


def implementation_url_for(tool_id: str, catalog_tools_root: Path) -> str:
    return load_required_toolspec_string(
        tool_id=tool_id,
        catalog_tools_root=catalog_tools_root,
        field_name="implementation_url",
    )


def normalize_repo_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized.split(":", 1)[1]
    return normalized


def git_origin_url(repo_dir: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def clone_repo(*, tool_id: str, implementation_url: str, repo_dir: Path) -> bool:
    if repo_dir.exists():
        if not repo_dir.is_dir():
            print(f"[{tool_id}] FAILED: repo target exists and is not a directory: {repo_dir}")
            return False
        if not (repo_dir / ".git").exists():
            print(
                f"[{tool_id}] FAILED: repo target already exists but is not a git checkout: {repo_dir}"
            )
            return False

        origin_url = git_origin_url(repo_dir)
        if origin_url and normalize_repo_url(origin_url) != normalize_repo_url(
            implementation_url
        ):
            print(
                f"[{tool_id}] FAILED: existing repo origin '{origin_url}' does not match toolspec implementation_url '{implementation_url}'."
            )
            return False

        print(f"[{tool_id}] SKIP: repo already present at {repo_dir}")
        return True

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"[{tool_id}] cloning {implementation_url} -> {repo_dir}")
    result = subprocess.run(
        ["git", "clone", implementation_url, str(repo_dir)],
        text=True,
        check=False,
    )
    if result.returncode == 0:
        print("  OK")
        return True

    print(f"  FAILED (exit code {result.returncode})")
    return False


def clean_repo(*, tool_id: str, repo_dir: Path) -> bool:
    if not repo_dir.exists():
        print(f"[{tool_id}] SKIP: repo directory does not exist")
        return True

    print(f"[{tool_id}] removing {repo_dir}")
    try:
        shutil.rmtree(repo_dir)
    except OSError as exc:
        print(f"  FAILED: {exc}")
        return False

    print("  OK")
    return True


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    discovered = discover_tool_source_dirs(args.tool_sources_root)
    if not discovered:
        raise RuntimeError(
            f"No tool source directories found under: {args.tool_sources_root}"
        )

    selected = select_tools(discovered, args.tool)

    if args.action == "list":
        for tool_id, tool_source_dir in selected:
            implementation_url = implementation_url_for(tool_id, args.catalog_tools_root)
            repo_dir = repo_dir_for(tool_source_dir)
            status = "missing"
            if repo_dir.exists():
                status = "git" if (repo_dir / ".git").exists() else "non-git"
            print(
                f"- {tool_id}: implementation_url={implementation_url} repo_dir={repo_dir} status={status}"
            )
        return 0

    failures = 0
    for tool_id, tool_source_dir in selected:
        repo_dir = repo_dir_for(tool_source_dir)
        if args.action == "clone":
            implementation_url = implementation_url_for(tool_id, args.catalog_tools_root)
            ok = clone_repo(
                tool_id=tool_id,
                implementation_url=implementation_url,
                repo_dir=repo_dir,
            )
        else:
            ok = clean_repo(tool_id=tool_id, repo_dir=repo_dir)

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
