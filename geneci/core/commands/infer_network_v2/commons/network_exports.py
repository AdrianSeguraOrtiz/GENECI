"""Export merged network CSV files to external graph formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import dedent
from typing import Any
from xml.etree import ElementTree as ET

MERGED_NETWORK_REQUIRED_COLUMNS = [
    "source",
    "target",
    "score",
    "sign",
    "evidence",
    "context",
    "tool_id",
]

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
GEXF_NS = "http://www.gexf.net/1.2draft"

CYTOSCAPE_TOOL_PALETTE = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#F0E442",
    "#999999",
]

CYTOSCAPE_WIDTH_POINTS = [0.0, 0.25, 0.5, 0.75, 1.0]
CYTOSCAPE_WIDTH_VALUES = [1.0, 2.5, 4.0, 6.0, 8.0]
CYTOSCAPE_OPACITY_POINTS = [0.0, 1.0]
CYTOSCAPE_OPACITY_VALUES = [80, 220]


def _context_scope(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized.startswith("group:"):
        return "group"
    return "global"


def _load_merged_network_rows(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.exists() or not csv_path.is_file():
        raise ValueError(f"Merged network CSV not found: {csv_path}")

    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        missing = [col for col in MERGED_NETWORK_REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(
                f"Merged network CSV is missing required columns {missing}: {csv_path}"
            )

        for idx, row in enumerate(reader, start=1):
            rows.append(
                {
                    "row_index": idx,
                    "source": str(row["source"]),
                    "target": str(row["target"]),
                    "score": float(row["score"]),
                    "sign": str(row["sign"]),
                    "evidence": str(row["evidence"]),
                    "context": str(row["context"]),
                    "context_scope": _context_scope(str(row["context"])),
                    "tool_id": str(row["tool_id"]),
                }
            )
    return rows


def _edge_id(row: dict[str, Any]) -> str:
    return (
        f"{row['tool_id']}|{row['context']}|{row['source']}|{row['target']}|"
        f"{int(row['row_index'])}"
    )


def _collect_nodes(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row["source"]) for row in rows} | {str(row["target"]) for row in rows})


def export_network_graphml(csv_path: Path, out_path: Path) -> int:
    rows = _load_merged_network_rows(csv_path)
    nodes = _collect_nodes(rows)

    graphml = ET.Element(
        "graphml",
        {
            "xmlns": GRAPHML_NS,
            "xmlns:xsi": XSI_NS,
            "xsi:schemaLocation": (
                "http://graphml.graphdrawing.org/xmlns "
                "http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"
            )
        },
    )
    key_specs = [
        ("node_label", "node", "label", "string"),
        ("edge_weight", "edge", "weight", "double"),
        ("edge_score", "edge", "score", "double"),
        ("edge_sign", "edge", "sign", "string"),
        ("edge_evidence", "edge", "evidence", "string"),
        ("edge_context", "edge", "context", "string"),
        ("edge_context_scope", "edge", "context_scope", "string"),
        ("edge_tool_id", "edge", "tool_id", "string"),
    ]
    for key_id, key_for, attr_name, attr_type in key_specs:
        ET.SubElement(graphml, "key", id=key_id, **{"for": key_for, "attr.name": attr_name, "attr.type": attr_type})

    graph = ET.SubElement(graphml, "graph", id="G", edgedefault="directed")

    for node_id in nodes:
        node = ET.SubElement(graph, "node", id=node_id)
        data = ET.SubElement(node, "data", key="node_label")
        data.text = node_id

    for row in rows:
        edge = ET.SubElement(
            graph,
            "edge",
            id=_edge_id(row),
            source=str(row["source"]),
            target=str(row["target"]),
        )
        values = [
            ("edge_weight", format(float(row["score"]), ".12g")),
            ("edge_score", format(float(row["score"]), ".12g")),
            ("edge_sign", str(row["sign"])),
            ("edge_evidence", str(row["evidence"])),
            ("edge_context", str(row["context"])),
            ("edge_context_scope", str(row["context_scope"])),
            ("edge_tool_id", str(row["tool_id"])),
        ]
        for key, value in values:
            data = ET.SubElement(edge, "data", key=key)
            data.text = value

    tree = ET.ElementTree(graphml)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return len(rows)


def export_network_gexf(csv_path: Path, out_path: Path) -> int:
    rows = _load_merged_network_rows(csv_path)
    nodes = _collect_nodes(rows)

    gexf = ET.Element("gexf", {"xmlns": GEXF_NS, "version": "1.2"})
    graph = ET.SubElement(
        gexf,
        "graph",
        mode="static",
        defaultedgetype="directed",
    )

    edge_attributes = ET.SubElement(graph, "attributes", **{"class": "edge"})
    for attr_id, title, attr_type in [
        ("score", "score", "double"),
        ("sign", "sign", "string"),
        ("evidence", "evidence", "string"),
        ("context", "context", "string"),
        ("context_scope", "context_scope", "string"),
        ("tool_id", "tool_id", "string"),
    ]:
        ET.SubElement(
            edge_attributes,
            "attribute",
            id=attr_id,
            title=title,
            type=attr_type,
        )

    nodes_el = ET.SubElement(graph, "nodes")
    for node_id in nodes:
        ET.SubElement(
            nodes_el,
            "node",
            id=node_id,
            label=node_id,
        )

    edges_el = ET.SubElement(graph, "edges")
    for row in rows:
        edge = ET.SubElement(
            edges_el,
            "edge",
            id=_edge_id(row),
            source=str(row["source"]),
            target=str(row["target"]),
            weight=format(float(row["score"]), ".12g"),
        )
        attvalues = ET.SubElement(edge, "attvalues")
        for attr_id, value in [
            ("score", format(float(row["score"]), ".12g")),
            ("sign", str(row["sign"])),
            ("evidence", str(row["evidence"])),
            ("context", str(row["context"])),
            ("context_scope", str(row["context_scope"])),
            ("tool_id", str(row["tool_id"])),
        ]:
            ET.SubElement(
                attvalues,
                "attvalue",
                {"for": attr_id, "value": value},
            )

    tree = ET.ElementTree(gexf)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return len(rows)


def export_cytoscape_style_script(
    *,
    csv_path: Path,
    graphml_path: Path,
    out_path: Path,
) -> int:
    rows = _load_merged_network_rows(csv_path)
    tool_ids = sorted(
        {str(row["tool_id"]).strip() for row in rows if str(row["tool_id"]).strip()}
    )
    tool_colors = {
        tool_id: CYTOSCAPE_TOOL_PALETTE[idx % len(CYTOSCAPE_TOOL_PALETTE)]
        for idx, tool_id in enumerate(tool_ids)
    }
    style_name = f"GENECI :: {graphml_path.stem}"

    script = dedent(
        f"""\
        #!/usr/bin/env python3
        \"\"\"Load the sibling GraphML export into Cytoscape Desktop and apply a GENECI style preset.

        Requirements:
          - Cytoscape Desktop running with CyREST enabled (default http://127.0.0.1:1234)
          - py4cytoscape installed in the Python environment running this script

        Usage:
          python {out_path.name}
          python {out_path.name} --graphml /path/to/{graphml_path.name}
          python {out_path.name} --skip-layout
        \"\"\"

        from __future__ import annotations

        import argparse
        from pathlib import Path
        import sys

        try:
            import py4cytoscape as p4c
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(
                "This preset requires py4cytoscape. Install it with: pip install py4cytoscape"
            ) from exc


        SCRIPT_DIR = Path(__file__).resolve().parent
        DEFAULT_GRAPHML = SCRIPT_DIR / {graphml_path.name!r}
        STYLE_NAME = {style_name!r}
        TOOL_IDS = {json.dumps(tool_ids, ensure_ascii=True)}
        TOOL_COLORS = {json.dumps(tool_colors, ensure_ascii=True, sort_keys=True)}
        WIDTH_POINTS = {json.dumps(CYTOSCAPE_WIDTH_POINTS)}
        WIDTH_VALUES = {json.dumps(CYTOSCAPE_WIDTH_VALUES)}
        OPACITY_POINTS = {json.dumps(CYTOSCAPE_OPACITY_POINTS)}
        OPACITY_VALUES = {json.dumps(CYTOSCAPE_OPACITY_VALUES)}


        def _pick_group_line_style(base_url: str) -> str:
            try:
                available = set(p4c.get_line_styles(base_url=base_url))
            except Exception:
                return "LONG_DASH"
            for candidate in ("LONG_DASH", "EQUAL_DASH", "DOT", "SOLID"):
                if candidate in available:
                    return candidate
            return "SOLID"


        def _pick_layout_name(base_url: str) -> str | None:
            try:
                available = set(p4c.get_layout_names(base_url=base_url))
            except Exception:
                return None
            for candidate in ("force-directed", "prefuse-force-directed"):
                if candidate in available:
                    return candidate
            return None


        def _style_defaults(group_line_style: str) -> dict[str, object]:
            return {{
                "node fill color": "#7dd3fc",
                "node border paint": "#0369a1",
                "node border width": 1.5,
                "node size": 36,
                "node label color": "#0f172a",
                "node label font size": 14,
                "edge width": 1.0,
                "edge transparency": 160,
                "edge line type": "SOLID",
                "edge source arrow shape": "NONE",
                "edge target arrow shape": "NONE",
                "network background paint": "#f8fafc",
            }}


        def _build_mappings(group_line_style: str) -> list[dict[str, object]]:
            mappings = [
                p4c.map_visual_property("node label", "label", "p"),
                p4c.map_visual_property(
                    "edge width",
                    "score",
                    "c",
                    WIDTH_POINTS,
                    WIDTH_VALUES,
                ),
                p4c.map_visual_property(
                    "edge transparency",
                    "score",
                    "c",
                    OPACITY_POINTS,
                    OPACITY_VALUES,
                ),
                p4c.map_visual_property(
                    "edge line type",
                    "context_scope",
                    "d",
                    ["global", "group"],
                    ["SOLID", group_line_style],
                ),
            ]
            if TOOL_IDS:
                mappings.append(
                    p4c.map_visual_property(
                        "edge unselected paint",
                        "tool_id",
                        "d",
                        TOOL_IDS,
                        [TOOL_COLORS[tool_id] for tool_id in TOOL_IDS],
                    )
                )
            return mappings


        def _recreate_style(style_name: str, group_line_style: str, base_url: str) -> None:
            try:
                if style_name in p4c.get_visual_style_names(base_url=base_url):
                    p4c.delete_visual_style(style_name, base_url=base_url)
            except Exception:
                pass

            p4c.create_visual_style(
                style_name,
                mappings=_build_mappings(group_line_style),
                base_url=base_url,
            )
            p4c.update_style_defaults(
                style_name,
                _style_defaults(group_line_style),
                base_url=base_url,
            )
            p4c.lock_node_dimensions(True, style_name=style_name, base_url=base_url)
            p4c.match_arrow_color_to_edge(True, style_name=style_name, base_url=base_url)


        def main() -> int:
            parser = argparse.ArgumentParser(
                description="Import the sibling GENECI GraphML export into Cytoscape and apply a preset style."
            )
            parser.add_argument(
                "--graphml",
                type=Path,
                default=DEFAULT_GRAPHML,
                help="GraphML export to import into Cytoscape.",
            )
            parser.add_argument(
                "--base-url",
                default="http://127.0.0.1:1234/v1",
                help="CyREST base URL for a running Cytoscape Desktop instance.",
            )
            parser.add_argument(
                "--skip-layout",
                action="store_true",
                help="Do not run a force-directed layout after importing the network.",
            )
            args = parser.parse_args()

            graphml_path = args.graphml.resolve()
            if not graphml_path.exists():
                raise SystemExit(f"GraphML export not found: {{graphml_path}}")

            result = p4c.import_network_from_file(
                str(graphml_path),
                base_url=args.base_url,
            )
            network_suid = result["networks"][0]
            group_line_style = _pick_group_line_style(args.base_url)
            _recreate_style(STYLE_NAME, group_line_style, args.base_url)
            p4c.set_visual_style(STYLE_NAME, network=network_suid, base_url=args.base_url)

            if not args.skip_layout:
                layout_name = _pick_layout_name(args.base_url)
                if layout_name:
                    try:
                        p4c.layout_network(layout_name, network=network_suid, base_url=args.base_url)
                    except Exception as exc:
                        print(f"Warning: could not run layout '{{layout_name}}': {{exc}}", file=sys.stderr)

            print("Imported:", graphml_path)
            print("Network SUID:", network_suid)
            print("Applied style:", STYLE_NAME)
            print("Tool colors:", ", ".join(f"{{tool_id}}={{TOOL_COLORS[tool_id]}}" for tool_id in TOOL_IDS) or "<none>")
            print("Group contexts use line type:", group_line_style)
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(script, encoding="utf-8")
    try:
        out_path.chmod(0o755)
    except OSError:
        pass
    return len(rows)
