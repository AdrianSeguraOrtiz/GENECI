# Tool Integration Playbook

This playbook defines the recommended hybrid workflow for integrating a new inference tool into `infer_network_v2`.

Use it when you have local evidence under:

```text
components/inference_tools_dev/tools/<tool_id>/
  repo/
  papers/
```

`repo/` and `papers/` are evidence sources for analysis only. They must not become runtime dependencies.
For new integrations, assume `papers/` contains one or more PDF files. Convert them to text before semantic analysis.
Runtime behavior must be reproducible from:
- `geneci/inference_catalog/tools/<tool_id>/toolspec.json`
- the wrapper under `components/inference_tools_dev/tools/<tool_id>/`
- the `Dockerfile` under `components/inference_tools_dev/tools/<tool_id>/`

## Scope

The goal of an integration is to produce:
- a coherent `toolspec.json`
- reuse of existing normalized inputs when semantics match
- a new `input_spec` only when the semantic content does not match current inputs
- a wrapper that maps upstream behavior to the GENECI runtime contract
- a `Dockerfile` that installs the tool from a stable public source
- smoketests and fixtures
- an `integration_decisions.md` file documenting the decisions taken

## Source-of-truth rules

1. Prefer the upstream implementation and paper over assumptions.
2. Keep `toolspec.json` aligned with the real upstream interface.
3. Reuse an existing normalized input only if the semantic content matches.
4. Create a new normalized input only when the current catalog cannot express the same information content.
5. Do not depend on the local `repo/` folder at runtime.
6. Installation preference:
   - package manager / official library first
   - upstream public repo pinned to tag/commit if no package exists
   - never depend on an unpinned floating source if avoidable

## Official End-to-End Procedure

Follow these steps in order. A tool is not considered fully integrated until you reach the final image/cost steps.

### Step 0. Choose `<tool_id>` and wrapper language

Manual action:
- choose a stable lowercase id using letters, digits, `_` or `-`
- choose the initial wrapper language label (`python`, `r`, `matlab`, `julia`, `java`, ...)
- if the upstream repo is a multi-tool library, decide which method/package/function/CLI entrypoint is the actual target
- if installation details are unclear in the repo, decide what clarification you will provide later in the prompt

This id will be reused in:
- [tool source dir](tools/<tool_id>/)
- [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- [smoketest config](tests/smoketest_configs/<tool_id>.json)

### Step 1. Create the scaffold

Command:

```bash
make scaffold-tool TOOL=<tool_id> WRAPPER=python
```

Variants:
- use `WRAPPER=r` if the wrapper should be R-based
- use another label such as `WRAPPER=matlab`, `WRAPPER=julia` or `WRAPPER=java` for a generic scaffold
- if the wrapper file extension differs from the language label, pass it through `ARGS`, for example:

```bash
make scaffold-tool TOOL=<tool_id> WRAPPER=matlab ARGS="--wrapper-ext m"
```

Expected files after this step:
- [tool source dir](tools/<tool_id>/)
- [integration_decisions.md](tools/<tool_id>/integration_decisions.md)
- [Dockerfile](tools/<tool_id>/Dockerfile)
- [wrapper stub](tools/<tool_id>/run_tool.py)
- [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- [smoketest config](tests/smoketest_configs/<tool_id>.json)

### Step 2. Place the upstream evidence

Manual action:
- copy or clone the upstream implementation into [repo/](tools/<tool_id>/repo/)
- copy one or more local PDF papers into [papers/](tools/<tool_id>/papers/)

Minimum evidence expected in [repo/](tools/<tool_id>/repo/):
- README or package docs
- examples
- config files or CLI help
- the relevant function/module/script if the repo contains multiple tools
- output examples if available

Minimum evidence expected in [papers/](tools/<tool_id>/papers/):
- primary method paper PDF
- implementation/package paper PDF if different
- any additional paper needed to justify special inputs, assumptions or outputs

### Step 3. Extract local PDFs

Command:

```bash
make prepare-tool-papers TOOL=<tool_id>
```

Rules:
- the generated `.txt` files are analysis helpers only
- the PDFs remain the primary evidence source
- if extraction quality is poor, record that in [integration_decisions.md](tools/<tool_id>/integration_decisions.md)

### Step 4. Sanity-check the local layout

Manual action:
- confirm that these paths exist before starting Phase 1:
  - [repo/](tools/<tool_id>/repo/)
  - [papers/](tools/<tool_id>/papers/)
  - [integration_decisions.md](tools/<tool_id>/integration_decisions.md)
  - [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- confirm that at least one extracted paper text file exists if PDFs were provided

### Step 5. Execute Phase 1: evidence and contract

Goal:
- produce/update [integration_decisions.md](tools/<tool_id>/integration_decisions.md)
- draft [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- propose a new normalized input only if the current catalog cannot express the same semantic content

Prompt to paste in chat:

```text
Please integrate the new tool `<tool_id>` following [TOOL_INTEGRATION_PLAYBOOK.md](components/inference_tools_dev/TOOL_INTEGRATION_PLAYBOOK.md), but only execute Phase 1 for now.

Context:
- Upstream repo is under [repo/](components/inference_tools_dev/tools/<tool_id>/repo/)
- Local papers are under [papers/](components/inference_tools_dev/tools/<tool_id>/papers/)
- Existing scaffold files already exist
- The working decision log is [integration_decisions.md](components/inference_tools_dev/tools/<tool_id>/integration_decisions.md)
- The ToolSpec draft location is [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- Optional manual clarifications from the integrator:
  - target method inside a multi-tool library/repo: `<optional>`
  - relevant module / package / script / function / CLI entrypoint: `<optional>`
  - preferred installation source if upstream docs are unclear: `<optional>`
  - preferred version / tag / commit if needed: `<optional>`

Requirements:
- Review the upstream repo and the local papers
- Produce or update [integration_decisions.md](components/inference_tools_dev/tools/<tool_id>/integration_decisions.md)
- Draft [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- Reuse existing normalized inputs when their semantic content matches
- If current normalized inputs do not fit semantically, propose and implement a new input spec under [geneci/inference_catalog/input_specs/](geneci/inference_catalog/input_specs/)
- Do not implement the wrapper yet
- In [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json), store publication DOIs as full canonical URLs (`https://doi.org/...`) and store `first_author` as the full author name
- Populate `year`, `method_summary` and `method_keywords` with explicit evidence from the primary paper/repo, not with wrapper-level wording
- Explicitly decide and document which upstream public entrypoint the integration mirrors
- If any upstream default is data-dependent or runtime-dependent, document the exact rule and how the ToolSpec preserves it
- Determine whether the wrapper should preserve raw method scores directly or whether the chosen upstream public interface already defines the score scale
- For every non-trivial field in [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json), record:
  - chosen value
  - evidence path(s)
  - rationale
  - uncertainty if any
- Use the field-by-field evidence policy from [TOOL_INTEGRATION_PLAYBOOK.md](components/inference_tools_dev/TOOL_INTEGRATION_PLAYBOOK.md)
- If optional manual clarifications are provided, treat them as authoritative context for locating the target implementation and installation route unless stronger primary evidence clearly disproves them

Focus especially on:
1. input semantics and conditional required inputs
2. parameter mapping and defaults
3. output semantics and how they should map to raw `network.csv`
4. installation source preference: package first, pinned upstream source second
5. explicit evidence for `accepts`, `assumes`, `extra_inputs`, `outputs`, `progress`, `params` and `artifacts_aux`
```

### Step 6. Review the Phase 1 outputs

Manual action:
- inspect [integration_decisions.md](tools/<tool_id>/integration_decisions.md)
- inspect [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json)
- decide whether the proposed contract is acceptable before any wrapper code is written

Do not continue to Phase 2 until the contract looks correct.

### Step 7. Execute Phase 2: implementation

Goal:
- implement the wrapper and Dockerfile
- keep [toolspec.json](../../geneci/inference_catalog/tools/<tool_id>/toolspec.json) aligned with the real implementation
- add or update smoketest fixtures/config

Prompt to paste in chat:

```text
Please continue the integration of `<tool_id>` following [TOOL_INTEGRATION_PLAYBOOK.md](components/inference_tools_dev/TOOL_INTEGRATION_PLAYBOOK.md), executing Phase 2.

Requirements:
- Use [integration_decisions.md](components/inference_tools_dev/tools/<tool_id>/integration_decisions.md) as the working contract
- Implement the wrapper under [tools/<tool_id>/](components/inference_tools_dev/tools/<tool_id>/) and the corresponding [Dockerfile](components/inference_tools_dev/tools/<tool_id>/Dockerfile)
- Do not depend on the local [repo/](components/inference_tools_dev/tools/<tool_id>/repo/) folder at runtime
- Install the method from an official package when possible, otherwise from a pinned upstream repo/tag/commit
- Install runtime dependencies with the package manager of the same interpreter/runtime that will execute the wrapper
- If the runtime build pipeline requires [template_map.json](components/inference_tools_dev/scripts/template_map.json), register `<tool_id>` there with the correct runtime and template bundles
- Preserve data-dependent or runtime-dependent upstream defaults; if the ToolSpec uses a sentinel such as `null` to mean "defer to upstream default", implement that by omitting the argument rather than hard-coding a replacement value
- Make the wrapper produce raw `network.csv` scores for the chosen upstream interface and `progress.json`
- Do not apply GENECI-specific score normalization in the wrapper; downstream normalization is handled later by [merge.py](geneci/core/commands/infer_network_v2/commons/merge.py)
- Do not write rows with `score == 0` to `network.csv`; if the upstream method produces a dense matrix, filter zero-score edges in the wrapper before export
- For undirected methods, export one row per unordered pair and exclude self-loops unless stronger primary evidence clearly requires another edge convention
- Add or update [smoketest config](components/inference_tools_dev/tests/smoketest_configs/<tool_id>.json) and any needed fixtures under [tests/fixtures/](components/inference_tools_dev/tests/fixtures/)
- Build the image and run the smoketest during this phase; if it fails, fix the implementation and repeat until it passes
- Keep [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json) aligned with the implemented behavior
- Update [integration_decisions.md](components/inference_tools_dev/tools/<tool_id>/integration_decisions.md) so it reflects implemented behavior and records the smoketest outcome
- If the integrator provided optional clarifications about the target method or installation source, keep respecting them during implementation unless stronger primary evidence clearly disproves them
```

### Step 8. Execute Phase 3: verification and final alignment

Goal:
- validate schemas
- run the smoketest again as final confirmation
- leave [integration_decisions.md](tools/<tool_id>/integration_decisions.md) concise and complete

Prompt to paste in chat:

```text
Please finish the integration of `<tool_id>` following [TOOL_INTEGRATION_PLAYBOOK.md](components/inference_tools_dev/TOOL_INTEGRATION_PLAYBOOK.md), executing Phase 3.

Requirements:
- Validate [toolspec.json](geneci/inference_catalog/tools/<tool_id>/toolspec.json) and all relevant input specs under [geneci/inference_catalog/input_specs/](geneci/inference_catalog/input_specs/)
- Run the smoketest for `<tool_id>`
- Fix any remaining inconsistency between the wrapper, the ToolSpec, the normalized inputs and the smoketest
- Leave [integration_decisions.md](components/inference_tools_dev/tools/<tool_id>/integration_decisions.md) complete and concise
```

### Step 9. Generate the planning cost profile

Command:

```bash
make benchmark-tool-costs ARGS="--tool <tool_id>"
```

If you need a smaller or custom benchmark matrix, customize `ARGS`, for example:

```bash
make benchmark-tool-costs ARGS="--tool <tool_id> --size 50x20 --size 100x40 --threads 1,2 --ram-gb 8,16 --repeats 1"
```

Then validate the resulting [cost.json](../../geneci/inference_catalog/tools/<tool_id>/cost.json):

```bash
make validate-tool-costs ARGS="--tool <tool_id>"
```

Note:
- [benchmark_costs.py](scripts/benchmark_costs.py) uses its own local image tag `inference-tools-<tool_id>:benchmark-local`
- do not pass `--skip-build` unless that benchmark-local image already exists

### Step 10. Validate the full catalog state

Command:

```bash
make validate-inference-catalog
```

Optional focused verification:

```bash
make verify-tool TOOL=<tool_id>
```

Optional focused smoketest-config validation:

```bash
make validate-smoketest-configs ARGS="--tool <tool_id>"
```

### Step 11. Build and optionally publish the final image

Build the final packaged image:

```bash
make build-tool-images ARGS="--tool <tool_id>"
```

Optionally push it:

```bash
make push-tool-images ARGS="--tool <tool_id>"
```

If another machine or CI needs to pull it explicitly:

```bash
make pull-tool-images ARGS="--tool <tool_id>"
```

## ToolSpec Field Evidence Guide

When drafting `toolspec.json`, use the following field-by-field evidence policy.

### Fixed by project contract

- `schema_version`
  - value: `1.0`
  - evidence: `geneci/inference_catalog/schemas/toolspec.schema.json`
- `id`
  - value: `<tool_id>`
  - evidence: folder name under `components/inference_tools_dev/tools/` and `geneci/inference_catalog/tools/`
- `docker_image`
  - value source: project naming convention
  - evidence: local project convention, not upstream evidence
  - note: still record the naming decision in `integration_decisions.md`

### Identity and provenance

- `name`
  - look in:
    - repo README title
    - package/project name in upstream docs
    - paper title and abstract
  - search for:
    - official spelling and capitalization of the method name
- `publication`
  - look in:
    - paper PDFs
    - repo README citation section
    - package metadata / documentation
  - search for:
    - DOI(s), primary method paper, follow-up implementation paper if relevant
  - note:
    - store DOI references as full canonical URLs: `https://doi.org/...`
    - primary method paper should appear first
- `first_author`
  - look in:
    - primary paper PDF
  - search for:
    - full name of the first author of `publication[0]`
- `year`
  - look in:
    - primary paper PDF
    - repo citation section
    - package metadata when it cites the primary paper
  - search for:
    - publication year of `publication[0]`
- `method_summary`
  - look in:
    - paper abstract
    - paper methods/introduction
    - repo README description
  - search for:
    - the core modeling idea in one or two sentences
  - rule:
    - summarize the method itself, not the wrapper implementation details
- `method_keywords`
  - look in:
    - paper title/abstract
    - repo README
    - implementation docs
  - search for:
    - 3-6 short lower_snake_case keywords capturing the method family or central ideas
  - rule:
    - prefer reusable conceptual terms such as `mutual_information`, `tree_ensemble`, `stability_selection`, `single_cell`
- `implementation_url`
  - look in:
    - official package page
    - CRAN / Bioconductor / PyPI page
    - upstream GitHub repository
  - search for:
    - canonical public source matching the implementation you will install

### Interface boundary

Before finalizing params, inputs and outputs, explicitly decide which upstream public entrypoint the integration mirrors.

- look in:
  - package docs / man pages
  - exported functions
  - CLI usage/help
  - examples in README and papers
- search for:
  - whether the method exists as:
    - a low-level algorithm primitive
    - a higher-level convenience pipeline that includes preprocessing/postprocessing
- rule:
  - choose the narrowest public upstream interface that cleanly matches GENECI inputs
  - record the decision explicitly in `integration_decisions.md`
  - if the wrapper intentionally targets a convenience wrapper instead of the bare algorithm, document the consequence for params and output semantics
  - if the upstream package offers both a score-preserving low-level interface and a convenience wrapper that only rescales the same scores, prefer the score-preserving interface so raw `network.csv` remains comparable with other v2 tools

### Dynamic defaults

If an upstream default depends on the dataset or runtime state, do not silently replace it with an arbitrary constant.

- look in:
  - function signatures
  - source code defaults
  - docs/examples
- search for:
  - expressions such as `sqrt(NROW(dataset))`, `ncol(X)`, `auto`, `None`, inferred thread counts, or data-dependent heuristics
- rule:
  - record the exact upstream default rule in `integration_decisions.md`
  - decide how the ToolSpec will preserve that behavior
  - if a sentinel such as `null` is used in the ToolSpec to mean "defer to upstream default", document that explicitly

### Dataset compatibility

- `accepts`
  - look in:
    - repo input examples
    - README usage examples
    - CLI/config format
    - paper methods and datasets
  - search for:
    - what each expression-matrix column semantically represents:
      - `samples`
      - `cells`
      - `timepoints`
      - `perturbations`
  - rule:
    - decide from method semantics, not only file shape
- `assumes`
  - look in:
    - paper abstract, introduction and methods
    - repo README
    - preprocessing assumptions in code/examples
  - search for:
    - whether the method is specifically for scRNA, bulk, or genuinely generic
  - rule:
    - use `scrna_specific` only when the method materially depends on single-cell structure
    - use `bulk_specific` only when it is explicitly designed for bulk/cohort data
    - otherwise use `generic`

### Extra inputs

- `extra_inputs.required`
- `extra_inputs.optional`
- `extra_inputs.conditional_required`
  - look in:
    - CLI flags / argument parser
    - example config files
    - README parameter docs
    - code paths that fail when files are missing
    - paper methods if a prior/annotation is part of the method
  - search for:
    - files beyond expression matrix
    - whether they are always required, mode-dependent, or optional
  - rule:
    - if a file is needed only when certain parameter values are used, model it in `conditional_required`
    - if the semantic content does not match an existing normalized input, propose a new `input_spec`

### Output semantics

- `outputs.directed`
- `outputs.sign`
- `outputs.evidence`
  - look in:
    - paper method definition
    - output files in repo/examples
    - package docs describing edge meaning
  - search for:
    - whether edges are directed
    - whether sign is available
    - whether evidence is association, causal, or pseudotime-directed
  - also determine:
    - whether the chosen upstream interface returns raw method scores or already-normalized scores
  - rule:
    - `network.csv` should preserve the direct scores of the chosen upstream interface
    - do not add an extra GENECI-specific score normalization layer in the wrapper; downstream normalization is handled later by `infer_network_v2`
    - exact zero-score edges should be omitted from `network.csv`; zero means "no retained interaction", not a useful stored edge

### Progress

- `progress.kind`
- `progress.note`
  - look in:
    - upstream logs
    - iteration counters
    - target-gene loops
    - partitioned tasks or phases
  - search for:
    - a stable observable unit that the wrapper can convert into `progress.json`
  - rule:
    - this field is defined by wrapper instrumentation, but it must still be justified from real upstream execution behavior

### Parameters

- `params`
  - look in:
    - CLI flags
    - function signatures
    - README parameter tables
    - config examples
    - defaults in code
  - search for:
    - parameter names
    - data types
    - defaults
    - enum values
    - numeric bounds
  - rule:
    - prefer upstream parameter names unless there is a strong normalization reason not to
    - if defaults conflict across sources, document the conflict and justify the chosen value

### Auxiliary artifacts

- `artifacts_aux`
  - look in:
    - example output directories
    - repo docs on generated files
    - logs and temporary outputs that are useful for debugging
  - search for:
    - non-trivial files/dirs worth validating in smoketests

## Required Structure of `integration_decisions.md`

The decision log must include:
- what value was chosen
- where the evidence came from
- why that evidence supports the chosen value
- whether the value is certain or uncertain

If a value is unclear:
- say that it is unclear
- list the conflicting evidence
- explain the chosen temporary resolution

## Quick Command Summary

From repository root:

```bash
make scaffold-tool TOOL=<tool_id> WRAPPER=python
make prepare-tool-papers TOOL=<tool_id>
make verify-tool TOOL=<tool_id>
make validate-smoketest-configs ARGS="--tool <tool_id>"
make benchmark-tool-costs ARGS="--tool <tool_id>"
make validate-tool-costs ARGS="--tool <tool_id>"
make build-tool-images ARGS="--tool <tool_id>"
make push-tool-images ARGS="--tool <tool_id>"
```

Notes:
- `WRAPPER` can be `python`, `r`, or another implementation language label such as `matlab`, `julia`, `java`
- only `python` and `r` currently get language-specific scaffold templates
- use `ARGS="--wrapper-ext <ext>"` when the desired file extension is not the obvious default
- `verify-tool` is intended for late-phase verification, not for an empty scaffold
- `run_smoketests.py` already builds the tool image unless explicitly skipped

## Review Checklist

Before considering a tool integrated, confirm:
- local paper PDFs were extracted to text and reviewed
- `toolspec.json` matches the real upstream interface
- every non-trivial `toolspec` field has explicit evidence in `integration_decisions.md`
- conditional inputs are modeled in the catalog when needed
- no normalized input is being reused with the wrong semantics
- the wrapper does not rely on the local `repo/`
- the `Dockerfile` uses a stable public source
- the output mapping to raw `network.csv` is documented in `integration_decisions.md`
- any per-tool normalization is left to downstream runtime merge, not silently added by the wrapper unless the chosen upstream public interface itself defines that scale
- smoketest passes
- `cost.json` exists and validates if planner support is expected for the tool
- the packaged image can be built, and pushed if publication is part of the integration task
