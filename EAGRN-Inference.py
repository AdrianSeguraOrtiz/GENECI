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



@app.command()
def extract_data(
        database: Optional[List[Database]] = typer.Option(..., case_sensitive=False, help="Databases for downloading expression data.")
    ):
    """
        Download differential expression data from various databases such as DREAM4, SynTReN, Rogers and GeneNetWeaver.
    """

    for db in database:
        Path(f'./expression_data/{db}/EXP/').mkdir(exist_ok=True, parents=True)
        Path(f'./expression_data/{db}/GS/').mkdir(exist_ok=True, parents=True)

        typer.echo(f"Extracting data from {db}")

        client = docker.from_env()
        container = client.containers.run(
            image="eagrn-inference/extract_data",
            volumes={Path("./expression_data/").absolute(): {"bind": "/usr/local/src/expression_data", "mode": "rw"}},
            command=db,
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
def infer_networks(
        expression_data: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns."), 
        technique: Optional[List[Technique]]= typer.Option(..., case_sensitive=False, help="Inference techniques to be performed.")
    ):
    """
        Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.
    """

    Path(f'./inferred_networks/{Path(expression_data).stem}/lists/').mkdir(exist_ok=True, parents=True)
    tmp_exp_dir = f"./inferred_networks/{Path(expression_data).name}"
    shutil.copyfile(expression_data, tmp_exp_dir)

    for tec in technique:
        typer.echo(f"Infer network from {expression_data} with {tec}")

        client = docker.from_env()
        container = client.containers.run(
            image=f"eagrn-inference/infer_networks/{tec.lower()}",
            volumes={Path("./inferred_networks/").absolute(): {"bind": "/usr/local/src/inferred_networks", "mode": "rw"}},
            command=tmp_exp_dir,
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

    gene_names = f'./inferred_networks/{Path(expression_data).stem}/gene_names.txt'
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
        gene_names: Path = typer.Option(..., exists=True, file_okay=True, help="Path to the TXT file with the name of the contemplated genes separated by comma and without space."),
        cut_off_criteria: CutOffCriteriaOnlyConf = typer.Option(..., case_sensitive=False, help="Criteria for determining which links will be part of the final binary matrix."), 
        cut_off_value: float = typer.Option(..., help="Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10")
    ):
    """
    Converts a list of confidence values into a binary matrix that represents the final gene network.
    """
    # Asegurarse de organizar correctamente la carpeta de entrada antes de llamar al jar y después deshacer.

    typer.echo(f"Apply cut to {confidence_list} with {cut_off_criteria} and value {cut_off_value}")
    


@app.command()
def optimize_ensemble(confidence_lists: str, crossover: str, mutation: str, repairer: str, population_size: str, num_evaluations: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Optimize ensemble for {confidence_lists}")


@app.command()
def evaluate(undirected_network: str, undirected_gold_standard: str):
    typer.echo(f"Evaluate {undirected_network} comparing with {undirected_gold_standard}")


@app.command()
def run(expression_data: str, technique: str, crossover: str, mutation: str, repairer: str, population_size: str, num_evaluations: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Run algorithm for {expression_data}")


if __name__ == "__main__":
    app()