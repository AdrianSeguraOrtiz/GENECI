import os
import typer
import synapseclient


def dream4(
    output_folder: str = typer.Option(..., help="Path to output folder"),
):
    """
    Download DREAM4 challenge datasets from Synapse using a Personal Access Token (PAT)
    provided via the SYNAPSE_AUTH_TOKEN environment variable.
    """

    # Obtener el token del entorno
    token = os.getenv("SYNAPSE_AUTH_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing SYNAPSE_AUTH_TOKEN environment variable. "
            "Please provide it when running the container."
        )

    # Iniciar sesión en Synapse de forma silenciosa y no interactiva
    syn = synapseclient.Synapse()
    syn.login(authToken=token, silent=True)

    # Identificadores Synapse de los datasets DREAM4
    syn_ids = [
        "syn4558440", "syn4558441", "syn4558442", "syn4558443", "syn4558444",
        "syn4558445", "syn4558446", "syn4558447", "syn4558448", "syn4558449"
    ]

    # Descargar los datasets al directorio de salida
    for sid in syn_ids:
        syn.get(sid, downloadLocation=output_folder)

    typer.echo(f"✅ Download completed successfully in: {output_folder}")


if __name__ == "__main__":
    typer.run(dream4)
