from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ._helpers import InferNetworkV2CoreTestCase


class InferNetworkV2PlanTests(InferNetworkV2CoreTestCase):
    def test_preflight_and_plan_generate_frozen_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output_dir = base / "out"
            manifest_path, tools_params_path = self._write_dataset_bundle(
                base,
                tf_values=["G1", "G2"],
            )

            preflight = self.mod.preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=tools_params_path,
                strict=False,
            )
            self.assertIn("catalog", preflight)
            self.assertIn("runs", preflight)
            self.assertEqual(preflight["runs"]["selected"], ["aracne__01"])

            run_dir = self.mod.plan_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=tools_params_path,
                output_dir=output_dir,
                planner="heuristic",
                strict=False,
                preflight_report=preflight,
            )
            self.assertTrue((run_dir / "plan.json").exists())
            self.assertTrue((run_dir / "preflight_report.json").exists())
            self.assertTrue((run_dir / "run_report.json").exists())
            self.assertTrue((run_dir / "input" / "dataset-manifest.json").exists())
            self.assertTrue((run_dir / "input" / "tools_params.json").exists())
            self.assertTrue((run_dir / "input" / "expression.tsv").exists())
            self.assertTrue((run_dir / "input" / "extra" / "tf_list.txt").exists())
            self.assertTrue(
                (run_dir / "tools" / "aracne__01" / "resolved_params.json").exists()
            )

            plan_payload = json.loads(
                (run_dir / "plan.json").read_text(encoding="utf-8")
            )
            self.assertIn("input_fingerprints", plan_payload)
            self.assertTrue(plan_payload["input_fingerprints"])

            report_payload = json.loads(
                (run_dir / "run_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report_payload["status"], "planned")

    def test_plan_rejects_invalid_planner_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output_dir = base / "out"
            manifest_path, tools_params_path = self._write_dataset_bundle(
                base,
                tf_values=["G1", "G2"],
            )
            preflight = self.mod.preflight_infer_network_new(
                dataset_manifest_path=manifest_path,
                tools_params_path=tools_params_path,
                strict=False,
            )

            with self.assertRaisesRegex(ValueError, "max_cores must be >= 1"):
                self.mod.plan_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=tools_params_path,
                    output_dir=output_dir,
                    max_cores=0,
                    planner="heuristic",
                    strict=False,
                    preflight_report=preflight,
                )

            with self.assertRaisesRegex(ValueError, "planner must be one of"):
                self.mod.plan_infer_network_new(
                    dataset_manifest_path=manifest_path,
                    tools_params_path=tools_params_path,
                    output_dir=output_dir,
                    planner="unknown_planner",
                    strict=False,
                    preflight_report=preflight,
                )
