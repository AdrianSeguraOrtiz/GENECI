import shutil
from pathlib import Path
from typing import List, Optional

from geneci.config import tag, temp_folder_str
from geneci.core.utils.docker import (
    available_images,
    client,
    get_volume,
    wait_and_close_container,
)
from geneci.enums import Mode, NodesDistribution


def draw_network(
    confidence_list: Optional[List[str]],
    mode: Mode = Mode.Interactive2D,
    nodes_distribution: NodesDistribution = NodesDistribution.Spring,
    confidence_cut_off: float = 0.5,
    output_folder: Path = "<<conf_list_path>>/../network_graphics",
):
    """Draw gene regulatory networks from confidence lists."""

    print(f"\n Draw gene regulatory networks for {', '.join(confidence_list)}")

    tmp_input_folder = f"{temp_folder_str}/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)

    tmp_output_folder = f"{temp_folder_str}/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    command = ""
    for file in confidence_list:
        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        command += f"--confidence-list {tmp_file_dir} "
        shutil.copyfile(file, tmp_file_dir)

    image = f"adriansegura99/geneci_draw-network:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{command} --mode {mode.value} --nodes-distribution {nodes_distribution.value} --confidence-cut-off {confidence_cut_off} --output-folder {tmp_output_folder}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    if str(output_folder) == "<<conf_list_path>>/../network_graphics":
        output_folder = Path(
            f"{Path(confidence_list[0]).parent.parent}/network_graphics/"
        )
    Path(output_folder).mkdir(exist_ok=True, parents=True)

    for f in Path(tmp_output_folder).glob("*"):
        shutil.move(f, f"{output_folder}/{f.name}")

    shutil.rmtree(temp_folder_str)


__all__ = ["draw_network"]
