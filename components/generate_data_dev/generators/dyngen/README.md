dyngen docker wrapper notes:

- installs `dyngen` from CRAN, pinned to version `1.1.1`
- predownloads dyngen cacheable data files during image build
- executes the public package API via `initialise_model()` and `generate_dataset()`
- supports the GENECI canonical profiles `scrna_global` and `scrna_grouped`
- exposes a broad serializable parameter surface from the public dyngen API:
  - backbone template
  - cell / TF / target / housekeeping counts
  - distance metric
  - TF-network settings
  - feature-network settings
  - gold-standard settings
  - simulation settings
  - experiment sampling settings
- derives `groups.tsv` from `milestone_percentages`
- derives optional `lineage_tree.tsv` from `milestone_network` and aggregated `regulatory_network_sc`
- writes `progress.json`, normalized outputs and raw `.rds` provenance artefacts
