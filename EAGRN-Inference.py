import typer
from typing import List, Optional
from enum import Enum
from pathlib import Path
import docker

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


@app.command()
def extract_data(database: Optional[List[Database]] = typer.Option(
        ..., case_sensitive=False, help="Databases for downloading expression data."
    )):

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
def infer_networks(expression_data: Path = typer.Option(
        ..., exists=True, file_okay=True, help="Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns."
    ), technique: Optional[List[Technique]]= typer.Option(
        ..., case_sensitive=False, help="Inference techniques to be performed."
    )):

    Path(f'./inferred_networks/{Path(expression_data).stem}/lists/').mkdir(exist_ok=True, parents=True)

    for tec in technique:
        typer.echo(f"Infer network from {expression_data} with {tec}")

        client = docker.from_env()
        container = client.containers.run(
            image=f"eagrn-inference/infer_networks/{tec.lower()}",
            volumes={Path("./inferred_networks/").absolute(): {"bind": "/usr/local/src/inferred_networks", "mode": "rw"}},
            command=str(expression_data),
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
def apply_cut(confidence_list: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Apply cut to {confidence_list} with {cut_off_criteria} and value {cut_off_value}")


@app.command()
def optimize_ensemble(confidence_lists: str, crossover: str, mutation: str, repairer: str, population_size: str, num_evaluations: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Optimize ensemble for {confidence_lists}")


@app.command()
def evaluate(undirected_network: str, undirected_gold_standard: str):
    typer.echo(f"Evaluate {undirected_network} comparing with {undirected_gold_standard}")


@app.command()
def run(expression_data: str, techniques: str, crossover: str, mutation: str, repairer: str, population_size: str, num_evaluations: str, cut_off_criteria: str, cut_off_value: str):
    typer.echo(f"Run algorithm for {expression_data}")


if __name__ == "__main__":
    app()