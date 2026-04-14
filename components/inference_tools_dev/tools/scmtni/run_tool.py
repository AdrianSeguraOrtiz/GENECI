"""
scMTNI wrapper for the inference_tools execution contract.

This wrapper assumes params.json is already resolved/validated by the orchestrator.
It only enforces minimal runtime checks (paths, required keys, basic types).
"""

import argparse
import csv
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from _run_tool_common import load_params as _load_params
from _run_tool_common import optional_extra_file as _optional_extra_file
from _run_tool_common import require_extra_file as _require_extra_file
from _run_tool_common import require_param_keys
from _run_tool_common import tail_text as _tail_text
from _run_tool_common import validate_runtime_inputs, warn_unknown_params
from _run_tool_common import write_progress as _write_progress

SCMTNI_BIN = Path("/app/bin/scMTNI")
ITERATION_RE = re.compile(r"\bITERATION\s+(\d+)\b")
MAX_ITERATIONS_PROGRESS = 100


def _resolve_params(raw_params: Dict[str, Any]) -> Dict[str, Any]:
    required_keys = {"x", "p", "b", "q", "indep", "split_genes"}
    require_param_keys(raw_params, required_keys)
    warn_unknown_params(raw_params, required_keys)

    x_value = raw_params["x"]
    p_value = raw_params["p"]
    b_value = raw_params["b"]
    q_value = raw_params["q"]
    indep_value = raw_params["indep"]
    split_genes_value = raw_params["split_genes"]

    if not isinstance(x_value, int) or x_value < 1:
        raise ValueError("x must be an integer >= 1.")

    if not isinstance(p_value, (int, float)):
        raise ValueError("p must be numeric.")
    p_value = float(p_value)
    if p_value < 0 or p_value > 1:
        raise ValueError("p must be in [0, 1].")

    if not isinstance(b_value, (int, float)):
        raise ValueError("b must be numeric.")
    b_value = float(b_value)

    if not isinstance(q_value, (int, float)):
        raise ValueError("q must be numeric.")
    q_value = float(q_value)
    if q_value < 0:
        raise ValueError("q must be >= 0.")

    if not isinstance(indep_value, bool):
        raise ValueError("indep must be a boolean.")

    if not isinstance(split_genes_value, bool):
        raise ValueError("split_genes must be a boolean.")

    return {
        "x": x_value,
        "p": p_value,
        "b": b_value,
        "q": q_value,
        "indep": indep_value,
        "split_genes": split_genes_value,
    }


def _validate_inputs(
    input_path: Path, params_path: Path, extra_dir: Path, threads: int
) -> None:
    validate_runtime_inputs(
        input_path=input_path,
        params_path=params_path,
        extra_dir=extra_dir,
        threads=threads,
        required_paths=[SCMTNI_BIN],
    )


def _split_fields(line: str) -> List[str]:
    if "\t" in line:
        return [token.strip() for token in line.split("\t")]
    if "," in line:
        return [token.strip() for token in line.split(",")]
    return [token.strip() for token in line.split()]


def _read_expression_tsv(
    expr_path: Path,
) -> Tuple[List[str], List[str], List[List[float]]]:
    with expr_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("expression.tsv is empty.") from exc

        if len(header) < 2:
            raise ValueError(
                "expression.tsv must have at least 2 columns: gene + >=1 observation."
            )

        sample_ids = [token.strip() for token in header[1:]]
        if any(not token for token in sample_ids):
            raise ValueError("expression.tsv header has empty sample/cell names.")

        genes: List[str] = []
        values_by_gene: List[List[float]] = []
        seen_genes = set()

        for row_number, row in enumerate(reader, start=2):
            if not row:
                continue

            gene = row[0].strip()
            if not gene:
                continue

            if gene in seen_genes:
                continue

            values_raw = row[1:]
            if len(values_raw) != len(sample_ids):
                raise ValueError(
                    f"expression.tsv row {row_number} has {len(values_raw)} values but expected {len(sample_ids)}."
                )

            values: List[float] = []
            for raw in values_raw:
                try:
                    values.append(float(raw))
                except ValueError as exc:
                    raise ValueError(
                        f"expression.tsv row {row_number} contains non-numeric value: {raw!r}"
                    ) from exc

            genes.append(gene)
            values_by_gene.append(values)
            seen_genes.add(gene)

    if not genes:
        raise ValueError("expression.tsv has no usable gene rows.")

    return genes, sample_ids, values_by_gene


def _load_groups(
    groups_path: Path, sample_ids: Sequence[str]
) -> Tuple[List[str], Dict[str, List[int]]]:
    lines: List[List[str]] = []
    with groups_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = [f for f in _split_fields(stripped) if f]
            if fields:
                lines.append(fields)

    if not lines:
        raise ValueError("groups file is empty.")

    one_column_mode = all(len(fields) == 1 for fields in lines)

    sample_to_cluster: Dict[str, str] = {}

    if one_column_mode:
        if len(lines) != len(sample_ids):
            raise ValueError(
                "groups file in one-column mode must have exactly one row per sample in expression.tsv "
                f"(expected {len(sample_ids)}, got {len(lines)})."
            )
        for idx, sample in enumerate(sample_ids):
            sample_to_cluster[sample] = lines[idx][0]
    else:
        for idx, fields in enumerate(lines):
            if len(fields) < 2:
                raise ValueError(
                    f"groups line {idx + 1} must have either 1 column or at least 2 columns."
                )

            sample = fields[0]
            cluster = fields[1]

            if idx == 0:
                s0 = sample.lower()
                c0 = cluster.lower()
                if s0 in {"sample", "cell", "column", "observation", "id"} and c0 in {
                    "group",
                    "cluster",
                    "cell_type",
                    "label",
                }:
                    continue

            if sample in sample_to_cluster:
                raise ValueError(f"Duplicate sample in groups file: {sample}")
            sample_to_cluster[sample] = cluster

    missing = [sample for sample in sample_ids if sample not in sample_to_cluster]
    if missing:
        preview = ", ".join(missing[:8])
        raise ValueError(f"groups file is missing assignments for samples: {preview}")

    cluster_to_indices: Dict[str, List[int]] = {}
    cluster_order: List[str] = []
    for idx, sample in enumerate(sample_ids):
        cluster = sample_to_cluster[sample]
        if cluster not in cluster_to_indices:
            cluster_to_indices[cluster] = []
            cluster_order.append(cluster)
        cluster_to_indices[cluster].append(idx)

    return cluster_order, cluster_to_indices


def _read_lineage_tree(lineage_path: Path) -> List[Tuple[str, str, float, float]]:
    edges: List[Tuple[str, str, float, float]] = []

    with lineage_path.open("r", encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            fields = [f for f in _split_fields(stripped) if f]
            if len(fields) < 4:
                raise ValueError(
                    f"lineage_tree line {line_number} must have 4 columns: child, parent, gain_rate, loss_rate."
                )

            child, parent = fields[0], fields[1]

            if line_number == 1:
                if child.lower() in {"child", "cluster", "cell"} and parent.lower() in {
                    "parent",
                    "ancestor",
                }:
                    continue

            try:
                gain = float(fields[2])
                loss = float(fields[3])
            except ValueError as exc:
                raise ValueError(
                    f"lineage_tree line {line_number} has non-numeric gain/loss values: {fields[2]!r}, {fields[3]!r}"
                ) from exc

            edges.append((child, parent, gain, loss))

    if not edges:
        raise ValueError("lineage_tree file has no usable rows.")

    return edges


def _validate_lineage_clusters(
    lineage_edges: Sequence[Tuple[str, str, float, float]], clusters: Sequence[str]
) -> None:
    present = set()
    for child, parent, _, _ in lineage_edges:
        present.add(child)
        present.add(parent)

    missing = [cluster for cluster in clusters if cluster not in present]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            "lineage_tree does not include all clusters present in groups/expression data. "
            f"Missing clusters: {joined}"
        )


def _write_cell_order(cell_order_path: Path, clusters: Sequence[str]) -> None:
    with cell_order_path.open("w", encoding="utf-8") as fh:
        for cluster in clusters:
            fh.write(f"{cluster}\n")


def _write_cluster_tables(
    *,
    genes: Sequence[str],
    sample_ids: Sequence[str],
    values_by_gene: Sequence[Sequence[float]],
    cluster_order: Sequence[str],
    cluster_to_indices: Dict[str, List[int]],
    runtime_dir: Path,
) -> Dict[str, Path]:
    cluster_tables: Dict[str, Path] = {}

    for cluster in cluster_order:
        indices = cluster_to_indices[cluster]
        if not indices:
            raise ValueError(
                f"Cluster {cluster!r} has no assigned samples in groups file."
            )

        table_path = runtime_dir / f"{cluster}.table"
        with table_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
            header = ["Gene"] + [sample_ids[idx] for idx in indices]
            writer.writerow(header)

            for gene, row_values in zip(genes, values_by_gene):
                out_gene = f"{gene}_{cluster}"
                out_values = [f"{row_values[idx]:.12g}" for idx in indices]
                writer.writerow([out_gene] + out_values)

        cluster_tables[cluster] = table_path

    return cluster_tables


def _write_orthogroup_files(
    *,
    genes: Sequence[str],
    cluster_order: Sequence[str],
    runtime_dir: Path,
) -> Tuple[Dict[str, int], Path, Path]:
    gene_to_og: Dict[str, int] = {}
    og_map_path = runtime_dir / "ogids.tsv"
    target_og_path = runtime_dir / "target_ogids.txt"

    with (
        og_map_path.open("w", encoding="utf-8", newline="") as og_fh,
        target_og_path.open("w", encoding="utf-8") as targets_fh,
    ):
        og_writer = csv.writer(og_fh, delimiter="\t", lineterminator="\n")
        og_writer.writerow(["Gene_OGID", "NAME"])

        for idx, gene in enumerate(genes, start=1):
            gene_to_og[gene] = idx
            members = [f"{gene}_{cluster}" for cluster in cluster_order]
            og_writer.writerow([f"OG{idx}_1", ",".join(members)])
            targets_fh.write(f"{idx}\n")

    return gene_to_og, og_map_path, target_og_path


def _parse_ogid(token: str) -> Optional[int]:
    clean = token.strip()
    if not clean:
        return None

    if clean.isdigit():
        return int(clean)

    match = re.match(r"^OG(\d+)(?:_.*)?$", clean)
    if match is None:
        return None

    return int(match.group(1))


def _normalize_gene_token(token: str, clusters: Sequence[str]) -> str:
    for cluster in clusters:
        suffix = f"_{cluster}"
        if token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _write_tf_og_file(
    *,
    tf_input_path: Path,
    gene_to_og: Dict[str, int],
    cluster_order: Sequence[str],
    runtime_dir: Path,
) -> Path:
    og_ids = set()

    with tf_input_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            token = raw_line.strip()
            if not token or token.startswith("#"):
                continue

            parsed_og = _parse_ogid(token)
            if parsed_og is not None:
                if 1 <= parsed_og <= len(gene_to_og):
                    og_ids.add(parsed_og)
                else:
                    print(
                        f"Warning: tf_list OG id out of range and ignored: {parsed_og}",
                        file=sys.stderr,
                    )
                continue

            normalized = _normalize_gene_token(token, cluster_order)
            if normalized in gene_to_og:
                og_ids.add(gene_to_og[normalized])
            else:
                print(
                    f"Warning: tf_list entry not found in expression genes: {token}",
                    file=sys.stderr,
                )

    if not og_ids:
        raise ValueError(
            "No valid TF entries found in tf_list after mapping to expression genes."
        )

    tf_og_path = runtime_dir / "tf_ogids.txt"
    with tf_og_path.open("w", encoding="utf-8") as fh:
        for og_id in sorted(og_ids):
            fh.write(f"{og_id}\n")

    return tf_og_path


def _load_prior_rows_by_group(
    prior_path: Path,
) -> Dict[str, List[Tuple[str, str, float]]]:
    rows_by_group: Dict[str, List[Tuple[str, str, float]]] = {}

    with prior_path.open("r", encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            fields = [f for f in _split_fields(stripped) if f]
            if len(fields) < 4:
                continue

            group, source, target, raw_score = fields[0], fields[1], fields[2], fields[3]

            try:
                score = float(raw_score)
            except ValueError:
                if line_number == 1 and group.lower() == "group":
                    continue
                raise ValueError(
                    "Invalid score in prior_grn_by_group at "
                    f"line {line_number}: {raw_score!r}"
                )

            rows_by_group.setdefault(group, []).append((source, target, score))

    return rows_by_group


def _write_motif_files(
    *,
    prior_path: Optional[Path],
    q_value: float,
    cluster_order: Sequence[str],
    gene_to_og: Dict[str, int],
    runtime_dir: Path,
) -> Dict[str, Path]:
    motif_paths: Dict[str, Path] = {}

    if prior_path is None:
        if q_value > 0:
            raise FileNotFoundError(
                "q > 0 requires prior_grn_by_group, but /io/extra/prior_grn_by_group.tsv was not provided."
            )

        for cluster in cluster_order:
            motif_path = runtime_dir / f"{cluster}_prior.tsv"
            motif_path.touch(exist_ok=True)
            motif_paths[cluster] = motif_path
        return motif_paths

    prior_rows_by_group = _load_prior_rows_by_group(prior_path)
    if not prior_rows_by_group:
        print(
            "Warning: prior_grn_by_group has no usable rows; using empty per-cluster motif files.",
            file=sys.stderr,
        )

    unknown_groups = sorted(set(prior_rows_by_group).difference(cluster_order))
    if unknown_groups:
        joined = ", ".join(unknown_groups[:8])
        print(
            "Warning: prior_grn_by_group contains groups not present in groups.tsv "
            f"and they will be ignored: {joined}",
            file=sys.stderr,
        )

    for cluster in cluster_order:
        motif_path = runtime_dir / f"{cluster}_prior.tsv"
        cluster_rows = prior_rows_by_group.get(cluster, [])
        if q_value > 0 and not cluster_rows:
            print(
                f"Warning: prior_grn_by_group has no rows for cluster '{cluster}'; using empty motif file.",
                file=sys.stderr,
            )
        with motif_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t", lineterminator="\n")

            for src, tgt, score in cluster_rows:
                src_gene = _normalize_gene_token(src, cluster_order)
                tgt_gene = _normalize_gene_token(tgt, cluster_order)

                if src_gene not in gene_to_og or tgt_gene not in gene_to_og:
                    continue

                writer.writerow(
                    [f"{src_gene}_{cluster}", f"{tgt_gene}_{cluster}", f"{score:.12g}"]
                )

        motif_paths[cluster] = motif_path

    return motif_paths


def _strip_cluster_suffix(token: str, cluster: str) -> str:
    suffix = f"_{cluster}"
    if token.endswith(suffix):
        return token[: -len(suffix)]
    return token


def _write_runtime_config(
    *,
    cluster_order: Sequence[str],
    cluster_tables: Dict[str, Path],
    motif_paths: Dict[str, Path],
    raw_output_root: Path,
    runtime_dir: Path,
) -> Path:
    runtime_config_path = runtime_dir / "scmtni_config.tsv"
    with runtime_config_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        for cluster in cluster_order:
            writer.writerow(
                [
                    cluster,
                    str(cluster_tables[cluster]),
                    str(raw_output_root / cluster),
                    "NA",
                    "NA",
                    str(motif_paths[cluster]),
                ]
            )
    return runtime_config_path


def _run_scmtni(
    *,
    runtime_config_path: Path,
    tf_og_path: Path,
    target_og_path: Path,
    lineage_tree_path: Optional[Path],
    og_map_path: Path,
    cell_order_path: Path,
    params: Dict[str, Any],
    threads: int,
    output_dir: Path,
    progress_path: Path,
) -> None:
    cmd: List[str] = [
        str(SCMTNI_BIN),
        "-f",
        str(runtime_config_path),
        "-x",
        str(params["x"]),
        "-l",
        str(tf_og_path),
        "-n",
        str(target_og_path),
        "-m",
        str(og_map_path),
        "-s",
        str(cell_order_path),
        "-p",
        str(params["p"]),
        "-b",
        str(params["b"]),
        "-q",
        str(params["q"]),
    ]

    if params["indep"]:
        cmd.extend(["-i", "yes"])
    else:
        if lineage_tree_path is None:
            raise FileNotFoundError(
                "Required extra input 'lineage_tree' not found for indep=false. "
                "Expected file: lineage_tree.tsv"
            )
        cmd.extend(["-d", str(lineage_tree_path)])

    if params["split_genes"]:
        cmd.extend(["-c", "yes"])

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)

    log_path = output_dir / "scmtni.log"
    with log_path.open("w", encoding="utf-8") as log_fh:
        process = subprocess.Popen(
            cmd,
            cwd=str(output_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        if process.stdout is None:
            raise RuntimeError("Failed to capture scMTNI stdout stream.")

        last_iteration = -1
        saw_inference = False

        for line in process.stdout:
            log_fh.write(line)

            if not saw_inference:
                saw_inference = True
                _write_progress(
                    progress_path,
                    status="running",
                    percent=12,
                    phase="inference",
                    message="Running scMTNI optimization",
                )

            match = ITERATION_RE.search(line)
            if match is None:
                continue

            iteration = int(match.group(1))
            if iteration <= last_iteration:
                continue

            last_iteration = iteration
            completed = min(iteration + 1, MAX_ITERATIONS_PROGRESS)
            percent = 10 + int((completed / MAX_ITERATIONS_PROGRESS) * 80)
            _write_progress(
                progress_path,
                status="running",
                percent=min(90, percent),
                phase="inference",
                message="Running scMTNI optimization",
                completed=completed,
                total=MAX_ITERATIONS_PROGRESS,
            )

        return_code = process.wait()

    if return_code != 0:
        logs_tail = _tail_text(log_path)
        if logs_tail:
            raise RuntimeError(
                f"scMTNI failed with exit code {return_code}.\n\nlog tail:\n{logs_tail}"
            )
        raise RuntimeError(f"scMTNI failed with exit code {return_code}.")


def _collect_network_rows(
    *, raw_output_root: Path, clusters: Sequence[str], max_regulators: int
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for cluster in clusters:
        cluster_path = (
            raw_output_root / cluster / "fold0" / f"var_mb_pw_k{max_regulators}.txt"
        )
        if not cluster_path.exists():
            raise FileNotFoundError(
                f"Expected cluster output not found: {cluster_path}"
            )

        with cluster_path.open("r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                parts = stripped.split("\t")
                if len(parts) < 3:
                    continue

                source = parts[0].strip()
                target = parts[1].strip()
                raw_score = parts[2].strip()

                if not source or not target:
                    continue

                try:
                    coeff = float(raw_score)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid coefficient at {cluster_path}:{line_number}: {raw_score!r}"
                    ) from exc

                rows.append(
                    {
                        "source": _strip_cluster_suffix(source, cluster),
                        "target": _strip_cluster_suffix(target, cluster),
                        "score": abs(coeff),
                        "sign": "?",
                        "evidence": "association",
                        "context": f"group:{cluster}",
                    }
                )

    rows = [row for row in rows if row["score"] != 0.0]

    rows.sort(key=lambda row: row["score"], reverse=True)
    return rows


def _write_network_csv(network_path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    with network_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["source", "target", "score", "sign", "evidence", "context"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--extra", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    _validate_inputs(args.input, args.params, args.extra, args.threads)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    progress_path = args.output_dir / "progress.json"
    _write_progress(
        progress_path,
        status="running",
        percent=0,
        phase="init",
        message="Initializing",
    )

    try:
        raw_params = _load_params(args.params)
        params = _resolve_params(raw_params)

        groups_path = _require_extra_file(args.extra, "groups.tsv", "groups")
        tf_path = _require_extra_file(args.extra, "tf_list.txt", "tf_list")
        lineage_tree_path = _optional_extra_file(args.extra, "lineage_tree.tsv")
        prior_path = _optional_extra_file(args.extra, "prior_grn_by_group.tsv")

        _write_progress(
            progress_path,
            status="running",
            percent=5,
            phase="load_input",
            message="Loading expression and extra inputs",
        )

        genes, sample_ids, values_by_gene = _read_expression_tsv(args.input)
        cluster_order, cluster_to_indices = _load_groups(groups_path, sample_ids)

        if params["indep"] and len(cluster_order) != 1:
            raise ValueError(
                "indep=true expects exactly one cluster in groups. "
                f"Found {len(cluster_order)} clusters: {cluster_order}"
            )

        lineage_edges: Optional[List[Tuple[str, str, float, float]]] = None
        if not params["indep"]:
            if lineage_tree_path is None:
                raise FileNotFoundError(
                    "Required extra input 'lineage_tree' not found for indep=false. "
                    "Expected file: lineage_tree.tsv"
                )
            lineage_edges = _read_lineage_tree(lineage_tree_path)
            _validate_lineage_clusters(lineage_edges, cluster_order)

        runtime_dir = args.output_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        raw_output_root = args.output_dir / "raw"
        raw_output_root.mkdir(parents=True, exist_ok=True)

        cluster_tables = _write_cluster_tables(
            genes=genes,
            sample_ids=sample_ids,
            values_by_gene=values_by_gene,
            cluster_order=cluster_order,
            cluster_to_indices=cluster_to_indices,
            runtime_dir=runtime_dir,
        )

        gene_to_og, og_map_path, target_og_path = _write_orthogroup_files(
            genes=genes,
            cluster_order=cluster_order,
            runtime_dir=runtime_dir,
        )

        tf_og_path = _write_tf_og_file(
            tf_input_path=tf_path,
            gene_to_og=gene_to_og,
            cluster_order=cluster_order,
            runtime_dir=runtime_dir,
        )

        motif_paths = _write_motif_files(
            prior_path=prior_path,
            q_value=params["q"],
            cluster_order=cluster_order,
            gene_to_og=gene_to_og,
            runtime_dir=runtime_dir,
        )

        cell_order_path = runtime_dir / "cell_order.txt"
        _write_cell_order(cell_order_path, cluster_order)

        runtime_config_path = _write_runtime_config(
            cluster_order=cluster_order,
            cluster_tables=cluster_tables,
            motif_paths=motif_paths,
            raw_output_root=raw_output_root,
            runtime_dir=runtime_dir,
        )

        _write_progress(
            progress_path,
            status="running",
            percent=10,
            phase="inference",
            message="Starting scMTNI inference",
        )

        _run_scmtni(
            runtime_config_path=runtime_config_path,
            tf_og_path=tf_og_path,
            target_og_path=target_og_path,
            lineage_tree_path=lineage_tree_path,
            og_map_path=og_map_path,
            cell_order_path=cell_order_path,
            params=params,
            threads=args.threads,
            output_dir=args.output_dir,
            progress_path=progress_path,
        )

        _write_progress(
            progress_path,
            status="running",
            percent=96,
            phase="write_output",
            message="Writing network.csv",
        )

        rows = _collect_network_rows(
            raw_output_root=raw_output_root,
            clusters=cluster_order,
            max_regulators=params["x"],
        )
        _write_network_csv(args.output_dir / "network.csv", rows)

        _write_progress(
            progress_path,
            status="completed",
            percent=100,
            phase="done",
            message="Inference finished",
            completed=len(rows),
            total=len(rows),
        )
    except Exception as exc:
        _write_progress(
            progress_path,
            status="failed",
            percent=100,
            phase="failed",
            message="Inference failed",
            error=str(exc),
        )
        raise


if __name__ == "__main__":
    main()
