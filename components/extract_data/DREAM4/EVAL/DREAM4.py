from pathlib import Path
import pandas as pd
import typer
import synapseclient
import zipfile


def dream5(
        output_folder: str = typer.Option(..., help="Path to output folder"),
        username: str = typer.Option(..., help="Synapse account username"),
        password: str = typer.Option(..., help="Synapse account password"),
    ):

    syn = synapseclient.Synapse()
    syn.login(username, password)

    """
        self._download_data('pdf_size100_1.mat', 'syn4558445')
        self._download_data('pdf_size100_2.mat', 'syn4558446')
        self._download_data('pdf_size100_3.mat', 'syn4558447')
        self._download_data('pdf_size100_4.mat', 'syn4558448')
        self._download_data('pdf_size100_5.mat', 'syn4558449')

        self._download_data('pdf_size100_multifactorial_1.mat', 'syn4558450')
        self._download_data('pdf_size100_multifactorial_2.mat', 'syn4558451')
        self._download_data('pdf_size100_multifactorial_3.mat', 'syn4558452')
        self._download_data('pdf_size100_multifactorial_4.mat', 'syn4558453')
        self._download_data('pdf_size100_multifactorial_5.mat', 'syn4558454')

        self._download_data('pdf_size10_1.mat', 'syn4558440')
        self._download_data('pdf_size10_2.mat', 'syn4558441')
        self._download_data('pdf_size10_3.mat', 'syn4558442')
        self._download_data('pdf_size10_4.mat', 'syn4558443')
        self._download_data('pdf_size10_5.mat', 'syn4558444')
    """

    file_ids = ["net1", "net2", "net3", "net4"]

    zip_metadata = syn.get("syn2787219", downloadLocation=output_folder)
    
    zip_data = zipfile.ZipFile(zip_metadata.path)
    zip_infos = zip_data.infolist()

    for f in zip_infos:
        if not f.filename.startswith("__MACOSX") and (f.filename.endswith(".mat") or f.filename.endswith(".tsv")):
            f.filename = Path(f.filename).name
            zip_data.extract(f, f'{output_folder}/DREAM5/EVAL/')
    
    Path(zip_metadata.path).unlink()


if __name__ == "__main__":
    typer.run(dream5)