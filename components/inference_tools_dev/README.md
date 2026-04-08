# inference_tools_dev (dev tooling)

Development and maintenance tooling for the packaged inference catalog in `geneci/inference_catalog/`.

Use this area for:
- validating ToolSpecs
- validating tool `cost.json` profiles
- building tool Docker images
- pushing/pulling tool Docker images
- running smoketests
- benchmarking and updating `cost` profiles
- cloning upstream implementation repositories for local inspection
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
  scripts/
    shared/
    validate_toolspecs.py
    validate_input_specs.py
    validate_tool_costs.py
    build_tool_images.py
    sync_tool_images.py
    run_smoketests.py
    benchmark_costs.py
    sync_tool_repos.py
    template_map.json
    templates/
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

### `validate_tool_costs.py`

Validates `geneci/inference_catalog/tools/*/cost.json` against `geneci/inference_catalog/schemas/toolcost.schema.json`.
It also checks that `benchmark_config.params_profile` is consistent with the corresponding ToolSpec.

```bash
python components/inference_tools_dev/scripts/validate_tool_costs.py
```

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

### `sync_tool_repos.py`

Lists, clones, or removes local upstream source checkouts under
`components/inference_tools_dev/tools/<tool_id>/repo`, using `toolspec.implementation_url`.

```bash
python components/inference_tools_dev/scripts/sync_tool_repos.py list
python components/inference_tools_dev/scripts/sync_tool_repos.py clone --tool genie3
python components/inference_tools_dev/scripts/sync_tool_repos.py clean --tool genie3
```

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
make validate-tool-costs
make validate-inference-catalog
make clone-tool-repos ARGS="--tool genie3"
make clean-tool-repos ARGS="--tool genie3"
make test-all
```

Environment note:
- `Makefile` uses root `.venv/bin/python` when available, otherwise falls back to `python`.
- Recommended workflow is a single root virtual environment for CLI/core/GUI and dev tooling scripts.
- If dev packages are missing in that environment, run `make install-dev-deps`.

## Adding or updating a tool

1. Edit the runtime metadata in `geneci/inference_catalog/tools/<tool_id>/toolspec.json`.
2. Edit build sources/wrappers in `components/inference_tools_dev/tools/<tool_id>/`.
3. Optionally clone the upstream implementation into `tools/<tool_id>/repo/` with `sync_tool_repos.py clone`.
4. Validate ToolSpec with `validate_toolspecs.py`.
5. Add/update `components/inference_tools_dev/param_overrides/<tool_id>.json` if dev smoke/benchmark runs should differ from ToolSpec defaults.
6. Add/update smoketest config in `components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json` (if needed).
7. Run `run_smoketests.py`.
8. Optionally run `benchmark_costs.py` to refresh `cost.json`, then validate with `validate_tool_costs.py`.

## Runtime docs

For runtime catalog structure/contracts and schemas, see `geneci/inference_catalog/README.md`.
