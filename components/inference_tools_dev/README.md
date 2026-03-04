# inference_tools_dev (dev tooling)

Development and maintenance tooling for the packaged inference catalog in `geneci/inference_catalog/`.

Use this area for:
- validating ToolSpecs
- building tool Docker images
- running smoketests
- benchmarking and updating `cost` profiles
- keeping shared fixtures and smoketest-only configs

Runtime catalog assets consumed by `infer_network_v2` live in `geneci/inference_catalog/`.
Tool build sources and dev-only assets live in `components/inference_tools_dev/tools/`.

## Layout

```text
components/inference_tools_dev/
  tools/
    <tool_id>/
      Dockerfile
      run_tool.py | run_tool.R
      assets/
        params.json
  scripts/
    validate_toolspecs.py
    validate_input_specs.py
    build_tool_images.py
    run_smoketests.py
    benchmark_costs.py
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

### `validate_input_specs.py`

Validates `geneci/inference_catalog/input_specs/*.json` against `geneci/inference_catalog/schemas/input-spec.schema.json`.

```bash
python components/inference_tools_dev/scripts/validate_input_specs.py
```

### `run_smoketests.py`

Runs tool smoketests using:
- tools from `geneci/inference_catalog/tools/`
- tool sources/assets from `components/inference_tools_dev/tools/`
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
3. `components/inference_tools_dev/tools/<tool_id>/assets/<filename>`

### `benchmark_costs.py`

Runs Docker benchmarks and writes `cost.json` profiles under the packaged catalog.

```bash
python components/inference_tools_dev/scripts/benchmark_costs.py
```

## Root Makefile shortcuts

From repository root:

```bash
make env-info
make install-dev-deps
make build-tool-images ARGS="--tool genie3"
make run-tool-smoketests ARGS="--tool genie3 --show-output"
make benchmark-tool-costs ARGS="--tool genie3 --repeats 2"
make validate-toolspecs
make validate-input-specs
make validate-inference-catalog
make test-all
```

Environment note:
- `Makefile` uses root `.venv/bin/python` when available, otherwise falls back to `python`.
- Recommended workflow is a single root virtual environment for CLI/core/GUI and dev tooling scripts.
- If dev packages are missing in that environment, run `make install-dev-deps`.

## Adding or updating a tool

1. Edit the runtime metadata in `geneci/inference_catalog/tools/<tool_id>/toolspec.json`.
2. Edit build sources/wrappers/dev assets in `components/inference_tools_dev/tools/<tool_id>/`.
3. Validate ToolSpec with `validate_toolspecs.py`.
4. Add/update smoketest config in `components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json` (if needed).
5. Run `run_smoketests.py`.
6. Optionally run `benchmark_costs.py` to refresh `cost.json`.

## Runtime docs

For runtime catalog structure/contracts and schemas, see `geneci/inference_catalog/README.md`.
