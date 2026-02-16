import csv
import shutil
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from geneci.config import tag, temp_folder_str
from geneci.core.utils.docker import (
    available_images,
    client,
    get_volume,
    wait_and_close_container,
)
from geneci.core.utils.io import get_gene_names_from_conf_list
from geneci.enums import Database, Perturbation, Topology


def expression_data(
    database: Optional[List[Database]],
    output_dir: Path = Path("./input_data"),
    username: str = None,
    password: str = None,
):
    """Download benchmark expression datasets."""

    if (Database.DREAM3 in database or Database.DREAM5 in database) and (
        not username or not password
    ):
        print(
            "You must enter your Synapse credentials in order to download some of the selected data."
        )
        raise ValueError("Missing Synapse credentials.")

    for db in database:
        output_folder = Path(f"./{output_dir}/{db.value}/EXP/")
        output_folder.mkdir(exist_ok=True, parents=True)

        print(f"\n Extracting expression data from {db.value}")

        if db == Database.DREAM3:
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category ExpressionData --output-folder ./EXP/  --username {username} --password {password}"

        elif db == Database.DREAM4:
            image = f"adriansegura99/geneci_extract-data_dream4-expgs:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = "ExpressionData ./EXP/ "

        elif db == Database.DREAM5:
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category ExpressionData --output-folder ./EXP/  --username {username} --password {password}"

        elif db == Database.IRMA:
            image = f"adriansegura99/geneci_extract-data_irma:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = "ExpressionData ./EXP/ "

        else:
            image = f"adriansegura99/geneci_extract-data_grndata:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"{db.value} ExpressionData ./EXP/ "

        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        logs, _ = wait_and_close_container(container)
        print(logs)


def generate_from_scratch(
    topology: Topology,
    network_size: int,
    perturbation: Perturbation,
    output_dir: Path = Path("./input_data"),
):
    """Simulate expression data from scratch with SysGenSIM."""

    print(
        f"\n Simulate network of {network_size} genes with {topology.value} topology applying {perturbation.value} perturbation."
    )

    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    image = f"adriansegura99/geneci_generate-data_sysgensim:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str, True),
        command=f"'' {topology.value} {network_size} {perturbation.value} /tmp/.X11-unix/{temp_folder_str}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    exp_file = next(tmp_folder.glob("*_gene_expression_matrix.tsv"))
    top_file = next(tmp_folder.glob("*_topological_properties.tsv"))
    exp_df = pd.read_csv(exp_file, sep="\t")
    top_df = pd.read_csv(top_file, sep="\t")
    genes = top_df.iloc[:, 0]
    completed_exp_df = pd.concat([genes, exp_df.iloc[:, :-1]], join="inner", axis=1)

    edge_file = next(tmp_folder.glob("*_edge_list.tsv"))
    edge_list = pd.read_csv(edge_file, sep="\t", names=["source", "target", "weight"])
    edge_df = (
        edge_list.pivot(index="source", columns="target", values="weight")
        .reindex(columns=genes, index=genes)
        .fillna(0)
        .abs()
        .astype(int)
    )

    output_folder_exp = Path(f"./{output_dir}/simulated_scratch/EXP/")
    output_folder_exp.mkdir(exist_ok=True, parents=True)
    output_folder_gs = Path(f"./{output_dir}/simulated_scratch/GS/")
    output_folder_gs.mkdir(exist_ok=True, parents=True)

    name = f"sim_{topology.value}_size-{network_size}_{perturbation.value}"
    completed_exp_df.to_csv(
        f"{output_folder_exp}/{name}_exp.csv", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    edge_df.to_csv(f"{output_folder_gs}/{name}_gs.csv", quoting=csv.QUOTE_NONNUMERIC)

    shutil.rmtree(temp_folder_str)


def generate_from_real_network(
    real_list_of_links: Path,
    perturbation: Perturbation,
    output_dir: Path = Path("./input_data"),
):
    """Simulate expression data from a real-world network with SysGenSIM."""

    print(
        f"\n Simulate expression data from {real_list_of_links.name} real-world network applying {perturbation.value} perturbation."
    )

    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    gene_names = list(get_gene_names_from_conf_list(real_list_of_links))
    tmp_gene_names = ["G" + str(i) for i in range(1, len(gene_names) + 1)]
    map_names = {gene_names[i]: tmp_gene_names[i] for i in range(len(gene_names))}
    df_links = pd.read_csv(
        real_list_of_links, header=None, names=["Source", "Target", "Conf"]
    )
    df_links = df_links.replace({"Source": map_names, "Target": map_names})

    tmp_network_dir = f"./{temp_folder_str}/{Path(real_list_of_links).stem}.tsv"
    df_links.to_csv(tmp_network_dir, sep="\t", header=False, index=False)

    image = f"adriansegura99/geneci_generate-data_sysgensim:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str, True),
        command=f"/tmp/.X11-unix/{tmp_network_dir} '' '' {perturbation.value} /tmp/.X11-unix/{temp_folder_str}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    exp_file = next(tmp_folder.glob("*_gene_expression_matrix.tsv"))
    top_file = next(tmp_folder.glob("*_topological_properties.tsv"))
    exp_df = pd.read_csv(exp_file, sep="\t")
    top_df = pd.read_csv(top_file, sep="\t")
    tmp_genes = top_df.iloc[:, 0]
    map_tmp_names = {tmp_gene_names[i]: gene_names[i] for i in range(len(tmp_gene_names))}
    genes = [map_tmp_names[key] for key in tmp_genes]
    completed_exp_df = pd.concat(
        [pd.Series(genes), exp_df.iloc[:, :-1]], join="inner", axis=1
    )

    for col in completed_exp_df.columns[1:]:
        zscore = np.abs(stats.zscore(completed_exp_df[col]))
        outliers = zscore > 3
        upper_limit = np.max(completed_exp_df.loc[zscore <= 3, col])
        completed_exp_df.loc[outliers, col] = upper_limit

    edge_file = next(tmp_folder.glob("*_edge_list.tsv"))
    edge_list = pd.read_csv(edge_file, sep="\t", names=["source", "target", "weight"])
    edge_df = (
        edge_list.pivot(index="source", columns="target", values="weight")
        .reindex(columns=tmp_genes, index=tmp_genes)
        .fillna(0)
        .abs()
        .astype(int)
    )
    edge_df.columns = genes
    edge_df.index = genes

    output_folder_exp = Path(f"./{output_dir}/simulated_based_on_real/EXP/")
    output_folder_exp.mkdir(exist_ok=True, parents=True)
    output_folder_gs = Path(f"./{output_dir}/simulated_based_on_real/GS/")
    output_folder_gs.mkdir(exist_ok=True, parents=True)

    name = f"sim_{real_list_of_links.stem}_{perturbation.value}"
    completed_exp_df.to_csv(
        f"{output_folder_exp}/{name}_exp.csv", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    edge_df.to_csv(f"{output_folder_gs}/{name}_gs.csv", quoting=csv.QUOTE_NONNUMERIC)

    shutil.rmtree(temp_folder_str)


__all__ = ["expression_data", "generate_from_scratch", "generate_from_real_network"]
