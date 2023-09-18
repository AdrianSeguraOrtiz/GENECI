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


def dream5(
        category: Category = typer.Option(..., help="Type of data to be downloaded"),
        output_folder: str = typer.Option(..., help="Path to output folder"),
        username: str = typer.Option(..., help="Synapse account username"),
        password: str = typer.Option(..., help="Synapse account password"),
    ):

    syn = synapseclient.Synapse()
    syn.login(username, password)

    file_ids = ["net1", "net2", "net3", "net4"]

    if category.name == "ExpressionData":
        syn_exp_ids = ["syn2787226", "syn2787230", "syn2787234", "syn2787238"]
        for i in range(len(syn_exp_ids)):
            net_exp_metadata = syn.get(syn_exp_ids[i], downloadLocation=output_folder)
            net_exp = pd.read_table(net_exp_metadata.path, sep="\t").T

            nrow, ncol = net_exp.shape
            net_exp.columns = [f'V{str(i)}' for i in range(1, ncol + 1)]
            net_exp.index = [f'G{str(i)}' for i in range(1, nrow + 1)]

            net_exp.to_csv(f'{output_folder}/{file_ids[i]}_exp.csv', quoting=2)
            Path(net_exp_metadata.path).unlink()

    elif category.name == "GoldStandard":
        syn_gs_ids = ["syn2787240", "syn2787242", "syn2787243", "syn2787244"]
        for i in range(len(syn_gs_ids)):
            list_gs_metadata = syn.get(syn_gs_ids[i], downloadLocation=output_folder)
            list_gs = pd.read_table(list_gs_metadata.path, sep="\t")

            list_genes = list(set(list_gs.iloc[:, [0,1]].stack()))
            max_ind = max([int(g.replace('G', '')) for g in list_genes])
            genes = [f'G{str(i)}' for i in range(1, max_ind + 1)]

            net_gs = pd.DataFrame(0, columns=genes, index=genes)
            for ind in list_gs.index[list_gs.iloc[:, 2] == 1]:
                net_gs.loc[list_gs.iloc[ind, 0], list_gs.iloc[ind, 1]] = 1

            net_gs.to_csv(f'{output_folder}/{file_ids[i]}_gs.csv', quoting=2)
            Path(list_gs_metadata.path).unlink()

    elif category.name == "EvaluationData":
        zip_metadata = syn.get("syn2787219", downloadLocation=output_folder)
        
        zip_data = zipfile.ZipFile(zip_metadata.path)
        zip_infos = zip_data.infolist()

        for f in zip_infos:
            if not f.filename.startswith("__MACOSX") and (f.filename.endswith(".mat") or f.filename.endswith(".tsv")):
                f.filename = Path(f.filename).name
                zip_data.extract(f, output_folder)
        
        Path(zip_metadata.path).unlink()


if __name__ == "__main__":
    typer.run(dream5)