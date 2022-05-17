import typer
from typing import List, Optional
import networkx as nx

def draw_network(
        confidence_list: Optional[List[str]] = typer.Option(..., help="Paths of the CSV files with the confidence lists to be represented."),
    ):

    print("Hola")


if __name__ == "__main__":
    typer.run(draw_network)