# Simulator Integration Playbook

This playbook defines the recommended workflow for integrating a benchmark data simulator into `generate-v2`.

Use it when you have local evidence under:

```text
components/generate_data/<SimulatorName>/
  repo/
  papers/
```

`repo/`, `papers/` and locally downloaded HTML/PDF documentation are evidence sources for analysis only. They must not become runtime dependencies.

Runtime behavior must be reproducible from:
- `geneci/generation_catalog/simulators/<simulator_id>/simulatorspec.json`
- the wrapper under `components/generate_data_dev/generators/<simulator_id>/`
- the `Dockerfile` under `components/generate_data_dev/generators/<simulator_id>/`

The catalog must contain only simulators that are fully integrated, dockerized and smoketested. Do not add placeholder specs for simulators that are still under review.

## Scope

The goal of an integration is to produce:
- a coherent `simulatorspec.json`
- a wrapper that maps upstream simulator behavior to the GENECI output contract
- a `Dockerfile` that installs the simulator from a stable public source
- a smoke-test matrix covering every declared profile and extra combination
- an `integration_decisions.md` file documenting evidence and tradeoffs
- a `progress.json` implementation for observable execution state

The goal is not to reproduce a local vertical slice, bundled example export or copied repo execution. The wrapper must execute the public simulator installation declared by the integration.

## Source-Of-Truth Rules

1. Prefer the upstream implementation and paper over assumptions.
2. Keep `simulatorspec.json` aligned with the real upstream interface and the implemented wrapper.
3. The catalog is executable truth: if a simulator is listed, GENECI must be able to run it through Docker.
4. Do not depend on local `components/generate_data/<SimulatorName>/repo/` at runtime.
5. Installation preference:
   - official package manager / library first
   - upstream public repo pinned to tag/commit if no package exists
   - never depend on unpinned floating source if avoidable
6. Docker image names must follow:

```text
adriansegura99/simulator_<simulator_id>:1.0.0
```

7. `publication` must be a list. Store DOI references as full canonical URLs such as `https://doi.org/...`.
8. `first_author` must be the full first-author name from the primary publication, not only surname.
9. Expose the full public parameter surface that is serializable and supportable through JSON. Function-valued callbacks may be represented by explicit presets, but should not be faked as arbitrary JSON parameters.
10. Every supported profile/extra combination must be covered by tests.

## Canonical Concepts

### Canonical Profiles

`generate-v2` currently recognizes these data profiles:
- `bulk_steady_state`
- `bulk_time_series`
- `bulk_perturbational`
- `scrna_global`
- `scrna_grouped`

Do not create a new canonical profile just because one inference tool has special input needs. Use extras for additional files.

### Extras

Supported extras currently include:
- `groups`
- `lineage_tree`
- `tf_list`
- `prior_grn_by_group`

Extras describe optional generated artifacts that can accompany a canonical profile. For example, `scMTNI` should be viewed as consuming `scrna_grouped` plus extras, not as defining a new simulator profile.

### Truth Outputs

Truth output modes are:
- `none`
- `native`
- `derivable`

Use these modes for:
- `global_network`
- `legacy_binary_matrix`
- `group_networks`

Be explicit about whether a truth output comes directly from the simulator or is derived by the wrapper from simulator-native state.

## Official End-To-End Procedure

Follow these steps in order. A simulator is not considered integrated until the Docker image and smoke-test matrix pass.

### Step 0. Choose `<simulator_id>` And Target Scope

Manual action:
- choose a stable lowercase id using letters, digits and `_`
- confirm the canonical upstream project name and implementation URL
- decide which public package, repo tag or commit will be installed
- decide which upstream public API/CLI entrypoint the wrapper mirrors
- list which canonical profiles are realistically supported
- list which extras are native or derivable

This id will be reused in:
- simulator spec: `geneci/generation_catalog/simulators/<simulator_id>/simulatorspec.json`
- wrapper dir: `components/generate_data_dev/generators/<simulator_id>/`
- smoke configs: `components/generate_data_dev/tests/smoketest_configs/<simulator_id>*.json`
- Docker image: `adriansegura99/simulator_<simulator_id>:1.0.0`

### Step 1. Place And Prepare Upstream Evidence

Manual action:
- clone or copy the upstream implementation into:

```text
components/generate_data/<SimulatorName>/repo/
```

- copy one or more local papers into:

```text
components/generate_data/<SimulatorName>/papers/
```

- convert PDFs to text if needed, keeping both PDF and `.txt` files as evidence.
- collect public docs such as CRAN pages, vignettes or HTML manuals when useful.

Minimum evidence expected in `repo/`:
- README or package docs
- examples/vignettes
- config files or CLI help
- relevant exported functions/scripts
- output examples if available

Minimum evidence expected in `papers/`:
- primary simulator paper
- implementation/package paper if different
- any additional paper needed to justify lineage, perturbation, multi-omics or ground-truth semantics

### Step 2. Execute Phase 1: Evidence And Contract

Goal:
- produce/update `integration_decisions.md`
- draft `simulatorspec.json`
- decide the public installation route
- decide the wrapper entrypoint and output mapping
- decide the smoke-test matrix

Prompt to paste in chat:

```text
Please integrate the simulator `<simulator_id>` following [SIMULATOR_INTEGRATION_PLAYBOOK.md](components/generate_data_dev/SIMULATOR_INTEGRATION_PLAYBOOK.md), but only execute Phase 1 for now.

Context:
- Upstream repo is under [repo/](components/generate_data/<SimulatorName>/repo/)
- Local papers are under [papers/](components/generate_data/<SimulatorName>/papers/)
- Optional docs are under [components/generate_data/<SimulatorName>/](components/generate_data/<SimulatorName>/)
- The SimulatorSpec target is [simulatorspec.json](geneci/generation_catalog/simulators/<simulator_id>/simulatorspec.json)
- The wrapper target directory is [components/generate_data_dev/generators/<simulator_id>/](components/generate_data_dev/generators/<simulator_id>/)
- Optional manual clarifications from the integrator:
  - preferred installation route: `<optional>`
  - preferred version/tag/commit: `<optional>`
  - target function/CLI/API entrypoint: `<optional>`
  - profiles/extras that must be prioritized: `<optional>`

Requirements:
- Review the upstream repo, local paper text/PDFs and available docs
- Produce or update [integration_decisions.md](components/generate_data_dev/generators/<simulator_id>/integration_decisions.md)
- Draft [simulatorspec.json](geneci/generation_catalog/simulators/<simulator_id>/simulatorspec.json)
- Do not implement the wrapper yet
- Store publication references as a list of full canonical URLs
- Store `first_author` as the full first-author name
- Set `docker_image` to `adriansegura99/simulator_<simulator_id>:1.0.0`
- Identify every canonical profile the simulator can support
- Identify every extra that is native or derivable
- Identify required, optional and conditional simulator input files
- Identify the full public serializable parameter surface
- Explicitly document parameters that are intentionally represented as presets because upstream expects function-valued callbacks
- Document any capability that exists scientifically but will not be claimed because the wrapper cannot support it yet
- For every non-trivial `simulatorspec.json` field, record:
  - chosen value
  - evidence path(s)
  - rationale
  - uncertainty if any
- Do not add placeholder specs for other simulators

Focus especially on:
1. canonical profile support
2. optional and conditional input files
3. extras and truth-output derivation
4. parameter mapping and defaults
5. output normalization into `expression.tsv`, `extras/`, `truth/` and provenance
6. public installation source and version pinning
7. smoke-test matrix needed to cover the declared contract
```

### Step 3. Review Phase 1

Manual action:
- inspect `integration_decisions.md`
- inspect `simulatorspec.json`
- confirm that the catalog only claims what the wrapper will actually implement
- confirm that the selected installation route is public and reproducible
- confirm that no local repo path is part of runtime behavior

Do not continue to Phase 2 until the contract looks correct.

### Step 4. Execute Phase 2: Wrapper And Docker Implementation

Goal:
- implement the wrapper
- implement the Dockerfile
- keep `simulatorspec.json` aligned with actual behavior
- add smoke-test configs covering all declared profiles/extras
- make the wrapper produce `progress.json`

Prompt to paste in chat:

```text
Please continue the integration of `<simulator_id>` following [SIMULATOR_INTEGRATION_PLAYBOOK.md](components/generate_data_dev/SIMULATOR_INTEGRATION_PLAYBOOK.md), executing Phase 2.

Requirements:
- Use [integration_decisions.md](components/generate_data_dev/generators/<simulator_id>/integration_decisions.md) as the working contract
- Implement the wrapper under [components/generate_data_dev/generators/<simulator_id>/](components/generate_data_dev/generators/<simulator_id>/)
- Implement [Dockerfile](components/generate_data_dev/generators/<simulator_id>/Dockerfile)
- Do not depend on local [repo/](components/generate_data/<SimulatorName>/repo/) at runtime
- Install the simulator from an official package when possible, otherwise from a pinned upstream tag/commit
- The container must read `/work/request/simulator-run-request.json`
- The container must write the normalized output tree directly under `/work/out/`
- The wrapper must execute the public simulator package/API/CLI, not a GENECI-side reimplementation
- The wrapper must write `progress.json`
- Preserve raw upstream outputs, config snapshots, logs and session info under `provenance/raw/`
- Produce:
  - `expression.tsv`
  - `truth/global_network.csv`
  - `truth/legacy/global_gs.csv`
  - optional `extras/`
  - `simulator-output-manifest.json`
- Add smoke-test configs under [components/generate_data_dev/tests/smoketest_configs/](components/generate_data_dev/tests/smoketest_configs/)
- The smoke-test matrix must cover every declared profile and every declared extra path
- Build the image and run the smoke tests during this phase
- If implementation constraints require changing the spec, update `simulatorspec.json` and document why in `integration_decisions.md`
```

### Step 5. Execute Phase 3: Verification And Final Alignment

Goal:
- validate schemas
- run smoke tests again
- run `generate-v2` compatibility tests
- leave the decision log complete and concise

Prompt to paste in chat:

```text
Please finish the integration of `<simulator_id>` following [SIMULATOR_INTEGRATION_PLAYBOOK.md](components/generate_data_dev/SIMULATOR_INTEGRATION_PLAYBOOK.md), executing Phase 3.

Requirements:
- Validate [simulatorspec.json](geneci/generation_catalog/simulators/<simulator_id>/simulatorspec.json)
- Run the simulator smoke-test matrix
- Run the relevant `generate-v2` tests
- Confirm generated `dataset-manifest.json` files pass `infer-network-v2 preflight`
- Fix any mismatch between wrapper behavior, `simulatorspec.json`, smoke configs and output schemas
- Leave [integration_decisions.md](components/generate_data_dev/generators/<simulator_id>/integration_decisions.md) complete and concise
```

### Step 6. Build, Verify And Optionally Publish The Image

Validate the catalog and smoke-test config first:

```bash
make validate-simulatorspecs ARGS="--simulator <simulator_id>"
make validate-simulator-smoketest-configs ARGS="--simulator <simulator_id>"
```

Build or rebuild the simulator image:

```bash
make build-simulator-images ARGS="--simulator <simulator_id>"
```

Run the smoke-test matrix:

```bash
make run-simulator-smoketests ARGS="--simulator <simulator_id> --skip-build"
```

Or run the complete per-simulator verification:

```bash
make verify-simulator SIMULATOR=<simulator_id>
```

If image publication is part of the task, push:

```bash
make push-simulator-images ARGS="--simulator <simulator_id>"
```

If another machine or CI needs the image explicitly:

```bash
make pull-simulator-images ARGS="--simulator <simulator_id>"
```

## Runtime Contract

### Container Input

The core mounts:

```text
/work/request/simulator-run-request.json
/work/inputs/
/work/out/
```

The input request has this shape:

```json
{
  "schema_version": "1.0",
  "simulator_id": "<simulator_id>",
  "profile": "scrna_grouped",
  "seed": 1,
  "effective_extras": ["groups", "tf_list"],
  "input_files": {},
  "params": {},
  "output_dir_in_container": "/work/out"
}
```

Rules:
- `effective_extras` includes profile-required extras plus user-requested extras.
- `input_files` maps simulator input ids to read-only paths under `/work/inputs/`.
- `params` contains values already schema-validated by `generate-v2`.
- The wrapper should still validate assumptions that depend on simulator internals.
- Exit nonzero on failure.

### Container Output

The wrapper must write under `/work/out/`:

```text
expression.tsv
extras/
truth/
  global_network.csv
  legacy/
    global_gs.csv
provenance/
  raw/
simulator-output-manifest.json
progress.json
```

Optional files:

```text
extras/groups.tsv
extras/lineage_tree.tsv
extras/tf_list.txt
extras/prior_grn_by_group.tsv
truth/group_networks/<group>.csv
```

The core validates only the normalized contract. It must not parse simulator-native files directly.

### Progress

Every wrapper should emit `progress.json` with at least:

```json
{
  "schema_version": "1.0",
  "status": "running",
  "step": "run_simulator",
  "updated_at": "2026-04-21 12:00:00 UTC",
  "message": "Running upstream simulator."
}
```

Recommended steps:
- `validate_request`
- `prepare_run`
- `run_simulator`
- `derive_extras`
- `derive_truth`
- `write_manifest`
- `done`
- `failed`

On failure, write `status = "failed"` when possible before exiting nonzero.

## SimulatorSpec Field Evidence Guide

When drafting `simulatorspec.json`, use this field-by-field evidence policy.

### Fixed By Project Contract

- `schema_version`
  - value: `1.0`
  - evidence: `geneci/generation_catalog/schemas/simulatorspec.schema.json`
- `id`
  - value: `<simulator_id>`
  - evidence: folder name under `geneci/generation_catalog/simulators/`
- `docker_image`
  - value: `adriansegura99/simulator_<simulator_id>:1.0.0`
  - evidence: GENECI naming convention
  - record the decision in `integration_decisions.md`

### Identity And Provenance

- `name`
  - look in:
    - paper title
    - package docs
    - repo README
  - use official spelling and capitalization
- `publication`
  - look in:
    - primary paper
    - package citation
    - repo citation section
  - store as list
  - primary simulator paper first
  - DOI references must be full URLs
- `first_author`
  - use full name from the primary paper
- `year`
  - publication year of `publication[0]`
- `simulation_summary`
  - summarize the simulator model, not the wrapper
- `simulation_keywords`
  - use reusable lower_snake_case terms, for example:
    - `single_cell`
    - `trajectory`
    - `bulk`
    - `perturbation`
    - `dynamic_grn`
- `implementation_url`
  - canonical public source matching what the Dockerfile installs

### Simulator Inputs

- `simulator_inputs.required`
- `simulator_inputs.optional`
- `simulator_inputs.conditional_required`

Look in:
- function signatures
- CLI docs
- config examples
- README examples
- paper methods
- code paths that fail when files are missing

Rules:
- if the simulator can run from built-in templates, do not declare unnecessary required inputs
- if a file is needed only for specific params or extras, model it in `conditional_required`
- describe formats explicitly
- do not confuse generated extras with simulator-side inputs

Examples:
- custom regulatory network input
- differentiation tree
- perturbation design
- kinetic parameter file
- real expression reference file

### Profile Capabilities

For each canonical profile, determine:
- whether the simulator can generate the expression profile
- which extras are native
- which extras are derivable
- which truth outputs are native or derivable

Evidence sources:
- paper simulation scenarios
- repo examples/vignettes
- package function docs
- upstream output structures

Rules:
- decide from simulator semantics, not only matrix shape
- `scrna_grouped` requires expression plus a defensible group assignment
- `bulk_time_series` requires temporal semantics, not just ordered samples
- `bulk_perturbational` requires perturbation/intervention semantics
- do not claim `lineage_tree` unless the simulator has trajectory/tree/state-transition information or the wrapper can derive it defensibly
- do not claim `prior_grn_by_group` unless there is a defensible modality or simulator state from which to derive it

### Truth Outputs

For each profile, set:
- `global_network`
- `legacy_binary_matrix`
- `group_networks`

Rules:
- `native`: directly available from simulator internals or declared inputs
- `derivable`: computed by wrapper from simulator-native state
- `none`: unavailable or not defensible

Document:
- edge direction convention
- edge sign convention
- score meaning
- thresholding rule, if any
- whether group truth is public output or only provenance

### Parameters

Expose the full public parameter surface that is serializable and testable.

Look in:
- package function signatures
- man pages / CRAN docs
- README examples
- vignettes
- code defaults

Rules:
- prefer upstream parameter names unless GENECI has a strong reason to normalize
- preserve upstream defaults when they are stable
- if a default is data-dependent, document the exact rule
- use nested `object` params to mirror upstream grouped params
- expose function-valued hooks only as explicit presets when practical
- do not include arbitrary code strings as parameters
- every declared parameter must be accepted by the wrapper

### Auxiliary Artifacts

Use `artifacts_aux` for non-public but useful native outputs:
- raw simulator model objects
- milestone/cell-state metadata
- reaction logs
- velocity matrices
- cell-specific GRNs
- upstream config snapshots
- session info

These artifacts usually belong in `provenance/raw/`, not as first-class benchmark outputs.

## Output Mapping Rules

### `expression.tsv`

Use tab-separated format:

```text
gene	cell_1	cell_2	...
G1	0	3	...
```

Rules:
- first column is gene id
- remaining columns are samples/cells/timepoints/perturbations
- column semantics must match the selected canonical profile
- preserve simulator count/abundance scale unless a documented upstream export requires transformation

### `groups.tsv`

Use:

```text
cell	cluster
cell_1	group_a
cell_2	group_b
```

Rules:
- exactly one group assignment per expression column
- `cell` values must match expression column names
- group labels should be stable and human-readable

### `lineage_tree.tsv`

Use:

```text
child	parent	gain_rate	loss_rate
group_b	group_a	0.1	0.2
```

Rules:
- `child` and `parent` must exist in `groups.tsv`
- root groups have no row
- `gain_rate` and `loss_rate` must be in `[0, 1]`
- document how rates are derived

### `tf_list.txt`

Use one TF id per line.

Rules:
- ids must be a subset of expression genes
- if the simulator does not distinguish TFs natively, document the derivation rule

### `prior_grn_by_group.tsv`

Use:

```text
group	source	target	score
group_a	TF1	G2	0.7
```

Rules:
- `group` must exist in `groups.tsv`
- `source` and `target` must be expression genes
- `score` should be in `[0, 1]`
- document whether the prior is modality-grounded, truth-derived, or heuristic
- avoid deriving a prior directly from clean truth unless the benchmark explicitly intends that

### `truth/global_network.csv`

Use:

```text
source,target,score,sign,evidence,context
TF1,G2,1,+,simulated_truth,global
```

Rules:
- do not include self-loops unless upstream semantics require them
- omit exact zero-score edges
- preserve direction if the simulator has directed regulatory semantics
- `context = global`

### `truth/group_networks/<group>.csv`

Same columns as global truth.

Rules:
- `context = group:<group_label>`
- every file must correspond to a group in `groups.tsv`
- include in `ground-truth-manifest.json` as `{group, path}`

### `truth/legacy/global_gs.csv`

Legacy binary adjacency matrix for existing evaluation compatibility.

Rules:
- derive from `truth/global_network.csv`
- include all genes present in expression where practical
- use `1` for present edge and `0` otherwise

## Smoke-Test Requirements

Every completed simulator must have one or more configs under:

```text
components/generate_data_dev/tests/smoketest_configs/<simulator_id>*.json
```

The matrix must cover:
- every declared canonical profile
- every declared extra at least once
- representative parameter groups
- conditional-input behavior when supported
- the presence of `progress.json`
- required public output files
- important provenance files

For `dyngen`, this currently means:
- `scrna_global`
- `scrna_global + tf_list`
- `scrna_grouped + groups`
- `scrna_grouped + groups + lineage_tree + tf_list`
- `scrna_grouped + groups + tf_list + RNA velocity parameter path`

Run:

```bash
make verify-simulator SIMULATOR=<simulator_id>
```

## Required Structure Of `integration_decisions.md`

The decision log must include:
- upstream evidence reviewed
- selected installation route and version/tag/commit
- selected public API/CLI entrypoint
- supported profiles and why
- unsupported profiles and why
- native and derivable extras
- simulator-side input files
- parameter mapping and unsupported function-valued hooks
- output mapping
- progress strategy
- smoke-test matrix and outcome

For every non-trivial decision, record:
- chosen value
- evidence path(s)
- rationale
- uncertainty if any

If a value is unclear:
- say that it is unclear
- list conflicting evidence
- explain the chosen temporary resolution

## Quick Command Summary

From repository root:

```bash
make validate-generation-catalog
make validate-simulatorspecs ARGS="--simulator <simulator_id>"
make validate-simulator-smoketest-configs ARGS="--simulator <simulator_id>"
make build-simulator-images ARGS="--simulator <simulator_id>"
make run-simulator-smoketests ARGS="--simulator <simulator_id> --skip-build"
make verify-simulator SIMULATOR=<simulator_id>
make list-simulator-images
make scaffold-simulator SIMULATOR=<simulator_id> WRAPPER=python
make prepare-simulator-papers SIMULATOR=<simulator_id>
python -m pytest tests/generation_catalog/test_simulatorspecs.py -q
python -m pytest tests/core/commands/generate_v2/test_generate_v2.py -q
```

For R wrappers:

```bash
Rscript -e "invisible(parse(file='components/generate_data_dev/generators/<simulator_id>/run_simulator.R'))"
```

## Review Checklist

Before considering a simulator integrated, confirm:
- local paper text/PDFs and repo/docs were reviewed
- `simulatorspec.json` validates
- `publication` is a list of full URLs
- `first_author` is a full name
- `docker_image` follows `adriansegura99/simulator_<simulator_id>:1.0.0`
- the Dockerfile installs from a stable public source
- runtime does not depend on the local evidence repo
- every declared profile is covered by smoke tests
- every declared extra is covered by smoke tests
- every declared parameter is accepted by the wrapper
- `progress.json` is written
- `simulator-output-manifest.json` validates
- generated `dataset-manifest.json` passes `infer-network-v2 preflight`
- truth outputs and legacy matrix are consistent
- provenance contains enough raw simulator state to debug or audit the run
- no incomplete simulator appears in `geneci/generation_catalog/simulators/`
