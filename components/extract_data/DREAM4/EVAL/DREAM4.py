import typer
import synapseclient


def dream4(
        output_folder: str = typer.Option(..., help="Path to output folder"),
        username: str = typer.Option(..., help="Synapse account username"),
        password: str = typer.Option(..., help="Synapse account password"),
    ):

    syn = synapseclient.Synapse()
    syn.login(username, password)

    syn_ids = ["syn4558440", "syn4558441", "syn4558442", "syn4558443", "syn4558444", "syn4558445", "syn4558446", "syn4558447", "syn4558448", "syn4558449"]

    for id in syn_ids:
        syn.get(id, downloadLocation = output_folder)


if __name__ == "__main__":
    typer.run(dream4)