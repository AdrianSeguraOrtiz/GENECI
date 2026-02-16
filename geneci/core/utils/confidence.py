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


def weighted_confidence(
    weight_file_summand: Optional[List[str]],
    output_file: Path = "<<conf_list_path>>/../weighted_confidence.csv",
):
    """Compute weighted confidence aggregation over multiple confidence lists."""

    print("\n Calculating the weighted sum of confidence levels")

    tmp_input_folder = f"{temp_folder_str}/input"
    Path(tmp_input_folder).mkdir(exist_ok=True, parents=True)

    tmp_output_folder = f"{temp_folder_str}/output"
    Path(tmp_output_folder).mkdir(exist_ok=True, parents=True)

    tmp_output_file = f"{tmp_output_folder}/{Path(output_file).name}"

    sum_weights = 0
    command = ""

    for summand in weight_file_summand:
        pair = summand.split("*")

        if len(pair) != 2:
            raise ValueError(
                f"The entry {summand} is invalid, remember to separate weight and file name by the '*' character"
            )

        weight = pair[0]
        sum_weights += float(weight)

        file = pair[1]

        tmp_file_dir = f"{tmp_input_folder}/{Path(file).name}"
        shutil.copyfile(file, tmp_file_dir)

        command += f" {weight}*{tmp_file_dir}"

    if abs(sum_weights - 1) > 0.01:
        raise ValueError("The sum of the weights must be 1")

    image = f"adriansegura99/geneci_weighted-confidence:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_output_file} {command}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    if str(output_file) == "<<conf_list_path>>/../weighted_confidence.csv":
        output_file = Path(f"{Path(file).parent.parent}/weighted_confidence.csv")
    Path(output_file).parent.mkdir(exist_ok=True, parents=True)

    shutil.move(tmp_output_file, output_file)
    shutil.rmtree(temp_folder_str)


__all__ = ["weighted_confidence"]
