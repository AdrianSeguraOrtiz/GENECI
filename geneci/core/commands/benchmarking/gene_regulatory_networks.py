import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests

from geneci.config import tag, temp_folder_str
from geneci.core.utils.docker import (
    available_images,
    client,
    get_volume,
    wait_and_close_container,
)
from geneci.enums import Database, FromRealGenerateDatabase, real_networks_dict


def download_real_network(
    database: FromRealGenerateDatabase,
    id: str,
    output_dir: Path = Path("./input_data"),
):
    """Download and normalize real GRN interaction lists for simulation workflows."""

    print(f"Downloading real network {id} from {database.value} database")

    if id not in real_networks_dict[database.value]:
        print("The entered id is not available in the selected database.")
        print(f"Please choose one of the following: {real_networks_dict[database.value]}")
        raise ValueError("Invalid network identifier for the selected database.")

    sep = "\t"
    header = 0
    is_zip = False
    if database == FromRealGenerateDatabase.TFLink:
        link = f"https://cdn.netbiol.org/tflink/download_files/TFLink_{id}_interactions_SS_simpleFormat_v1.0.tsv"
    elif database == FromRealGenerateDatabase.RegulonDB:
        link = "http://regulondb.ccg.unam.mx/menu/download/datasets/files/NetWorkTFGene.txt"
    elif database == FromRealGenerateDatabase.RegNetwork:
        link = "https://regnetworkweb.org/download/RegulatoryDirections.zip"
        net_file = f"new_kegg.{id}.reg.direction.txt"
        sep = " "
        header = None
        is_zip = True
    elif database == FromRealGenerateDatabase.BioGrid:
        link = "https://downloads.thebiogrid.org/Download/BioGRID/Release-Archive/BIOGRID-4.4.218/BIOGRID-ORGANISM-4.4.218.tab3.zip"
        net_file = f"BIOGRID-ORGANISM-{id}-4.4.218.tab3.txt"
        header = None
        is_zip = True
    elif database == FromRealGenerateDatabase.GRNdb:
        link = f"http://www.grndb.com/download/txt?condition={id}"
    else:
        print(
            "The selected database is not currently available, please choose another one."
        )
        raise ValueError("Unsupported database.")

    tmp_folder = Path(temp_folder_str)
    tmp_folder.mkdir(exist_ok=True, parents=True)

    local_tmp_file = f"{temp_folder_str}/raw_real_network.tsv"

    with requests.get(link, stream=True, verify=False) as r:
        if is_zip:
            zip_file = zipfile.ZipFile(BytesIO(r.content))
            zip_file.extract(net_file, temp_folder_str)
            shutil.move(f"{temp_folder_str}/{net_file}", local_tmp_file)
        else:
            with open(local_tmp_file, "wb") as f:
                shutil.copyfileobj(r.raw, f)

    df = pd.read_csv(local_tmp_file, sep=sep, header=header, comment="#")

    if database == FromRealGenerateDatabase.TFLink:
        df = df[["Name.TF", "Name.Target", "Detection.method"]]
        df = df[df["Name.Target"] != "-"]
        df[["Name.TF", "Name.Target"]] = df[["Name.TF", "Name.Target"]].replace(
            {",|;": "-"}, regex=True
        )
        cnt = 0
        while len(df.index) > 500:
            df = df[df["Detection.method"].str.count(";") > cnt]
            cnt += 1
        df["Detection.method"] = 1
    elif database == FromRealGenerateDatabase.RegulonDB:
        df = df.iloc[:, [1, 4, 5, 6]]
        df.columns = ["Name.TF", "Name.Target", "Regulation.Sign", "Confidence"]
        df = df[df["Confidence"] != "Weak"]
        df = df[df["Regulation.Sign"] != "?"]
        df = df.iloc[:, [0, 1, 2]]
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["+"], 1)
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["-"], -1)
    elif database == FromRealGenerateDatabase.RegNetwork:
        df = df.iloc[:, [0, 2, 4]]
        df.columns = ["Name.TF", "Name.Target", "Regulation.Sign"]
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["-->"], 1)
        df["Regulation.Sign"] = df["Regulation.Sign"].replace(["--|", "-/-", "-p"], -1)
    elif database == FromRealGenerateDatabase.BioGrid:
        df = df.iloc[:, [7, 8]]
        df.insert(2, "Sign", 1)
    elif database == FromRealGenerateDatabase.GRNdb:
        df = df[["TF", "gene", "Confidence"]]
        df = df[df["Confidence"] == "High"]
        df["Confidence"] = 1
    else:
        print(
            "The selected database is not currently available, please choose another one."
        )
        raise ValueError("Unsupported database.")

    df = df.drop_duplicates()

    output_folder = f"{output_dir}/simulated_based_on_real/RAW/"
    Path(output_folder).mkdir(exist_ok=True, parents=True)
    df.to_csv(f"{output_folder}/{database.value}_{id}.tsv", header=False, index=False)

    shutil.rmtree(temp_folder_str)


def gold_standard(
    database: Optional[List[Database]],
    output_dir: Path = Path("./input_data"),
    username: str = None,
    password: str = None,
):
    """Download benchmark gold-standard networks."""

    if (Database.DREAM3 in database or Database.DREAM5 in database) and (
        not username or not password
    ):
        print(
            "You must enter your Synapse credentials in order to download some of the selected data."
        )
        raise ValueError("Missing Synapse credentials.")

    for db in database:
        output_folder = Path(f"./{output_dir}/{db.value}/GS/")
        output_folder.mkdir(exist_ok=True, parents=True)

        print(f"\n Extracting gold standards from {db.value}")

        if db == Database.DREAM3:
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category GoldStandard --output-folder ./GS/  --username {username} --password {password}"

        elif db == Database.DREAM4:
            image = f"adriansegura99/geneci_extract-data_dream4-expgs:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = "GoldStandard ./GS/ "

        elif db == Database.DREAM5:
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category GoldStandard --output-folder ./GS/  --username {username} --password {password}"

        elif db == Database.IRMA:
            image = f"adriansegura99/geneci_extract-data_irma:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = "GoldStandard ./GS/ "

        else:
            image = f"adriansegura99/geneci_extract-data_grndata:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"{db.value} GoldStandard ./GS/ "

        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        logs, _ = wait_and_close_container(container)
        print(logs)


__all__ = ["download_real_network", "gold_standard"]
