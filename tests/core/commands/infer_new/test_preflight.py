from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._helpers import InferNetworkV2CoreTestCase


class InferNetworkV2PreflightTests(InferNetworkV2CoreTestCase):
    def test_preflight_fails_when_input_spec_cross_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest_path, _tools_params_path = self._write_dataset_bundle(
                base,
                tf_values=["G1", "UNKNOWN_TF"],
            )

            with self.assertRaisesRegex(ValueError, "Input validation failed"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=None,
                    strict=False,
                )

    def test_preflight_invalid_tool_params_non_strict_skips_and_strict_raises(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest_path, tools_params_path = self._write_dataset_bundle(
                base,
                tf_values=["G1", "G2"],
            )
            tools_payload = json.loads(tools_params_path.read_text(encoding="utf-8"))
            tools_payload["runs"][0]["params"] = {"alpha": "NOT_A_FLOAT"}
            tools_params_path.write_text(
                json.dumps(tools_payload, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )

            preflight_report = self.mod.preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=tools_params_path,
                strict=False,
            )
            self.assertEqual(preflight_report["runs"]["selected"], [])
            self.assertIn("aracne__01", preflight_report["runs"]["skipped"])

            with self.assertRaisesRegex(ValueError, "invalid parameter set"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=tools_params_path,
                    strict=True,
                )

    def test_preflight_fails_when_groups_file_has_wrong_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "gene\tS1\tS2",
                    "G1\t1\t2",
                    "G2\t3\t4",
                ],
            )
            (base / "groups.tsv").write_text(
                "\n".join(
                    [
                        "cell\tpseudotime",
                        "S1\t0.10",
                        "S2\t0.20",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_path = self._write_manifest(
                base,
                expression_matrix="expression.tsv",
                extras={"groups": "groups.tsv"},
            )

            with self.assertRaisesRegex(ValueError, "Input validation failed"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=None,
                    strict=False,
                )

    def test_preflight_accepts_groups_with_sample_column_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "gene\tS1\tS2",
                    "G1\t1\t2",
                    "G2\t3\t4",
                ],
            )
            (base / "groups.tsv").write_text(
                "\n".join(
                    [
                        "sample\tcluster",
                        "S1\tA",
                        "S2\tB",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_path = self._write_manifest(
                base,
                expression_matrix="expression.tsv",
                column_kind="samples",
                extras={"groups": "groups.tsv"},
            )

            preflight = self.mod.preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=None,
                strict=False,
            )
            extras_validation = preflight["input_validation"]["extras"]["groups"]
            self.assertEqual(extras_validation["status"], "ok")
            self.assertFalse(extras_validation["errors"])

    def test_preflight_fails_when_expression_first_header_is_not_gene_like(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "cell\tpseudotime",
                    "C1\t0.10",
                    "C2\t0.20",
                ],
            )
            manifest_path = self._write_manifest(
                base,
                expression_matrix="expression.tsv",
                columns=1,
            )

            with self.assertRaisesRegex(ValueError, "Input validation failed"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=None,
                    strict=False,
                )

    def test_preflight_fails_when_expression_has_duplicated_gene_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "gene\tS1\tS2",
                    "G1\t1\t2",
                    "G1\t3\t4",
                ],
            )
            manifest_path = self._write_manifest(
                base, expression_matrix="expression.tsv"
            )

            with self.assertRaisesRegex(ValueError, "Input validation failed"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=None,
                    strict=False,
                )

    def test_preflight_fails_when_expression_has_non_numeric_data_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "gene\tS1\tS2",
                    "G1\t1\tNOT_A_NUMBER",
                    "G2\t3\t4",
                ],
            )
            manifest_path = self._write_manifest(
                base, expression_matrix="expression.tsv"
            )

            with self.assertRaisesRegex(ValueError, "Input validation failed"):
                self.mod.preflight_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=None,
                    strict=False,
                )

    def test_preflight_accepts_valid_expression_matrix_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_expression_matrix(
                base,
                lines=[
                    "gene\tsample_A\tsample_B",
                    "G1\t1.0\t2.5",
                    "G2\t3.2\t4.8",
                ],
            )
            manifest_path = self._write_manifest(
                base, expression_matrix="expression.tsv"
            )

            preflight = self.mod.preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=None,
                strict=False,
            )
            expr_validation = preflight["input_validation"]["expression_matrix"]
            self.assertEqual(expr_validation["status"], "ok")
            self.assertFalse(expr_validation["errors"])
