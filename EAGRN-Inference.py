import typer
from typing import List, Optional
from enum import Enum
from pathlib import Path
import docker
import shutil
import matplotlib.pyplot as plt
import multiprocessing

app = typer.Typer()
evaluate_app = typer.Typer()
app.add_typer(evaluate_app, name="evaluate", help="Evaluate the accuracy of the inferred network with respect to its gold standard.")
extract_data_app = typer.Typer()
app.add_typer(extract_data_app, name="extract-data", help="Extract data from different simulators and known challenges. These include DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.")

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


def get_gene_names(conf_list):
    gene_list = set()
    with open(conf_list, "r") as f:
        for row in f:
            row_list = row.split(",")
            gene_list.add(row_list[0])
            gene_list.add(row_list[1])
    return gene_list


@extract_data_app.command()
def expression_data(
        database: Optional[List[Database]] = typer.Option(..., case_sensitive=False, help="Databases for downloading expression data."),
        output_dir: Path = typer.Option(Path("./input_data"), help="Path to the output folder."), 
        username: str = typer.Option(None, help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5."),
        password: str = typer.Option(None, help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5."),
    ):
    """
        Download differential expression data from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.
    """

    if (Database.DREAM3 in database or Database.DREAM5 in database) and (not username or not password):
        typer.echo("You must enter your Synapse credentials in order to download some of the selected data.")
        raise typer.Exit()

    for db in database:
        Path(f'./{output_dir}/{db}/EXP/').mkdir(exist_ok=True, parents=True)

        typer.echo(f"Extracting expression data from {db}")

        if db == "DREAM3":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream3",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category ExpressionData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream4/expgs",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream5",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category ExpressionData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )
        
        elif db == "IRMA":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/irma",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        else:
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/grndata",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"{db} ExpressionData {output_dir}",
                detach=True,
                tty=True,
            )

        r = container.wait()
        logs = container.logs()
        if logs:
            typer.echo(logs.decode("utf-8"))

        container.stop()
        container.remove(v=True)

@extract_data_app.command()
def gold_standard(
        database: Optional[List[Database]] = typer.Option(..., case_sensitive=False, help="Databases for downloading gold standards."),
        output_dir: Path = typer.Option(Path("./input_data"), help="Path to the output folder."), 
        username: str = typer.Option(None, help="Synapse account username. Only necessary when selecting DREAM3 or DREAM5."),
        password: str = typer.Option(None, help="Synapse account password. Only necessary when selecting DREAM3 or DREAM5."),
    ):
    """
        Download gold standards from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.
    """

    if (Database.DREAM3 in database or Database.DREAM5 in database) and (not username or not password):
        typer.echo("You must enter your Synapse credentials in order to download some of the selected data.")
        raise typer.Exit()

    for db in database:
        Path(f'./{output_dir}/{db}/GS/').mkdir(exist_ok=True, parents=True)

        typer.echo(f"Extracting gold standards from {db}")

        if db == "DREAM3":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream3",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category GoldStandard --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream4/expgs",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream5",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category GoldStandard --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )
        
        elif db == "IRMA":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/irma",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        else:
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/grndata",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"{db} GoldStandard {output_dir}",
                detach=True,
                tty=True,
            )

        r = container.wait()
        logs = container.logs()
        if logs:
            typer.echo(logs.decode("utf-8"))

        container.stop()
        container.remove(v=True)

@extract_data_app.command()
def evaluation_data(
        database: Optional[List[EvalDatabase]] = typer.Option(..., case_sensitive=False, help="Databases for downloading evaluation data."),
        output_dir: Path = typer.Option(Path("./input_data"), help="Path to the output folder."), 
        username: str = typer.Option(..., help="Synapse account username."),
        password: str = typer.Option(..., help="Synapse account password."),
    ):
    """
        Download evaluation data from various DREAM challenges.
    """

    for db in database:
        Path(f'./{output_dir}/{db}/EVAL/').mkdir(exist_ok=True, parents=True)

        typer.echo(f"Extracting evaluation data from {db}")

        if db == "DREAM3":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream3",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category EvaluationData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM4":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream4/eval",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        elif db == "DREAM5":
            client = docker.from_env()
            container = client.containers.run(
                image="eagrn-inference/extract_data/dream5",
                volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
                command=f"--category EvaluationData --output-folder {output_dir} --username {username} --password {password}",
                detach=True,
                tty=True,
            )

        r = container.wait()
        logs = container.logs()
        if logs:
            typer.echo(logs.decode("utf-8"))

        container.stop()
        container.remove(v=True)


@app.command()
def infer_network(
        expression_data: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns."), 
        technique: Optional[List[Technique]] = typer.Option(..., case_sensitive=False, help="Inference techniques to be performed."),
        output_dir: Path = typer.Option(Path("./inferred_networks"), help="Path to the output folder."),
    ):
    """
        Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.
    """

    Path(f'./{output_dir}/{expression_data.stem}/lists/').mkdir(exist_ok=True, parents=True)
    tmp_exp_dir = f"./{output_dir}/{expression_data.name}"
    shutil.copyfile(expression_data, tmp_exp_dir)

    containers = list()
    for tec in technique:
        typer.echo(f"Infer network from {expression_data} with {tec}")

        if tec == "GENIE3_RF":
            image = f"eagrn-inference/infer_network/genie3"
            variant = "RF"
        elif tec == "GENIE3_GBM":
            image = f"eagrn-inference/infer_network/genie3"
            variant = "GBM"
        elif tec == "GENIE3_ET":
            image = f"eagrn-inference/infer_network/genie3"
            variant = "ET"
        else:
            image = f"eagrn-inference/infer_network/{tec.lower()}"
            variant = None

        client = docker.from_env()
        container = client.containers.run(
            image=image,
            volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
            command=f"{tmp_exp_dir} {output_dir} {variant}",
            detach=True,
            tty=True,
        )
        containers.append(container)

    for container in containers:
        r = container.wait()
        logs = container.logs()
        if logs:
            typer.echo(logs.decode("utf-8"))

        container.stop()
        container.remove(v=True)
    
    Path(tmp_exp_dir).unlink()

    gene_names = f'./{output_dir}/{expression_data.stem}/gene_names.txt'
    if (not Path(gene_names).is_file()):
        with open(expression_data, "r") as f:
            gene_list = [row.split(",")[0].replace('\"', '') for row in f]
            if gene_list[0] == "": 
                del gene_list[0]

        with open(gene_names, "w") as f:
            f.write(",".join(gene_list))


@app.command()
def apply_cut(
        confidence_list: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the CSV file with the list of trusted values."), 
        gene_names: Path = typer.Option(None, exists=True, file_okay=True, help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the list of trusts will be considered."),
        cut_off_criteria: CutOffCriteriaOnlyConf = typer.Option(..., case_sensitive=False, help="Criteria for determining which links will be part of the final binary matrix."), 
        cut_off_value: float = typer.Option(..., help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10"),
        output_file: Path = typer.Option("<<conf_list_path>>/../networks/<<conf_list_name>>.csv", help="Path to the output CSV file that will contain the binary matrix resulting from the cutting operation."),
    ):
    """
    Converts a list of confidence values into a binary matrix that represents the final gene network.
    """

    typer.echo(f"Apply cut to {confidence_list} with {cut_off_criteria} and value {cut_off_value}")

    Path("tmp").mkdir(exist_ok=True, parents=True)
    tmp_confidence_list_dir = f"tmp/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    if gene_names:
        tmp_gene_names_dir = f"tmp/{Path(gene_names).name}"
        shutil.copyfile(gene_names, tmp_gene_names_dir)
    else:
        tmp_gene_names_dir = "tmp/gene_names.txt"
        gene_list = get_gene_names(confidence_list)
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    if str(output_file) == "<<conf_list_path>>/../networks/<<conf_list_name>>.csv":
        output_file = Path(f"{Path(confidence_list).parents[1]}/networks/{Path(confidence_list).name}")
    
    client = docker.from_env()
    container = client.containers.run(
        image="eagrn-inference/apply_cut",
        volumes={Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}},
        command=f"{tmp_confidence_list_dir} {tmp_gene_names_dir} tmp/{output_file} {cut_off_criteria} {cut_off_value}",
        detach=True,
        tty=True,
    )

    r = container.wait()
    logs = container.logs()
    if logs:
        typer.echo(logs.decode("utf-8"))

    container.stop()
    container.remove(v=True)

    Path(output_file.parent).mkdir(exist_ok=True, parents=True)
    shutil.copyfile(f"tmp/{output_file}", output_file)
    shutil.rmtree("tmp")
    

@app.command()
def optimize_ensemble(
        confidence_list: Optional[List[str]] = typer.Option(..., help="Paths of the CSV files with the confidence lists to be agreed upon."),
        gene_names: Path = typer.Option(None, exists=True, file_okay=True, help="Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered."),
        crossover: Crossover = typer.Option("SBXCrossover", help="Crossover operator"), 
        crossover_probability: float = typer.Option(0.9, help="Crossover probability"),
        mutation: Mutation = typer.Option("PolynomialMutation", help="Mutation operator"), 
        mutation_probability: float = typer.Option(-1, help="Mutation probability. [default: 1/len(files)]", show_default=False),
        repairer: Repairer = typer.Option("StandardizationRepairer", help="Solution repairer to keep the sum of weights equal to 1"), 
        population_size: int = typer.Option(100, help="Population size"), 
        num_evaluations: int = typer.Option(25000, help="Number of evaluations"), 
        cut_off_criteria: CutOffCriteria = typer.Option("MinConfDist", case_sensitive=False, help="Criteria for determining which links will be part of the final binary matrix."), 
        cut_off_value: float = typer.Option(0.5, help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2"),
        f1_weight: float = typer.Option(0.75, help="Weight associated with the first function of the optimization process. This function tries to maximize the quality of good links (improve trust and frequency of appearance) while minimizing their quantity. It tries to establish some contrast between good and bad links so that the links finally reported are of high reliability."),
        f2_weight: float = typer.Option(0.25, help="Weight associated with the second function of the optimization process. This function tries to increase the degree (number of links) of those genes with a high potential to be considered as hubs. At the same time, it is intended that the number of genes that meet this condition should be relatively low, since this is what is usually observed in real gene networks. The objective is to promote the approximation of the network to a scale-free configuration and to move away from random structure."),
        threads: int = typer.Option(multiprocessing.cpu_count(), help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used."),
        graphics: bool = typer.Option(True, help="Indicate if you do not want to represent the evolution of the fitness value."),
        output_dir: Path = typer.Option("<<conf_list_path>>/../ea_consensus", help="Path to the output folder."),
    ):
    """
    Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm
    """
    typer.echo(f"Optimize ensemble for {confidence_list}")

    if len(confidence_list) < 2:
        typer.echo("Insufficient number of confidence lists provided")
        raise typer.Abort()
    
    if f1_weight + f2_weight != 1:
        typer.echo("The weights of both fitness functions must add up to 1")
        raise typer.Abort()

    if threads < 1:
        typer.echo("The number of threads must be at least 1")
        raise typer.Abort()
    elif threads == 1:
        algorithm = "SingleThread"
    else:
        algorithm = "AsyncParallel"

    if mutation_probability == -1:
        mutation_probability = 1/len(confidence_list)

    for file in confidence_list:
        Path("tmp/lists").mkdir(exist_ok=True, parents=True)
        shutil.copyfile(file, f"tmp/lists/{Path(file).name}")
    
    tmp_gene_names_dir = "tmp/gene_names.txt"
    if gene_names:
        shutil.copyfile(gene_names, tmp_gene_names_dir)
    else:
        gene_list = set()
        for file in confidence_list:
            gene_list.update(get_gene_names(file))
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    client = docker.from_env()
    container = client.containers.run(
        image="eagrn-inference/optimize_ensemble",
        volumes={Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}},
        command=f"tmp/ {crossover} {crossover_probability} {mutation} {mutation_probability} {repairer} {population_size} {num_evaluations} {cut_off_criteria} {cut_off_value} {f1_weight} {f2_weight} {algorithm} {threads}",
        detach=True,
        tty=True,
    )

    r = container.wait()
    logs = container.logs()
    if logs:
        typer.echo(logs.decode("utf-8"))

    container.stop()
    container.remove(v=True)

    if graphics:
        f = open("tmp/ea_consensus/fitness_evolution.txt", "r")
        str_lines = f.readlines()
        str_fitness = str_lines[0].split(", ")
        fitness = [float(i) for i in str_fitness]
        str_f1 = str_lines[1].split(", ")
        f1 = [float(i) for i in str_f1]
        str_f2 = str_lines[2].split(", ")
        f2 = [float(i) for i in str_f2]
        
        
        plt.plot(fitness, label="Fitness")
        plt.plot(f1, label="Function 1")
        plt.plot(f2, label="Function 2")
        plt.title("Fitness evolution")
        plt.ylabel("Fitness")
        plt.xlabel("Generation")
        plt.legend()
        plt.savefig("tmp/ea_consensus/fitness_evolution.pdf")


    if str(output_dir) == "<<conf_list_path>>/../ea_consensus":
        output_dir = Path(f"{Path(confidence_list[0]).parents[1]}/ea_consensus")

    output_dir.mkdir(exist_ok=True, parents=True)
    for f in Path("tmp/ea_consensus").glob('*'):
        shutil.move(f, f"{output_dir}/{f.name}")
    shutil.rmtree("tmp")
    

@evaluate_app.command()
def dream_prediction(
        challenge: Challenge = typer.Option(..., help="DREAM challenge to which the inferred network belongs"),
        network_id: str = typer.Option(..., help="Predicted network identifier. Ex: 10_1"),
        synapse_file: List[Path] = typer.Option(..., help="Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data."),
        confidence_list: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the CSV file with the list of trusted values."), 
    ):
    """
    Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.
    """
    typer.echo(f"Evaluate {confidence_list} prediction for {network_id} network in {challenge.name} challenge")

    Path("tmp/synapse/").mkdir(exist_ok=True, parents=True)

    tmp_confidence_list_dir = f"tmp/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    tmp_synapse_files_dir = "tmp/synapse/"
    for f in synapse_file:
        shutil.copyfile(f, tmp_synapse_files_dir + Path(f).name)

    client = docker.from_env()
    container = client.containers.run(
        image="eagrn-inference/evaluate/dream_prediction",
        volumes={Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}},
        command=f"--challenge {challenge.name} --network-id {network_id} --synapse-folder {tmp_synapse_files_dir} --confidence-list {tmp_confidence_list_dir}",
        detach=True,
        tty=True,
    )

    r = container.wait()
    logs = container.logs()
    if logs:
        typer.echo(logs.decode("utf-8"))

    container.stop()
    container.remove(v=True)

    shutil.rmtree("tmp")

@evaluate_app.command()
def generic_prediction(
        inferred_binary_matrix: Path = typer.Option(..., exists=True, file_okay=True, help=""),
        gs_binary_matrix: Path = typer.Option(..., exists=True, file_okay=True, help=""), 
    ):
    """
    Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.
    """

    typer.echo(f"Evaluate {inferred_binary_matrix} prediction with respect {gs_binary_matrix} gold standard")

    Path("tmp/").mkdir(exist_ok=True)
    tmp_ibm_dir = f"tmp/{Path(inferred_binary_matrix).name}"
    shutil.copyfile(inferred_binary_matrix, tmp_ibm_dir)
    tmp_gsbm_dir = f"tmp/{Path(gs_binary_matrix).name}"
    shutil.copyfile(gs_binary_matrix, tmp_gsbm_dir)

    client = docker.from_env()
    container = client.containers.run(
        image="eagrn-inference/evaluate/generic_prediction",
        volumes={Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}},
        command=f"{tmp_ibm_dir} {tmp_gsbm_dir}",
        detach=True,
        tty=True,
    )

    r = container.wait()
    logs = container.logs()
    if logs:
        typer.echo(logs.decode("utf-8"))

    container.stop()
    container.remove(v=True)

    shutil.rmtree("tmp")


@app.command()
def run(
        expression_data: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns."), 
        technique: Optional[List[Technique]] = typer.Option(..., case_sensitive=False, help="Inference techniques to be performed."),
        crossover: Crossover = typer.Option("SBXCrossover", help="Crossover operator"), 
        crossover_probability: float = typer.Option(0.9, help="Crossover probability"),
        mutation: Mutation = typer.Option("PolynomialMutation", help="Mutation operator"), 
        mutation_probability: float = typer.Option(-1, help="Mutation probability. [default: 1/len(files)]", show_default=False),
        repairer: Repairer = typer.Option("StandardizationRepairer", help="Solution repairer to keep the sum of weights equal to 1"), 
        population_size: int = typer.Option(100, help="Population size"), 
        num_evaluations: int = typer.Option(25000, help="Number of evaluations"), 
        cut_off_criteria: CutOffCriteria = typer.Option("MinConfDist", case_sensitive=False, help="Criteria for determining which links will be part of the final binary matrix."), 
        cut_off_value: float = typer.Option(0.5, help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2"),
        f1_weight: float = typer.Option(0.75, help="Weight associated with the first function of the optimization process. This function tries to maximize the quality of good links (improve trust and frequency of appearance) while minimizing their quantity. It tries to establish some contrast between good and bad links so that the links finally reported are of high reliability."),
        f2_weight: float = typer.Option(0.25, help="Weight associated with the second function of the optimization process. This function tries to increase the degree (number of links) of those genes with a high potential to be considered as hubs. At the same time, it is intended that the number of genes that meet this condition should be relatively low, since this is what is usually observed in real gene networks. The objective is to promote the approximation of the network to a scale-free configuration and to move away from random structure."),
        threads: int = typer.Option(multiprocessing.cpu_count(), help="Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used."),
        graphics: bool = typer.Option(True, help="Indicate if you do not want to represent the evolution of the fitness value."),
        output_dir: Path = typer.Option(Path("./inferred_networks"), help="Path to the output folder."),
    ):
    """
        Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.
    """
    typer.echo(f"Run algorithm for {expression_data}")
    
    infer_network(
        expression_data, 
        technique, 
        output_dir
    )

    confidence_list = list(Path(f'./{output_dir}/{expression_data.stem}/lists/').glob("GRN_*.csv"))
    gene_names = Path(f'./{output_dir}/{expression_data.stem}/gene_names.txt')

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
        f1_weight,
        f2_weight,
        threads,
        graphics,
        output_dir="<<conf_list_path>>/../ea_consensus"
    )

@app.command()
def draw_network(
        confidence_list: Optional[List[str]] = typer.Option(
            ..., help="Paths of the CSV files with the confidence lists to be represented"
        ),
        mode: Mode = typer.Option("Both", help="Mode of representation"),
        nodes_distribution: NodesDistribution = typer.Option(
            "Spring", help="Node distribution in graph"
        ),
        output_folder: str = typer.Option("<<conf_list_path>>/../network_graphics", help="Path to output folder"),
    ):
    """
        Draw gene regulatory networks from confidence lists.
    """
    typer.echo(f"Draw gene regulatory networks for {', '.join(confidence_list)}")

    tmp_input_folder = "tmp/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)

    tmp_output_folder = "tmp/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    command = ""
    for file in confidence_list:
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        command += f"--confidence-list {tmp_file_dir} "
        shutil.copyfile(file, tmp_file_dir)

    client = docker.from_env()
    container = client.containers.run(
        image="eagrn-inference/draw_network",
        volumes={Path(f"./tmp/").absolute(): {"bind": f"/usr/local/src/tmp", "mode": "rw"}},
        command=f"{command} --mode {mode} --nodes-distribution {nodes_distribution} --output-folder {tmp_output_folder}",
        detach=True,
        tty=True,
    )

    r = container.wait()
    logs = container.logs()
    if logs:
        typer.echo(logs.decode("utf-8"))

    container.stop()
    container.remove(v=True)

    if str(output_folder) == "<<conf_list_path>>/../network_graphics":
        output_folder = Path(f"{Path(confidence_list[0]).parents[1]}/network_graphics/")
    
    output_folder.mkdir(exist_ok=True, parents=True)
    for f in Path(tmp_output_folder).glob('*'):
        shutil.move(f, f"{output_folder}/{f.name}")
    shutil.rmtree("tmp")


if __name__ == "__main__":
    app()