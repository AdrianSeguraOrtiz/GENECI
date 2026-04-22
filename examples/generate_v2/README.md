# generate-v2 examples

These examples exercise the current complete generate-v2 flow with `dyngen`.

The selected simulator instances are in:

```text
examples/generate_v2/dyngen_two_configs_runs.json
```

It runs the same simulator twice with different configurations:

- `dyngen_bifurcating`
- `dyngen_linear`

Each simulator entry requests `replicates = 2`, so the plan creates four independent simulator tasks:

- `dyngen_bifurcating__r01`
- `dyngen_bifurcating__r02`
- `dyngen_linear__r01`
- `dyngen_linear__r02`

Use `--max-parallel-tasks` to control how many of those tasks can run concurrently. Setting it to `4` allows the four replicas/configurations to run in parallel if enough CPU and Docker resources are available.

## Global scRNA

```bash
.venv/bin/geneci benchmarking generate-v2 preflight \
  --scenario examples/generate_v2/dyngen_scrna_global_scenario.json \
  --output-json /tmp/geneci-generate-v2-global/preflight-report.json

.venv/bin/geneci benchmarking generate-v2 plan \
  --scenario examples/generate_v2/dyngen_scrna_global_scenario.json \
  --simulator-runs examples/generate_v2/dyngen_two_configs_runs.json \
  --max-parallel-tasks 4 \
  --out /tmp/geneci-generate-v2-global/simulation-plan.json

.venv/bin/geneci benchmarking generate-v2 run \
  --plan /tmp/geneci-generate-v2-global/simulation-plan.json \
  --output-dir /tmp/geneci-generate-v2-global/benchmarks_v2 \
  --progress-poll-seconds 0.5
```

## Grouped scRNA with lineage

```bash
.venv/bin/geneci benchmarking generate-v2 preflight \
  --scenario examples/generate_v2/dyngen_scrna_grouped_lineage_scenario.json \
  --output-json /tmp/geneci-generate-v2-grouped/preflight-report.json

.venv/bin/geneci benchmarking generate-v2 plan \
  --scenario examples/generate_v2/dyngen_scrna_grouped_lineage_scenario.json \
  --simulator-runs examples/generate_v2/dyngen_two_configs_runs.json \
  --max-parallel-tasks 4 \
  --out /tmp/geneci-generate-v2-grouped/simulation-plan.json

.venv/bin/geneci benchmarking generate-v2 run \
  --plan /tmp/geneci-generate-v2-grouped/simulation-plan.json \
  --output-dir /tmp/geneci-generate-v2-grouped/benchmarks_v2 \
  --progress-poll-seconds 0.5
```

The same flow can be executed in one command:

```bash
.venv/bin/geneci benchmarking generate-v2 execute \
  --scenario examples/generate_v2/dyngen_scrna_grouped_lineage_scenario.json \
  --simulator-runs examples/generate_v2/dyngen_two_configs_runs.json \
  --output-dir /tmp/geneci-generate-v2-execute/benchmarks_v2 \
  --max-parallel-tasks 4 \
  --progress-poll-seconds 0.5
```

The grouped benchmark package will contain dataset manifests such as:

```text
/tmp/geneci-generate-v2-grouped/benchmarks_v2/demo_dyngen_scrna_grouped/datasets/demo_dyngen_scrna_grouped__dyngen_bifurcating__r01/dataset-manifest.json
```

That dataset can then be checked by infer-network-v2:

```bash
.venv/bin/geneci infer-network-v2 preflight \
  --dataset-manifest /tmp/geneci-generate-v2-grouped/benchmarks_v2/demo_dyngen_scrna_grouped/datasets/demo_dyngen_scrna_grouped__dyngen_bifurcating__r01/dataset-manifest.json
```
