from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

CLI_MODULE = importlib.import_module("geneci.cli.app")
app = CLI_MODULE.app


class GenerateV2CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_help_shows_generate_v2_subcommands(self) -> None:
        result = self.runner.invoke(app, ["benchmarking", "generate-v2", "--help"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("preflight", result.output)
        self.assertIn("plan", result.output)
        self.assertIn("run", result.output)
        self.assertIn("execute", result.output)

    def test_preflight_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "scenario.json"
            output_json = Path(tmp) / "preflight-report.json"
            scenario_path.write_text("{}", encoding="utf-8")
            with patch.object(
                CLI_MODULE,
                "core_preflight_generate_v2_scenario",
                return_value={
                    "scenario": {
                        "id": "bench",
                        "profile": "scrna_grouped",
                        "requested_extras": ["lineage_tree"],
                        "effective_extras": ["groups", "lineage_tree"],
                        "inputs": {},
                        "input_files": {},
                    },
                    "catalog_summary": {
                        "total": 3,
                        "eligible": 0,
                        "warning": 1,
                        "blocked": 2,
                    },
                    "eligible": [],
                    "warning": [
                        {
                            "simulator_id": "dyngen",
                            "warnings": ["derived extras required: lineage_tree"],
                        }
                    ],
                    "blocked": [],
                },
            ) as mock_fn:
                result = self.runner.invoke(
                    app,
                    [
                        "benchmarking",
                        "generate-v2",
                        "preflight",
                        "--scenario",
                        str(scenario_path),
                        "--output-json",
                        str(output_json),
                    ],
                )
                output_json_exists = output_json.exists()

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        self.assertTrue(output_json_exists)
        self.assertIn("preflight report written", result.output)
        self.assertIn("scenario preflight", result.output)

    def test_plan_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "scenario.json"
            simulator_runs_path = Path(tmp) / "simulator-runs.json"
            output_path = Path(tmp) / "simulation-plan.json"
            scenario_path.write_text("{}", encoding="utf-8")
            simulator_runs_path.write_text(
                '{"schema_version":"1.0","runs":[]}\n', encoding="utf-8"
            )
            with patch.object(
                CLI_MODULE,
                "core_plan_generate_v2_request",
                return_value=output_path,
            ) as mock_fn:
                result = self.runner.invoke(
                    app,
                    [
                        "benchmarking",
                        "generate-v2",
                        "plan",
                        "--scenario",
                        str(scenario_path),
                        "--simulator-runs",
                        str(simulator_runs_path),
                        "--out",
                        str(output_path),
                        "--max-parallel-tasks",
                        "1",
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args.kwargs
        self.assertEqual(kwargs["scenario_request_path"], scenario_path)
        self.assertEqual(kwargs["simulator_runs_path"], simulator_runs_path)
        self.assertEqual(kwargs["output_path"], output_path)
        self.assertEqual(kwargs["max_parallel_tasks"], 1)

    def test_run_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "simulation-plan.json"
            output_dir = Path(tmp) / "out"
            plan_path.write_text("{}", encoding="utf-8")
            with patch.object(
                CLI_MODULE,
                "core_run_generate_v2",
                return_value=output_dir / "bench",
            ) as mock_fn:
                result = self.runner.invoke(
                    app,
                    [
                        "benchmarking",
                        "generate-v2",
                        "run",
                        "--plan",
                        str(plan_path),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args.kwargs
        self.assertEqual(kwargs["plan_path"], plan_path)
        self.assertEqual(kwargs["output_dir"], output_dir)

    def test_execute_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "scenario.json"
            simulator_runs_path = Path(tmp) / "simulator-runs.json"
            output_dir = Path(tmp) / "out"
            scenario_path.write_text("{}", encoding="utf-8")
            simulator_runs_path.write_text("{}", encoding="utf-8")
            with patch.object(
                CLI_MODULE,
                "core_execute_generate_v2",
                return_value=output_dir / "bench",
            ) as mock_fn:
                result = self.runner.invoke(
                    app,
                    [
                        "benchmarking",
                        "generate-v2",
                        "execute",
                        "--scenario",
                        str(scenario_path),
                        "--simulator-runs",
                        str(simulator_runs_path),
                        "--output-dir",
                        str(output_dir),
                        "--max-parallel-tasks",
                        "2",
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args.kwargs
        self.assertEqual(kwargs["scenario_request_path"], scenario_path)
        self.assertEqual(kwargs["simulator_runs_path"], simulator_runs_path)
        self.assertEqual(kwargs["output_dir"], output_dir)
        self.assertEqual(kwargs["max_parallel_tasks"], 2)
