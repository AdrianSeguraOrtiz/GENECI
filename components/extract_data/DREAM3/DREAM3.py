from pathlib import Path
import os
import pandas as pd
import typer
import synapseclient
from enum import Enum
import zipfile


class Category(str, Enum):
    ExpressionData = "ExpressionData"
    GoldStandard = "GoldStandard"
    EvaluationData = "EvaluationData"


def dream3(
    category: Category = typer.Option(..., help="Type of data to be downloaded"),
    output_folder: str = typer.Option(..., help="Path to output folder"),
):
    """
    Download DREAM3 datasets from Synapse using a Personal Access Token (PAT)
    provided via the SYNAPSE_AUTH_TOKEN environment variable.
    """
    token = os.getenv("SYNAPSE_AUTH_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing SYNAPSE_AUTH_TOKEN environment variable. "
            "Provide it when running the container."
        )

    syn = synapseclient.Synapse()
    syn.login(authToken=token, silent=True)

    output_folder = str(output_folder)  # ensure string for syn.get paths

    if category.name == "ExpressionData":
        syn_exp_ids = ["syn2853601", "syn2853602", "syn2853603"]

        for id in syn_exp_ids:
            zip_metadata = syn.get(id, downloadLocation=output_folder)

            with zipfile.ZipFile(zip_metadata.path) as zip_data:
                for f in zip_data.infolist():
                    if f.filename.endswith("-trajectories.tsv"):
                        # Evitar path traversal: quedarnos con el nombre base
                        f.filename = Path(f.filename).name
                        zip_data.extract(f, output_folder)
                        tsv_path = Path(output_folder) / f.filename

                        df = pd.read_table(tsv_path, sep="\t")
                        if "Time" in df.columns:
                            df.drop("Time", inplace=True, axis=1)
                        net_exp = df.T

                        nrow, ncol = net_exp.shape
                        net_exp.columns = [f"V{i}" for i in range(1, ncol + 1)]
                        net_exp.index = [f"G{i}" for i in range(1, nrow + 1)]

                        net_exp.to_csv(
                            Path(output_folder) / f"{tsv_path.stem}_exp.csv",
                            quoting=2,
                        )
                        tsv_path.unlink(missing_ok=True)

            Path(zip_metadata.path).unlink(missing_ok=True)

    elif category.name == "GoldStandard":
        syn_gs_ids = [
            "syn2853606", "syn2853607", "syn2853608", "syn2853609", "syn2853610",
            "syn2853611", "syn2853612", "syn2853613", "syn2853614", "syn2853615",
            "syn2853616", "syn2853617", "syn2853618", "syn2853619", "syn2853620",
        ]

        for id in syn_gs_ids:
            list_gs_metadata = syn.get(id, downloadLocation=output_folder)
            list_gs = pd.read_table(list_gs_metadata.path, sep="\t")

            list_genes = list(set(list_gs.iloc[:, [0, 1]].stack()))
            max_ind = max(int(g.replace("G", "")) for g in list_genes)
            genes = [f"G{i}" for i in range(1, max_ind + 1)]

            net_gs = pd.DataFrame(0, columns=genes, index=genes)
            for ind in list_gs.index[list_gs.iloc[:, 2] == 1]:
                net_gs.loc[list_gs.iloc[ind, 0], list_gs.iloc[ind, 1]] = 1

            out_csv = Path(output_folder) / f"{Path(list_gs_metadata.path).stem}_gs.csv"
            net_gs.to_csv(out_csv, quoting=2)
            Path(list_gs_metadata.path).unlink(missing_ok=True)

    elif category.name == "EvaluationData":
        syn_eval_ids = [
            "syn4558474", "syn4558475", "syn4558476", "syn4558477", "syn4558478",
            "syn4558479", "syn4558480", "syn4558481", "syn4558482", "syn4558483",
            "syn4558484", "syn4558485", "syn4558486", "syn4558487", "syn4558488",
        ]
        syn_gs_ids = [
            "syn2853606", "syn2853607", "syn2853608", "syn2853609", "syn2853610",
            "syn2853611", "syn2853612", "syn2853613", "syn2853614", "syn2853615",
            "syn2853616", "syn2853617", "syn2853618", "syn2853619", "syn2853620",
        ]

        for id in syn_eval_ids + syn_gs_ids:
            syn.get(id, downloadLocation=output_folder)


if __name__ == "__main__":
    typer.run(dream3)
