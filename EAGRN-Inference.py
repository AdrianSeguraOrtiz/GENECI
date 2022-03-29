import typer
from typing import List, Optional
from enum import Enum
from pathlib import Path
import docker
import shutil

app = typer.Typer()

class Database(str, Enum):
    DREAM4 = "DREAM4"
    SynTReN = "SynTReN"
    Rogers = "Rogers"
    GeneNetWeaver = "GeneNetWeaver"

class Technique(str, Enum):
    ARACNE = "ARACNE"
    BC3NET = "BC3NET"
    C3NET = "C3NET"
    CLR = "CLR"
    GENIE3 = "GENIE3"
    MRNET = "MRNET"
    MRNETB = "MRNETB"
    PCIT = "PCIT"

class CutOffCriteriaOnlyConf(str, Enum):
    MinConfidence = "MinConfidence"
    MaxNumLinksBestConf = "MaxNumLinksBestConf"

class CutOffCriteria(str, Enum):
    MinConfidence = "MinConfidence"
    MaxNumLinksBestConf = "MaxNumLinksBestConf"
    MinConfFreq = "MinConfFreq"

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

@app.command()
def extract_data(
        database: Optional[List[Database]] = typer.Option(..., case_sensitive=False, help="Databases for downloading expression data."),
        output_dir: Path = typer.Option("expression_data", help="Path to the output folder."), 
    ):
    """
        Download differential expression data from various databases such as DREAM4, SynTReN, Rogers and GeneNetWeaver.
    """

    for db in database:
        Path(f'./{output_dir}/{db}/EXP/').mkdir(exist_ok=True, parents=True)
        Path(f'./{output_dir}/{db}/GS/').mkdir(exist_ok=True, parents=True)

        typer.echo(f"Extracting data from {db}")

        client = docker.from_env()
        container = client.containers.run(
            image="eagrn-inference/extract_data",
            volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
            command=f"{db} {output_dir}",
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
        output_dir: Path = typer.Option("inferred_networks", help="Path to the output folder."),
    ):
    """
        Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.
    """

    Path(f'./{output_dir}/{Path(expression_data).stem}/lists/').mkdir(exist_ok=True, parents=True)
    tmp_exp_dir = f"./{output_dir}/{Path(expression_data).name}"
    shutil.copyfile(expression_data, tmp_exp_dir)

    for tec in technique:
        typer.echo(f"Infer network from {expression_data} with {tec}")

        client = docker.from_env()
        container = client.containers.run(
            image=f"eagrn-inference/infer_network/{tec.lower()}",
            volumes={Path(f"./{output_dir}/").absolute(): {"bind": f"/usr/local/src/{output_dir}", "mode": "rw"}},
            command=f"{tmp_exp_dir} {output_dir}",
            detach=True,
            tty=True,
        )

        r = container.wait()
        logs = container.logs()
        if logs:
            typer.echo(logs.decode("utf-8"))

        container.stop()
        container.remove(v=True)
    
    Path(tmp_exp_dir).unlink()

    gene_names = f'./{output_dir}/{Path(expression_data).stem}/gene_names.txt'
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
        output_file: Path = typer.Option("../networks/<<conf_list_name>>.csv", help="Path to the output CSV file that will contain the binary matrix resulting from the cutting operation."),
    ):
    """
    Converts a list of confidence values into a binary matrix that represents the final gene network.
    """

    typer.echo(f"Apply cut to {confidence_list} with {cut_off_criteria} and value {cut_off_value}")

    Path("tmp").mkdir(exist_ok=True, parents=True)
    tmp_confidence_list_dir = f"tmp/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    if not gene_names:
        tmp_gene_names_dir = "tmp/gene_names.txt"
        gene_list = set()
        with open(confidence_list, "r") as f:
            for row in f:
                row_list = row.split(",")
                gene_list.add(row_list[0])
                gene_list.add(row_list[1])
        
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))
    else:
        tmp_gene_names_dir = f"tmp/{Path(gene_names).name}"
        shutil.copyfile(gene_names, tmp_gene_names_dir)

    if str(output_file) == "../networks/<<conf_list_name>>.csv":
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
        crossover: Crossover = typer.Option("SBXCrossover", help="Crossover operator"), 
        mutation: Mutation = typer.Option("PolynomialMutation", help="Mutation operator"), 
        repairer: Repairer = typer.Option("GreedyRepair", help="Solution repairer to keep the sum of weights equal to 1"), 
        population_size: int = typer.Option(100, help="Population size"), 
        num_evaluations: int = typer.Option(10000, help="Number of evaluations"), 
        cut_off_criteria: CutOffCriteria = typer.Option("MinConfFreq", case_sensitive=False, help="Criteria for determining which links will be part of the final binary matrix."), 
        cut_off_value: float = typer.Option(0.2, help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfFreq = 0.2"),
        output_dir: Path = typer.Option("inferred_networks", help="Path to the output folder."),
    ):
    """
    Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm
    """
    # networkFolder = "/mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/";
    # strCrossover = "SBXCrossover";
    # strMutation = "PolynomialMutation";
    # strRepairer = "GreedyRepair";
    # populationSize = 100;
    # numEvaluations = 10000;
    # strCutOffCriteria = "MinConfFreq";
    # cutOffValue = 0.2;
    typer.echo(f"Optimize ensemble for {', '.join(confidence_list)}")


@app.command()
def evaluate(undirected_network: str, undirected_gold_standard: str):
    typer.echo(f"Evaluate {undirected_network} comparing with {undirected_gold_standard}")


@app.command()
def run(expression_data: str, technique: str, crossover: str, mutation: str, repairer: str, population_size: str, num_evaluations: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Run algorithm for {expression_data}")


if __name__ == "__main__":
    app()