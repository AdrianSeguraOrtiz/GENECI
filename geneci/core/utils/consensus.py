import pandas as pd


def simple_consensus(
    files: list[str],
    method: str,
    output_file: str,
):
    """Apply simple consensus methods over multiple confidence-list files."""
    dfs = [
        pd.read_csv(f, header=None, names=["source", "target", f"confidence{i}"])
        for i, f in enumerate(files)
    ]

    res = dfs.pop(0)
    for df in dfs:
        res = pd.merge(res, df, on=["source", "target"], how="outer")
    res = res.fillna(0)

    confidence_cols = [col for col in res.columns if col.startswith("confidence")]

    if method == "MeanWeights":
        res["score"] = res[confidence_cols].mean(axis=1)

    elif method == "MedianWeights":
        res["score"] = res[confidence_cols].median(axis=1)

    elif method == "RankAverage":
        for col in confidence_cols:
            res[col + "_rank"] = res[col].rank(method="average", ascending=False)
        rank_cols = [col + "_rank" for col in confidence_cols]
        res["avg_rank"] = res[rank_cols].mean(axis=1)
        res["score"] = 1 - (res["avg_rank"] - res["avg_rank"].min()) / (
            res["avg_rank"].max() - res["avg_rank"].min()
        )

    elif method == "BayesianFusion":
        alpha_prior = 1
        beta_prior = 1
        res["alpha"] = alpha_prior + res[confidence_cols].sum(axis=1)
        res["beta"] = beta_prior + (1 - res[confidence_cols]).sum(axis=1)
        res["score"] = res["alpha"] / (res["alpha"] + res["beta"])

    else:
        raise ValueError(f"Unsupported method: {method}")

    res[["source", "target", "score"]].to_csv(output_file, header=False, index=False)


__all__ = ["simple_consensus"]
