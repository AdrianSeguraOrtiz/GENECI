import csv
import math
import multiprocessing
import random
import re
import shutil
import string
import zipfile
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from geneci.utils import chord_diagram, plot_moving_medians, plot_polar, get_optimal_cpu_distribution

import docker
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import typer
from plotly.subplots import make_subplots
from rich import print
from scipy import stats
import matplotlib as mpl

# Header
__version__ = "4.0.1.1"
__author__ = "Adrian Segura Ortiz <adrianseor.99@uma.es>"

HEADER = "\n".join(
    [
        "                 __  ___  _  _  ___   __  __            ",
        "                / _)(  _)( \( )(  _) / _)(  )           ",
        "               ( (/\ ) _) )  (  ) _)( (_  )(            ",
        "                \__/(___)(_)\_)(___) \__)(__)           ",
        "                                                        ",
        f" version: {__version__}     Author: {__author__}        ",
        "                                                        ",
    ]
)

# Generate temp folder name
temp_folder_str = "tmp-" + "".join(random.choices(string.ascii_lowercase, k=10))

# Definition of enumerated classes.
class Topology(str, Enum):
    Random = "random"
    RandomAcyclic = "random-acyclic"
    ScaleFree = "scale-free"
    SmallWorld = "small-world"
    Eipo = "eipo"
    RandomModular = "random-modular"
    EipoModular = "eipo-modular"


class Perturbation(str, Enum):
    Knockout = "knockout"
    Knockdown = "knockdown"
    Overexpression = "overexpression"
    Mixed = "mixed"


class FromRealGenerateDatabase(str, Enum):
    TFLink = "TFLink"
    RegulonDB = "RegulonDB"
    RegNetwork = "RegNetwork"
    BioGrid = "BioGrid"
    GRNdb = "GRNdb"


real_networks_dict = {
    "TFLink": [
        "Caenorhabditis_elegans",
        "Drosophila_melanogaster",
        "Rattus_norvegicus",
        "Saccharomyces_cerevisiae",
    ],
    "RegulonDB": ["Escherichia_coli"],
    "RegNetwork": ["human", "mouse"],
    "BioGrid": [
        "Human_papillomavirus_5",
        "Human_papillomavirus_6b",
        "Bacillus_subtilis_168",
        "Bos_taurus",
        "Macaca_mulatta",
        "Middle-East_Respiratory_Syndrome-related_Coronavirus",
        "Canis_familiaris",
        "Chlamydomonas_reinhardtii",
        "Chlorocebus_sabaeus",
        "Neurospora_crassa_OR74A",
        "Cricetulus_griseus",
        "Danio_rerio",
        "Oryctolagus_cuniculus",
        "Oryza_sativa_Japonica",
        "Emericella_nidulans_FGSC_A4",
        "Plasmodium_falciparum_3D7",
        "Gallus_gallus",
        "Glycine_max",
        "Simian_Immunodeficiency_Virus",
        "Human_Herpesvirus_1",
        "Simian_Virus_40",
        "Human_Herpesvirus_4",
        "Human_Herpesvirus_5",
        "Streptococcus_pneumoniae_ATCCBAA255",
        "Strongylocentrotus_purpuratus",
        "Sus_scrofa",
        "Human_Herpesvirus_8",
        "Vaccinia_Virus",
        "Human_Immunodeficiency_Virus_2",
        "Xenopus_laevis",
        "Human_papillomavirus_16",
        "Zea_mays",
    ],
    "GRNdb": [
        "Fetal-Brain",
        "Fetal-Thymus",
        "Adult-Pancreas",
        "Adult-Muscle",
        "Adult-Adipose",
        "Adult-Ascending-Colon",
        "Adult-Lung",
        "Adult-Liver",
        "Fetal-Calvaria",
        "Adult-Epityphlon",
        "Adult-Rectum",
    ]
}


class Database(str, Enum):
    DREAM3 = "DREAM3"
    DREAM4 = "DREAM4"
    DREAM5 = "DREAM5"
    SynTReN = "SynTReN"
    Rogers = "Rogers"
    GeneNetWeaver = "GeneNetWeaver"
    IRMA = "IRMA"


class EvalDatabase(str, Enum):
    DREAM3 = "DREAM3"
    DREAM4 = "DREAM4"
    DREAM5 = "DREAM5"


class Technique(str, Enum):
    ARACNE = "ARACNE"
    BC3NET = "BC3NET"
    C3NET = "C3NET"
    CLR = "CLR"
    GENIE3_RF = "GENIE3_RF"
    GRNBOOST2 = "GRNBOOST2"
    GENIE3_ET = "GENIE3_ET"
    MRNET = "MRNET"
    MRNETB = "MRNETB"
    PCIT = "PCIT"
    TIGRESS = "TIGRESS"
    KBOOST = "KBOOST"
    MEOMI = "MEOMI"
    JUMP3 = "JUMP3"
    NARROMI = "NARROMI"
    CMI2NI = "CMI2NI"
    RSNET = "RSNET"
    PCACMI = "PCACMI"
    LOCPCACMI = "LOCPCACMI"
    PLSNET = "PLSNET"
    PIDC = "PIDC"
    PUC = "PUC"
    GRNVBEM = "GRNVBEM"
    LEAP = "LEAP"
    NONLINEARODES = "NONLINEARODES"
    INFERELATOR = "INFERELATOR"


class CutOffCriteria(str, Enum):
    MinConf = "MinConf"
    NumLinksWithBestConf = "NumLinksWithBestConf"
    PercLinksWithBestConf = "PercLinksWithBestConf"


class Challenge(str, Enum):
    D3C4 = "D3C4"
    D4C2 = "D4C2"
    D5C4 = "D5C4"


class NodesDistribution(str, Enum):
    Spring = "Spring"
    Circular = "Circular"
    Kamada_kawai = "Kamada_kawai"


class Mode(str, Enum):
    Static2D = "Static2D"
    Interactive2D = "Interactive2D"
    Compare2D = "Compare2D"
    Interactive3D = "Interactive3D"


class Algorithm(str, Enum):
    GA = "GA"
    NSGAII = "NSGAII"
    NSGAIIExternalFile = "NSGAIIExternalFile"
    SMPSO = "SMPSO"
    
class MemeticDistanceType(str, Enum):
    all = "all"
    some = "some"
    one = "one"
    
class SimpleConsensusCriteria(str, Enum):
    MeanWeights = "MeanWeights"
    MedianWeights = "MedianWeights"
    RankAverage = "RankAverage"
    BayesianFusion = "BayesianFusion"

# Activate docker client.
client = docker.from_env()

# List available images on the current device.
available_images = [
    img for tags in [i.tags for i in client.images.list() if len(i.tags) > 0] for img in tags
]

# Set docker tag
tag = "4.0.0"

# Function for obtaining the list of genes from lists of confidence levels.
def get_gene_names_from_conf_list(conf_list):
    gene_list = set()
    with open(conf_list, "r") as f:
        for row in f:
            row_list = row.split(",")
            gene_list.add(row_list[0])
            gene_list.add(row_list[1])
    f.close()
    return gene_list


# Function for obtaining the list of genes from expression file.
def get_gene_names_from_expression_file(expression_file):
    with open(expression_file, "r") as f:
        gene_list = [row.split(",")[0].replace('"', "") for row in f]
        if gene_list[0] == "":
            del gene_list[0]
    f.close()
    return gene_list


# Function to wait and close container in execution
def wait_and_close_container(container):
    # Wait for the container to run
    container.wait()

    # Get logs from container
    logs = container.logs()

    # Get execution time
    state = client.api.inspect_container(container.id)["State"]
    execution_time = pd.to_datetime(state["FinishedAt"]) - pd.to_datetime(
        state["StartedAt"]
    )

    # Stop and remove the container
    container.stop()
    container.remove(v=True)

    # Return logs
    return (logs.decode("utf-8"), execution_time)


# Function to obtain the definition of a volume given a folder
def get_volume(folder, isMatlab=False):
    dockerDir = "/tmp/.X11-unix/" if isMatlab else "/usr/local/src/"
    return {
        Path(folder).absolute(): {
            "bind": f"{dockerDir}/{Path(folder).name}",
            "mode": "rw",
        }
    }


# Function to get weights from VAR.csv file
def get_weights(filename):

    ## Open the file with the weights assigned to each inference technique.
    f = open(filename, "r")

    ## Each line contains the distribution of weights proposed by a solution of the pareto front.
    lines = f.readlines()

    ## Extract filenames from header
    filenames = lines[0].replace("\n", "").split(",")
    
    # Eliminate header before reading weights
    del lines[0]

    ## The vector that will store the vectors with these weights is created (list formed by lists).
    weights = list()

    ## For each weight distribution ...
    for line in lines:

        # Converts to the appropriate type (float)
        solution = [float(w) for w in line.split(",")]

        # Added to the list
        weights.append(solution)

    # Return list of weights
    return (filenames, weights)


# Function to write evaluation CSV file
def write_evaluation_csv(
    output_path, sorted_idx, confidence_list, objective_labels, weights, df
):
    df['aupr_scaled'] = (df['aupr'] - min(df['aupr'])) / (max(df['aupr']) - min(df['aupr']))
    df['auroc_scaled'] = (df['auroc'] - min(df['auroc'])) / (max(df['auroc']) - min(df['auroc']))
    df['mean_scaled'] = (df['aupr_scaled'] + df['auroc_scaled']) / 2
    
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
        f.close()


# Applications for the definition of Typer commands and subcommands.
app = typer.Typer(rich_markup_mode="rich")

## Evaluation
evaluate_app = typer.Typer()
app.add_typer(
    evaluate_app,
    name="evaluate",
    help="Evaluate the accuracy of the inferred network with respect to its gold standard.",
    rich_help_panel="Additional commands",
)

### Dream challenges
dream_prediction_app = typer.Typer()
evaluate_app.add_typer(
    dream_prediction_app,
    name="dream-prediction",
    help="Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.",
)

### Generic challenges
generic_prediction_app = typer.Typer()
evaluate_app.add_typer(
    generic_prediction_app,
    name="generic-prediction",
    help="Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.",
)

## Data extraction
extract_data_app = typer.Typer()
app.add_typer(
    extract_data_app,
    name="extract-data",
    help="Extract public data generated by simulators such as SynTReN, Rogers and GeneNetWeaver, as well as data from known challenges like DREAM3, DREAM4, DREAM5 and IRMA.",
    rich_help_panel="Additional commands",
)

## Data generation
generate_data_app = typer.Typer()
app.add_typer(
    generate_data_app,
    name="generate-data",
    help="Simulate time series with gene expression levels using the SysGenSIM simulator. They can be generated from scratch or based on the interactions of a real gene network.",
    rich_help_panel="Additional commands",
)

# Command for expression data simulation from scratch.
@generate_data_app.command()
def generate_from_scratch(
    topology: Topology = typer.Option(
        ...,
        case_sensitive=False,
        help="The type of topology to be attributed to the simulated gene network.",
    ),
    network_size: int = typer.Option(
        ...,
        min=20,
        help="Number of genes that will make up the simulated gene network.",
    ),
    perturbation: Perturbation = typer.Option(
        ...,
        case_sensitive=False,
        help="Type of perturbation to apply on the network to simulate expression levels for genes.",
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Simulate time series with gene expression levels using the SysGenSIM simulator from scratch.
    """

    # Report information to the user.
    print(
        f"\n Simulate network of {network_size} genes with {topology.value} topology applying {perturbation.value} perturbation."
    )

    # Create temporary folder.
    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    # Define docker image
    image = f"adriansegura99/geneci_generate-data_sysgensim:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # Run container
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str, True),
        command=f"'' {topology.value} {network_size} {perturbation.value} /tmp/.X11-unix/{temp_folder_str}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Process the expression file so that it is in the correct format.
    exp_file = next(tmp_folder.glob("*_gene_expression_matrix.tsv"))
    top_file = next(tmp_folder.glob("*_topological_properties.tsv"))
    exp_df = pd.read_csv(exp_file, sep="\t")
    top_df = pd.read_csv(top_file, sep="\t")
    genes = top_df.iloc[:, 0]
    completed_exp_df = pd.concat([genes, exp_df.iloc[:, :-1]], join="inner", axis=1)

    # Process the edge list so that it is in the correct format.
    edge_file = next(tmp_folder.glob("*_edge_list.tsv"))
    edge_list = pd.read_csv(edge_file, sep="\t", names=["source", "target", "weight"])
    edge_df = (
        edge_list.pivot(index="source", columns="target", values="weight")
        .reindex(columns=genes, index=genes)
        .fillna(0)
        .abs()
        .astype(int)
    )

    # Create output folders
    output_folder_exp = Path(f"./{output_dir}/simulated_scratch/EXP/")
    output_folder_exp.mkdir(exist_ok=True, parents=True)
    output_folder_gs = Path(f"./{output_dir}/simulated_scratch/GS/")
    output_folder_gs.mkdir(exist_ok=True, parents=True)

    # Save tables to their final destinations
    name = f"sim_{topology.value}_size-{network_size}_{perturbation.value}"
    completed_exp_df.to_csv(
        f"{output_folder_exp}/{name}_exp.csv", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    edge_df.to_csv(f"{output_folder_gs}/{name}_gs.csv", quoting=csv.QUOTE_NONNUMERIC)

    # Remove temp folder.
    shutil.rmtree(temp_folder_str)


# Command to download real networks, perform filtering and formatting
@generate_data_app.command()
def download_real_network(
    database: FromRealGenerateDatabase = typer.Option(
        ...,
        case_sensitive=False,
        help="Database from which the real gene regulatory network is to be obtained.",
    ),
    id: str = typer.Option(
        ..., help="The identifier of the gene network within the selected database."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Download real gene regulatory networks in the form of interaction lists to be fed into the expression data simulator.
    """

    # Report information to the user.
    print(f"Downloading real network {id} from {database.value} database")

    # Check that the identifier represents a gene network in the selected database.
    if id not in real_networks_dict[database.value]:
        print("The entered id is not available in the selected database.")
        print(f"Please choose one of the following: {real_networks_dict[database.value]}")
        raise typer.Exit()

    # Define link
    sep = "\t"
    header = 0
    is_zip = False
    if database == FromRealGenerateDatabase.TFLink:
        link = f"https://cdn.netbiol.org/tflink/download_files/TFLink_{id}_interactions_SS_simpleFormat_v1.0.tsv"
    elif database == FromRealGenerateDatabase.RegulonDB:
        link = "http://regulondb.ccg.unam.mx/menu/download/datasets/files/NetWorkTFGene.txt"
    elif database == FromRealGenerateDatabase.RegNetwork:
        link = "https://regnetworkweb.org/download/RegulatoryDirections.zip"
        net_file = f"new_kegg.{id}.reg.direction.txt"
        sep = " "
        header = None
        is_zip = True
    elif database == FromRealGenerateDatabase.BioGrid:
        link = "https://downloads.thebiogrid.org/Download/BioGRID/Release-Archive/BIOGRID-4.4.218/BIOGRID-ORGANISM-4.4.218.tab3.zip"
        net_file = f"BIOGRID-ORGANISM-{id}-4.4.218.tab3.txt"
        header = None
        is_zip = True
    elif database == FromRealGenerateDatabase.GRNdb:
        link = f"http://www.grndb.com/download/txt?condition={id}"
    else:
        print(
            "The selected database is not currently available, please choose another one."
        )
        raise typer.Exit()

    # Create temporary folder
    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    # Define temporal file
    local_tmp_file = f"{temp_folder_str}/raw_real_network.tsv"

    # Doownload raw data
    with requests.get(link, stream=True, verify=False) as r:
        if is_zip:
            zip_file = zipfile.ZipFile(BytesIO(r.content))
            zip_file.extract(net_file, temp_folder_str)
            shutil.move(f"{temp_folder_str}/{net_file}", local_tmp_file)
        else:
            with open(local_tmp_file, "wb") as f:
                shutil.copyfileobj(r.raw, f)

    # Insert data in pandas dataframe
    df = pd.read_csv(local_tmp_file, sep=sep, header=header, comment="#")

    # Process dataframe
    if database == FromRealGenerateDatabase.TFLink:
        df = df[["Name.TF", "Name.Target", "Detection.method"]]
        df = df[df["Name.Target"] != "-"]
        df[["Name.TF", "Name.Target"]] = df[["Name.TF", "Name.Target"]].replace(
            {",|;": "-"}, regex=True
        )
        cnt = 0
        while len(df.index) > 500:
            df = df[df["Detection.method"].str.count(";") > cnt]
            cnt += 1
        df["Detection.method"] = 1
    elif database == FromRealGenerateDatabase.RegulonDB:
        df = df.iloc[:, [1, 4, 5, 6]]
        df.columns = ["Name.TF", "Name.Target", "Regulation.Sign", "Confidence"]
        df = df[df["Confidence"] != "Weak"]
        df = df[df["Regulation.Sign"] != "?"]
        df = df.iloc[:, [0, 1, 2]]
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["+"], 1)
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["-"], -1)
    elif database == FromRealGenerateDatabase.RegNetwork:
        df = df.iloc[:, [0, 2, 4]]
        df.columns = ["Name.TF", "Name.Target", "Regulation.Sign"]
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["-->"], 1)
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["--|", "-/-", "-p"], -1)
    elif database == FromRealGenerateDatabase.BioGrid:
        df = df.iloc[:, [7,8]]
        df.insert(2, "Sign", 1)
    elif database == FromRealGenerateDatabase.GRNdb:
        df = df[["TF", "gene", "Confidence"]]
        df = df[df["Confidence"] == "High"]
        df["Confidence"] = 1
    else:
        print(
            "The selected database is not currently available, please choose another one."
        )
        raise typer.Exit()
    
    # Remove duplicates
    df = df.drop_duplicates()

    # Save in output file
    output_folder = f"{output_dir}/simulated_based_on_real/RAW/"
    Path(output_folder).mkdir(exist_ok=True, parents=True)
    df.to_csv(f"{output_folder}/{database.value}_{id}.tsv", header=False, index=False)

    # Remove temp folder.
    shutil.rmtree(temp_folder_str)


# Command for expression data simulation from scratch.
@generate_data_app.command()
def generate_from_real_network(
    real_list_of_links: Path = typer.Option(
        ...,
        help="Path to the csv file with the list of links. You can only specify either a value of 1 for an activation link or -1 to indicate inhibition.",
    ),
    perturbation: Perturbation = typer.Option(
        ...,
        case_sensitive=False,
        help="Type of perturbation to apply on the network to simulate expression levels for genes.",
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
):
    """
    Simulate time series with gene expression levels using the SysGenSIM simulator from real-world networks.
    """

    # Report information to the user.
    print(
        f"\n Simulate expression data from {real_list_of_links.name} real-world network applying {perturbation.value} perturbation."
    )

    # Create temporary folder.
    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    # Process the input list of links so that it can be correctly interpreted by the simulator.
    gene_names = list(get_gene_names_from_conf_list(real_list_of_links))
    tmp_gene_names = ["G" + str(i) for i in range(1, len(gene_names) + 1)]
    map_names = {gene_names[i]: tmp_gene_names[i] for i in range(len(gene_names))}
    df_links = pd.read_csv(
        real_list_of_links, header=None, names=["Source", "Target", "Conf"]
    )
    df_links = df_links.replace({"Source": map_names, "Target": map_names})

    # Temporarily save modified input file to the temporary folder in order to facilitate the container volume.
    tmp_network_dir = f"./{temp_folder_str}/{Path(real_list_of_links).stem}.tsv"
    df_links.to_csv(tmp_network_dir, sep="\t", header=False, index=False)

    # Define docker image
    image = f"adriansegura99/geneci_generate-data_sysgensim:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # Run container
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str, True),
        command=f"/tmp/.X11-unix/{tmp_network_dir} '' '' {perturbation.value} /tmp/.X11-unix/{temp_folder_str}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Process the expression file so that it is in the correct format.
    exp_file = next(tmp_folder.glob("*_gene_expression_matrix.tsv"))
    top_file = next(tmp_folder.glob("*_topological_properties.tsv"))
    exp_df = pd.read_csv(exp_file, sep="\t")
    top_df = pd.read_csv(top_file, sep="\t")
    tmp_genes = top_df.iloc[:, 0]
    map_tmp_names = {
        tmp_gene_names[i]: gene_names[i] for i in range(len(tmp_gene_names))
    }
    genes = [map_tmp_names[key] for key in tmp_genes]
    completed_exp_df = pd.concat(
        [pd.Series(genes), exp_df.iloc[:, :-1]], join="inner", axis=1
    )

    # Cap high outliers
    for col in completed_exp_df.columns[1:]:
        zscore = np.abs(stats.zscore(completed_exp_df[col]))
        outliers = zscore > 3
        upper_limit = np.max(completed_exp_df.loc[zscore <= 3, col])
        completed_exp_df.loc[outliers, col] = upper_limit

    # Process the edge list so that it is in the correct format.
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

    # Create output folders
    output_folder_exp = Path(f"./{output_dir}/simulated_based_on_real/EXP/")
    output_folder_exp.mkdir(exist_ok=True, parents=True)
    output_folder_gs = Path(f"./{output_dir}/simulated_based_on_real/GS/")
    output_folder_gs.mkdir(exist_ok=True, parents=True)

    # Save tables to their final destinations
    name = f"sim_{real_list_of_links.stem}_{perturbation.value}"
    completed_exp_df.to_csv(
        f"{output_folder_exp}/{name}_exp.csv", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    edge_df.to_csv(f"{output_folder_gs}/{name}_gs.csv", quoting=csv.QUOTE_NONNUMERIC)

    # Remove temp folder.
    shutil.rmtree(temp_folder_str)


# Command for expression data extraction.
@extract_data_app.command()
def expression_data(
    database: Optional[List[Database]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading expression data."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(
        None,
        help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5.",
    ),
    password: str = typer.Option(
        None,
        help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5.",
    ),
):
    """
    Download time series of gene expression data (already produced by simulators and published in challenges).
    """

    # Demand the proportion of credentials if necessary.
    if (Database.DREAM3 in database or Database.DREAM5 in database) and (
        not username or not password
    ):
        print(
            "You must enter your Synapse credentials in order to download some of the selected data."
        )
        raise typer.Exit()

    # Scroll through the list of databases specified by the user to extract data from each of them.
    for db in database:

        # Create the output folder
        output_folder = Path(f"./{output_dir}/{db.value}/EXP/")
        output_folder.mkdir(exist_ok=True, parents=True)

        # Report information to the user
        print(f"\n Extracting expression data from {db.value}")

        # Execute the corresponding image according to the database.
        if db == Database.DREAM3:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category ExpressionData --output-folder ./EXP/  --username {username} --password {password}"

        elif db == Database.DREAM4:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream4-expgs:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"ExpressionData ./EXP/ "

        elif db == Database.DREAM5:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category ExpressionData --output-folder ./EXP/  --username {username} --password {password}"

        elif db == Database.IRMA:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_irma:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"ExpressionData ./EXP/ "

        else:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_grndata:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"{db.value} ExpressionData ./EXP/ "

        # Run container
        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        # Wait, stop and remove the container. Then print reported logs
        logs, _ = wait_and_close_container(container)
        print(logs)


# Command to extract gold standards
@extract_data_app.command()
def gold_standard(
    database: Optional[List[Database]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading gold standards."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(
        None,
        help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5.",
    ),
    password: str = typer.Option(
        None,
        help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5.",
    ),
):
    """
    Download gold standards (of networks already produced by simulators and published in challenges).
    """

    # Demand the proportion of credentials if necessary.
    if (Database.DREAM3 in database or Database.DREAM5 in database) and (
        not username or not password
    ):
        print(
            "You must enter your Synapse credentials in order to download some of the selected data."
        )
        raise typer.Exit()

    # Scroll through the list of databases specified by the user to extract data from each of them.
    for db in database:

        # Create the output folder
        output_folder = Path(f"./{output_dir}/{db.value}/GS/")
        output_folder.mkdir(exist_ok=True, parents=True)

        # Report information to the user
        print(f"\n Extracting gold standards from {db.value}")

        # Execute the corresponding image according to the database.
        if db == Database.DREAM3:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category GoldStandard --output-folder ./GS/  --username {username} --password {password}"

        elif db == Database.DREAM4:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream4-expgs:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"GoldStandard ./GS/ "

        elif db == Database.DREAM5:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category GoldStandard --output-folder ./GS/  --username {username} --password {password}"

        elif db == Database.IRMA:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_irma:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"GoldStandard ./GS/ "

        else:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_grndata:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"{db.value} GoldStandard ./GS/ "

        # Run container
        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        # Wait, stop and remove the container. Then print reported logs
        logs, _ = wait_and_close_container(container)
        print(logs)


# Command to extract evaluation data
@extract_data_app.command()
def evaluation_data(
    database: Optional[List[EvalDatabase]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading evaluation data."
    ),
    output_dir: Path = typer.Option(
        Path("./input_data"), help="Path to the output folder."
    ),
    username: str = typer.Option(..., help="Synapse account username."),
    password: str = typer.Option(..., help="Synapse account password."),
):
    """
    Download evaluation data of DREAM challenges.
    """

    # Scroll through the list of databases specified by the user to extract data from each of them.
    for db in database:

        # Create the output folder
        output_folder = Path(f"./{output_dir}/{db.value}/EVAL/")
        output_folder.mkdir(exist_ok=True, parents=True)

        # Report information to the user
        print(f"\n Extracting evaluation data from {db.value}")

        # Execute the corresponding image according to the database.
        if db == EvalDatabase.DREAM3:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category EvaluationData --output-folder ./EVAL/  --username {username} --password {password}"

        elif db == EvalDatabase.DREAM4:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream4-eval:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = (
                f"--output-folder ./EVAL/  --username {username} --password {password}"
            )

        elif db == EvalDatabase.DREAM5:

            # Define docker image
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"

            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)

            # Construct the command based on the parameters entered by the user
            command = f"--category EvaluationData --output-folder ./EVAL/  --username {username} --password {password}"

        # Run container
        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        # Wait, stop and remove the container. Then print reported logs
        logs, _ = wait_and_close_container(container)
        print(logs)


# Command for inferring networks by applying individual techniques.
@app.command(rich_help_panel="Commands for two-step main execution")
def infer_network(
    expression_data: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.",
    ),
    technique: Optional[List[Technique]] = typer.Option(
        ..., case_sensitive=False, help="Inference techniques to be performed."
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
    ),
    str_threads: str = typer.Option(
        None,
        help="Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.",
    ),
    temp_folder_str: str = typer.Option(
        temp_folder_str,
        help="Path to the temporary folder that will make volume for Docker containers. By default, the central temporary folder of execution is used. Useful parameter for parallel executions from Python",
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks"), help="Path to the output folder."
    ),
):
    """
    Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3_RF, GRNBOOST2, GENIE3_ET, MRNET, MRNETB, PCIT, TIGRESS, KBOOST, MEOMI, JUMP3, NARROMI, CMI2NI, RSNET, PCACMI, LOCPCACMI, PLSNET, PIDC, PUC, GRNVBEM, LEAP, NONLINEARODES and INFERELATOR
    """

    # Calculate dict of techniques cpus
    if str_threads:
        try:
            cores_ids = [int(i) for i in str_threads.split(",")]
        except:
            print(
                f"The str_threads variable must be a comma-separated list of integers. The value entered: {str_threads} does not satisfy this condition"
            )
            raise typer.Exit()
    else:
        cores_ids = list(range(threads))
    cpus_dict = get_optimal_cpu_distribution(technique, cores_ids)

    # Report information to the user.
    print(f"\n Infer network from {expression_data.name} with {len(technique)} techniques and saving results in {output_dir}")
    print(f"\n Total cores: {len(cores_ids)}")
    print("Distribution:")
    print(cpus_dict)

    # Create temporary folder.
    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    # Temporarily copy the input file to the temporary folder in order to facilitate the container volume.
    tmp_exp_dir = f"./{temp_folder_str}/{Path(expression_data).name}"
    shutil.copyfile(expression_data, tmp_exp_dir)

    # The different images corresponding to the inference techniques are run in parallel.
    containers = list()
    for tec in technique:

        # Report information to the user.
        print(f"\n Infer network from {expression_data} with {tec.value}")

        # The image is selected according to the chosen technique.
        if tec == Technique.GENIE3_RF:
            image = f"adriansegura99/geneci_infer-network_genie3:{tag}"
            variant = "RF"
        elif tec == Technique.GRNBOOST2:
            image = f"adriansegura99/geneci_infer-network_genie3:{tag}"
            variant = "GBM"
        elif tec == Technique.GENIE3_ET:
            image = f"adriansegura99/geneci_infer-network_genie3:{tag}"
            variant = "ET"
        else:
            image = f"adriansegura99/geneci_infer-network_{tec.value.lower()}:{tag}"
            variant = None

        # In case the image comes from a matlab tool, we assign the corresponding prefix.
        if tec in [
            Technique.JUMP3,
            Technique.NARROMI,
            Technique.CMI2NI,
            Technique.RSNET,
            Technique.PCACMI,
            Technique.LOCPCACMI,
            Technique.PLSNET,
            Technique.GRNVBEM,
        ]:
            command = f"/tmp/.X11-unix/{tmp_exp_dir} /tmp/.X11-unix/{temp_folder_str}"
            isMatlab = True
        else:
            command = f"{tmp_exp_dir} {temp_folder_str}"
            if variant:
                command += f" {variant}"
            isMatlab = False

        # Set the docker client
        client = docker.from_env()
        
        # In case it is not available on the device, it is downloaded from the repository.
        if not image in available_images:
            print("Downloading docker image ...")
            client.images.pull(repository=image)
            
        # The image is executed with the parameters set by the user.
        container = client.containers.run(
            image=image,
            volumes=get_volume(temp_folder_str, isMatlab),
            command=command,
            detach=True,
            tty=True,
            cpuset_cpus=",".join([str(i) for i in cpus_dict[tec]]),
        )

        # The container is added to the list so that the following can be executed
        containers.append(container)

    # For each container, we wait for it to finish its execution, stop and delete it.
    str_times = ""
    for i, container in enumerate(containers):

        # Wait, stop and remove the container.
        logs, execution_time = wait_and_close_container(container)

        # Register execution time
        str_times += "\t- " + technique[i].value + ":\t" + str(execution_time) + "\n"

        # Print reported logs
        print(logs)

    # The initially copied input file are deleted.
    Path(tmp_exp_dir).unlink()

    # Create measurements folder to save execution times
    measurements_folder = Path(f"./{output_dir}/{expression_data.stem}/measurements/")
    measurements_folder.mkdir(exist_ok=True, parents=True)

    # Write execution times in txt file
    with open(f"./{measurements_folder}/techniques_times.txt", "w") as f:
        f.write("Infer gene regulatory network with available techniques: \n")
        f.write(str_times + "\n")

    # Create output folder.
    output_folder = Path(f"./{output_dir}/{expression_data.stem}/lists/")
    output_folder.mkdir(exist_ok=True, parents=True)

    # Move results to the output folder.
    for f in tmp_folder.glob("*"):
        shutil.move(f, f"{output_folder}/{f.name}")
    tmp_folder.rmdir()

    # An additional file is created with the list of genes for the subsequent optimization process.
    gene_names = f"./{output_dir}/{expression_data.stem}/gene_names.txt"

    # If it doens't exist ...
    if not Path(gene_names).is_file():
        # Get gene names from expression file
        gene_list = get_gene_names_from_expression_file(expression_data)

        # Write gene names to default file
        with open(gene_names, "w") as f:
            f.write(",".join(gene_list))

# Command for network binarization
@app.command(rich_help_panel="Additional commands")
def apply_cut(
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
    gene_names: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the list of trusts will be considered.",
    ),
    cut_off_criteria: CutOffCriteria = typer.Option(
        ...,
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
    ),
    cut_off_value: float = typer.Option(
        ...,
        help="Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4",
    ),
    output_file: Path = typer.Option(
        "<<conf_list_path>>/../networks/<<conf_list_name>>.csv",
        help="Path to the output CSV file that will contain the binary matrix resulting from the cutting operation.",
    ),
):
    """
    Converts a list of confidence values into a binary matrix that represents the final gene network.
    """

    # Report information to the user.
    print(
        f"Apply cut to {confidence_list} with {cut_off_criteria.value} and value {cut_off_value}"
    )

    # A temporary folder is created and the list of input confidences is copied.
    Path(temp_folder_str).mkdir(exist_ok=True, parents=True)
    tmp_confidence_list_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    # Define default temp path to gene names list
    tmp_gene_names_dir = f"{temp_folder_str}/gene_names.txt"

    # If a gene list is provided it is copied to the temporary directory
    if gene_names:
        shutil.copyfile(gene_names, tmp_gene_names_dir)

    # Or else it is created from the trusted list.
    else:
        # Get gene names from confidence list file
        gene_list = get_gene_names_from_conf_list(confidence_list)

        # Write gene names to default file
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    # The output file is defined and the necessary folders of its path are created.
    if str(output_file) == "<<conf_list_path>>/../networks/<<conf_list_name>>.csv":
        output_file = Path(
            f"{Path(confidence_list).parent.parent}/networks/{Path(confidence_list).name}"
        )
    Path(output_file).parent.mkdir(exist_ok=True, parents=True)

    # Define docker image
    image = f"adriansegura99/geneci_apply-cut:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_confidence_list_dir} {tmp_gene_names_dir} {temp_folder_str}/{Path(output_file).name} {cut_off_criteria.value} {cut_off_value}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Copy the output file from the temporary folder to the final one and delete the temporary one.
    shutil.copyfile(f"{temp_folder_str}/{Path(output_file).name}", output_file)
    shutil.rmtree(temp_folder_str)

@app.command(rich_help_panel="Additional commands")
def plot_optimization(
    fun_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the FUN CSV file.",
    ),
    fitness_evolution_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the fitness evolution TXT file.",
    ),
    plot_fitness_evolution: bool = typer.Option(
        True,
        help="Indicate if you want to represent the evolution of the fitness values.",
    ),
    plot_pareto_front: bool = typer.Option(
        True,
        help="Indicate if you want to represent the Pareto front (only available for multi-objective mode of 2 or 3 functions).",
    ),
    plot_parallel_coordinates: bool = typer.Option(
        True,
        help="Indicate if you want to represent the parallel coordinate graph (only available for multi-objective mode).",
    ),
    plot_chord_diagram: bool = typer.Option(
        True,
        help="Indicate if you want to represent the chordplot (only available for multi-objective mode).",
    ),
    only_files: bool = typer.Option(
        False,
        help="Indicate if you just want to generate the display files without showing them on the screen. Note: The chord diagram cannot be generated in files, your request will be ignored.",
    ),
    output_dir: Path = typer.Option(
        "<<fun_file>>/..",
        help="Path to the output folder.",
    ),
):
    '''
    Graph execution results. The evolution of Fitness functions, the Pareto front, the parallel coordinate graph and the chord diagram 
    can be represented. In addition, all of them will be stored in files except the chord diagram, whose interactivity is too complex to be stored.
    '''
    
    # Show figures in localhost
    mpl.use('WebAgg')
    
    # Define and create the output folder
    if str(output_dir) == "<<fun_file>>/..":
        output_dir = Path(fun_file).parent
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Get function names
    functions = pd.read_csv(fun_file, nrows=0).columns.tolist()
    
    # If specified, the evolution of the fitness values ​​is graphed
    if plot_fitness_evolution:

        # Create grid for graphs
        if len(functions) == 1:
            r = 1
            c = 1
        elif len(functions) == 2:
            r = 1
            c = 2
        else:
            r = math.ceil(len(functions) / 2)
            c = 2
        fig = make_subplots(rows=r, cols=c, subplot_titles=functions)

        # Read file with the fitness values
        df = pd.read_csv(fitness_evolution_file, header=None)

        # For each objective ...
        for i, fitness in df.iterrows():

            # Get row and column index
            curr_row = math.ceil((i + 1) / c)
            curr_col = (i + 1) - (c * (curr_row - 1))

            # Plot it under the label of its function
            fig.add_trace(
                go.Scatter(x=list(range(len(fitness))), y=fitness),
                row=curr_row,
                col=curr_col,
            )
            fig.update_xaxes(title_text="Generation", row=curr_row, col=curr_col)
            fig.update_yaxes(title_text="Fitness", row=curr_row, col=curr_col)

        # Customize and save the figure
        fig.update_layout(title_text="Fitness evolution", showlegend=False)
        fig.write_html(f"{output_dir}/fitness_evolution.html")
        if not only_files: fig.show()

    # If specified, the Pareto front is represented
    if plot_pareto_front:

        # Verify that the number of fitness functions is 2 or 3
        if len(functions) != 2 and len(functions) != 3:
            print("[bold yellow]Warning:[/bold yellow] The Pareto front cannot be represented if the number of objectives is other than 2 or 3. Your intention will be ignored.")
        else:

            # Read file with the fitness values associated with the non-dominated solutions.
            df = pd.read_csv(fun_file)

            # If there are two objectives ...
            if len(functions) == 2:
                ## Get columns as lists
                fitness_o1 = df[functions[0]].tolist()
                fitness_o2 = df[functions[1]].tolist()

                ## Obtain the order corresponding to the first objective in order to plot the front in an appropriate way.
                sorted_idx = np.argsort(fitness_o1)

                ## Sort all vectors according to the indices obtained above.
                fitness_o1 = [fitness_o1[i] for i in sorted_idx]
                fitness_o2 = [fitness_o2[i] for i in sorted_idx]

                # Plot, customize, save the figure
                fig = px.line(
                    x=fitness_o1, y=fitness_o2, markers=True, title="Pareto front"
                )
                fig.update_xaxes(title_text=functions[0])
                fig.update_yaxes(title_text=functions[1])
                fig.write_html(f"{output_dir}/pareto_front.html")
                if not only_files: fig.show()

            elif len(functions) == 3:
                # Crear el gráfico tridimensional
                fig = go.Figure(data=[go.Scatter3d(
                    x=df[functions[0]],
                    y=df[functions[1]],
                    z=df[functions[2]],
                    mode='markers',
                )])

                # Establecer los nombres de los ejes y el título del gráfico
                fig.update_layout(
                    scene=dict(
                        xaxis_title=functions[0],
                        yaxis_title=functions[1],
                        zaxis_title=functions[2],
                        xaxis_title_font=dict(size=20),
                        yaxis_title_font=dict(size=20), 
                        zaxis_title_font=dict(size=20),
                        xaxis=dict(
                            tickfont=dict(
                                size=14  # Tamaño de la fuente del eje X
                            )
                        ),
                        yaxis=dict(
                            tickfont=dict(
                                size=14  # Tamaño de la fuente del eje Y
                            )
                        ),
                        zaxis=dict(
                            tickfont=dict(
                                size=14  # Tamaño de la fuente del eje Z
                            )
                        ),
                    ),
                    title='Pareto front'
                )

                # Mostrar el gráfico en HTML
                fig.write_html(f"{output_dir}/pareto_front.html")
                if not only_files: fig.show()

    # If specified, the parallel coordinates graph is plotted
    if plot_parallel_coordinates:

        # Verify that the number of fitness functions is greater than 1
        if len(functions) == 1:
            print("[bold yellow]Warning:[/bold yellow] Cannot graph parallel coordinates for a single fitness function. Your intention will be ignored.")
        else:
            # Read file with the fitness values associated with the non-dominated solutions.
            df = pd.read_csv(fun_file)

            # Plot parallel coordinates graph
            fig = px.parallel_coordinates(
                df, dimensions=functions, title="Graph of parallel coordinates"
            )
            fig.write_html(
                f"{output_dir}/parallel_coordinates.html"
            )
            if not only_files: fig.show()
    
    # If specified, the chord diagram is plotted
    if plot_chord_diagram and not only_files:
        
        # Verify that the number of fitness functions is greater than 1
        if len(functions) == 1:
            print("[bold yellow]Warning:[/bold yellow] Cannot graph chord plot for a single fitness function. Your intention will be ignored.")
        else:
            # Read file with the fitness values associated with the non-dominated solutions.
            df = pd.read_csv(fun_file)
            
            # Normalize each column of the dataframe
            for feature_name in df.columns:
                max_value = df[feature_name].max()
                min_value = df[feature_name].min()
                df[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
            
            # Show chord diagram
            chord_diagram(df, nbins=24)


# Command to optimize the ensemble of techniques
@app.command(rich_help_panel="Commands for two-step main execution")
def optimize_ensemble(
    confidence_list: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists to be agreed upon.",
        rich_help_panel="Input data",
    ),
    gene_names: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.",
        rich_help_panel="Input data",
    ),
    time_series: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.",
        rich_help_panel="Times series - Loyalty",
    ),
    known_interactions: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the known interactions between genes. If specified, a local search process will be performed before mutation.",
        rich_help_panel="Local search",
    ),
    crossover_probability: float = typer.Option(
        0.9, help="Crossover probability", rich_help_panel="Crossover"
    ),
    num_parents: int = typer.Option(
        3, help="Number of parents", rich_help_panel="Crossover"
    ),
    mutation_probability: float = typer.Option(
        -1,
        help="Mutation probability. [default: 1/len(files)]",
        show_default=False,
        rich_help_panel="Mutation",
    ),
    mutation_strength: float = typer.Option(
        0.1, help="Mutation strength", rich_help_panel="Mutation"
    ),
    memetic_distance_type: MemeticDistanceType = typer.Option(
        MemeticDistanceType.all, help="Memetic distance type", rich_help_panel="Local search"
    ),
    memetic_probability: float = typer.Option(0.55, help="Memetic probability", rich_help_panel="Local search"),
    population_size: int = typer.Option(
        100, help="Population size", rich_help_panel="Diversity and depth"
    ),
    num_evaluations: int = typer.Option(
        25000, help="Number of evaluations", rich_help_panel="Diversity and depth"
    ),
    cut_off_criteria: CutOffCriteria = typer.Option(
        "PercLinksWithBestConf",
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
        rich_help_panel="Cut-Off",
    ),
    cut_off_value: float = typer.Option(
        0.4,
        help="Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4",
        rich_help_panel="Cut-Off",
    ),
    function: Optional[List[str]] = typer.Option(
        ...,
        help='''A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. \n
                Available terms: \n
                    \t - Quality \n
                    \t - DegreeDistribution \n
                    \t - Motifs \n
                    \t - Dynamicity \n
                    \t - ReduceNonEssentialsInteractions \n
                    \t - EigenVectorDistribution \n
                    \t - Loyalty \n
                    \t - Clustering \n
                Examples: \n
                    \t - Objective of one term: "Quality" \n
                    \t - Objective of two terms: "0.5*Quality+0.5*DegreeDistribution" \n''',
        rich_help_panel="Fitness",
    ),
    reference_point: str = typer.Option(
        "-",
        help="Reference point for the Pareto front. If specified, the search will be oriented towards this point. The format is 'f1;f2;f3'.",
        rich_help_panel="Fitness",
    ),
    algorithm: Algorithm = typer.Option(
        ...,
        help="Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).",
        rich_help_panel="Orchestration",
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
        rich_help_panel="Orchestration",
    ),
    plot_results: bool = typer.Option(
        True,
        help="Indicate if you want to represent results graphically.",
        rich_help_panel="Graphics",
    ),
    compare_performance: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Reference front with which to compare performance. Specifically, a graph will be returned to show for each generation the percentage of reference front solutions that have already been dominated by the current population. If a reference point is specified to carry out an articulated selection, the part of the reference front covered by that reference point will only be taken into account.",
        rich_help_panel="Graphics",
    ),
    output_dir: Path = typer.Option(
        "<<conf_list_path>>/../ea_consensus",
        help="Path to the output folder.",
        rich_help_panel="Output",
    ),
):
    """
    Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm
    """

    # Report information to the user.
    print(f"\n Optimize ensemble for {confidence_list}")

    # If the number of trusted lists is less than two, an error is sent
    if len(confidence_list) < 2:
        print(
            "[bold red]Error:[/bold red] Insufficient number of confidence lists provided"
        )
        raise typer.Abort()

    # Create the string representing the set of fitness functions to be checked in the input to the evolutionary algorithm
    str_functions = ";".join(function)

    # If the mutation probability is the one established by default, the optimal value is chosen
    if mutation_probability == -1:
        mutation_probability = 1 / len(confidence_list)

    # The temporary folder is created
    Path(f"{temp_folder_str}/lists").mkdir(exist_ok=True, parents=True)

    # Input trust lists are copied
    for file in confidence_list:
        shutil.copyfile(file, f"{temp_folder_str}/lists/{Path(file).name}")

    # Define default temp path to gene names list
    tmp_gene_names_dir = f"{temp_folder_str}/gene_names.txt"

    # If a gene list is provided it is copied to the temporary directory
    if gene_names:
        shutil.copyfile(gene_names, tmp_gene_names_dir)

    # Or else it is created from the trusted list.
    else:

        # Create an empty set to later store the name of the genes
        gene_list = set()

        # For each file provided in the input, the genes contained in the file are read and added to the set
        for file in confidence_list:
            gene_list.update(get_gene_names_from_conf_list(file))

        # Write gene names to default file
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    # Copy the file with the time series if specified
    tmp_time_series_dir = f"{temp_folder_str}/time_series.csv"
    if time_series:
        shutil.copyfile(time_series, tmp_time_series_dir)
        
    # If known links are provided, they are copied to the temporary directory
    tmp_known_interactions_dir = f"{temp_folder_str}/known_interactions.csv"
    if known_interactions:
        shutil.copyfile(known_interactions, tmp_known_interactions_dir)
        
     # Copy the file with the reference front if specified
    tmp_reference_front_dir = f"{temp_folder_str}/reference_front.csv"
    if compare_performance:
        shutil.copyfile(compare_performance, tmp_reference_front_dir)

    # Define docker image
    image = f"adriansegura99/geneci_optimize-ensemble:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{temp_folder_str} {crossover_probability} {num_parents} {mutation_probability} {mutation_strength} {population_size} {num_evaluations} {cut_off_criteria.value} {cut_off_value} {str_functions} {algorithm.value} {threads} {plot_results} {memetic_distance_type.value} {memetic_probability} {reference_point}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)
    
    if plot_results:
        plot_optimization(
            fun_file=f"{temp_folder_str}/ea_consensus/FUN.csv",
            fitness_evolution_file=f"{temp_folder_str}/ea_consensus/fitness_evolution.txt",
            plot_fitness_evolution=True,
            plot_pareto_front=True,
            plot_parallel_coordinates=True,
            plot_chord_diagram=True,
            output_dir="<<fun_file>>/..",
        )
    
    if compare_performance:
        # Leer el archivo con los datos de comparación
        with open(f"{temp_folder_str}/ea_consensus/compare_performance.txt", 'r') as file:
            line = file.readline().strip()

        # Convertir la línea en una lista de números
        data = list(map(float, line.split(',')))

        # Crear un gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(data))), y=data, mode='lines+markers'))

        # Configurar el diseño
        fig.update_layout(
            title="Gráfico de datos",
            xaxis_title="Generation",
            yaxis_title="Percentage of reference front solutions dominated"
        )
        fig.write_html(f"{temp_folder_str}/ea_consensus/compare_performance.html")

    # Define and create the output folder
    if str(output_dir) == "<<conf_list_path>>/../ea_consensus":
        output_dir = f"{Path(confidence_list[0]).parent.parent}/ea_consensus"
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    # All output files are moved and the temporary directory is deleted
    for f in Path(f"{temp_folder_str}/ea_consensus").glob("*"):
        shutil.move(f, f"{output_dir}/{f.name}")
    shutil.rmtree(temp_folder_str)


# Commands to evaluate the accuracy of DREAM inferred networks
## Command for evaluate one list
@dream_prediction_app.command()
def dream_list_of_links(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.",
    ),
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
):
    """
    Evaluate one list of links with confidence levels.
    """

    # Report information to the user.
    print(
        f"Evaluate {confidence_list} prediction for {network_id} network in {challenge.value} challenge"
    )

    # Create temporary folder
    Path(f"{temp_folder_str}/synapse/").mkdir(exist_ok=True, parents=True)

    # Copy evaluation files
    tmp_synapse_files_dir = f"{temp_folder_str}/synapse/"
    for f in synapse_file:
        shutil.copyfile(f, tmp_synapse_files_dir + Path(f).name)

    # Copy confidence list
    tmp_confidence_list_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    # Define docker image
    image = f"adriansegura99/geneci_evaluate_dream-prediction:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"--challenge {challenge.value} --network-id {network_id} --synapse-folder {tmp_synapse_files_dir} --confidence-list {tmp_confidence_list_dir}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Delete temp folder
    shutil.rmtree(temp_folder_str)

    # For coding use
    return logs


## Command for evaluate weight distribution
@dream_prediction_app.command()
def dream_weight_distribution(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.",
    ),
    weight_file_summand: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv",
    ),
):
    """
    Evaluate one weight distribution.
    """
    # Generate temp folder name
    second_temp_folder_str = "tmp-" + "".join(
        random.choices(string.ascii_lowercase, k=10)
    )

    # Calculate the list of links from the distribution of weights
    weighted_confidence(
        weight_file_summand=weight_file_summand,
        output_file=Path(f"./{second_temp_folder_str}/temporal_list.csv"),
    )

    # Calculate the AUROC and AUPR values for the generated list.
    values = dream_list_of_links(
        challenge=challenge,
        network_id=network_id,
        synapse_file=synapse_file,
        confidence_list=f"./{second_temp_folder_str}/temporal_list.csv",
    )

    # Delete temp folder
    shutil.rmtree(second_temp_folder_str)

    # For coding use
    return values


## Command for evaluate pareto front
@dream_prediction_app.command()
def dream_pareto_front(
    challenge: Challenge = typer.Option(
        ..., help="DREAM challenge to which the inferred network belongs"
    ),
    network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
    synapse_file: List[Path] = typer.Option(
        ...,
        help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.",
    ),
    weights_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the weights corresponding to a pareto front.",
    ),
    fitness_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the fitness values corresponding to a pareto front.",
    ),
    confidence_folder: Path = typer.Option(
        ...,
        help="Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'",
    ),
    output_dir: Path = typer.Option("<<weights_file_dir>>", help="Output folder path"),
    plot_metrics: bool = typer.Option(
        True,
        help="Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.",
    ),
):
    """
    Evaluate pareto front.
    """

    # Define and create the output folder
    if str(output_dir) == "<<weights_file_dir>>":
        output_dir = Path(weights_file).parent
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    # 1. Distribution of weights
    filenames, weights = get_weights(weights_file)

    # 2. Evaluation Metrics
    ## The lists where the auroc and aupr values are going to be stored are created.
    auprs = list()
    aurocs = list()

    ## For each weight distribution (solution) ...
    for solution in weights:

        # The list of summands formed by products between the weights and the inference files provided in the input is constructed.
        weight_file_summand = list()
        for i in range(len(solution)):
            weight_file_summand.append(f"{solution[i]}*{confidence_folder}/{filenames[i]}")

        # The function responsible for evaluating weight distributions is called
        values = dream_weight_distribution(
            challenge=challenge,
            network_id=network_id,
            synapse_file=synapse_file,
            weight_file_summand=weight_file_summand,
        )

        # The obtained accuracy values are read and stored in the list.
        str_aupr = re.search("AUPR: (.*)\n", values)
        auprs.append(float(str_aupr.group(1)))
        str_auroc = re.search("AUROC: (.*)\n", values)
        aurocs.append(float(str_auroc.group(1)))

    ## Get mean between auprs and aurocs values
    acc_means = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs, aurocs)]

    ## Get order
    auprs_scaled = (np.array(auprs) - min(auprs)) / (max(auprs) - min(auprs))
    aurocs_scaled = (np.array(aurocs) - min(aurocs)) / (max(aurocs) - min(aurocs))
    score = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs_scaled, aurocs_scaled)]

    # 3. Fitness Values
    ## Get fitness dataframe
    fitness_df = pd.read_csv(fitness_file)

    ## Extract objective labels
    objective_labels = list(fitness_df.columns)

    ## Create evaluation dataframe
    evaluation_df = pd.DataFrame(
        data={"score": score, "acc_mean": acc_means, "aupr": auprs, "auroc": aurocs}
    )

    ## Concat both dataframes
    df = pd.concat([fitness_df, evaluation_df], axis=1)

    # 4. Writing the output CSV file
    ## Get the order corresponding to the best mean between aupr and auroc
    sorted_idx = np.argsort([-s for s in score])

    ## Write CSV file
    write_evaluation_csv(
        f"{output_dir}/evaluated_front.csv", sorted_idx, [f"{confidence_folder}/{f}" for f in filenames], objective_labels, weights, df.copy()
    )
    
    # 5. Plot the information on a graph if specified
    if plot_metrics:
        
        # Evaluated parallel coordinates
        fig = px.parallel_coordinates(
            df,
            color="acc_mean",
            dimensions=df.columns,
            color_continuous_scale=px.colors.sequential.Blues,
            title="Evaluated graph of parallel coordinates",
        )
        fig.write_html(f"{output_dir}/evaluated_parallel_coordinates.html")
        
        # Moving medians objectives vs metrics
        ## AUROC
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUROC",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUROC.pdf"
        )
        ## AUPR
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUPR",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUPR.pdf"
        )
        
        # Moving medians techniques vs objectives
        for fitness_func in objective_labels:
            plot_moving_medians(
                file_path=f"{output_dir}/evaluated_front.csv",
                x=fitness_func,
                y=filenames,
                normalized=False,
                label="Techniques Weights",
                output_path=f"{output_dir}/moving_medians_techniches_vs_{fitness_func}.pdf"
            )
        
        # Polar plot
        auprs = dict()
        aurocs = dict()
        for f in filenames:
            # Evaluate technique
            values = dream_list_of_links(
                challenge=challenge,
                network_id=network_id,
                synapse_file=synapse_file,
                confidence_list=f"{confidence_folder}/{f}"
            )

            # The obtained accuracy values are read and stored in the list.
            str_aupr = re.search("AUPR: (.*)\n", values)
            auprs[f] = float(str_aupr.group(1))
            str_auroc = re.search("AUROC: (.*)\n", values)
            aurocs[f] = float(str_auroc.group(1))
            
        ## AUROC
        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=aurocs,
            metric="AUROC",
            output_path=f"{output_dir}/polar_plot_AUROC.pdf"
        )
        
        ## AUPR
        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=auprs,
            metric="AUPR",
            output_path=f"{output_dir}/polar_plot_AUPR.pdf"
        )


# Command to evaluate the accuracy of generic inferred networks
@generic_prediction_app.command()
def generic_list_of_links(
    confidence_list: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the list of trusted values.",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
):
    """
    Evaluate one list of links with confidence levels.
    """
    # Report information to the user.
    print(
        f"Evaluate {confidence_list} prediction with respect {gs_binary_matrix} gold standard"
    )

    # Create temporary folder
    Path(temp_folder_str).mkdir(exist_ok=True)

    # Extract gene names from gold standard matrix
    with open(gs_binary_matrix) as f:
        gene_names = f.readline().replace("\n", "").replace('"', "").split(",")
        del gene_names[0]

    # Store inferred confidence values in matrix format
    df = pd.DataFrame(0.0, index=gene_names, columns=gene_names)
    f = open(confidence_list, "r")
    lines = f.readlines()
    for line in lines:
        vline = line.replace("\n", "").split(",")
        df.at[vline[0], vline[1]] = float(vline[2])

    # Save dataframe in temporal folder
    tmp_inferred_matrix_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    df.to_csv(tmp_inferred_matrix_dir, sep=",")

    # And its respective gold standard
    tmp_gsbm_dir = f"{temp_folder_str}/{Path(gs_binary_matrix).name}"
    shutil.copyfile(gs_binary_matrix, tmp_gsbm_dir)

    # Define docker image
    image = f"adriansegura99/geneci_evaluate_generic-prediction:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_inferred_matrix_dir} {tmp_gsbm_dir}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Delete temp folder
    shutil.rmtree(temp_folder_str)

    # For coding use
    return logs


## Command for evaluate weight distribution
@generic_prediction_app.command()
def generic_weight_distribution(
    weight_file_summand: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
):
    """
    Evaluate one weight distribution.
    """
    # Generate temp folder name
    second_temp_folder_str = "tmp-" + "".join(
        random.choices(string.ascii_lowercase, k=10)
    )

    # Calculate the list of links from the distribution of weights
    weighted_confidence(
        weight_file_summand=weight_file_summand,
        output_file=Path(f"./{second_temp_folder_str}/temporal_list.csv"),
    )

    # Calculate the AUROC and AUPR values for the generated list.
    values = generic_list_of_links(
        confidence_list=f"./{second_temp_folder_str}/temporal_list.csv",
        gs_binary_matrix=gs_binary_matrix,
    )

    # Delete temp folder
    shutil.rmtree(second_temp_folder_str)

    # For coding use
    return values


## Command for evaluate pareto front
@generic_prediction_app.command()
def generic_pareto_front(
    weights_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the weights corresponding to a pareto front.",
    ),
    fitness_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="File with the fitness values corresponding to a pareto front.",
    ),
    confidence_folder: Path = typer.Option(
        ...,
        help="Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'",
    ),
    gs_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Gold standard binary network"
    ),
    output_dir: Path = typer.Option("<<weights_file_dir>>", help="Output folder path"),
    plot_metrics: bool = typer.Option(
        True,
        help="Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.",
    ),
):
    """
    Evaluate pareto front.
    """

    # Define and create the output folder
    if str(output_dir) == "<<weights_file_dir>>":
        output_dir = Path(weights_file).parent
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    # 1. Distribution of weights
    filenames, weights = get_weights(weights_file)

    # 2. Evaluation Metrics
    ## The lists where the auroc and aupr values are going to be stored are created.
    auprs = list()
    aurocs = list()

    ## For each weight distribution (solution) ...
    for solution in weights:

        # The list of summands formed by products between the weights and the inference files provided in the input is constructed.
        weight_file_summand = list()
        for i in range(len(solution)):
            weight_file_summand.append(f"{solution[i]}*{confidence_folder}/{filenames[i]}")

        # The function responsible for evaluating weight distributions is called
        values = generic_weight_distribution(
            weight_file_summand=weight_file_summand,
            gs_binary_matrix=gs_binary_matrix,
        )

        # The obtained accuracy values are read and stored in the list.
        str_aupr = re.search('AUPR: (.*)"', values)
        auprs.append(float(str_aupr.group(1)))
        str_auroc = re.search('AUROC: (.*)"', values)
        aurocs.append(float(str_auroc.group(1)))

    ## Get mean between auprs and aurocs values
    acc_means = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs, aurocs)]

    ## Get order
    auprs_scaled = (np.array(auprs) - min(auprs)) / (max(auprs) - min(auprs))
    aurocs_scaled = (np.array(aurocs) - min(aurocs)) / (max(aurocs) - min(aurocs))
    score = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs_scaled, aurocs_scaled)]

    # 3. Fitness Values
    ## Get fitness dataframe
    fitness_df = pd.read_csv(fitness_file)

    ## Extract objective labels
    objective_labels = list(fitness_df.columns)

    ## Create evaluation dataframe
    evaluation_df = pd.DataFrame(
        data={"score": score, "acc_mean": acc_means, "aupr": auprs, "auroc": aurocs}
    )

    ## Concat both dataframes
    df = pd.concat([fitness_df, evaluation_df], axis=1)
    
    # 4. Writing the output CSV file
    ## Get the order corresponding to the best mean between aupr and auroc
    sorted_idx = np.argsort([-s for s in score])

    ## Write CSV file
    write_evaluation_csv(
        f"{output_dir}/evaluated_front.csv", sorted_idx, [f"{confidence_folder}/{f}" for f in filenames], objective_labels, weights, df.copy()
    )
    
    # 5. Plot the information on a graph if specified
    if plot_metrics:
        
        # Evaluated parallel coordinates
        fig = px.parallel_coordinates(
            df,
            color="acc_mean",
            dimensions=df.columns,
            color_continuous_scale=px.colors.sequential.Blues,
            title="Evaluated graph of parallel coordinates",
        )
        fig.write_html(f"{output_dir}/evaluated_parallel_coordinates.html")
        
        # Moving medians objectives vs metrics
        ## AUROC
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUROC",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUROC.pdf"
        )
        ## AUPR
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUPR",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUPR.pdf"
        )
        
        # Moving medians techniques vs objectives
        for fitness_func in objective_labels:
            plot_moving_medians(
                file_path=f"{output_dir}/evaluated_front.csv",
                x=fitness_func,
                y=filenames,
                normalized=False,
                label="Techniques Weights",
                output_path=f"{output_dir}/moving_medians_techniches_vs_{fitness_func}.pdf"
            )
            
        # Polar plot
        auprs = dict()
        aurocs = dict()
        for f in filenames:
            # Evaluate technique
            values = generic_list_of_links(
                confidence_list=f"{confidence_folder}/{f}",
                gs_binary_matrix=gs_binary_matrix,
            )

            # The obtained accuracy values are read and stored in the list.
            str_aupr = re.search('AUPR: (.*)"', values)
            auprs[f] = float(str_aupr.group(1))
            str_auroc = re.search('AUROC: (.*)"', values)
            aurocs[f] = float(str_auroc.group(1))
            
        ## AUROC
        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=aurocs,
            metric="AUROC",
            output_path=f"{output_dir}/polar_plot_AUROC.pdf"
        )
        
        ## AUPR
        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=auprs,
            metric="AUPR",
            output_path=f"{output_dir}/polar_plot_AUPR.pdf"
        )

# Command that unites individual inference with consensus optimization
@app.command(rich_help_panel="Main Command")
def run(
    expression_data: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.",
        rich_help_panel="Input data",
    ),
    time_series: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.",
        rich_help_panel="Times series - Loyalty",
    ),
    known_interactions: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the known interactions between genes. If specified, a local search process will be performed before mutation.",
        rich_help_panel="Local search",
    ),
    technique: Optional[List[Technique]] = typer.Option(
        ...,
        case_sensitive=False,
        help="Inference techniques to be performed.",
        rich_help_panel="Individual inference",
    ),
    crossover_probability: float = typer.Option(
        0.9, help="Crossover probability", rich_help_panel="Crossover"
    ),
    num_parents: int = typer.Option(
        3, help="Number of parents", rich_help_panel="Crossover"
    ),
    mutation_probability: float = typer.Option(
        -1,
        help="Mutation probability. [default: 1/len(files)]",
        show_default=False,
        rich_help_panel="Mutation",
    ),
    mutation_strength: float = typer.Option(
        0.1, help="Mutation strength", rich_help_panel="Mutation"
    ),
    memetic_distance_type: MemeticDistanceType = typer.Option(
        MemeticDistanceType.all, help="Memetic distance type", rich_help_panel="Local search",
    ),
    memetic_probability: float = typer.Option(0.55, help="Memetic probability", rich_help_panel="Local search",),
    population_size: int = typer.Option(
        100, help="Population size", rich_help_panel="Diversity and depth"
    ),
    num_evaluations: int = typer.Option(
        25000, help="Number of evaluations", rich_help_panel="Diversity and depth"
    ),
    cut_off_criteria: CutOffCriteria = typer.Option(
        "PercLinksWithBestConf",
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
        rich_help_panel="Cut-Off",
    ),
    cut_off_value: float = typer.Option(
        0.4,
        help="Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4",
        rich_help_panel="Cut-Off",
    ),
    function: Optional[List[str]] = typer.Option(
        ...,
        help='''A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. \n
                Available terms: \n
                    \t - Quality \n
                    \t - DegreeDistribution \n
                    \t - Motifs \n
                    \t - Dynamicity \n
                    \t - ReduceNonEssentialsInteractions \n
                    \t - EigenVectorDistribution \n
                    \t - Loyalty \n
                    \t - Clustering \n
                Examples: \n
                    \t - Objective of one term: "Quality" \n
                    \t - Objective of two terms: "0.5*Quality+0.5*DegreeDistribution" \n''',
        rich_help_panel="Fitness",
    ),
    reference_point: str = typer.Option(
        "-",
        help="Reference point for the Pareto front. If specified, the search will be oriented towards this point. The format is 'f1;f2;f3'.",
        rich_help_panel="Fitness",
    ),
    algorithm: Algorithm = typer.Option(
        ...,
        help="Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).",
        rich_help_panel="Orchestration",
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
        rich_help_panel="Orchestration",
    ),
    str_threads: str = typer.Option(
        None,
        help="Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.",
        rich_help_panel="Orchestration",
    ),
    plot_results: bool = typer.Option(
        True,
        help="Indicate if you want to represent results graphically.",
        rich_help_panel="Graphics",
    ),
    compare_performance: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Reference front with which to compare performance. Specifically, a graph will be returned to show for each generation the percentage of reference front solutions that have already been dominated by the current population. If a reference point is specified to carry out an articulated selection, the part of the reference front covered by that reference point will only be taken into account.",
        rich_help_panel="Graphics",
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks"),
        help="Path to the output folder.",
        rich_help_panel="Output",
    ),
):
    """
    Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.
    """

    # Report information to the user.
    print(f"\n Run algorithm for {expression_data}")

    # Run inference command
    infer_network(expression_data, technique, threads, str_threads, temp_folder_str, output_dir)

    # Extract results
    confidence_list = list(
        Path(f"./{output_dir}/{expression_data.stem}/lists/").glob("GRN_*.csv")
    )
    gene_names = Path(f"./{output_dir}/{expression_data.stem}/gene_names.txt")

    # Run ensemble optimization command
    optimize_ensemble(
        confidence_list=confidence_list,
        gene_names=gene_names,
        time_series=time_series,
        known_interactions=known_interactions,
        crossover_probability=crossover_probability,
        num_parents=num_parents,
        mutation_probability=mutation_probability,
        mutation_strength=mutation_strength,
        memetic_distance_type=memetic_distance_type,
        memetic_probability=memetic_probability,
        population_size=population_size,
        num_evaluations=num_evaluations,
        cut_off_criteria=cut_off_criteria,
        cut_off_value=cut_off_value,
        function=function,
        reference_point=reference_point,
        algorithm=algorithm,
        threads=threads,
        plot_results=plot_results,
        compare_performance=compare_performance,
        output_dir="<<conf_list_path>>/../ea_consensus",
    )


# Command for graphical representation of networks.
@app.command(rich_help_panel="Additional commands")
def draw_network(
    confidence_list: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists to be represented"
    ),
    mode: Mode = typer.Option("Interactive2D", help="Mode of representation"),
    nodes_distribution: NodesDistribution = typer.Option(
        "Spring", help="Node distribution in graph. Note: Interactive2D mode has its own distribution of nodes, so in case of be selected this parameter will be ignored"
    ),
    confidence_cut_off: float = typer.Option(
        0.5, help="Cut off value for confidence"
    ),
    output_folder: Path = typer.Option(
        "<<conf_list_path>>/../network_graphics", help="Path to output folder"
    ),
):
    """
    Draw gene regulatory networks from confidence lists.
    """

    # Report information to the user.
    print(f"\n Draw gene regulatory networks for {', '.join(confidence_list)}")

    # Create input temporary folder.
    tmp_input_folder = f"{temp_folder_str}/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)

    # Create output temporary folder.
    tmp_output_folder = f"{temp_folder_str}/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    # Create input command and copy the trust lists to represent.
    command = ""
    for file in confidence_list:
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        command += f"--confidence-list {tmp_file_dir} "
        shutil.copyfile(file, tmp_file_dir)

    # Define docker image
    image = f"adriansegura99/geneci_draw-network:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{command} --mode {mode.value} --nodes-distribution {nodes_distribution.value} --confidence-cut-off {confidence_cut_off} --output-folder {tmp_output_folder}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Define and create the output folder
    if str(output_folder) == "<<conf_list_path>>/../network_graphics":
        output_folder = Path(
            f"{Path(confidence_list[0]).parent.parent}/network_graphics/"
        )
    Path(output_folder).mkdir(exist_ok=True, parents=True)

    # Move all output files
    for f in Path(tmp_output_folder).glob("*"):
        shutil.move(f, f"{output_folder}/{f.name}")

    # Delete temporary directory
    shutil.rmtree(temp_folder_str)


# Command for get weighted confidence levels from files and a given distribution of weights
@app.command(rich_help_panel="Additional commands")
def weighted_confidence(
    weight_file_summand: Optional[List[str]] = typer.Option(
        ...,
        help="Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv",
    ),
    output_file: Path = typer.Option(
        "<<conf_list_path>>/../weighted_confidence.csv", help="Output file path"
    ),
):
    """
    Calculate the weighted sum of the confidence levels reported in several files based on a given distribution of weights.
    """

    # Report information to the user.
    print(
        f"\n Calculating the weighted sum of confidence levels"
    )

    # Create input temporary folder.
    tmp_input_folder = f"{temp_folder_str}/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)

    # Create output temporary folder.
    tmp_output_folder = f"{temp_folder_str}/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    # Define default temporary output file
    tmp_output_file = f"{tmp_output_folder}/{Path(output_file).name}"

    # The entered summands are validated.
    ## Instantiate a variable to store the cumulative sum of weights
    sum = 0

    ## Instantiate another variable to store the new command with the temporary paths of the input files
    command = ""

    ## For each summand ...
    for summand in weight_file_summand:

        # Separate both products (weight and file)
        pair = summand.split("*")

        # If two elements are not detected, an error is thrown.
        if len(pair) != 2:
            print(
                f"[bold red]Error:[/bold red] The entry {summand} is invalid, remember to separate weight and file name by the '*' character"
            )
            raise typer.Abort()

        # Extract the weight
        weight = pair[0]

        # Convert it to the appropriate rate and add it to the accumulated sum.
        sum += float(weight)

        # Extract the file
        file = pair[1]

        # Define temporary file path and copy to it
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        shutil.copyfile(file, tmp_file_dir)

        # Add to command
        command += f" {weight}*{tmp_file_dir}"

    # If the sum of weights is not 1, an exception is thrown.
    if abs(sum - 1) > 0.01:
        print("[bold red]Error:[/bold red] The sum of the weights must be 1")
        raise typer.Abort()

    # Define docker image
    image = f"adriansegura99/geneci_weighted-confidence:{tag}"

    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_output_file} {command}",
        detach=True,
        tty=True,
    )

    # Wait, stop and remove the container. Then print reported logs
    logs, _ = wait_and_close_container(container)
    print(logs)

    # Define and create the output folder
    if str(output_file) == "<<conf_list_path>>/../weighted_confidence.csv":
        output_file = Path(f"{Path(file).parent.parent}/weighted_confidence.csv")
    Path(output_file).parent.mkdir(exist_ok=True, parents=True)

    # Output file is moved and the temporary directory is deleted
    shutil.move(tmp_output_file, output_file)
    shutil.rmtree(temp_folder_str)


if __name__ == "__main__":
    print(HEADER)
    app()