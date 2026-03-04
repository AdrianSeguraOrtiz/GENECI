from pathlib import Path

import pandas as pd


def get_gene_names_from_conf_list(conf_list):
    """Obtain the set of gene names from a confidence list CSV."""
    gene_list = set()
    with open(conf_list, "r") as f:
        for row in f:
            row_list = row.split(",")
            gene_list.add(row_list[0])
            gene_list.add(row_list[1])
    return gene_list


def get_gene_names_from_expression_file(expression_file):
    """Obtain ordered gene names from an expression file."""
    with open(expression_file, "r") as f:
        gene_list = [row.split(",")[0].replace('"', "") for row in f]
        if gene_list[0] == "":
            del gene_list[0]
    return gene_list


def get_weights(filename):
    """Get file names and corresponding weights from a VAR/FUN-like CSV."""
    with open(filename, "r") as f:
        lines = f.readlines()

    filenames = lines[0].replace("\n", "").split(",")
    del lines[0]

    weights = []
    for line in lines:
        solution = [float(w) for w in line.split(",")]
        weights.append(solution)

    return (filenames, weights)


def write_evaluation_csv(
    output_path, sorted_idx, confidence_list, objective_labels, weights, df
):
    """Write evaluation dataframe with objective and metric summaries."""
    df["aupr_scaled"] = (df["aupr"] - min(df["aupr"])) / (
        max(df["aupr"]) - min(df["aupr"])
    )
    df["auroc_scaled"] = (df["auroc"] - min(df["auroc"])) / (
        max(df["auroc"]) - min(df["auroc"])
    )
    df["mean_scaled"] = (df["aupr_scaled"] + df["auroc_scaled"]) / 2

    with open(output_path, "w") as f:
        f.write(
            f"Weights{',' * len(confidence_list)}Fitness Values{',' * len(objective_labels)}Evaluation Values,,,,,\n"
        )
        f.write(
            f"{','.join([Path(f).name for f in confidence_list])},{','.join(objective_labels)},Accuracy Mean,AUROC,AUPR,AUPR Scaled,AUROC Scaled,Mean Scaled\n"
        )
        for i in sorted_idx:
            f.write(
                f"{','.join([str(w) for w in weights[i]])},{','.join([str(df[lab][i]) for lab in objective_labels])},{str(df['acc_mean'][i])},{str(df['auroc'][i])},{str(df['aupr'][i])},{str(df['aupr_scaled'][i])},{str(df['auroc_scaled'][i])},{str(df['mean_scaled'][i])}\n"
            )


def get_expression_data_from_module(
    expression_data_file: str, module_file: str, output_file: str
):
    """Extract a subset of expression data containing genes from a given module."""
    module_df = pd.read_csv(module_file)
    genes = set(module_df.iloc[:, 0]) | set(module_df.iloc[:, 1])

    expression_df = pd.read_csv(expression_data_file, index_col=0)
    filtered_df = expression_df.loc[expression_df.index.intersection(genes)]
    filtered_df.to_csv(output_file)

    return filtered_df


__all__ = [
    "get_gene_names_from_conf_list",
    "get_gene_names_from_expression_file",
    "get_weights",
    "write_evaluation_csv",
    "get_expression_data_from_module",
]
