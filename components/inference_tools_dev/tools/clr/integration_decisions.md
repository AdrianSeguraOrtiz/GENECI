# clr Integration Decisions

## Sources Reviewed

- Upstream repo:
  - `components/inference_tools_dev/tools/clr/repo/DESCRIPTION`
  - `components/inference_tools_dev/tools/clr/repo/inst/CITATION`
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd`
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd`
  - `components/inference_tools_dev/tools/clr/repo/man/syn.data.Rd`
  - `components/inference_tools_dev/tools/clr/repo/R/build.mim.R`
  - `components/inference_tools_dev/tools/clr/repo/R/minet.R`
  - `components/inference_tools_dev/tools/clr/repo/src/clr.cpp`
- Local papers:
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.pdf`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.pdf`
- Extracted helper text:
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt`
- Manual clarifications from the integrator:
  - target method: CLR inside the `minet` library
  - preferred installation route: `BiocManager::install("minet")`
- External authoritative installation page:
  - `https://bioconductor.org/packages/minet/`

## Paper Preparation

- PDF inputs found:
  - `pbio.0050008.pdf`
  - `1471-2105-9-461.pdf`
- Extracted text files used for analysis:
  - `pbio.0050008.txt`
  - `1471-2105-9-461.txt`
- Extraction quality / problems:
  - Both papers are readable after extraction.
  - Mathematical formulas and some figure captions in `1471-2105-9-461.txt` are slightly garbled, but the method, package interface and workflow sections are clear enough for Phase 1 decisions.

## Method Summary

CLR is a mutual-information-based network inference method. In the `minet` package, `build.mim(dataset, estimator, disc, nbins)` computes the mutual-information matrix and `clr(mim)` transforms it into a weighted adjacency matrix using the CLR score. The package targets transcriptional network inference from expression data, but its documented interface is generic over any dataset arranged as observations by variables. Mutual information is symmetric, so CLR as implemented in `minet` does not infer direction or regulatory sign by itself.

## ToolSpec Evidence Ledger

For each field below:
- chosen value
- evidence
- rationale
- uncertainty

### `schema_version`

- chosen value: `1.0`
- evidence:
  - `geneci/inference_catalog/schemas/toolspec.schema.json`
- rationale:
  - fixed by the project schema contract
- uncertainty:
  - none

### `id`

- chosen value: `clr`
- evidence:
  - folder names under `components/inference_tools_dev/tools/clr/`
  - folder names under `geneci/inference_catalog/tools/clr/`
- rationale:
  - fixed by the chosen stable tool identifier
- uncertainty:
  - none

### `name`

- chosen value: `CLR`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:2-6`
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:17-18`
- rationale:
  - the method is consistently referred to by its acronym CLR in the package docs and the primary paper
- uncertainty:
  - low

### `publication`

- chosen value:
  - `https://doi.org/10.1371/journal.pbio.0050008`
  - `https://doi.org/10.1186/1471-2105-9-461`
- evidence:
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:26-27`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:19`
  - `components/inference_tools_dev/tools/clr/repo/inst/CITATION:1-10`
- rationale:
  - the CLR method paper should come first
  - the `minet` implementation paper should come second because it is the implementation we plan to package
- uncertainty:
  - none

### `first_author`

- chosen value: `Jeremiah J. Faith`
- evidence:
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:26-27`
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:32-37`
- rationale:
  - this is the first author of the primary CLR publication
- uncertainty:
  - none

### `year`

- chosen value: `2007`
- evidence:
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:26-27`
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:32-37`
- rationale:
  - this is the publication year of the primary CLR paper listed first in `publication`
- uncertainty:
  - none

### `method_summary`

- chosen value:
  - `Context Likelihood of Relatedness infers a symmetric weighted gene-gene network by comparing each mutual-information score against the empirical background distributions of both genes. In this integration, mutual information is computed with minet::build.mim and then minet::clr is applied so the wrapper preserves the method's raw CLR scores in network.csv.`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:17-31`
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:141-145`
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:210-215`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:21-25`
- rationale:
  - the summary captures the core CLR scoring idea and the fact that the wrapper uses the score-preserving `build.mim(...) + clr(...)` path rather than the normalized convenience wrapper
- uncertainty:
  - low

### `method_keywords`

- chosen value:
  - `mutual_information`
  - `information_theory`
  - `context_likelihood`
  - `z_score`
  - `undirected`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:20-30`
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:141-145`
  - `components/inference_tools_dev/tools/clr/papers/pbio.0050008.txt:210-215`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:116-122`
- rationale:
  - these keywords describe the method family, the specific CLR mechanism, and the non-directed nature of the resulting network
- uncertainty:
  - low

### `implementation_url`

- chosen value: `https://bioconductor.org/packages/minet/`
- evidence:
  - manual clarification from the integrator: install with `BiocManager::install("minet")`
  - `https://bioconductor.org/packages/minet/` lines 38-46
  - `https://bioconductor.org/packages/minet/` lines 78-81
  - `https://bioconductor.org/packages/3.22/bioc/src/contrib/minet_3.68.0.tar.gz`
  - `components/inference_tools_dev/tools/clr/repo/DESCRIPTION:1-11`
- rationale:
  - the package is currently published on Bioconductor and the official installation instructions match the integrator's clarification
  - runtime installation is pinned to the Bioconductor 3.22 source tarball for `minet` 3.68.0, while `implementation_url` remains the canonical package page
- uncertainty:
  - low

### `docker_image`

- chosen value: `adriansegura99/inference-tools_clr:1.0.0`
- evidence:
  - local project naming convention visible in the existing ToolSpecs under `geneci/inference_catalog/tools/*/toolspec.json`
- rationale:
  - this follows the same repository/tag convention already used by the current catalog
- uncertainty:
  - low

### `accepts`

- chosen value:
  - `samples`
  - `cells`
  - `timepoints`
  - `perturbations`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:5-13`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:6-25`
  - `components/inference_tools_dev/tools/clr/repo/man/syn.data.Rd:7-9`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:29-40`
- rationale:
  - the package API only requires a numeric dataset with observations in rows and variables in columns
  - CLR does not model single-cell-specific, time-series-specific or perturbation-specific structure; it only consumes repeated observations of gene expression
  - after transposing the standardized GENECI `expression_matrix`, any supported observation-column kind can satisfy that contract
- uncertainty:
  - medium
  - the published evaluations are bulk microarray-based, but the documented package interface is generic over observation rows

### `assumes`

- chosen value: `generic`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:7-13`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:9-25`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:29-40`
- rationale:
  - the implementation does not require single-cell metadata, lineage information, priors, or bulk-only perturbation design
  - it only assumes a matrix of repeated observations for genes/features
- uncertainty:
  - medium
  - practical validation in the literature is mostly on bulk microarray data

### `extra_inputs`

- chosen value:
  - `required`: `[]`
  - `optional`: `[]`
  - `conditional_required`: `[]`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:6-18`
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:5-23`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:6-25`
- rationale:
  - upstream CLR/minet consumes only the dataset plus scalar parameters
  - there is no documented support for TF lists, priors, groups, lineage trees or other auxiliary artefacts
  - the original CLR paper uses known transcription factors for evaluation/biological interpretation, but that restriction is not part of the `minet` CLR API
- uncertainty:
  - low

### `outputs`

- chosen value:
  - `directed`: `false`
  - `sign`: `none`
  - `evidence`: `association`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:11-18`
  - `components/inference_tools_dev/tools/clr/repo/src/clr.cpp:47-59`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:116-122`
  - `components/inference_tools_dev/tools/clr/papers/1471-2105-9-461.txt:496-497`
- rationale:
  - the implementation returns a symmetric weighted adjacency matrix
  - the package paper explicitly states that mutual information is symmetric and does not allow edge direction to be derived
  - the scores quantify statistical evidence / association, not signed regulatory effect
- uncertainty:
  - low

### `progress`

- chosen value:
  - `kind`: `none`
  - `note`: `minet/CLR exposes no native callbacks or incremental counters for MIM construction or CLR scoring; the wrapper can only report coarse lifecycle states.`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:6-18`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:21-25`
  - `components/inference_tools_dev/tools/clr/repo/R/minet.R:10-25`
- rationale:
  - the upstream interface is a pure batch function call returning only the final matrix
  - there is no documented progress channel analogous to iterations, target genes or task partitions
- uncertainty:
  - low

### `params`

- chosen value:
  - `estimator`
  - `disc`
  - `nbins`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:5-35`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:6-25`
  - `components/inference_tools_dev/tools/clr/repo/R/build.mim.R:11-39`
  - `components/inference_tools_dev/tools/clr/repo/R/minet.R:10-25`
- rationale:
  - the wrapper computes `build.mim(dataset, estimator, disc, nbins)` and then applies `clr(mim)`
  - `method` should not be user-exposed because this integration fixes the second stage to CLR
  - `estimator`, `disc` and `nbins` are the tunable dataset-level inputs documented by the upstream package for MIM construction
- uncertainty:
  - medium for `nbins`
  - upstream default is dynamic (`sqrt(NROW(dataset))`), so the ToolSpec will encode `null` as "use upstream default at runtime"

### `artifacts_aux`

- chosen value: `[]`
- evidence:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:11-18`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:16-20`
  - `components/inference_tools_dev/tools/clr/repo/R/minet.R:10-25`
- rationale:
  - the upstream API specifies only an in-memory adjacency matrix result
  - no auxiliary files are part of the upstream contract
  - any future log files would be wrapper-level implementation details, not Phase 1 tool semantics
- uncertainty:
  - low

## Upstream Interface

### Required inputs

- A numeric dataset where rows are observations/samples and columns are variables/features:
  - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:5-23`
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:6-25`
- For GENECI this maps to:
  - standardized `expression_matrix`
  - wrapper responsibility to transpose from `gene x observation` to `observation x gene`

### Optional or conditional inputs

- None at the upstream method level.
- No extra files are needed or documented for `build.mim(...)` + `clr(mim)`.

### Parameters and defaults

- `estimator`
  - default: `"spearman"`
  - allowed values: `"mi.empirical"`, `"mi.mm"`, `"mi.shrink"`, `"mi.sg"`, `"pearson"`, `"spearman"`, `"kendall"`
  - evidence:
    - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:5-13`
    - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:6-14`
- `disc`
  - default: `"none"`
  - allowed values: `"none"`, `"equalfreq"`, `"equalwidth"`, `"globalequalwidth"`
  - evidence:
    - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:11-13`
    - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:11-14`
- `nbins`
  - upstream default: `sqrt(NROW(dataset))`
  - evidence:
    - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:12-13`
    - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:13-14`
- `method`
  - fixed internally to `"clr"` for this integration
  - evidence:
    - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:10`
    - `components/inference_tools_dev/tools/clr/repo/R/minet.R:15-16`

### Primary outputs

- `clr(mim)` returns a weighted adjacency matrix:
  - `components/inference_tools_dev/tools/clr/repo/man/clr.Rd:11-18`
- `minet(dataset, method="clr", ...)` returns a normalized matrix because it divides the raw network by `max(net)`:
  - `components/inference_tools_dev/tools/clr/repo/man/minet.Rd:16-20`
  - `components/inference_tools_dev/tools/clr/repo/R/minet.R:13-25`
- For GENECI v2, the wrapper intentionally avoids that final normalization step so `network.csv` carries raw CLR scores and downstream normalization remains the responsibility of the merge stage:
  - `geneci/core/commands/infer_network_v2/commons/merge.py:121-146`

## Normalized Input Mapping

### Reused input specs

- `expression_matrix`
  - rationale:
    - the upstream API needs one expression matrix and no additional artefacts
    - the only transformation required is orientation: GENECI stores genes in rows and observations in columns, while `minet` expects observations in rows and genes in columns
  - evidence:
    - `geneci/inference_catalog/input_specs/expression_matrix.json`
    - `components/inference_tools_dev/tools/clr/repo/man/build.mim.Rd:7-13`
    - `components/inference_tools_dev/tools/clr/repo/man/syn.data.Rd:7-9`

### New input specs required

- None.
- No current CLR/minet requirement justifies `tf_list`, priors, groups or any new semantic input.

## Output Mapping to `network.csv`

Implemented mapping:

- read `expression.tsv`
- transpose to `observation x gene`
- call `build.mim(dataset, estimator=..., disc=..., nbins=...)`
- call `clr(mim)` on that mutual-information matrix
- obtain a symmetric weighted adjacency matrix with raw CLR scores
- export one row per unordered pair of distinct genes
- exclude diagonal/self-edges
- expected columns:
  - `source`: first gene in the pair
  - `target`: second gene in the pair
  - `score`: raw CLR score returned by `clr(mim)`
  - `sign`: `?`
  - `evidence`: `association`
  - `context`: `global`

Important design choice:

- The wrapper uses `build.mim(...) + clr(mim)` instead of the convenience wrapper `minet(..., method="clr")`.
- Consequence:
  - `network.csv` preserves raw CLR scores for the chosen upstream interface
  - downstream GENECI normalization still happens later in `network.normalized.csv`, consistently with the other v2 tools

Uncertainty:

- low
- the package already exposes both pieces needed for dataset-level invocation (`build.mim`) and score-preserving CLR application (`clr`)
- this choice matches the v2 convention that wrapper outputs are raw for the selected upstream interface and normalized later by the merge stage

## Installation Strategy

Preferred public installation source:

- Bioconductor package page:
  - `https://bioconductor.org/packages/minet/`
- pinned source tarball used by the Dockerfile:
  - `https://bioconductor.org/packages/3.22/bioc/src/contrib/minet_3.68.0.tar.gz`
- evidence:
  - `https://bioconductor.org/packages/minet/` lines 38-46
  - `https://bioconductor.org/packages/3.22/bioc/src/contrib/minet_3.68.0.tar.gz`

Fallback pinned source if needed:

- Bioconductor source repository:
  - `https://git.bioconductor.org/packages/minet`
- evidence:
  - `https://bioconductor.org/packages/minet/` lines 78-80
- note:
  - if package installation ever becomes unsuitable, pin an explicit commit/tag in the Phase 2 Dockerfile

## Wrapper Notes

Implemented wrapper:

- language: R
- install `jsonlite` and `infotheo` from CRAN
- install `minet` from the pinned Bioconductor 3.22 source tarball for version `3.68.0`
- parse resolved `estimator`, `disc`, `nbins`
- if `nbins` is `null`, omit it so that upstream default `sqrt(NROW(dataset))` remains in effect
- transpose `expression.tsv` to the orientation expected by `minet`
- call `build.mim(...)`
- call `clr(mim)`
- convert the symmetric matrix to `network.csv`
- do not depend on `components/inference_tools_dev/tools/clr/repo/` at runtime

Implemented runtime validations:

- ensure the expression matrix is numeric after transpose
- ensure `nbins >= 1` when explicitly provided
- consider warning if a discrete MI estimator is chosen with `disc = "none"` on continuous expression data

## Smoketest Plan

- fixture:
  - reuse the standard small expression fixture already used by other generic tools
- params:
  - `estimator = "spearman"`
  - `disc = "none"`
  - `nbins = null`
- checks:
  - `network.csv` exists and is non-empty
  - `progress.json` exists
  - all exported scores are numeric and non-negative
  - no extra inputs are required
- result:
  - smoketest passed against the shared fixture, producing a 10-edge undirected network for 5 genes

## Known Limitations / Open Questions

- The package and implementation are generic, but the literature evidence is strongest for bulk microarray data.
- `nbins` has a dynamic upstream default, so the ToolSpec must encode it indirectly using `null` as a sentinel.
- The upstream package has no native way to restrict inference to known TF regulators only; if we ever want a TF-constrained CLR variant, that should probably be a separate tool contract instead of silently repurposing `tf_list`.
