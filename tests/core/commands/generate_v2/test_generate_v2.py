from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from geneci.core.commands.benchmarking.generate_v2.catalog import (
    _load_simulator_catalog,
)
from geneci.core.commands.benchmarking.generate_v2.plan import plan_generate_v2_request
from geneci.core.commands.benchmarking.generate_v2.pipeline import run_generate_v2
from geneci.core.commands.benchmarking.generate_v2.request import (
    validate_simulation_plan,
)
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
        inputs: dict[str, object] | None = None,
        organism: dict[str, object] | None = None,
    ) -> Path:
        payload = {
            "schema_version": "1.0",
            "id": request_id,
            "profile": profile,
            "requested_extras": requested_extras,
            "inputs": inputs or {},
        }
        if organism is not None:
            payload["organism"] = organism
        request_path = base / "scenario.json"
        request_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return request_path

    def _write_plan(
        self,
        base: Path,
        *,
        request_id: str,
        profile: str,
        simulator_id: str,
        requested_extras: list[str],
        simulator_params: dict[str, object],
        run_id: str = "dyngen_default",
        organism: dict[str, object] | None = None,
        replicates: int = 1,
        base_seed: int = 100,
    ) -> Path:
        seeds = [base_seed + idx for idx in range(replicates)]
        payload = {
            "schema_version": "1.0",
            "id": request_id,
            "profile": profile,
            "organism": organism or {"kind": "synthetic", "tax_id": None},
            "requested_extras": requested_extras,
            "effective_extras": sorted(
                set(requested_extras).union(
                    {"groups"} if profile == "scrna_grouped" else set()
                )
            ),
            "inputs": {},
            "input_files": {},
            "base_seed": base_seed,
            "runs": [
                {
                    "run_id": run_id,
                    "simulator_id": simulator_id,
                    "simulator_params": simulator_params,
                    "replicates": replicates,
                    "base_seed": base_seed,
                    "replicate_seeds": seeds,
                }
            ],
            "tasks": [
                {
                    "task_id": f"{run_id}__r{idx:02d}",
                    "run_id": run_id,
                    "simulator_id": simulator_id,
                    "replicate_index": idx,
                    "seed": seed,
                    "dataset_id": f"{request_id}__{run_id}__r{idx:02d}",
                }
                for idx, seed in enumerate(seeds, start=1)
            ],
            "execution": {"max_parallel_tasks": 1},
        }
        plan_path = base / "simulation-plan.json"
        plan_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return plan_path

    def _write_simulator_runs(
        self,
        base: Path,
        runs: list[dict[str, object]],
    ) -> Path:
        simulator_runs_path = base / "simulator-runs.json"
        simulator_runs_path.write_text(
            json.dumps(
                {"schema_version": "1.0", "runs": runs},
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return simulator_runs_path

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
        self.assertIn("simulator_runs", schemas)
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
        self.assertEqual(report["catalog_summary"]["warning"], 0)
        self.assertEqual(report["catalog_summary"]["eligible"], 1)
        self.assertEqual(report["eligible"][0]["simulator_id"], "dyngen")
        self.assertIn("groups", report["eligible"][0]["derived_extras_used"])
        self.assertIn("lineage_tree", report["eligible"][0]["derived_extras_used"])
        self.assertEqual(report["eligible"][0]["warnings"], [])

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
                inputs={"custom_backbone": {"path": "custom.tsv"}},
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

    def test_validate_plan_accepts_dyngen_grouped_lineage_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = self._write_plan(
                Path(tmp),
                request_id="dyngen_lineage_ok",
                profile="scrna_grouped",
                simulator_id="dyngen",
                requested_extras=["lineage_tree"],
                simulator_params={"num_cells": 10},
            )
            resolved = validate_simulation_plan(plan_path)

        self.assertEqual(resolved.profile, "scrna_grouped")
        self.assertEqual(len(resolved.simulator_runs), 1)
        self.assertEqual(resolved.simulator_runs[0].simulator_id, "dyngen")
        self.assertEqual(resolved.effective_extras, ["groups", "lineage_tree"])

    def test_validate_plan_rejects_unsupported_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = self._write_plan(
                Path(tmp),
                request_id="bulk_bad",
                profile="bulk_time_series",
                simulator_id="dyngen",
                requested_extras=[],
                simulator_params={},
            )
            with self.assertRaisesRegex(ValueError, "does not support profile"):
                validate_simulation_plan(plan_path)

    def test_validate_plan_accepts_same_simulator_with_distinct_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = {
                "schema_version": "1.0",
                "id": "multi_sim",
                "profile": "scrna_global",
                "organism": {"kind": "synthetic", "tax_id": None},
                "requested_extras": [],
                "effective_extras": [],
                "inputs": {},
                "base_seed": 100,
                "runs": [
                    {
                        "run_id": "dyngen_a",
                        "simulator_id": "dyngen",
                        "simulator_params": {},
                        "replicates": 2,
                        "base_seed": 100,
                        "replicate_seeds": [100, 101],
                    },
                    {
                        "run_id": "dyngen_b",
                        "simulator_id": "dyngen",
                        "simulator_params": {},
                        "replicates": 2,
                        "base_seed": 102,
                        "replicate_seeds": [102, 103],
                    },
                ],
                "tasks": [
                    {
                        "task_id": "dyngen_a__r01",
                        "run_id": "dyngen_a",
                        "simulator_id": "dyngen",
                        "replicate_index": 1,
                        "seed": 100,
                        "dataset_id": "multi_sim__dyngen_a__r01",
                    },
                    {
                        "task_id": "dyngen_a__r02",
                        "run_id": "dyngen_a",
                        "simulator_id": "dyngen",
                        "replicate_index": 2,
                        "seed": 101,
                        "dataset_id": "multi_sim__dyngen_a__r02",
                    },
                    {
                        "task_id": "dyngen_b__r01",
                        "run_id": "dyngen_b",
                        "simulator_id": "dyngen",
                        "replicate_index": 1,
                        "seed": 102,
                        "dataset_id": "multi_sim__dyngen_b__r01",
                    },
                    {
                        "task_id": "dyngen_b__r02",
                        "run_id": "dyngen_b",
                        "simulator_id": "dyngen",
                        "replicate_index": 2,
                        "seed": 103,
                        "dataset_id": "multi_sim__dyngen_b__r02",
                    },
                ],
                "execution": {"max_parallel_tasks": 2},
            }
            plan_path = base / "simulation-plan.json"
            plan_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            resolved = validate_simulation_plan(plan_path)

        self.assertEqual(
            [run.run_id for run in resolved.simulator_runs],
            ["dyngen_a", "dyngen_b"],
        )
        self.assertEqual(resolved.simulator_runs[0].replicate_seeds, [100, 101])
        self.assertEqual(resolved.simulator_runs[1].replicate_seeds, [102, 103])
        self.assertEqual(resolved.execution["max_parallel_tasks"], 2)

    def test_plan_generates_valid_dyngen_simulation_plan_from_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            scenario_path = self._write_scenario_request(
                base,
                request_id="plan_dyngen",
                profile="scrna_grouped",
                requested_extras=["lineage_tree", "tf_list"],
            )
            simulator_runs_path = self._write_simulator_runs(
                base,
                [
                    {
                        "run_id": "dyngen_small",
                        "simulator_id": "dyngen",
                        "replicates": 2,
                        "params": {"num_cells": 25},
                    },
                    {
                        "run_id": "dyngen_linear",
                        "simulator_id": "dyngen",
                        "replicates": 2,
                        "params": {"num_cells": 30, "backbone_template": "linear"},
                    },
                ],
            )
            output_path = base / "simulation-plan.json"
            planned_path = plan_generate_v2_request(
                scenario_request_path=scenario_path,
                simulator_runs_path=simulator_runs_path,
                output_path=output_path,
                max_parallel_tasks=2,
            )
            payload = json.loads(planned_path.read_text(encoding="utf-8"))
            resolved = validate_simulation_plan(planned_path)

        self.assertEqual(planned_path, output_path)
        self.assertEqual(
            [run["run_id"] for run in payload["runs"]],
            ["dyngen_small", "dyngen_linear"],
        )
        self.assertEqual(payload["profile"], "scrna_grouped")
        self.assertEqual(payload["requested_extras"], ["lineage_tree", "tf_list"])
        simulator_params = payload["runs"][0]["simulator_params"]
        self.assertEqual(simulator_params["num_cells"], 25)
        self.assertIn("simulation_params", simulator_params)
        self.assertEqual(resolved.simulator_runs[0].run_id, "dyngen_small")
        self.assertEqual(len(resolved.tasks), 4)
        self.assertEqual(resolved.execution["max_parallel_tasks"], 2)
        self.assertEqual(
            resolved.effective_extras, ["groups", "lineage_tree", "tf_list"]
        )

    @unittest.skipUnless(
        _has_docker_runtime(), "docker runtime is required for dyngen tests"
    )
    def test_run_generate_v2_dyngen_grouped_is_consumable_by_infer_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan_path = self._write_plan(
                base,
                request_id="dyngen_stage1",
                profile="scrna_grouped",
                simulator_id="dyngen",
                run_id="dyngen_small",
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
                plan_path=plan_path,
                output_dir=base / "out",
            )
            dataset_dir = (
                benchmark_root / "datasets" / "dyngen_stage1__dyngen_small__r01"
            )
            manifest_path = dataset_dir / "dataset-manifest.json"

            self.assertTrue((dataset_dir / "extras" / "groups.tsv").exists())
            self.assertTrue((dataset_dir / "extras" / "tf_list.txt").exists())
            self.assertTrue((dataset_dir / "truth" / "global_network.csv").exists())

            report = preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=None,
                strict=False,
            )
            self.assertEqual(
                report["dataset"]["dataset_id"],
                "dyngen_stage1__dyngen_small__r01",
            )

    @unittest.skipUnless(
        _has_docker_runtime(), "docker runtime is required for dyngen tests"
    )
    def test_run_generate_v2_dyngen_grouped_lineage_tree_is_consumable_by_scmtni(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan_path = self._write_plan(
                base,
                request_id="dyngen_stage2",
                profile="scrna_grouped",
                simulator_id="dyngen",
                run_id="dyngen_lineage",
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
                plan_path=plan_path,
                output_dir=base / "out",
            )
            dataset_dir = (
                benchmark_root / "datasets" / "dyngen_stage2__dyngen_lineage__r01"
            )
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
                (
                    dataset_dir / "provenance" / "raw" / "group_edge_activity.tsv"
                ).exists()
            )
            self.assertTrue(
                (
                    dataset_dir / "provenance" / "raw" / "group_active_networks.tsv"
                ).exists()
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
            self.assertEqual(
                report["dataset"]["dataset_id"],
                "dyngen_stage2__dyngen_lineage__r01",
            )
            self.assertIn("scmtni__01", report["runs"]["selected"])
            self.assertNotIn("scmtni__01", report["runs"]["requirement_issues"])


if __name__ == "__main__":
    unittest.main()
