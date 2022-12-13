from pathlib import Path
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
        username: str = typer.Option(..., help="Synapse account username"),
        password: str = typer.Option(..., help="Synapse account password"),
    ):

    syn = synapseclient.Synapse()
    syn.login(username, password)

    if category.name == "ExpressionData":
        syn_exp_ids = ["syn2853601", "syn2853602", "syn2853603"]

        for id in syn_exp_ids:
            zip_metadata = syn.get(id, downloadLocation=output_folder)
            
            zip_data = zipfile.ZipFile(zip_metadata.path)
            zip_infos = zip_data.infolist()

            for f in zip_infos:
                if f.filename.endswith("-trajectories.tsv"):
                    f.filename = Path(f.filename).name
                    zip_data.extract(f, output_folder)
                    tsv_dir = f'{output_folder}/{f.filename}'

                    df = pd.read_table(tsv_dir, sep="\t")
                    df.drop("Time", inplace=True, axis=1)
                    net_exp = df.T

                    nrow, ncol = net_exp.shape
                    net_exp.columns = [f'V{str(i)}' for i in range(1, ncol + 1)]
                    net_exp.index = [f'G{str(i)}' for i in range(1, nrow + 1)]

                    net_exp.to_csv(f'{output_folder}/{Path(f.filename).stem}_exp.csv', quoting=2)
                    Path(tsv_dir).unlink()
            
            Path(zip_metadata.path).unlink()
        
    elif category.name == "GoldStandard":
        syn_gs_ids = ["syn2853606", "syn2853607", "syn2853608", "syn2853609", "syn2853610", "syn2853611", "syn2853612", "syn2853613", "syn2853614", "syn2853615", "syn2853616", "syn2853617", "syn2853618", "syn2853619", "syn2853620"]

        for id in syn_gs_ids:
            list_gs_metadata = syn.get(id, downloadLocation=output_folder)
            list_gs = pd.read_table(list_gs_metadata.path, sep="\t")

            list_genes = list(set(list_gs.iloc[:, [0,1]].stack()))
            max_ind = max([int(g.replace('G', '')) for g in list_genes])
            genes = [f'G{str(i)}' for i in range(1, max_ind + 1)]

            net_gs = pd.DataFrame(0, columns=genes, index=genes)
            for ind in list_gs.index[list_gs.iloc[:, 2] == 1]:
                net_gs.loc[list_gs.iloc[ind, 0], list_gs.iloc[ind, 1]] = 1

            net_gs.to_csv(f'{output_folder}/{Path(list_gs_metadata.path).stem}_gs.csv', quoting=2)
            Path(list_gs_metadata.path).unlink()
    
    elif category.name == "EvaluationData":
        syn_eval_ids = ["syn4558474", "syn4558475", "syn4558476", "syn4558477", "syn4558478", "syn4558479", "syn4558480", "syn4558481", "syn4558482", "syn4558483", "syn4558484", "syn4558485", "syn4558486", "syn4558487", "syn4558488"]
        syn_gs_ids = ["syn2853606", "syn2853607", "syn2853608", "syn2853609", "syn2853610", "syn2853611", "syn2853612", "syn2853613", "syn2853614", "syn2853615", "syn2853616", "syn2853617", "syn2853618", "syn2853619", "syn2853620"]

        for id in syn_eval_ids + syn_gs_ids:
            syn.get(id, downloadLocation = output_folder)


if __name__ == "__main__":
    typer.run(dream3)