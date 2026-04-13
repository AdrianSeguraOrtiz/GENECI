"""Shared Arboreto helpers for GENIE3/GRNBoost2 wrappers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
from arboreto.algo import _prepare_input
from arboreto.core import create_graph
from distributed import Client, LocalCluster, as_completed


def load_tf_list(extra_dir: Path) -> Optional[list[str]]:
    tf_path = extra_dir / "tf_list.txt"
    if not tf_path.exists():
        return None

    tfs: list[str] = []
    for line in tf_path.read_text(encoding="utf-8").splitlines():
        token = line.strip()
        if token and not token.startswith("#"):
            tfs.append(token)
    return tfs or None


def read_expression_tsv(expr_path: Path) -> pd.DataFrame:
    df = pd.read_csv(expr_path, sep="\t", header=0)
    if df.shape[1] < 2:
        raise ValueError(
            "expression.tsv must have at least 2 columns: gene + >=1 observation."
        )

    gene_col = df.columns[0]
    if df[gene_col].duplicated().any():
        df = df.drop_duplicates(subset=[gene_col], keep="first")

    genes = df[gene_col].astype(str).tolist()
    numeric = df.set_index(gene_col).apply(pd.to_numeric, errors="raise")

    obs_x_genes = numeric.T
    obs_x_genes.columns = genes
    return obs_x_genes


def infer_arboreto_local(
    *,
    expression_data: pd.DataFrame,
    tf_names: Any,
    regressor_type: str,
    regressor_kwargs: dict[str, Any],
    limit: Optional[int],
    seed: Optional[int],
    threads: int,
    on_partition_complete: Optional[Callable[[int, int], None]] = None,
) -> pd.DataFrame:
    cluster = LocalCluster(
        n_workers=threads,
        threads_per_worker=1,
        processes=True,
        diagnostics_port=None,
    )
    client = Client(cluster)
    try:
        expression_matrix, gene_names, parsed_tf_names = _prepare_input(
            expression_data, gene_names=None, tf_names=tf_names
        )
        links_graph, _ = create_graph(
            expression_matrix=expression_matrix,
            gene_names=gene_names,
            tf_names=parsed_tf_names,
            regressor_type=regressor_type,
            regressor_kwargs=regressor_kwargs,
            client=client,
            target_genes="all",
            limit=limit,
            include_meta=True,
            seed=seed,
        )

        delayed_parts = links_graph.to_delayed()
        futures = client.compute(delayed_parts)

        total = len(futures)
        completed = 0
        parts: list[pd.DataFrame] = []

        for future, part in as_completed(futures, with_results=True):
            _ = future
            parts.append(part)
            completed += 1
            if on_partition_complete is not None:
                on_partition_complete(completed, total)

        if not parts:
            return pd.DataFrame(columns=["TF", "target", "importance"])
        return pd.concat(parts, ignore_index=True).sort_values(
            by="importance", ascending=False
        )
    finally:
        client.close()
        cluster.close()


def validate_inferred_columns(inferred: pd.DataFrame) -> None:
    required = {"TF", "target", "importance"}
    if not required.issubset(set(inferred.columns)):
        raise ValueError(
            f"Unexpected output columns from arboreto: {list(inferred.columns)}"
        )


def to_standard_network(inferred: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "source": inferred["TF"].astype(str),
            "target": inferred["target"].astype(str),
            "score": pd.to_numeric(inferred["importance"], errors="raise"),
            "sign": ["?"] * len(inferred),
            "evidence": ["association"] * len(inferred),
            "context": ["global"] * len(inferred),
        }
    )
    return out.loc[out["score"] != 0].reset_index(drop=True)
