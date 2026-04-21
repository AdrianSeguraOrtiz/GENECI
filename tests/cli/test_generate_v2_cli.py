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
        self.assertIn("catalog", result.output)
        self.assertIn("preflight", result.output)
        self.assertIn("plan", result.output)
        self.assertIn("validate-request", result.output)
        self.assertIn("run", result.output)

    def test_catalog_list_calls_core(self) -> None:
        with patch.object(
            CLI_MODULE,
            "core_generate_v2_catalog_list",
            return_value=[{"id": "dyngen", "name": "dyngen", "supports_profiles": ["scrna_global"]}],
        ) as mock_fn:
            result = self.runner.invoke(app, ["benchmarking", "generate-v2", "catalog", "list"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        self.assertIn("dyngen", result.output)

    def test_preflight_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "scenario.json"
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
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        self.assertIn("scenario preflight", result.output)

    def test_plan_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario_path = Path(tmp) / "scenario.json"
            output_path = Path(tmp) / "benchmark-request.json"
            params_path = Path(tmp) / "params.json"
            scenario_path.write_text("{}", encoding="utf-8")
            params_path.write_text('{"num_cells": 25}\n', encoding="utf-8")
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
                        "--simulator-id",
                        "dyngen",
                        "--params",
                        str(params_path),
                        "--out",
                        str(output_path),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args.kwargs
        self.assertEqual(kwargs["scenario_request_path"], scenario_path)
        self.assertEqual(kwargs["simulator_id"], "dyngen")
        self.assertEqual(kwargs["simulator_params"], {"num_cells": 25})
        self.assertEqual(kwargs["output_path"], output_path)

    def test_validate_request_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.json"
            request_path.write_text("{}", encoding="utf-8")
            with patch.object(
                CLI_MODULE,
                "core_validate_generate_v2_request",
                return_value={
                    "request_id": "bench",
                    "profile": "scrna_grouped",
                    "simulator_id": "dyngen",
                    "replicates": 1,
                    "requested_extras": [],
                    "effective_extras": [],
                    "input_files": {},
                    "replicate_seeds": [1],
                },
            ) as mock_fn:
                result = self.runner.invoke(
                    app,
                    [
                        "benchmarking",
                        "generate-v2",
                        "validate-request",
                        "--request",
                        str(request_path),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        self.assertIn("generate-v2 request is valid", result.output)

    def test_run_calls_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.json"
            output_dir = Path(tmp) / "out"
            request_path.write_text("{}", encoding="utf-8")
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
                        "--request",
                        str(request_path),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args.kwargs
        self.assertEqual(kwargs["request_path"], request_path)
        self.assertEqual(kwargs["output_dir"], output_dir)
