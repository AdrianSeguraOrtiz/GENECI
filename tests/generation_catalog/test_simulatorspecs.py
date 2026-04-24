from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT / "geneci" / "generation_catalog" / "schemas" / "simulatorspec.schema.json"
)
SIMULATORS_DIR = REPO_ROOT / "geneci" / "generation_catalog" / "simulators"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SimulatorSpecCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.spec_paths = sorted(SIMULATORS_DIR.glob("*/simulatorspec.json"))
        cls.specs = {
            path.parent.name: _load_json(path)
            for path in cls.spec_paths
        }

    def test_catalog_contains_only_completed_dyngen_spec(self) -> None:
        self.assertEqual(set(self.specs), {"dyngen"})

    def test_all_simulator_specs_validate(self) -> None:
        for simulator_id, spec in self.specs.items():
            errors = sorted(
                self.validator.iter_errors(spec),
                key=lambda err: list(err.path),
            )
            self.assertFalse(
                errors,
                msg=f"{simulator_id} spec validation failed: "
                + "; ".join(f"{list(err.path)} -> {err.message}" for err in errors),
            )

    def test_dyngen_spec_uses_full_publication_url_and_full_first_author(self) -> None:
        dyngen = self.specs["dyngen"]
        self.assertEqual(
            dyngen["publication"],
            ["https://doi.org/10.1038/s41467-021-24152-2"],
        )
        self.assertEqual(dyngen["first_author"], "Robrecht Cannoodt")
        self.assertEqual(
            dyngen["docker_image"],
            "adriansegura99/simulator_dyngen:1.0.0",
        )

    def test_dyngen_capabilities_are_single_cell_only(self) -> None:
        dyngen = self.specs["dyngen"]
        self.assertEqual(
            set(dyngen["profile_capabilities"]),
            {"scrna_global", "scrna_grouped"},
        )
        global_capability = dyngen["profile_capabilities"]["scrna_global"]
        grouped = dyngen["profile_capabilities"]["scrna_grouped"]
        self.assertEqual(
            {item["id"] for item in global_capability["native_outputs"]},
            {
                "milestone_network",
                "milestone_percentages",
                "progressions",
                "rna_velocity",
                "regulatory_network_sc",
            },
        )
        self.assertEqual(
            set(grouped["derivable_extras"]),
            {"groups", "lineage_tree", "tf_list"},
        )
        self.assertEqual(grouped["truth_outputs"]["global_network"], "native")
        self.assertEqual(grouped["truth_outputs"]["group_networks"], "derivable")

    def test_dyngen_documents_every_derivation(self) -> None:
        dyngen = self.specs["dyngen"]
        for profile_id, capability in dyngen["profile_capabilities"].items():
            expected = set(capability["derivable_extras"])
            expected.update(
                key
                for key, mode in capability["truth_outputs"].items()
                if mode == "derivable"
            )
            documented = {item["artifact"] for item in capability["derivations"]}
            self.assertEqual(
                documented,
                expected,
                msg=f"{profile_id} derivation documentation mismatch",
            )
            for derivation in capability["derivations"]:
                self.assertTrue(derivation["source_artifacts"])
                self.assertTrue(derivation["method"])
                self.assertTrue(derivation["assumptions"])
                self.assertTrue(derivation["limitations"])

    def test_dyngen_declares_no_external_required_inputs(self) -> None:
        dyngen = self.specs["dyngen"]
        self.assertEqual(dyngen["simulator_inputs"]["required"], [])
        self.assertEqual(dyngen["simulator_inputs"]["optional"], [])

    def test_dyngen_exposes_broad_serializable_parameter_surface(self) -> None:
        dyngen = self.specs["dyngen"]
        for param_name in (
            "backbone_template",
            "num_cells",
            "num_tfs",
            "num_targets",
            "num_hks",
            "distance_metric",
            "tf_network_params",
            "feature_network_params",
            "gold_standard_params",
            "simulation_params",
            "experiment_params",
        ):
            self.assertIn(param_name, dyngen["params"])
        self.assertFalse(
            dyngen["params"]["simulation_params"]["properties"]["compute_dimred"]["default"]
        )
        self.assertFalse(
            dyngen["params"]["experiment_params"]["properties"]["map_reference_cpm"]["default"]
        )


if __name__ == "__main__":
    unittest.main()
