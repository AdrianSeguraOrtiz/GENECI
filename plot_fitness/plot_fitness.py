from posixpath import dirname
import typer
import matplotlib.pyplot as plt

from pathlib import Path

def plot_fitness(
    input_file: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
        help="Path to the input file with the vector of fitness values",
    )
):
    """
    Description: \n
    This script is in charge of plotting the fitness values obtained during the execution of the evolutionary algorithm.

    Example: \n
    >>> python ./plot_fitness/plot_fitness.py --input-file ./inferred_networks/dream4_010_01_exp/ea_consensus/fitness_evolution.txt
    """

    f = open(input_file, "r")
    str_line = f.readline()
    str_vector = str_line.split(", ")
    vector = [float(i) for i in str_vector]
    
    plt.plot(vector)
    plt.title("Fitness evolution")
    plt.ylabel("Fitness")
    plt.xlabel("Generation")
    plt.savefig(dirname(input_file) + "/fitness_evolution.pdf")


if __name__ == "__main__":
    typer.run(plot_fitness)