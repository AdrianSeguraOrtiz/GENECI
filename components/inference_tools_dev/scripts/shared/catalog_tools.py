"""Shared catalog and tool source helpers for dev scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

INFERENCE_TOOLS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_ROOT = REPO_ROOT / "geneci" / "inference_catalog"
DEFAULT_CATALOG_TOOLS_ROOT = CATALOG_ROOT / "tools"
DEFAULT_TOOL_SOURCES_ROOT = INFERENCE_TOOLS_ROOT / "tools"


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"File not found: {path}") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not read file: {path} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Malformed JSON in {path} (line {exc.lineno}, column {exc.colno}): {exc.msg}"
        ) from exc


def discover_catalog_tool_dirs(
    catalog_tools_root: Path,
    *,
    required_filename: str = "toolspec.json",
) -> list[tuple[str, Path]]:
    if not catalog_tools_root.exists() or not catalog_tools_root.is_dir():
        raise RuntimeError(f"Invalid catalog tools root: {catalog_tools_root}")

    discovered: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in catalog_tools_root.iterdir() if path.is_dir()
    ):
        if (tool_dir / required_filename).exists():
            discovered.append((tool_dir.name, tool_dir))
    return discovered


def discover_tool_source_dirs(tool_sources_root: Path) -> list[tuple[str, Path]]:
    if not tool_sources_root.exists() or not tool_sources_root.is_dir():
        raise RuntimeError(f"Invalid tool sources root: {tool_sources_root}")

    discovered: list[tuple[str, Path]] = []
    for tool_dir in sorted(
        path for path in tool_sources_root.iterdir() if path.is_dir()
    ):
        discovered.append((tool_dir.name, tool_dir))
    return discovered


def select_tools(
    discovered: list[tuple[str, Path]],
    filters: list[str],
) -> list[tuple[str, Path]]:
    by_tool_id = {tool_id: path for tool_id, path in discovered}
    if not filters:
        return discovered

    unknown = sorted(tool_id for tool_id in filters if tool_id not in by_tool_id)
    if unknown:
        raise RuntimeError(f"Unknown tool id(s): {unknown}")
    return [(tool_id, by_tool_id[tool_id]) for tool_id in filters]


def load_toolspec(catalog_tools_root: Path, tool_id: str) -> dict[str, Any]:
    toolspec_path = catalog_tools_root / tool_id / "toolspec.json"
    payload = load_json(toolspec_path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in: {toolspec_path}")
    return payload


def load_required_toolspec_string(
    *,
    tool_id: str,
    catalog_tools_root: Path,
    field_name: str,
) -> str:
    toolspec = load_toolspec(catalog_tools_root, tool_id)
    value = toolspec.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"[{tool_id}] toolspec.{field_name} must be a non-empty string."
        )
    return value.strip()


def load_toolspec_publications(
    *,
    tool_id: str,
    catalog_tools_root: Path,
) -> list[str]:
    toolspec = load_toolspec(catalog_tools_root, tool_id)
    value = toolspec.get("publication")

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise RuntimeError(f"[{tool_id}] toolspec.publication must not be empty.")
        return [normalized]

    if isinstance(value, list):
        publications: list[str] = []
        for idx, item in enumerate(value, start=1):
            if not isinstance(item, str) or not item.strip():
                raise RuntimeError(
                    f"[{tool_id}] toolspec.publication[{idx}] must be a non-empty string."
                )
            publications.append(item.strip())
        if not publications:
            raise RuntimeError(f"[{tool_id}] toolspec.publication must not be empty.")
        return publications

    raise RuntimeError(
        f"[{tool_id}] toolspec.publication must be a string or array of strings."
    )
