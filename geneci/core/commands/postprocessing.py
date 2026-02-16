import shutil
from pathlib import Path

from geneci.config import tag, temp_folder_str
from geneci.core.utils.docker import (
    available_images,
    client,
    get_volume,
    wait_and_close_container,
)
from geneci.core.utils.io import get_gene_names_from_conf_list
from geneci.enums import CutOffCriteria


def apply_cut(
    confidence_list: Path,
    gene_names: Path = None,
    cut_off_criteria: CutOffCriteria = None,
    cut_off_value: float = None,
    output_file: Path = "<<conf_list_path>>/../networks/<<conf_list_name>>.csv",
):
    """Convert a confidence list into a binary network matrix."""

    print(
        f"Apply cut to {confidence_list} with {cut_off_criteria.value} and value {cut_off_value}"
    )

    Path(temp_folder_str).mkdir(exist_ok=True, parents=True)
    tmp_confidence_list_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    tmp_gene_names_dir = f"{temp_folder_str}/gene_names.txt"

    if gene_names:
        shutil.copyfile(gene_names, tmp_gene_names_dir)
    else:
        gene_list = get_gene_names_from_conf_list(confidence_list)
        with open(tmp_gene_names_dir, "w") as f:
            f.write(",".join(sorted(gene_list)))

    if str(output_file) == "<<conf_list_path>>/../networks/<<conf_list_name>>.csv":
        output_file = Path(
            f"{Path(confidence_list).parent.parent}/networks/{Path(confidence_list).name}"
        )
    Path(output_file).parent.mkdir(exist_ok=True, parents=True)

    image = f"adriansegura99/geneci_apply-cut:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_confidence_list_dir} {tmp_gene_names_dir} {temp_folder_str}/{Path(output_file).name} {cut_off_criteria.value} {cut_off_value}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    shutil.copyfile(f"{temp_folder_str}/{Path(output_file).name}", output_file)
    shutil.rmtree(temp_folder_str)


__all__ = ["apply_cut"]
