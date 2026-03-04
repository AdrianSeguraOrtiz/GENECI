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
    from geneci.gui.infer_network_v2 import server as gui_server
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
class InferNetworkV2GuiServerTests(unittest.TestCase):
    def test_preflight_plan_run_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            expression_content = "gene\tS1\tS2\nG1\t1\t2\nG2\t3\t4\n"
            run_dir = tmp_root / "planned_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            def fake_preflight(
                *, dataset_manifest_path, tools_params_path, strict
            ):  # noqa: ANN001
                return {
                    "schema_version": "1.0",
                    "catalog": {
                        "eligible": [
                            {
                                "tool_id": "aracne3",
                                "status": "eligible",
                                "reasons": [],
                                "warnings": [],
                            }
                        ],
                        "warning": [],
                        "blocked": [],
                    },
                    "runs": {
                        "requested_total": 0,
                        "selected": [],
                        "catalog_tool_ids": {},
                        "resolved_params": {},
                        "skipped": {},
                    },
                    "warnings": [],
                    "inputs": {
                        "dataset_manifest_path": str(dataset_manifest_path),
                        "tools_params_path": (
                            str(tools_params_path) if tools_params_path else None
                        ),
                    },
                    "dataset": {},
                }

            def fake_plan(**kwargs):  # noqa: ANN003
                plan_payload = {
                    "run_id": "gui_run_001",
                    "waves": [
                        {
                            "index": 1,
                            "threads_used": 1,
                            "ram_gb_used": 1.0,
                            "eta_seconds": 1.0,
                            "tasks": [
                                {
                                    "tool_id": "aracne_run_01",
                                    "image": "dummy/image:latest",
                                    "threads": 1,
                                    "ram_gb": 1.0,
                                    "eta_seconds": 1.0,
                                    "eta_source": "test",
                                    "output_dir": "tools/aracne_run_01",
                                }
                            ],
                        }
                    ],
                    "eta_total_seconds": 1.0,
                    "input_fingerprints": {
                        "input/dataset-manifest.json": {"size_bytes": 10, "sha256": "x"}
                    },
                }
                (run_dir / "plan.json").write_text(
                    json.dumps(plan_payload, indent=2, ensure_ascii=True) + "\n",
                    encoding="utf-8",
                )
                (run_dir / "run_report.json").write_text(
                    json.dumps(
                        {
                            "run_id": "gui_run_001",
                            "status": "planned",
                            "execution": {
                                "planner_used": "heuristic",
                                "waves_total": 1,
                                "tools_selected": 1,
                                "tools_completed": 0,
                                "tools_failed": 0,
                                "elapsed_seconds": 0.0,
                            },
                            "warnings": [],
                            "outputs": {
                                "merged_network_raw": None,
                                "merged_network_normalized": None,
                                "rows_per_tool": {},
                            },
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return run_dir

            def fake_run(*, run_dir, progress_poll_seconds, strict):  # noqa: ANN001
                report_path = Path(run_dir) / "run_report.json"
                payload = json.loads(report_path.read_text(encoding="utf-8"))
                payload["status"] = "executed"
                payload["execution"]["tools_completed"] = 1
                payload["execution"]["elapsed_seconds"] = 0.7
                report_path.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
                    encoding="utf-8",
                )
                return Path(run_dir)

            with (
                patch.object(gui_server, "GUI_TMP_ROOT", tmp_root / "gui_tmp"),
                patch.object(gui_server.threading, "Thread", _ImmediateThread),
                patch.object(
                    gui_server,
                    "preflight_infer_network_new",
                    side_effect=fake_preflight,
                ),
                patch.object(
                    gui_server, "plan_infer_network_new", side_effect=fake_plan
                ),
                patch.object(
                    gui_server, "run_infer_network_new_plan", side_effect=fake_run
                ),
            ):
                client = TestClient(gui_server.create_app())

                preflight_response = client.post(
                    "/api/infer-network-v2/preflight",
                    data={
                        "config": json.dumps(
                            {
                                "dataset": {
                                    "id": "gui_dataset",
                                    "column_kind": "samples",
                                    "expression_profile": "mixed",
                                },
                                "options": {"output_dir": str(tmp_root / "out")},
                            }
                        )
                    },
                    files={
                        "expression_file": (
                            "expression.tsv",
                            expression_content,
                            "text/tab-separated-values",
                        ),
                    },
                )
                self.assertEqual(
                    preflight_response.status_code, 200, msg=preflight_response.text
                )
                job_id = preflight_response.json()["job_id"]

                job_payload = client.get(f"/api/infer-network-v2/jobs/{job_id}").json()
                self.assertEqual(job_payload["job"]["status"], "completed")
                self.assertEqual(job_payload["job"]["stage"], "preflight_ok")

                plan_response = client.post(
                    "/api/infer-network-v2/plan",
                    json={
                        "job_id": job_id,
                        "runs": [
                            {
                                "run_id": "aracne_run_01",
                                "tool_id": "aracne3",
                                "params": {},
                            }
                        ],
                        "options": {"planner": "heuristic"},
                    },
                )
                self.assertEqual(plan_response.status_code, 200, msg=plan_response.text)

                job_payload = client.get(f"/api/infer-network-v2/jobs/{job_id}").json()
                self.assertEqual(job_payload["job"]["stage"], "planned")
                self.assertTrue(job_payload["job"]["plan_path"])

                plan_payload = client.get(
                    f"/api/infer-network-v2/jobs/{job_id}/plan"
                ).json()
                self.assertIn("plan", plan_payload)
                self.assertIsNotNone(plan_payload["plan"])

                run_response = client.post(
                    "/api/infer-network-v2/run",
                    json={"job_id": job_id, "options": {"progress_poll_seconds": 0.1}},
                )
                self.assertEqual(run_response.status_code, 200, msg=run_response.text)

                job_payload = client.get(f"/api/infer-network-v2/jobs/{job_id}").json()
                self.assertEqual(job_payload["job"]["stage"], "executed")
                self.assertEqual(job_payload["run_report"]["status"], "executed")
                self.assertEqual(
                    job_payload["run_report"]["execution"]["tools_completed"], 1
                )

                files_response = client.get(
                    f"/api/infer-network-v2/jobs/{job_id}/files?mode=light"
                )
                self.assertEqual(
                    files_response.status_code, 200, msg=files_response.text
                )
                entries = files_response.json()["entries"]
                self.assertTrue(
                    any(item["path"] == "run/plan.json" for item in entries)
                )

                file_content = client.get(
                    f"/api/infer-network-v2/jobs/{job_id}/file-content",
                    params={"mode": "light", "path": "run/run_report.json"},
                )
                self.assertEqual(file_content.status_code, 200, msg=file_content.text)
                self.assertEqual(file_content.json()["viewer"], "json")

                file_missing = client.get(
                    f"/api/infer-network-v2/jobs/{job_id}/file-content",
                    params={"mode": "light", "path": "run/missing_file.txt"},
                )
                self.assertEqual(file_missing.status_code, 404)

    def test_run_endpoint_requires_planned_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            expression_content = "gene\tS1\tS2\nG1\t1\t2\nG2\t3\t4\n"

            def fake_preflight(
                *, dataset_manifest_path, tools_params_path, strict
            ):  # noqa: ANN001
                return {
                    "schema_version": "1.0",
                    "catalog": {"eligible": [], "warning": [], "blocked": []},
                    "runs": {
                        "requested_total": 0,
                        "selected": [],
                        "catalog_tool_ids": {},
                        "resolved_params": {},
                        "skipped": {},
                    },
                    "warnings": [],
                    "inputs": {
                        "dataset_manifest_path": str(dataset_manifest_path),
                        "tools_params_path": (
                            str(tools_params_path) if tools_params_path else None
                        ),
                    },
                    "dataset": {},
                }

            with (
                patch.object(gui_server, "GUI_TMP_ROOT", tmp_root / "gui_tmp"),
                patch.object(gui_server.threading, "Thread", _ImmediateThread),
                patch.object(
                    gui_server,
                    "preflight_infer_network_new",
                    side_effect=fake_preflight,
                ),
            ):
                client = TestClient(gui_server.create_app())

                preflight_response = client.post(
                    "/api/infer-network-v2/preflight",
                    data={
                        "config": json.dumps(
                            {
                                "dataset": {
                                    "id": "gui_dataset",
                                    "column_kind": "samples",
                                    "expression_profile": "mixed",
                                },
                                "options": {"output_dir": str(tmp_root / "out")},
                            }
                        )
                    },
                    files={
                        "expression_file": (
                            "expression.tsv",
                            expression_content,
                            "text/tab-separated-values",
                        ),
                    },
                )
                self.assertEqual(
                    preflight_response.status_code, 200, msg=preflight_response.text
                )
                job_id = preflight_response.json()["job_id"]

                run_response = client.post(
                    "/api/infer-network-v2/run",
                    json={"job_id": job_id, "options": {"progress_poll_seconds": 0.1}},
                )
                self.assertEqual(run_response.status_code, 400)
                self.assertIn("No planned run found", run_response.text)


if __name__ == "__main__":
    unittest.main()
