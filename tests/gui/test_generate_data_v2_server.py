from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
except Exception:  # noqa: BLE001
    TestClient = None

try:
    from geneci.gui.generate_data_v2 import server as gui_server
except Exception:  # noqa: BLE001
    gui_server = None


class _ImmediateThread:
    def __init__(
        self, *, target=None, kwargs=None, daemon=None
    ):  # noqa: ANN001, ANN204
        self._target = target
        self._kwargs = kwargs or {}
        self.daemon = daemon

    def start(self) -> None:
        if self._target is not None:
            self._target(**self._kwargs)


@unittest.skipIf(
    TestClient is None or gui_server is None,
    "GUI test dependencies are not installed",
)
class GenerateDataV2GuiServerTests(unittest.TestCase):
    def test_bootstrap_exposes_profile_extras_and_simulator_inputs(self) -> None:
        client = TestClient(gui_server.create_app())
        payload = client.get("/api/generate-data-v2/bootstrap").json()
        profiles = {item["id"]: item for item in payload["profiles"]}
        self.assertNotIn(
            "lineage_tree", profiles["bulk_steady_state"]["available_extras"]
        )
        self.assertIn("groups", profiles["scrna_grouped"]["available_extras"])
        self.assertIn("lineage_tree", profiles["scrna_grouped"]["available_extras"])
        self.assertIn("group_networks", profiles["scrna_grouped"]["available_extras"])
        inputs = {item["id"]: item for item in payload["simulator_inputs"]}
        self.assertTrue(inputs["grn"]["requires_organism"])
        self.assertEqual(
            inputs["grn"]["required_columns"], ["source", "target", "weight"]
        )
        simulators = {item["simulator_id"]: item for item in payload["simulators"]}
        grouped_native_outputs = {
            item["id"]
            for item in simulators["dyngen"]["profile_capabilities"]["scrna_grouped"][
                "native_outputs"
            ]
        }
        self.assertIn("rna_velocity", grouped_native_outputs)
        self.assertIn("regulatory_network_sc", grouped_native_outputs)

    def test_preflight_plan_run_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)

            def fake_preflight(scenario_path):  # noqa: ANN001
                payload = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
                return {
                    "schema_version": "1.0",
                    "scenario": {
                        "id": payload["id"],
                        "profile": payload["profile"],
                        "organism": payload["organism"],
                        "requested_extras": payload["requested_extras"],
                        "effective_extras": ["groups", "lineage_tree"],
                        "input_files": {},
                        "inputs": {},
                        "base_seed": payload.get("base_seed", 100),
                    },
                    "catalog_summary": {
                        "total": 1,
                        "eligible": 1,
                        "warning": 0,
                        "blocked": 0,
                    },
                    "eligible": [
                        {
                            "simulator_id": "dyngen",
                            "name": "dyngen",
                            "requested_profile": "scrna_grouped",
                            "requested_extras": ["lineage_tree"],
                            "effective_extras": ["groups", "lineage_tree"],
                            "input_files_used": [],
                            "native_extras_used": [],
                            "derived_extras_used": ["groups", "lineage_tree"],
                            "truth_outputs": {
                                "global_network": "native",
                                "legacy_binary_matrix": "derivable",
                                "group_networks": "derivable",
                            },
                            "status": "eligible",
                            "warnings": [],
                            "blocking_reasons": [],
                        }
                    ],
                    "warning": [],
                    "blocked": [],
                }

            def fake_plan(**kwargs):  # noqa: ANN003
                simulator_runs = json.loads(
                    Path(kwargs["simulator_runs_path"]).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    simulator_runs["runs"][0]["native_outputs"],
                    ["rna_velocity"],
                )
                plan_payload = {
                    "schema_version": "1.0",
                    "id": "gui_generate_test",
                    "profile": "scrna_grouped",
                    "organism": {"kind": "synthetic", "tax_id": None},
                    "requested_extras": ["lineage_tree"],
                    "effective_extras": ["groups", "lineage_tree"],
                    "inputs": {},
                    "runs": [
                        {
                            "run_id": "dyngen_a",
                            "simulator_id": "dyngen",
                            "simulator_params": {},
                            "replicates": 2,
                            "native_outputs": ["rna_velocity"],
                            "base_seed": 100,
                            "replicate_seeds": [100, 101],
                        }
                    ],
                    "tasks": [
                        {
                            "task_id": "dyngen_a__r01",
                            "run_id": "dyngen_a",
                            "simulator_id": "dyngen",
                            "replicate_index": 1,
                            "seed": 100,
                            "dataset_id": "gui_generate_test__dyngen_a__r01",
                        },
                        {
                            "task_id": "dyngen_a__r02",
                            "run_id": "dyngen_a",
                            "simulator_id": "dyngen",
                            "replicate_index": 2,
                            "seed": 101,
                            "dataset_id": "gui_generate_test__dyngen_a__r02",
                        },
                    ],
                    "execution": {"max_parallel_tasks": kwargs["max_parallel_tasks"]},
                    "base_seed": 100,
                }
                kwargs["output_path"].write_text(
                    json.dumps(plan_payload, indent=2, ensure_ascii=True) + "\n",
                    encoding="utf-8",
                )
                return kwargs["output_path"]

            def fake_run(**kwargs):  # noqa: ANN003
                callback = kwargs["progress_callback"]
                callback(
                    {
                        "task_id": "dyngen_a__r01",
                        "run_id": "dyngen_a",
                        "simulator_id": "dyngen",
                        "replicate_index": 1,
                        "seed": 100,
                        "dataset_id": "gui_generate_test__dyngen_a__r01",
                        "percent": 100,
                        "status": "completed",
                        "phase": "done",
                        "message": "done",
                        "updated_at": "2026-04-22T00:00:00Z",
                    }
                )
                benchmark_root = kwargs["output_dir"] / "gui_generate_test"
                input_dir = benchmark_root / "input"
                dataset_dir = (
                    benchmark_root / "datasets" / "gui_generate_test__dyngen_a__r01"
                )
                input_dir.mkdir(parents=True, exist_ok=True)
                (dataset_dir / "truth" / "legacy").mkdir(parents=True, exist_ok=True)
                (dataset_dir / "extras").mkdir(parents=True, exist_ok=True)
                (dataset_dir / "provenance").mkdir(parents=True, exist_ok=True)
                (input_dir / "scenario-request.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0",
                            "id": "gui_generate_test",
                            "profile": "scrna_grouped",
                            "requested_extras": ["lineage_tree"],
                            "organism": {"kind": "synthetic", "tax_id": None},
                            "base_seed": 100,
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (input_dir / "simulator-runs.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0",
                            "runs": [
                                {
                                    "run_id": "dyngen_a",
                                    "simulator_id": "dyngen",
                                    "replicates": 2,
                                    "native_outputs": ["rna_velocity"],
                                    "params": {},
                                }
                            ],
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (benchmark_root / "preflight-report.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0",
                            "scenario": {
                                "id": "gui_generate_test",
                                "profile": "scrna_grouped",
                                "organism": {"kind": "synthetic", "tax_id": None},
                                "requested_extras": ["lineage_tree"],
                                "effective_extras": ["groups", "lineage_tree"],
                                "input_files": {},
                                "inputs": {},
                                "base_seed": 100,
                            },
                            "catalog_summary": {
                                "total": 1,
                                "eligible": 1,
                                "warning": 0,
                                "blocked": 0,
                            },
                            "eligible": [],
                            "warning": [],
                            "blocked": [],
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (benchmark_root / "simulation-plan.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "1.0",
                            "id": "gui_generate_test",
                            "profile": "scrna_grouped",
                            "organism": {"kind": "synthetic", "tax_id": None},
                            "requested_extras": ["lineage_tree"],
                            "effective_extras": ["groups", "lineage_tree"],
                            "inputs": {},
                            "runs": [
                                {
                                    "run_id": "dyngen_a",
                                    "simulator_id": "dyngen",
                                    "simulator_params": {},
                                    "replicates": 2,
                                    "native_outputs": ["rna_velocity"],
                                    "base_seed": 100,
                                    "replicate_seeds": [100, 101],
                                }
                            ],
                            "tasks": [
                                {
                                    "task_id": "dyngen_a__r01",
                                    "run_id": "dyngen_a",
                                    "simulator_id": "dyngen",
                                    "replicate_index": 1,
                                    "seed": 100,
                                    "dataset_id": "gui_generate_test__dyngen_a__r01",
                                },
                                {
                                    "task_id": "dyngen_a__r02",
                                    "run_id": "dyngen_a",
                                    "simulator_id": "dyngen",
                                    "replicate_index": 2,
                                    "seed": 101,
                                    "dataset_id": "gui_generate_test__dyngen_a__r02",
                                },
                            ],
                            "execution": {"max_parallel_tasks": 2},
                            "base_seed": 100,
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                (benchmark_root / "benchmark-manifest.json").write_text(
                    '{"schema_version":"1.0","id":"gui_generate_test"}\n',
                    encoding="utf-8",
                )
                (dataset_dir / "dataset-manifest.json").write_text(
                    '{"schema_version":"1.0"}\n', encoding="utf-8"
                )
                (dataset_dir / "ground-truth-manifest.json").write_text(
                    '{"schema_version":"1.0"}\n', encoding="utf-8"
                )
                (dataset_dir / "expression.tsv").write_text(
                    "gene\tC1\nG1\t1\n", encoding="utf-8"
                )
                (dataset_dir / "extras" / "groups.tsv").write_text(
                    "cell\tcluster\nC1\tA\n", encoding="utf-8"
                )
                (dataset_dir / "truth" / "global_network.csv").write_text(
                    "source,target,score,sign,evidence,context\nG1,G2,1,+,simulated_truth,global\n",
                    encoding="utf-8",
                )
                (dataset_dir / "truth" / "legacy" / "global_gs.csv").write_text(
                    ",G1,G2\nG1,0,1\nG2,0,0\n", encoding="utf-8"
                )
                (
                    dataset_dir / "provenance" / "simulator-output-manifest.json"
                ).write_text('{"schema_version":"1.0"}\n', encoding="utf-8")
                (dataset_dir / "provenance" / "simulator-run.json").write_text(
                    '{"schema_version":"1.0"}\n', encoding="utf-8"
                )
                (dataset_dir / "provenance" / "progress.json").write_text(
                    '{"status":"completed","percent":100}\n', encoding="utf-8"
                )
                return benchmark_root

            with (
                patch.object(gui_server, "GUI_TMP_ROOT", tmp_root / "gui_tmp"),
                patch.object(gui_server, "STATE", gui_server.GuiState()),
                patch.object(gui_server.threading, "Thread", _ImmediateThread),
                patch.object(
                    gui_server,
                    "preflight_generate_v2_scenario",
                    side_effect=fake_preflight,
                ),
                patch.object(
                    gui_server,
                    "plan_generate_v2_request",
                    side_effect=fake_plan,
                ),
                patch.object(gui_server, "run_generate_v2", side_effect=fake_run),
            ):
                client = TestClient(gui_server.create_app())

                preflight_response = client.post(
                    "/api/generate-data-v2/preflight",
                    data={
                        "config": json.dumps(
                            {
                                "scenario": {
                                    "id": "gui_generate_test",
                                    "profile": "scrna_grouped",
                                    "requested_extras": ["lineage_tree"],
                                    "organism": {
                                        "kind": "synthetic",
                                        "tax_id": None,
                                    },
                                    "base_seed": 100,
                                },
                                "options": {
                                    "output_dir": str(tmp_root / "benchmarks_v2")
                                },
                            }
                        )
                    },
                )
                self.assertEqual(
                    preflight_response.status_code, 200, msg=preflight_response.text
                )
                job_id = preflight_response.json()["job_id"]

                job_payload = client.get(f"/api/generate-data-v2/jobs/{job_id}").json()
                self.assertEqual(job_payload["job"]["stage"], "preflight_ok")
                self.assertEqual(
                    job_payload["preflight_report"]["catalog_summary"]["eligible"],
                    1,
                )

                plan_response = client.post(
                    "/api/generate-data-v2/plan",
                    json={
                        "job_id": job_id,
                        "runs": [
                            {
                                "run_id": "dyngen_a",
                                "simulator_id": "dyngen",
                                "replicates": 2,
                                "native_outputs": ["rna_velocity"],
                                "params": {},
                            }
                        ],
                        "options": {"max_parallel_tasks": 2},
                    },
                )
                self.assertEqual(plan_response.status_code, 200, msg=plan_response.text)
                plan_payload = client.get(
                    f"/api/generate-data-v2/jobs/{job_id}/plan"
                ).json()
                self.assertEqual(
                    plan_payload["plan"]["execution"]["max_parallel_tasks"], 2
                )
                self.assertEqual(len(plan_payload["plan"]["tasks"]), 2)

                run_response = client.post(
                    "/api/generate-data-v2/run",
                    json={
                        "job_id": job_id,
                        "options": {
                            "max_parallel_tasks": 2,
                            "progress_poll_seconds": 0.1,
                        },
                    },
                )
                self.assertEqual(run_response.status_code, 200, msg=run_response.text)

                job_payload = client.get(f"/api/generate-data-v2/jobs/{job_id}").json()
                self.assertEqual(job_payload["job"]["stage"], "executed")
                self.assertEqual(
                    job_payload["runtime_progress"]["summary"]["completed"], 1
                )
                self.assertTrue(job_payload["reproducibility"]["available"])
                self.assertIn(
                    "/input/scenario-request.json",
                    job_payload["reproducibility"]["cli"]["primary_code"],
                )
                self.assertNotIn(
                    "/gui_tmp/",
                    job_payload["reproducibility"]["cli"]["primary_code"],
                )

                files_response = client.get(
                    f"/api/generate-data-v2/jobs/{job_id}/files?mode=light"
                )
                self.assertEqual(
                    files_response.status_code, 200, msg=files_response.text
                )
                entries = files_response.json()["entries"]
                self.assertTrue(
                    any(
                        item["path"] == "benchmark/benchmark-manifest.json"
                        for item in entries
                    )
                )
                self.assertTrue(
                    any(
                        item["path"] == "benchmark/input/scenario-request.json"
                        for item in entries
                    )
                )

                content_response = client.get(
                    f"/api/generate-data-v2/jobs/{job_id}/file-content",
                    params={
                        "mode": "light",
                        "path": "benchmark/benchmark-manifest.json",
                    },
                )
                self.assertEqual(
                    content_response.status_code, 200, msg=content_response.text
                )
                self.assertEqual(content_response.json()["viewer"], "json")
                self.assertIn("guide", content_response.json())

                bundle_response = client.get(
                    f"/api/generate-data-v2/jobs/{job_id}/bundle?mode=light"
                )
                self.assertEqual(bundle_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
