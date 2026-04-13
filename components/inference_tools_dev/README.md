# inference_tools_dev (dev tooling)

Development and maintenance tooling for the packaged inference catalog in `geneci/inference_catalog/`.

Use this area for:
- validating ToolSpecs
- validating smoketest configs
- validating tool `cost.json` profiles
- building tool Docker images
- pushing/pulling tool Docker images
- running smoketests
- benchmarking and updating `cost` profiles
- cloning upstream implementation repositories for local inspection
- fetching local publication caches from `toolspec.publication`
- keeping dev-only parameter overrides derived from ToolSpec defaults
- keeping shared fixtures and smoketest-only configs

Runtime catalog assets consumed by `infer_network_v2` live in `geneci/inference_catalog/`.
Tool build sources live in `components/inference_tools_dev/tools/`.
Dev-only parameter overrides live in `components/inference_tools_dev/param_overrides/`.

## Layout

```text
components/inference_tools_dev/
  param_overrides/
    <tool_id>.json       # optional, merged onto ToolSpec defaults for smoketests/benchmarks
  tools/
    <tool_id>/
      Dockerfile
      run_tool.py | run_tool.R
      repo/                # optional local clone of toolspec.implementation_url
      papers/              # optional local publication cache derived from toolspec.publication
  scripts/
    shared/
    scaffold_tool.py
    prepare_tool_papers.py
    validate_toolspecs.py
    validate_input_specs.py
    validate_smoketest_configs.py
    validate_tool_costs.py
    build_tool_images.py
    sync_tool_images.py
    run_smoketests.py
    benchmark_costs.py
    sync_tool_repos.py
    sync_tool_publications.py
    template_map.json
    templates/
  TOOL_INTEGRATION_PLAYBOOK.md
  tests/
    fixtures/
    schemas/
      smoketest.config.schema.json
    smoketest_configs/
      <tool_id>.json
```

```text
geneci/inference_catalog/
  schemas/
  tools/
    <tool_id>/
      toolspec.json
      cost.json           # optional
```

## Smoketest config location

Per-tool smoketest behavior is configured in:
- `components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json`
- Optional schema for those configs:
  - `components/inference_tools_dev/tests/schemas/smoketest.config.schema.json`

These files are intentionally kept out of the packaged runtime catalog.

## Scripts

### `validate_toolspecs.py`

Validates `geneci/inference_catalog/tools/*/toolspec.json` against `geneci/inference_catalog/schemas/toolspec.schema.json`.

```bash
python components/inference_tools_dev/scripts/validate_toolspecs.py
```

### `build_tool_images.py`

Builds Docker images for tools defined in the packaged catalog.

```bash
python components/inference_tools_dev/scripts/build_tool_images.py
```

### `sync_tool_images.py`

Lists, pushes, or pulls Docker images referenced by `toolspec.docker_image`.

```bash
python components/inference_tools_dev/scripts/sync_tool_images.py list
python components/inference_tools_dev/scripts/sync_tool_images.py push --tool genie3
python components/inference_tools_dev/scripts/sync_tool_images.py pull --tool tigress
```

### `validate_input_specs.py`

Validates `geneci/inference_catalog/input_specs/*.json` against `geneci/inference_catalog/schemas/input-spec.schema.json`.

```bash
python components/inference_tools_dev/scripts/validate_input_specs.py
```

### `validate_smoketest_configs.py`

Validates `components/inference_tools_dev/tests/smoketest_configs/*.json` against
`components/inference_tools_dev/tests/schemas/smoketest.config.schema.json`.
It also checks that:
- each config filename matches a real catalog tool id
- each `extra_files` entry resolves to an existing fixture via the same lookup order used by `run_smoketests.py`

```bash
python components/inference_tools_dev/scripts/validate_smoketest_configs.py
python components/inference_tools_dev/scripts/validate_smoketest_configs.py --tool clr
```

### `validate_tool_costs.py`

Validates `geneci/inference_catalog/tools/*/cost.json` against `geneci/inference_catalog/schemas/toolcost.schema.json`.
It also checks that `benchmark_config.params_profile` is consistent with the corresponding ToolSpec.

```bash
python components/inference_tools_dev/scripts/validate_tool_costs.py
```

### `scaffold_tool.py`

Creates a minimal scaffold for a new tool integration without introducing any new manifest file.
It creates:
- `geneci/inference_catalog/tools/<tool_id>/toolspec.json`
- `components/inference_tools_dev/tools/<tool_id>/integration_decisions.md`
- `components/inference_tools_dev/tools/<tool_id>/Dockerfile`
- `components/inference_tools_dev/tools/<tool_id>/run_tool.py`, `run_tool.R`, or a generic `run_tool.<ext>`
- `components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json`

It also ensures that `repo/` and `papers/` folders exist under the tool root.
Today only `python` and `r` have tailored wrapper templates. Any other wrapper language
produces a generic placeholder scaffold that should be specialized during integration.

```bash
python components/inference_tools_dev/scripts/scaffold_tool.py --tool mytool
python components/inference_tools_dev/scripts/scaffold_tool.py --tool mytool --wrapper r
python components/inference_tools_dev/scripts/scaffold_tool.py --tool mytool --wrapper matlab
python components/inference_tools_dev/scripts/scaffold_tool.py --tool mytool --wrapper matlab --wrapper-ext m
```

### `prepare_tool_papers.py`

Extracts local PDF papers under `components/inference_tools_dev/tools/<tool_id>/papers/`
into plain-text sidecar files for analysis.

```bash
python components/inference_tools_dev/scripts/prepare_tool_papers.py --tool mytool
python components/inference_tools_dev/scripts/prepare_tool_papers.py --tool mytool --force
```

Notes:
- this is for manually placed local PDFs
- the extracted text files are analysis helpers only
- runtime must not depend on them

### `run_smoketests.py`

Runs tool smoketests using:
- tools from `geneci/inference_catalog/tools/`
- tool sources from `components/inference_tools_dev/tools/`
- ToolSpec defaults plus optional overrides from `components/inference_tools_dev/param_overrides/`
- fixtures from `components/inference_tools_dev/tests/fixtures/`
- per-tool configs from `components/inference_tools_dev/tests/smoketest_configs/`

```bash
python components/inference_tools_dev/scripts/run_smoketests.py
```

List mode shows whether each tool has a custom smoketest config or uses defaults:

```bash
python components/inference_tools_dev/scripts/run_smoketests.py --list
```

Fixture resolution order:
1. `tests/fixtures/<tool_id>/<filename>`
2. `tests/fixtures/<filename>`

### `benchmark_costs.py`

Runs Docker benchmarks and writes `cost.json` profiles under the packaged catalog.
Benchmark params are derived from ToolSpec defaults plus optional overrides in
`components/inference_tools_dev/param_overrides/`.

```bash
python components/inference_tools_dev/scripts/benchmark_costs.py
```

Notes:
- the script builds and uses a local benchmark tag of the form `inference-tools-<tool_id>:benchmark-local`
- only use `--skip-build` if that benchmark-local image already exists

### `sync_tool_repos.py`

Lists, clones, or removes local upstream source checkouts under
`components/inference_tools_dev/tools/<tool_id>/repo`, using `toolspec.implementation_url`.

```bash
python components/inference_tools_dev/scripts/sync_tool_repos.py list
python components/inference_tools_dev/scripts/sync_tool_repos.py clone --tool genie3
python components/inference_tools_dev/scripts/sync_tool_repos.py clean --tool genie3
```

### `sync_tool_publications.py`

Lists, fetches, or removes local paper caches under
`components/inference_tools_dev/tools/<tool_id>/papers`, using `toolspec.publication`.

Fetch mode attempts to:
- store DOI/citation metadata when available
- resolve the landing page URL
- download a PDF when directly accessible
- extract `article.txt` from the PDF using `pdftotext` when available

```bash
python components/inference_tools_dev/scripts/sync_tool_publications.py list
python components/inference_tools_dev/scripts/sync_tool_publications.py fetch --tool genie3
python components/inference_tools_dev/scripts/sync_tool_publications.py clean --tool genie3
```

Notes:
- PDF download is best-effort; some publisher pages may not expose a directly downloadable PDF.
- `article.txt` generation depends on `pdftotext` being available in `PATH`.
- Fetched papers are treated as local cache and are ignored by git.

## Root Makefile shortcuts

From repository root:

```bash
make install-dev-deps
make build-tool-images ARGS="--tool genie3"
make push-tool-images ARGS="--tool genie3"
make pull-tool-images ARGS="--tool genie3"
make run-tool-smoketests ARGS="--tool genie3 --show-output"
make benchmark-tool-costs ARGS="--tool genie3 --repeats 2"
make validate-toolspecs
make validate-input-specs
make validate-smoketest-configs
make validate-tool-costs
make validate-inference-catalog
make scaffold-tool TOOL=mytool WRAPPER=python
make scaffold-tool TOOL=mytool WRAPPER=matlab ARGS="--wrapper-ext m"
make prepare-tool-papers TOOL=mytool
make verify-tool TOOL=genie3
make clone-tool-repos ARGS="--tool genie3"
make clean-tool-repos ARGS="--tool genie3"
make fetch-tool-publications ARGS="--tool genie3"
make clean-tool-publications ARGS="--tool genie3"
make test-all
```

Environment note:
- `Makefile` uses root `.venv/bin/python` when available, otherwise falls back to `python`.
- Recommended workflow is a single root virtual environment for CLI/core/GUI and dev tooling scripts.
- If dev packages are missing in that environment, run `make install-dev-deps`.

## Adding or updating a tool

1. Create the initial scaffold:
   - `make scaffold-tool TOOL=<tool_id> WRAPPER=python`
   - or use another language label such as `WRAPPER=matlab`, `WRAPPER=julia`, `WRAPPER=java`
   - if the desired source file extension differs from the wrapper label, pass it via `ARGS`, for example:
     `make scaffold-tool TOOL=<tool_id> WRAPPER=matlab ARGS="--wrapper-ext m"`
2. Place evidence under:
   - `components/inference_tools_dev/tools/<tool_id>/repo/`
   - `components/inference_tools_dev/tools/<tool_id>/papers/`
3. If papers are PDFs, extract them first:
   - `make prepare-tool-papers TOOL=<tool_id>`
4. Follow the official end-to-end sequence in `components/inference_tools_dev/TOOL_INTEGRATION_PLAYBOOK.md`.
   It covers:
   - manual preparation
   - Phase 1 prompt
   - Phase 2 prompt
   - Phase 3 prompt
   - cost profile generation
   - final image build / push
5. Use `components/inference_tools_dev/tools/<tool_id>/integration_decisions.md` as the only per-tool decision log.
6. Keep the final runtime contract in `geneci/inference_catalog/tools/<tool_id>/toolspec.json`.
7. Add/update `components/inference_tools_dev/param_overrides/<tool_id>.json` only if dev smoke/benchmark runs should differ from ToolSpec defaults.
8. Verify the integration:
   - `make verify-tool TOOL=<tool_id>`
9. Validate the per-tool smoketest config if it was changed:
   - `make validate-smoketest-configs ARGS="--tool <tool_id>"`
10. Generate `cost.json` if planner support is expected, then validate it.
11. Build and optionally push the final image.

## Runtime docs

For runtime catalog structure/contracts and schemas, see `geneci/inference_catalog/README.md`.
