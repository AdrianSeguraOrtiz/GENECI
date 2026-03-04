from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from ._module_loader import load_infer_new_module


class InferNetworkV2CoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_infer_new_module()

    def _write_expression_matrix(
        self,
        base: Path,
        *,
        lines: list[str],
        filename: str = "expression.tsv",
    ) -> Path:
        expression_path = base / filename
        expression_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return expression_path

    def _write_manifest(
        self,
        base: Path,
        *,
        expression_matrix: str = "expression.tsv",
        genes: int = 2,
        columns: int = 2,
        column_kind: str = "samples",
        expression_profile: str = "mixed",
        extras: dict[str, Any] | None = None,
    ) -> Path:
        manifest = {
            "schema_version": "1.0",
            "id": "toy_ds_manifest",
            "dataset": {
                "spec": {
                    "schema_version": "1.0",
                    "id": "toy_ds",
                    "name": "toy_ds",
                    "expression": {
                        "genes": genes,
                        "columns": columns,
                        "column_kind": column_kind,
                        "expression_profile": expression_profile,
                    },
                    "organism": {"tax_id": 9606},
                },
                "expression_matrix": expression_matrix,
            },
            "extras": extras or {},
        }
        manifest_path = base / "dataset-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        return manifest_path

    def _write_tools_params(
        self,
        base: Path,
        *,
        runs: list[dict[str, Any]],
    ) -> Path:
        tools_params_path = base / "tools_params.json"
        tools_params_path.write_text(
            json.dumps({"runs": runs}, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return tools_params_path

    def _write_dataset_bundle(
        self,
        base: Path,
        *,
        tf_values: list[str],
    ) -> tuple[Path, Path]:
        self._write_expression_matrix(
            base,
            lines=[
                "gene\tS1\tS2",
                "G1\t1\t2",
                "G2\t3\t4",
            ],
        )
        tf_list = base / "tf_list.txt"
        tf_list.write_text("\n".join(tf_values) + "\n", encoding="utf-8")

        manifest_path = self._write_manifest(
            base,
            expression_matrix="expression.tsv",
            extras={"tf_list": "tf_list.txt"},
        )
        tools_params_path = self._write_tools_params(
            base,
            runs=[
                {"run_id": "aracne__01", "tool_id": "aracne3", "params": {"seed": 42}},
            ],
        )
        return manifest_path, tools_params_path
