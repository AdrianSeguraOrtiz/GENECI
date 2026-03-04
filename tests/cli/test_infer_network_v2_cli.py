from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

CLI_MODULE = importlib.import_module("geneci.cli.app")
app = CLI_MODULE.app


class InferNetworkV2CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_help_shows_group_subcommands_and_no_plan_only(self) -> None:
        result = self.runner.invoke(app, ["infer-network-v2", "--help"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("plan", result.output)
        self.assertIn("run", result.output)
        self.assertIn("execute", result.output)
        self.assertNotIn("plan-only", result.output)

    def test_plan_subcommand_calls_core_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dataset_manifest = base / "dataset-manifest.json"
            tools_params = base / "tools_params.json"
            output_dir = base / "out"
            dataset_manifest.write_text("{}", encoding="utf-8")
            tools_params.write_text("{}", encoding="utf-8")

            with patch.object(
                CLI_MODULE,
                "core_plan_infer_network_new",
                return_value=output_dir / "run_1",
            ) as plan_mock:
                result = self.runner.invoke(
                    app,
                    [
                        "infer-network-v2",
                        "plan",
                        "--dataset-manifest",
                        str(dataset_manifest),
                        "--tools-params",
                        str(tools_params),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        plan_mock.assert_called_once()

    def test_run_subcommand_calls_core_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_dir"
            run_dir.mkdir(parents=True, exist_ok=True)
            with patch.object(
                CLI_MODULE, "core_run_infer_network_new_plan", return_value=run_dir
            ) as run_mock:
                result = self.runner.invoke(
                    app,
                    [
                        "infer-network-v2",
                        "run",
                        "--run-dir",
                        str(run_dir),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        run_mock.assert_called_once()
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_dir"], run_dir)
        self.assertEqual(kwargs["progress_poll_seconds"], 0.5)
        self.assertFalse(kwargs["strict"])

    def test_execute_subcommand_calls_core_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dataset_manifest = base / "dataset-manifest.json"
            tools_params = base / "tools_params.json"
            output_dir = base / "out"
            dataset_manifest.write_text("{}", encoding="utf-8")
            tools_params.write_text("{}", encoding="utf-8")

            with patch.object(
                CLI_MODULE, "core_infer_network_new", return_value=output_dir / "run_1"
            ) as exec_mock:
                result = self.runner.invoke(
                    app,
                    [
                        "infer-network-v2",
                        "execute",
                        "--dataset-manifest",
                        str(dataset_manifest),
                        "--tools-params",
                        str(tools_params),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        exec_mock.assert_called_once()

    def test_preflight_subcommand_writes_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dataset_manifest = base / "dataset-manifest.json"
            tools_params = base / "tools_params.json"
            output_json = base / "preflight-report.json"
            dataset_manifest.write_text("{}", encoding="utf-8")
            tools_params.write_text("{}", encoding="utf-8")

            fake_report = {
                "catalog": {"eligible": [], "warning": [], "blocked": []},
                "runs": {"selected": [], "skipped": {}},
            }
            with patch.object(
                CLI_MODULE, "core_preflight_infer_network_new", return_value=fake_report
            ) as preflight_mock:
                result = self.runner.invoke(
                    app,
                    [
                        "infer-network-v2",
                        "preflight",
                        "--dataset-manifest",
                        str(dataset_manifest),
                        "--tools-params",
                        str(tools_params),
                        "--output-json",
                        str(output_json),
                    ],
                )

            self.assertEqual(result.exit_code, 0, msg=result.output)
            preflight_mock.assert_called_once()
            self.assertTrue(output_json.exists())

    def test_run_subcommand_returns_exit_1_on_core_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_dir"
            run_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(
                CLI_MODULE,
                "core_run_infer_network_new_plan",
                side_effect=ValueError("synthetic run error"),
            ):
                result = self.runner.invoke(
                    app,
                    ["infer-network-v2", "run", "--run-dir", str(run_dir)],
                )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("synthetic run error", result.output)


if __name__ == "__main__":
    unittest.main()
