from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from geneci.core.commands.benchmarking.generate_v2.catalog import _load_simulator_catalog
from geneci.core.commands.benchmarking.generate_v2.plan import plan_generate_v2_request
from geneci.core.commands.benchmarking.generate_v2.pipeline import run_generate_v2
from geneci.core.commands.benchmarking.generate_v2.request import validate_benchmark_request
from geneci.core.commands.benchmarking.generate_v2.selection import (
    preflight_generate_v2_scenario,
)
from geneci.core.commands.infer_network_v2.preflight import preflight_infer_network_new


def _has_docker_runtime() -> bool:
    if shutil.which("docker") is None:
        return False
    result = subprocess.run(
        ["docker", "info"],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


class GenerateV2DyngenTests(unittest.TestCase):
    def _write_scenario_request(
        self,
        base: Path,
        *,
        request_id: str,
        profile: str,
        requested_extras: list[str],
        input_files: dict[str, str] | None = None,
        organism: dict[str, object] | None = None,
        replicates: int = 1,
    ) -> Path:
        payload = {
            "schema_version": "1.0",
            "id": request_id,
            "profile": profile,
            "replicates": replicates,
            "organism": organism or {"kind": "synthetic", "tax_id": None},
            "requested_extras": requested_extras,
            "input_files": input_files or {},
        }
        request_path = base / "scenario.json"
        request_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return request_path

    def _write_request(
        self,
        base: Path,
        *,
        request_id: str,
        profile: str,
        simulator_id: str,
        requested_extras: list[str],
        simulator_params: dict[str, object],
        organism: dict[str, object] | None = None,
        replicates: int = 1,
    ) -> Path:
        payload = {
            "schema_version": "1.0",
            "id": request_id,
            "profile": profile,
            "simulator_id": simulator_id,
            "replicates": replicates,
            "organism": organism or {"kind": "synthetic", "tax_id": None},
            "requested_extras": requested_extras,
            "input_files": {},
            "simulator_params": simulator_params,
        }
        request_path = base / "request.json"
        request_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return request_path

    def _write_tools_params(self, base: Path, runs: list[dict[str, object]]) -> Path:
        tools_params_path = base / "tools_params.json"
        tools_params_path.write_text(
            json.dumps({"runs": runs}, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return tools_params_path

    def test_catalog_loads_only_completed_dyngen_simulator(self) -> None:
        schemas, catalog = _load_simulator_catalog()
        self.assertEqual(sorted(catalog.keys()), ["dyngen"])
        self.assertIn("simulatorspec", schemas)
        self.assertIn("scenario_request", schemas)
        self.assertIn("preflight_report", schemas)
        self.assertEqual(
            catalog["dyngen"]["docker_image"],
            "adriansegura99/simulator_dyngen:1.0.0",
        )
        self.assertEqual(
            sorted(catalog["dyngen"]["profile_capabilities"]),
            ["scrna_global", "scrna_grouped"],
        )
        for param_name in (
            "num_tfs",
            "distance_metric",
            "tf_network_params",
            "feature_network_params",
            "gold_standard_params",
            "simulation_params",
            "experiment_params",
        ):
            self.assertIn(param_name, catalog["dyngen"]["params"])

    def test_dataset_manifest_schema_accepts_old_and_synthetic_organisms(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[4]
            / "geneci"
            / "inference_catalog"
            / "schemas"
            / "dataset-manifest.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)

        biological_manifest = {
            "schema_version": "1.0",
            "id": "bio_manifest",
            "dataset": {
                "spec": {
                    "schema_version": "1.0",
                    "id": "bio_ds",
                    "name": "bio_ds",
                    "expression": {
                        "genes": 2,
                        "columns": 2,
                        "column_kind": "samples",
                        "expression_profile": "bulk",
                    },
                    "organism": {"tax_id": 9606},
                },
                "expression_matrix": "expression.tsv",
            },
        }
        synthetic_manifest = {
            "schema_version": "1.0",
            "id": "syn_manifest",
            "dataset": {
                "spec": {
                    "schema_version": "1.0",
                    "id": "syn_ds",
                    "name": "syn_ds",
                    "expression": {
                        "genes": 2,
                        "columns": 2,
                        "column_kind": "cells",
                        "expression_profile": "scrna",
                    },
                    "organism": {"kind": "synthetic", "tax_id": None},
                },
                "expression_matrix": "expression.tsv",
            },
        }
        self.assertEqual(list(validator.iter_errors(biological_manifest)), [])
        self.assertEqual(list(validator.iter_errors(synthetic_manifest)), [])

    def test_preflight_classifies_dyngen_for_grouped_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = self._write_scenario_request(
                Path(tmp),
                request_id="scrna_grouped_lineage",
                profile="scrna_grouped",
                requested_extras=["lineage_tree"],
            )
            report = preflight_generate_v2_scenario(scenario_path)

        self.assertEqual(report["catalog_summary"]["total"], 1)
        self.assertEqual(report["catalog_summary"]["blocked"], 0)
        self.assertEqual(report["catalog_summary"]["warning"], 1)
        self.assertEqual(report["warning"][0]["simulator_id"], "dyngen")
        self.assertIn("lineage_tree", "; ".join(report["warning"][0]["warnings"]))

    def test_preflight_blocks_dyngen_when_docker_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = self._write_scenario_request(
                Path(tmp),
                request_id="runtime_blocked",
                profile="scrna_grouped",
                requested_extras=["lineage_tree"],
            )
            with patch(
                "geneci.core.commands.benchmarking.generate_v2.selection.subprocess.run"
            ) as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["docker", "info"],
                    returncode=1,
                    stdout="",
                    stderr="Cannot connect to the Docker daemon",
                )
                report = preflight_generate_v2_scenario(scenario_path)

        self.assertEqual(report["catalog_summary"]["blocked"], 1)
        self.assertEqual(report["blocked"][0]["simulator_id"], "dyngen")
        self.assertTrue(
            any(
                "docker daemon is not available" in reason
                for reason in report["blocked"][0]["blocking_reasons"]
            )
        )

    def test_preflight_blocks_unknown_simulator_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            custom_input = base / "custom.tsv"
            custom_input.write_text("id\tvalue\nx\t1\n", encoding="utf-8")
            scenario_path = self._write_scenario_request(
                base,
                request_id="unknown_input",
                profile="scrna_grouped",
                requested_extras=[],
                input_files={"custom_backbone": "custom.tsv"},
            )
            report = preflight_generate_v2_scenario(scenario_path)

        self.assertEqual(report["catalog_summary"]["blocked"], 1)
        self.assertEqual(report["blocked"][0]["simulator_id"], "dyngen")
        self.assertTrue(
            any(
                "unknown input_files" in reason
                for reason in report["blocked"][0]["blocking_reasons"]
            )
        )

    def test_validate_request_accepts_dyngen_grouped_lineage_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = self._write_request(
                Path(tmp),
                request_id="dyngen_lineage_ok",
                profile="scrna_grouped",
                simulator_id="dyngen",
                requested_extras=["lineage_tree"],
                simulator_params={"num_cells": 10},
            )
            resolved = validate_benchmark_request(request_path)

        self.assertEqual(resolved.profile, "scrna_grouped")
        self.assertEqual(resolved.simulator_id, "dyngen")
        self.assertEqual(resolved.effective_extras, ["groups", "lineage_tree"])

    def test_validate_request_rejects_unsupported_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = self._write_request(
                Path(tmp),
                request_id="bulk_bad",
                profile="bulk_time_series",
                simulator_id="dyngen",
                requested_extras=[],
                simulator_params={},
            )
            with self.assertRaisesRegex(ValueError, "does not support profile"):
                validate_benchmark_request(request_path)

    def test_plan_generates_valid_dyngen_benchmark_request_from_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            scenario_path = self._write_scenario_request(
                base,
                request_id="plan_dyngen",
                profile="scrna_grouped",
                requested_extras=["lineage_tree", "tf_list"],
            )
            output_path = base / "benchmark-request.json"
            planned_path = plan_generate_v2_request(
                scenario_request_path=scenario_path,
                simulator_id="dyngen",
                simulator_params={"num_cells": 25},
                output_path=output_path,
            )
            payload = json.loads(planned_path.read_text(encoding="utf-8"))
            resolved = validate_benchmark_request(planned_path)

        self.assertEqual(planned_path, output_path)
        self.assertEqual(payload["simulator_id"], "dyngen")
        self.assertEqual(payload["profile"], "scrna_grouped")
        self.assertEqual(payload["requested_extras"], ["lineage_tree", "tf_list"])
        self.assertEqual(payload["simulator_params"]["num_cells"], 25)
        self.assertIn("simulation_params", payload["simulator_params"])
        self.assertEqual(resolved.simulator_id, "dyngen")
        self.assertEqual(resolved.effective_extras, ["groups", "lineage_tree", "tf_list"])

    @unittest.skipUnless(_has_docker_runtime(), "docker runtime is required for dyngen tests")
    def test_run_generate_v2_dyngen_grouped_is_consumable_by_infer_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            request_path = self._write_request(
                base,
                request_id="dyngen_stage1",
                profile="scrna_grouped",
                simulator_id="dyngen",
                requested_extras=["tf_list"],
                simulator_params={
                    "num_cells": 12,
                    "simulation_params": {
                        "num_simulations": 4,
                        "compute_dimred": False,
                    },
                    "experiment_params": {
                        "map_reference_cpm": False,
                        "map_reference_ls": False,
                    },
                },
            )
            benchmark_root = run_generate_v2(
                request_path=request_path,
                output_dir=base / "out",
            )
            dataset_dir = benchmark_root / "datasets" / "dyngen_stage1__01"
            manifest_path = dataset_dir / "dataset-manifest.json"

            self.assertTrue((dataset_dir / "extras" / "groups.tsv").exists())
            self.assertTrue((dataset_dir / "extras" / "tf_list.txt").exists())
            self.assertTrue((dataset_dir / "truth" / "global_network.csv").exists())

            report = preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=None,
                strict=False,
            )
            self.assertEqual(report["dataset"]["dataset_id"], "dyngen_stage1__01")

    @unittest.skipUnless(_has_docker_runtime(), "docker runtime is required for dyngen tests")
    def test_run_generate_v2_dyngen_grouped_lineage_tree_is_consumable_by_scmtni(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            request_path = self._write_request(
                base,
                request_id="dyngen_stage2",
                profile="scrna_grouped",
                simulator_id="dyngen",
                requested_extras=["lineage_tree", "tf_list"],
                simulator_params={
                    "num_cells": 10,
                    "simulation_params": {
                        "num_simulations": 4,
                        "compute_dimred": False,
                    },
                    "experiment_params": {
                        "map_reference_cpm": False,
                        "map_reference_ls": False,
                    },
                },
            )
            benchmark_root = run_generate_v2(
                request_path=request_path,
                output_dir=base / "out",
            )
            dataset_dir = benchmark_root / "datasets" / "dyngen_stage2__01"
            manifest_path = dataset_dir / "dataset-manifest.json"
            tools_params_path = self._write_tools_params(
                base,
                [
                    {
                        "run_id": "scmtni__01",
                        "tool_id": "scmtni",
                        "params": {"indep": False, "q": 0},
                    }
                ],
            )

            self.assertTrue((dataset_dir / "extras" / "groups.tsv").exists())
            self.assertTrue((dataset_dir / "extras" / "lineage_tree.tsv").exists())
            self.assertTrue((dataset_dir / "extras" / "tf_list.txt").exists())
            self.assertTrue((dataset_dir / "truth" / "global_network.csv").exists())
            self.assertTrue(
                (dataset_dir / "provenance" / "raw" / "group_edge_activity.tsv").exists()
            )
            self.assertTrue(
                (dataset_dir / "provenance" / "raw" / "group_active_networks.tsv").exists()
            )

            dataset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                dataset_manifest["extras"]["lineage_tree"],
                "extras/lineage_tree.tsv",
            )
            simulator_run = json.loads(
                (dataset_dir / "provenance" / "simulator-run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("lineage_tree", simulator_run["effective_extras"])
            self.assertEqual(
                simulator_run["simulator_output"]["extras"]["lineage_tree"],
                "extras/lineage_tree.tsv",
            )

            report = preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=tools_params_path,
                strict=False,
            )
            self.assertEqual(report["dataset"]["dataset_id"], "dyngen_stage2__01")
            self.assertIn("scmtni__01", report["runs"]["selected"])
            self.assertNotIn("scmtni__01", report["runs"]["requirement_issues"])


if __name__ == "__main__":
    unittest.main()
