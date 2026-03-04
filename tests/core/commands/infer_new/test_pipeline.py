from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ._helpers import InferNetworkV2CoreTestCase


class InferNetworkV2PipelineTests(InferNetworkV2CoreTestCase):
    def test_execute_wrapper_calls_preflight_plan_and_run(self) -> None:
        with (
            patch(
                "geneci.core.commands.infer_network_v2.pipeline.preflight_infer_network_new",
                return_value={"runs": {"selected": []}},
            ) as preflight_mock,
            patch(
                "geneci.core.commands.infer_network_v2.pipeline.plan_infer_network_new",
                return_value=Path("/tmp/fake_run_dir"),
            ) as plan_mock,
            patch(
                "geneci.core.commands.infer_network_v2.pipeline.run_infer_network_new_plan",
                return_value=Path("/tmp/fake_run_dir"),
            ) as run_mock,
        ):
            out = self.mod.infer_network_new(
                dataset_manifest_path=Path("/tmp/dataset-manifest.json"),
                tools_params_path=Path("/tmp/tools_params.json"),
            )

        self.assertEqual(out, Path("/tmp/fake_run_dir"))
        preflight_mock.assert_called_once()
        plan_mock.assert_called_once()
        run_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
