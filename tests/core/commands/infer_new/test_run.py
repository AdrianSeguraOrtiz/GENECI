from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from ._helpers import InferNetworkV2CoreTestCase


class InferNetworkV2RunTests(InferNetworkV2CoreTestCase):
    def _prepare_planned_run(
        self,
        base: Path,
        *,
        tools_params_payload: dict | None = None,
    ) -> Path:
        output_dir = base / "out"
        manifest_path, tools_params_path = self._write_dataset_bundle(
            base,
            tf_values=["G1", "G2"],
        )
        if tools_params_payload is not None:
            tools_params_path.write_text(
                json.dumps(tools_params_payload, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )

        preflight = self.mod.preflight_infer_network_new(
            dataset_manifest_path=manifest_path,
            tools_params_path=tools_params_path,
            strict=False,
        )
        return self.mod.plan_infer_network_new(
            dataset_manifest_path=manifest_path,
            tools_params_path=tools_params_path,
            output_dir=output_dir,
            planner="heuristic",
            strict=False,
            preflight_report=preflight,
        )

    def test_run_plan_executes_from_frozen_dir_and_updates_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run_dir = self._prepare_planned_run(base)

            def fake_run_wave(
                *, wave, runtime_io_by_tool, pulled_images, poll_interval_s, warnings
            ):
                out = {}
                for task in wave.tasks:
                    out[task.tool_id] = self.mod.ToolExecutionResult(
                        tool_id=task.tool_id,
                        status="completed",
                        exit_code=0,
                        duration_seconds=0.5,
                        network_path=str(
                            (
                                run_dir
                                / "tools"
                                / task.tool_id
                                / "io"
                                / "out"
                                / "network.csv"
                            )
                        ),
                        progress_path=None,
                        logs_path=str(
                            (run_dir / "tools" / task.tool_id / "container.log")
                        ),
                        error=None,
                    )
                return out

            def fake_merge(*, run_dir, execution_results, warnings):
                raw = run_dir / "merged_network_raw.csv"
                norm = run_dir / "merged_network_normalized.csv"
                raw.write_text(
                    "source,target,score,sign,evidence,context,tool_id\n",
                    encoding="utf-8",
                )
                norm.write_text(
                    "source,target,score,sign,evidence,context,tool_id\n",
                    encoding="utf-8",
                )
                rows = {
                    tool_id: 1
                    for tool_id, result in execution_results.items()
                    if result.status == "completed"
                }
                return execution_results, rows, raw, norm

            with (
                patch("geneci.core.commands.infer_network_v2.run._ensure_docker_cli"),
                patch(
                    "geneci.core.commands.infer_network_v2.run._run_wave",
                    side_effect=fake_run_wave,
                ),
                patch(
                    "geneci.core.commands.infer_network_v2.run._merge_network_outputs",
                    side_effect=fake_merge,
                ),
            ):
                executed_run_dir = self.mod.run_infer_network_new_plan(
                    run_dir=run_dir,
                    progress_poll_seconds=0.1,
                    strict=False,
                )

            self.assertEqual(executed_run_dir, run_dir)
            report_payload = json.loads(
                (run_dir / "run_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report_payload["status"], "executed")
            self.assertEqual(report_payload["execution"]["tools_completed"], 1)
            self.assertEqual(report_payload["execution"]["tools_failed"], 0)
            self.assertIsNotNone(report_payload["outputs"]["merged_network_raw"])

    def test_run_plan_rejects_input_fingerprint_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run_dir = self._prepare_planned_run(base)

            expression_path = run_dir / "input" / "expression.tsv"
            expression_path.write_text(
                expression_path.read_text(encoding="utf-8") + "#changed\n",
                encoding="utf-8",
            )

            with patch(
                "geneci.core.commands.infer_network_v2.run._ensure_docker_cli"
            ) as ensure_docker:
                with self.assertRaisesRegex(
                    ValueError, "Input file changed since planning"
                ):
                    self.mod.run_infer_network_new_plan(run_dir=run_dir)
            ensure_docker.assert_not_called()

    def test_run_plan_strict_raises_when_partial_failures_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run_dir = self._prepare_planned_run(
                base,
                tools_params_payload={
                    "runs": [
                        {
                            "run_id": "aracne__01",
                            "tool_id": "aracne3",
                            "params": {"seed": 1},
                        },
                        {
                            "run_id": "aracne__02",
                            "tool_id": "aracne3",
                            "params": {"seed": 2},
                        },
                    ]
                },
            )

            def fake_run_wave(
                *, wave, runtime_io_by_tool, pulled_images, poll_interval_s, warnings
            ):
                out = {}
                for task in wave.tasks:
                    if task.tool_id.endswith("__01"):
                        status = "completed"
                        error = None
                        exit_code = 0
                    else:
                        status = "failed"
                        error = "synthetic test failure"
                        exit_code = 1
                    out[task.tool_id] = self.mod.ToolExecutionResult(
                        tool_id=task.tool_id,
                        status=status,
                        exit_code=exit_code,
                        duration_seconds=0.2,
                        network_path=str(
                            (
                                run_dir
                                / "tools"
                                / task.tool_id
                                / "io"
                                / "out"
                                / "network.csv"
                            )
                        ),
                        progress_path=None,
                        logs_path=str(
                            (run_dir / "tools" / task.tool_id / "container.log")
                        ),
                        error=error,
                    )
                return out

            def fake_merge(*, run_dir, execution_results, warnings):
                raw = run_dir / "merged_network_raw.csv"
                norm = run_dir / "merged_network_normalized.csv"
                raw.write_text(
                    "source,target,score,sign,evidence,context,tool_id\n",
                    encoding="utf-8",
                )
                norm.write_text(
                    "source,target,score,sign,evidence,context,tool_id\n",
                    encoding="utf-8",
                )
                rows = {
                    tool_id: 1
                    for tool_id, result in execution_results.items()
                    if result.status == "completed"
                }
                return execution_results, rows, raw, norm

            with (
                patch("geneci.core.commands.infer_network_v2.run._ensure_docker_cli"),
                patch(
                    "geneci.core.commands.infer_network_v2.run._run_wave",
                    side_effect=fake_run_wave,
                ),
                patch(
                    "geneci.core.commands.infer_network_v2.run._merge_network_outputs",
                    side_effect=fake_merge,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "strict mode"):
                    self.mod.run_infer_network_new_plan(
                        run_dir=run_dir,
                        progress_poll_seconds=0.1,
                        strict=True,
                    )
