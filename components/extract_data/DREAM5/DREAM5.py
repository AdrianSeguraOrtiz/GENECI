from pathlib import Path
import typer
import synapseclient

def dream5(
        output_folder: str = typer.Argument(..., help="Path to output folder"),
        username: str = typer.Argument(..., help="Synapse account username"),
        password: str = typer.Argument(..., help="Synapse account password"),
    ):

    syn = synapseclient.Synapse()
    syn.login(username, password)

    syn.get("syn2787209", downloadLocation=output_folder)

if __name__ == "__main__":
    typer.run(dream5)