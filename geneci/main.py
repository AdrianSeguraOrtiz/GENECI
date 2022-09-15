import multiprocessing
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Optional
from rich import print

import docker
import matplotlib.pyplot as plt
import typer

# Applications for the definition of Typer commands and subcommands.
app = typer.Typer(rich_markup_mode="rich")
evaluate_app = typer.Typer()
app.add_typer(
    evaluate_app,
    name="evaluate",
    help="Evaluate the accuracy of the inferred network with respect to its gold standard.",
    rich_help_panel="Additional commands"
)
extract_data_app = typer.Typer()
app.add_typer(
    extract_data_app,
    name="extract-data",
    help="Extract data from different simulators and known challenges. These include DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.",
    rich_help_panel="Additional commands"
)

# Activate docker client.
client = docker.from_env()
# List available images on the current device.
available_images = [
    i.tags[0].split(":")[0] if len(i.tags) > 0 else None for i in client.images.list()
]

# Definition of enumerated classes.
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
    GENIE3_GBM = "GENIE3_GBM"
    GENIE3_ET = "GENIE3_ET"
    MRNET = "MRNET"
    MRNETB = "MRNETB"
    PCIT = "PCIT"
    TIGRESS = "TIGRESS"
    KBOOST = "KBOOST"


class CutOffCriteriaOnlyConf(str, Enum):
    MinConfidence = "MinConfidence"
    MaxNumLinksBestConf = "MaxNumLinksBestConf"


class CutOffCriteria(str, Enum):
    MinConfidence = "MinConfidence"
    MaxNumLinksBestConf = "MaxNumLinksBestConf"
    MinConfDist = "MinConfDist"


class Crossover(str, Enum):
    SBXCrossover = "SBXCrossover"
    BLXAlphaCrossover = "BLXAlphaCrossover"
    DifferentialEvolutionCrossover = "DifferentialEvolutionCrossover"
    NPointCrossover = "NPointCrossover"
    NullCrossover = "NullCrossover"
    WholeArithmeticCrossover = "WholeArithmeticCrossover"


class Mutation(str, Enum):
    PolynomialMutation = "PolynomialMutation"
    CDGMutation = "CDGMutation"
    GroupedAndLinkedPolynomialMutation = "GroupedAndLinkedPolynomialMutation"
    GroupedPolynomialMutation = "GroupedPolynomialMutation"
    LinkedPolynomialMutation = "LinkedPolynomialMutation"
    NonUniformMutation = "NonUniformMutation"
    NullMutation = "NullMutation"
    SimpleRandomMutation = "SimpleRandomMutation"
    UniformMutation = "UniformMutation"


class Repairer(str, Enum):
    StandardizationRepairer = "StandardizationRepairer"
    GreedyRepair = "GreedyRepair"


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
    Interactive3D = "Interactive3D"
    Both = "Both"

class Algorithm(str, Enum):
    GA = "GA"
    NSGAII = "NSGAII"
    SMPSO = "SMPSO"
    MOEAD = "MOEAD"
    GDE3 = "GDE3"


# Function for obtaining the list of genes from lists of confidence levels.
def get_gene_names(conf_list):
    gene_list = set()
    with open(conf_list, "r") as f:
        for row in f:
            row_list = row.split(",")
            gene_list.add(row_list[0])
            gene_list.add(row_list[1])
    return gene_list


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
    Download differential expression data from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.
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
        Path(f"./{output_dir}/{db}/EXP/").mkdir(exist_ok=True, parents=True)
        # Report information to the user
        print(f"\n Extracting expression data from {db}")

        # Execute the corresponding image according to the database.
        if db == "DREAM3":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream3"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category ExpressionData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream4-expgs"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream5"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category ExpressionData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "IRMA":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_irma"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        else:
            # Define docker image
            image = "adriansegura99/geneci_extract-data_grndata"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"{db} ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        # Wait for the container to run and display reported logs
        r = container.wait()
        logs = container.logs()
        if logs:
            print(logs.decode("utf-8"))

        # Stop and remove the container
        container.stop()
        container.remove(v=True)


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
    Download gold standards from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.
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
        Path(f"./{output_dir}/{db}/GS/").mkdir(exist_ok=True, parents=True)
        # Report information to the user
        print(f"\n Extracting gold standards from {db}")

        # Execute the corresponding image according to the database.
        if db == "DREAM3":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream3"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category GoldStandard --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream4-expgs"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream5"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category GoldStandard --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "IRMA":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_irma"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        else:
            # Define docker image
            image = "adriansegura99/geneci_extract-data_grndata"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"{db} GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        # Wait for the container to run and display reported logs
        r = container.wait()
        logs = container.logs()
        if logs:
            print(logs.decode("utf-8"))

        # Stop and remove the container
        container.stop()
        container.remove(v=True)


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
    Download evaluation data from various DREAM challenges.
    """

    # # Scroll through the list of databases specified by the user to extract data from each of them.
    for db in database:
        # Create the output folder
        Path(f"./{output_dir}/{db}/EVAL/").mkdir(exist_ok=True, parents=True)
        # Report information to the user
        print(f"\n Extracting evaluation data from {db}")

        # Execute the corresponding image according to the database.
        if db == "DREAM3":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream3"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category EvaluationData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream4-eval"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            # Define docker image
            image = "adriansegura99/geneci_extract-data_dream5"
            # In case it is not available on the device, it is downloaded from the repository.
            if not image in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            # The image is executed with the parameters set by the user.
            container = client.containers.run(
                image=image,
                volumes={
                    Path(f"./{output_dir}/").absolute(): {
                        "bind": f"/usr/local/src/{output_dir}",
                        "mode": "rw",
                    }
                },
                command=f"--category EvaluationData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        # Wait for the container to run and display reported logs.
        r = container.wait()
        logs = container.logs()
        if logs:
            print(logs.decode("utf-8"))

        # Stop and remove the container.
        container.stop()
        container.remove(v=True)


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
    output_dir: Path = typer.Option(
        Path("./inferred_networks"), help="Path to the output folder."
    ),
):
    """
    Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.
    """

    # Create the output folder.
    Path(f"./{output_dir}/{expression_data.stem}/lists/").mkdir(
        exist_ok=True, parents=True
    )
    # Temporarily copy the input files to the same folder in order to facilitate the container volume.
    tmp_exp_dir = f"./{output_dir}/{expression_data.name}"
    shutil.copyfile(expression_data, tmp_exp_dir)

    # The different images corresponding to the inference techniques are run in parallel.
    containers = list()
    for tec in technique:
        # Report information to the user.
        print(f"\n Infer network from {expression_data} with {tec}")
        # The image is selected according to the chosen technique.
        if tec == "GENIE3_RF":
            image = f"adriansegura99/geneci_infer-network_genie3"
            variant = "RF"
        elif tec == "GENIE3_GBM":
            image = f"adriansegura99/geneci_infer-network_genie3"
            variant = "GBM"
        elif tec == "GENIE3_ET":
            image = f"adriansegura99/geneci_infer-network_genie3"
            variant = "ET"
        else:
            image = f"adriansegura99/geneci_infer-network_{tec.lower()}"
            variant = None

        # In case it is not available on the device, it is downloaded from the repository.
        if not image in available_images:
            print("Downloading docker image ...")
            client.images.pull(repository=image)
        # The image is executed with the parameters set by the user.
        container = client.containers.run(
            image=image,
            volumes={
                Path(f"./{output_dir}/").absolute(): {
                    "bind": f"/usr/local/src/{output_dir}",
                    "mode": "rw",
                }
            },
            command=f"{tmp_exp_dir} {output_dir} {variant}",
            detach=True,
            tty=True,
        )
        # The container is added to the list so that the following can be executed
        containers.append(container)

    # For each container, we wait for it to finish its execution, stop and delete it.
    for container in containers:
        # Wait for the container to run and display reported logs.
        r = container.wait()
        logs = container.logs()
        if logs:
            print(logs.decode("utf-8"))

        # Stop and remove the container.
        container.stop()
        container.remove(v=True)

    # The initially copied input files are deleted.
    Path(tmp_exp_dir).unlink()

    # An additional file is created with the list of genes for the subsequent optimization process.
    gene_names = f"./{output_dir}/{expression_data.stem}/gene_names.txt"
    if not Path(gene_names).is_file():
        with open(expression_data, "r") as f:
            gene_list = [row.split(",")[0].replace('"', "") for row in f]
            if gene_list[0] == "":
                del gene_list[0]

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
    cut_off_criteria: CutOffCriteriaOnlyConf = typer.Option(
        ...,
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
    ),
    cut_off_value: float = typer.Option(
        ...,
        help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10",
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
        f"Apply cut to {confidence_list} with {cut_off_criteria} and value {cut_off_value}"
    )

    # A temporary folder is created and the list of input confidences is copied.
    Path("tmp").mkdir(exist_ok=True, parents=True)
    tmp_confidence_list_dir = f"tmp/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    # If a gene list is provided it is copied to the temporary directory or else it is created from the trusted list.
    if gene_names:
        tmp_gene_names_dir = f"tmp/{Path(gene_names).name}"
        shutil.copyfile(gene_names, tmp_gene_names_dir)
    else:
        tmp_gene_names_dir = "tmp/gene_names.txt"
        gene_list = get_gene_names(confidence_list)
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    # The output file is defined and the necessary folders of its path are created.
    if str(output_file) == "<<conf_list_path>>/../networks/<<conf_list_name>>.csv":
        output_file = Path(
            f"{Path(confidence_list).parents[1]}/networks/{Path(confidence_list).name}"
        )
    output_file.parent.mkdir(exist_ok=True, parents=True)

    # Define docker image
    image = "adriansegura99/geneci_apply-cut"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"{tmp_confidence_list_dir} {tmp_gene_names_dir} tmp/{output_file} {cut_off_criteria} {cut_off_value}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        print(logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # Copy the output file from the temporary folder to the final one and delete the temporary one.
    shutil.copyfile(f"tmp/{output_file}", output_file)
    shutil.rmtree("tmp")


# Command to optimize the ensemble of techniques
@app.command(rich_help_panel="Commands for two-step main execution")
def optimize_ensemble(
    confidence_list: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists to be agreed upon.",
        rich_help_panel="Input data"
    ),
    gene_names: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.",
        rich_help_panel="Input data"
    ),
    time_series: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.",
        rich_help_panel="Input data"
    ),
    crossover: Crossover = typer.Option("SBXCrossover", help="Crossover operator", rich_help_panel="Crossover"),
    crossover_probability: float = typer.Option(0.9, help="Crossover probability", rich_help_panel="Crossover"),
    mutation: Mutation = typer.Option("PolynomialMutation", help="Mutation operator", rich_help_panel="Mutation"),
    mutation_probability: float = typer.Option(
        -1, help="Mutation probability. [default: 1/len(files)]", show_default=False, rich_help_panel="Mutation"
    ),
    repairer: Repairer = typer.Option(
        "StandardizationRepairer",
        help="Solution repairer to keep the sum of weights equal to 1",
        rich_help_panel="Repairer"
    ),
    population_size: int = typer.Option(100, help="Population size", rich_help_panel="Diversity and depth"),
    num_evaluations: int = typer.Option(25000, help="Number of evaluations", rich_help_panel="Diversity and depth"),
    cut_off_criteria: CutOffCriteria = typer.Option(
        "MinConfDist",
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
        rich_help_panel="Cut-Off"
    ),
    cut_off_value: float = typer.Option(
        0.5,
        help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2",
        rich_help_panel="Cut-Off"
    ),
    function: Optional[List[str]] = typer.Option(
        ["Quality", "Topology"], help="A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. Available terms: Quality, Topology and Loyalty.",
        rich_help_panel="Fitness"
    ),
    algorithm: Algorithm = typer.Option(
        "NSGAII", help="Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).",
        rich_help_panel="Orchestration"
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
        rich_help_panel="Orchestration"
    ),
    plot_evolution: bool = typer.Option(
        False,
        help="Indicate if you want to represent the evolution of the fitness value.",
        rich_help_panel="Graphics"
    ),
    output_dir: Path = typer.Option(
        "<<conf_list_path>>/../ea_consensus", help="Path to the output folder.",
        rich_help_panel="Output"
    ),
):
    """
    Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm
    """
    # Report information to the user.
    print(f"\n Optimize ensemble for {confidence_list}")

    # If the number of trusted lists is less than two, an error is sent
    if len(confidence_list) < 2:
        print("[bold red]Error:[/bold red] Insufficient number of confidence lists provided")
        raise typer.Abort()

    # Create the string representing the set of fitness functions to be checked in the input to the evolutionary algorithm
    functions = ";".join(function)

    # If the mutation probability is the one established by default, the optimal value is chosen
    if mutation_probability == -1:
        mutation_probability = 1 / len(confidence_list)

    # The temporary folder is created
    Path("tmp/lists").mkdir(exist_ok=True, parents=True)
    # Input trust lists are copied
    for file in confidence_list:
        shutil.copyfile(file, f"tmp/lists/{Path(file).name}")

    # If a gene list is provided it is copied to the temporary directory or else it is created from the trusted list.
    tmp_gene_names_dir = "tmp/gene_names.txt"
    if gene_names:
        shutil.copyfile(gene_names, tmp_gene_names_dir)
    else:
        gene_list = set()
        for file in confidence_list:
            gene_list.update(get_gene_names(file))
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))
    
    # Copy the file with the time series if specified
    tmp_time_series_dir = "tmp/time_series.csv"
    if time_series:
        shutil.copyfile(time_series, tmp_time_series_dir)

    # Define docker image
    image = "adriansegura99/geneci_optimize-ensemble"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"tmp/ {crossover} {crossover_probability} {mutation} {mutation_probability} {repairer} {population_size} {num_evaluations} {cut_off_criteria} {cut_off_value} {functions} {algorithm} {threads} {plot_evolution}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        if "Exception in thread" in logs.decode("utf-8"):
            print("\n" + "[bold red]Error:[/bold red] " + logs.decode("utf-8"))
            shutil.rmtree("tmp")
            raise typer.Abort()
        else:
            print("\n" + "[bold green]Ok![/bold green] \n" + logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # If specified, the evolution of the fitness values ​​is graphed
    if plot_evolution:
        f = open("tmp/ea_consensus/fitness_evolution.txt", "r")
        lines = f.readlines()
        for i in range(len(lines)):
            str_fitness = lines[i].split(", ")
            fitness = [float(i) for i in str_fitness]
            plt.plot(fitness, label=function[i])

        plt.title("Fitness evolution")
        plt.ylabel("Fitness")
        plt.xlabel("Generation")
        plt.legend()
        plt.savefig("tmp/ea_consensus/fitness_evolution.pdf")
        plt.close()

    # If there are two objectives the pareto front is plotted
    if len(function) == 2:
        f = open("tmp/ea_consensus/FUN.csv", "r")
        lines = f.readlines()
        x = list()
        y = list()
        for line in lines:
            point = line.split(",")
            x.append(float(point[0]))
            y.append(float(point[1]))
        x, y = zip(*sorted(zip(x, y)))
        plt.plot(x, y)
        plt.title("Pareto front")
        plt.ylabel(function[0])
        plt.xlabel(function[1])
        plt.savefig("tmp/ea_consensus/pareto_front.pdf")
        plt.close()

    # Define and create the output folder
    if str(output_dir) == "<<conf_list_path>>/../ea_consensus":
        output_dir = Path(f"{Path(confidence_list[0]).parents[1]}/ea_consensus")
    output_dir.mkdir(exist_ok=True, parents=True)

    # All output files are moved and the temporary directory is deleted
    for f in Path("tmp/ea_consensus").glob("*"):
        shutil.move(f, f"{output_dir}/{f.name}")
    shutil.rmtree("tmp")


# Command to evaluate the accuracy of DREAM inferred networks
@evaluate_app.command()
def dream_prediction(
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
    Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.
    """
    # Report information to the user.
    print(
        f"Evaluate {confidence_list} prediction for {network_id} network in {challenge.name} challenge"
    )

    # Create temporary folder.
    Path("tmp/synapse/").mkdir(exist_ok=True, parents=True)
    # Copy evaluation files.
    tmp_synapse_files_dir = "tmp/synapse/"
    for f in synapse_file:
        shutil.copyfile(f, tmp_synapse_files_dir + Path(f).name)
    # Copy confidence list.
    tmp_confidence_list_dir = f"tmp/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    # Define docker image
    image = "adriansegura99/geneci_evaluate_dream-prediction"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"--challenge {challenge.name} --network-id {network_id} --synapse-folder {tmp_synapse_files_dir} --confidence-list {tmp_confidence_list_dir}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        print(logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # Delete temp folder
    shutil.rmtree("tmp")


# Command to evaluate the accuracy of generic inferred networks
@evaluate_app.command()
def generic_prediction(
    inferred_binary_matrix: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Binary network to be evaluated"
    ),
    gs_binary_matrix: Path = typer.Option(..., exists=True, file_okay=True, help="Gold standard binary network"),
):
    """
    Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.
    """
    # Report information to the user.
    print(
        f"Evaluate {inferred_binary_matrix} prediction with respect {gs_binary_matrix} gold standard"
    )

    # Create temporary folder and copy the network to test and its respective gold standard
    Path("tmp/").mkdir(exist_ok=True)
    tmp_ibm_dir = f"tmp/{Path(inferred_binary_matrix).name}"
    shutil.copyfile(inferred_binary_matrix, tmp_ibm_dir)
    tmp_gsbm_dir = f"tmp/{Path(gs_binary_matrix).name}"
    shutil.copyfile(gs_binary_matrix, tmp_gsbm_dir)

    # Define docker image
    image = "adriansegura99/geneci_evaluate_generic-prediction"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"{tmp_ibm_dir} {tmp_gsbm_dir}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        print(logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # Delete temp folder
    shutil.rmtree("tmp")


# Command that unites individual inference with consensus optimization
@app.command(rich_help_panel="Main Command")
def run(
    expression_data: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.",
        rich_help_panel="Input data"
    ),
    technique: Optional[List[Technique]] = typer.Option(
        ..., case_sensitive=False, help="Inference techniques to be performed.", rich_help_panel="Individual inference"
    ),
    crossover: Crossover = typer.Option("SBXCrossover", help="Crossover operator", rich_help_panel="Crossover"),
    crossover_probability: float = typer.Option(0.9, help="Crossover probability", rich_help_panel="Crossover"),
    mutation: Mutation = typer.Option("PolynomialMutation", help="Mutation operator", rich_help_panel="Mutation"),
    mutation_probability: float = typer.Option(
        -1, help="Mutation probability. [default: 1/len(files)]", show_default=False, rich_help_panel="Mutation"
    ),
    repairer: Repairer = typer.Option(
        "StandardizationRepairer",
        help="Solution repairer to keep the sum of weights equal to 1",
        rich_help_panel="Repairer"
    ),
    population_size: int = typer.Option(100, help="Population size", rich_help_panel="Diversity and depth"),
    num_evaluations: int = typer.Option(25000, help="Number of evaluations", rich_help_panel="Diversity and depth"),
    cut_off_criteria: CutOffCriteria = typer.Option(
        "MinConfDist",
        case_sensitive=False,
        help="Criteria for determining which links will be part of the final binary matrix.",
        rich_help_panel="Cut-Off"
    ),
    cut_off_value: float = typer.Option(
        0.5,
        help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2",
        rich_help_panel="Cut-Off"
    ),
    function: Optional[List[str]] = typer.Option(
        ["Quality", "Topology"], help="A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. Available terms: Quality, Topology and Loyalty.",
        rich_help_panel="Fitness"
    ),
    algorithm: Algorithm = typer.Option(
        "NSGAII", help="Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).",
        rich_help_panel="Orchestration"
    ),
    threads: int = typer.Option(
        multiprocessing.cpu_count(),
        help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.",
        rich_help_panel="Orchestration"
    ),
    plot_evolution: bool = typer.Option(
        False,
        help="Indicate if you want to represent the evolution of the fitness value.",
        rich_help_panel="Graphics"
    ),
    output_dir: Path = typer.Option(
        Path("./inferred_networks"), help="Path to the output folder.",
        rich_help_panel="Output"
    ),
):
    """
    Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.
    """
    # Report information to the user.
    print(f"\n Run algorithm for {expression_data}")

    # Run inference command
    infer_network(expression_data, technique, output_dir)

    # Extract results
    confidence_list = list(
        Path(f"./{output_dir}/{expression_data.stem}/lists/").glob("GRN_*.csv")
    )
    gene_names = Path(f"./{output_dir}/{expression_data.stem}/gene_names.txt")

    # Run ensemble optimization command
    optimize_ensemble(
        confidence_list,
        gene_names,
        crossover,
        crossover_probability,
        mutation,
        mutation_probability,
        repairer,
        population_size,
        num_evaluations,
        cut_off_criteria,
        cut_off_value,
        function,
        algorithm,
        threads,
        plot_evolution,
        output_dir="<<conf_list_path>>/../ea_consensus",
    )


# Command for graphical representation of networks.
@app.command(rich_help_panel="Additional commands")
def draw_network(
    confidence_list: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists to be represented"
    ),
    mode: Mode = typer.Option("Both", help="Mode of representation"),
    nodes_distribution: NodesDistribution = typer.Option(
        "Spring", help="Node distribution in graph"
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
    tmp_input_folder = "tmp/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)
    # Create output temporary folder.
    tmp_output_folder = "tmp/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    # Create input command and copy the trust lists to represent.
    command = ""
    for file in confidence_list:
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        command += f"--confidence-list {tmp_file_dir} "
        shutil.copyfile(file, tmp_file_dir)

    # Define docker image
    image = "adriansegura99/geneci_draw-network"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"{command} --mode {mode} --nodes-distribution {nodes_distribution} --output-folder {tmp_output_folder}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        print(logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # Define and create the output folder
    if str(output_folder) == "<<conf_list_path>>/../network_graphics":
        output_folder = Path(f"{Path(confidence_list[0]).parents[1]}/network_graphics/")
    output_folder.mkdir(exist_ok=True, parents=True)

    # All output files are moved and the temporary directory is deleted
    for f in Path(tmp_output_folder).glob("*"):
        shutil.move(f, f"{output_folder}/{f.name}")
    shutil.rmtree("tmp")


# Command for get weighted confidence levels from files and a given distribution of weights
@app.command(rich_help_panel="Additional commands")
def weighted_confidence(
    file_weight_summand: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists together with its associated weights"
    ),
    output_file: Path = typer.Option(
        "<<conf_list_path>>/../weighted_confidence.csv", help="Output file path"
    ),
):
    """
    Calculate the weighted sum of the confidence levels reported in various files based on a given distribution of weights.
    """
    # Report information to the user.
    print(f"\n Calculating the weighted sum of confidence levels for entry {', '.join(file_weight_summand)}")

    # Create input temporary folder.
    tmp_input_folder = "tmp/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)
    # Create output temporary folder.
    tmp_output_folder = "tmp/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)
    tmp_output_file = tmp_output_folder + "/" + output_file.name

    # Read summands.
    sum = 0
    command = ""
    for summand in file_weight_summand:
        pair = summand.split("*")
        if len(pair) != 2: 
            print("[bold red]Error:[/bold red] The entry" + summand + "is invalid, remember to separate the file name and its weight by the '*' character")
            raise typer.Abort()
        file = pair[0]
        weight = pair[1]
        sum += float(weight)
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        shutil.copyfile(file, tmp_file_dir)
        command += " " + tmp_file_dir + "*" + weight

    # If the sum of weights is not 1, an exception is thrown.
    if sum != 1:
        print("[bold red]Error:[/bold red] The sum of the weights must be 1")
        raise typer.Abort()

    # Define docker image
    image = "adriansegura99/geneci_weighted-confidence"
    # In case it is not available on the device, it is downloaded from the repository.
    if not image in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)
    # The image is executed with the parameters set by the user.
    container = client.containers.run(
        image=image,
        volumes={
            Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}
        },
        command=f"{tmp_output_file} {command}",
        detach=True,
        tty=True,
    )

    # Wait for the container to run and display reported logs.
    r = container.wait()
    logs = container.logs()
    if logs:
        print(logs.decode("utf-8"))

    # Stop and remove the container.
    container.stop()
    container.remove(v=True)

    # Define and create the output folder
    if str(output_file) == "<<conf_list_path>>/../weighted_confidence.csv":
        output_file = Path(f"{Path(file).parents[1]}/weighted_confidence.csv")
    output_file.parent.mkdir(exist_ok=True, parents=True)

    # Output file is moved and the temporary directory is deleted
    shutil.move(tmp_output_file, output_file)
    shutil.rmtree("tmp")


if __name__ == "__main__":
    app()
