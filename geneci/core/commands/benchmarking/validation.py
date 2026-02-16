import random
import re
import shutil
import string
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px

from geneci.config import tag, temp_folder_str
from geneci.core.utils.confidence import weighted_confidence
from geneci.core.utils.docker import (
    available_images,
    client,
    get_volume,
    wait_and_close_container,
)
from geneci.core.utils.io import get_weights, write_evaluation_csv
from geneci.core.utils.plotting import plot_moving_medians, plot_polar
from geneci.enums import Challenge, EvalDatabase


def evaluation_data(
    database: Optional[List[EvalDatabase]],
    output_dir: Path = Path("./input_data"),
    username: str = None,
    password: str = None,
):
    """Download evaluation data for DREAM challenges."""

    for db in database:
        output_folder = Path(f"./{output_dir}/{db.value}/EVAL/")
        output_folder.mkdir(exist_ok=True, parents=True)

        print(f"\n Extracting evaluation data from {db.value}")

        if db == EvalDatabase.DREAM3:
            image = f"adriansegura99/geneci_extract-data_dream3:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category EvaluationData --output-folder ./EVAL/  --username {username} --password {password}"

        elif db == EvalDatabase.DREAM4:
            image = f"adriansegura99/geneci_extract-data_dream4-eval:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--output-folder ./EVAL/  --username {username} --password {password}"

        elif db == EvalDatabase.DREAM5:
            image = f"adriansegura99/geneci_extract-data_dream5:{tag}"
            if image not in available_images:
                print("Downloading docker image ...")
                client.images.pull(repository=image)
            command = f"--category EvaluationData --output-folder ./EVAL/  --username {username} --password {password}"

        container = client.containers.run(
            image=image,
            volumes=get_volume(output_folder),
            command=command,
            detach=True,
            tty=True,
        )

        logs, _ = wait_and_close_container(container)
        print(logs)


def dream_list_of_links(
    challenge: Challenge,
    network_id: str,
    synapse_file: List[Path],
    confidence_list: Path,
):
    """Evaluate one confidence list against DREAM challenge data."""

    print(
        f"Evaluate {confidence_list} prediction for {network_id} network in {challenge.value} challenge"
    )

    Path(f"{temp_folder_str}/synapse/").mkdir(exist_ok=True, parents=True)

    tmp_synapse_files_dir = f"{temp_folder_str}/synapse/"
    for f in synapse_file:
        shutil.copyfile(f, tmp_synapse_files_dir + Path(f).name)

    tmp_confidence_list_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    shutil.copyfile(confidence_list, tmp_confidence_list_dir)

    image = f"adriansegura99/geneci_evaluate_dream-prediction:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"--challenge {challenge.value} --network-id {network_id} --synapse-folder {tmp_synapse_files_dir} --confidence-list {tmp_confidence_list_dir}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    shutil.rmtree(temp_folder_str)

    return logs


def dream_weight_distribution(
    challenge: Challenge,
    network_id: str,
    synapse_file: List[Path],
    weight_file_summand: Optional[List[str]],
):
    """Evaluate one weighted confidence distribution in a DREAM challenge."""

    second_temp_folder_str = "tmp-" + "".join(
        random.choices(string.ascii_lowercase, k=10)
    )

    weighted_confidence(
        weight_file_summand=weight_file_summand,
        output_file=Path(f"./{second_temp_folder_str}/temporal_list.csv"),
    )

    values = dream_list_of_links(
        challenge=challenge,
        network_id=network_id,
        synapse_file=synapse_file,
        confidence_list=f"./{second_temp_folder_str}/temporal_list.csv",
    )

    shutil.rmtree(second_temp_folder_str)

    return values


def dream_pareto_front(
    challenge: Challenge,
    network_id: str,
    synapse_file: List[Path],
    weights_file: Path,
    fitness_file: Path,
    confidence_folder: Path,
    output_dir: Path = "<<weights_file_dir>>",
    plot_metrics: bool = True,
):
    """Evaluate a full Pareto front in a DREAM challenge."""

    if str(output_dir) == "<<weights_file_dir>>":
        output_dir = Path(weights_file).parent
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    filenames, weights = get_weights(weights_file)

    auprs = []
    aurocs = []

    for solution in weights:
        weight_file_summand = []
        for i in range(len(solution)):
            weight_file_summand.append(
                f"{solution[i]}*{confidence_folder}/{filenames[i]}"
            )

        values = dream_weight_distribution(
            challenge=challenge,
            network_id=network_id,
            synapse_file=synapse_file,
            weight_file_summand=weight_file_summand,
        )

        str_aupr = re.search("AUPR: (.*)\\n", values)
        auprs.append(float(str_aupr.group(1)))
        str_auroc = re.search("AUROC: (.*)\\n", values)
        aurocs.append(float(str_auroc.group(1)))

    acc_means = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs, aurocs)]

    auprs_scaled = (np.array(auprs) - min(auprs)) / (max(auprs) - min(auprs))
    aurocs_scaled = (np.array(aurocs) - min(aurocs)) / (max(aurocs) - min(aurocs))
    score = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs_scaled, aurocs_scaled)]

    fitness_df = pd.read_csv(fitness_file)
    objective_labels = list(fitness_df.columns)

    evaluation_df = pd.DataFrame(
        data={"score": score, "acc_mean": acc_means, "aupr": auprs, "auroc": aurocs}
    )
    df = pd.concat([fitness_df, evaluation_df], axis=1)

    sorted_idx = np.argsort([-s for s in score])

    write_evaluation_csv(
        f"{output_dir}/evaluated_front.csv",
        sorted_idx,
        [f"{confidence_folder}/{f}" for f in filenames],
        objective_labels,
        weights,
        df.copy(),
    )

    if plot_metrics:
        fig = px.parallel_coordinates(
            df,
            color="acc_mean",
            dimensions=df.columns,
            color_continuous_scale=px.colors.sequential.Blues,
            title="Evaluated graph of parallel coordinates",
        )
        fig.write_html(f"{output_dir}/evaluated_parallel_coordinates.html")

        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUROC",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUROC.pdf",
        )
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUPR",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUPR.pdf",
        )

        for fitness_func in objective_labels:
            plot_moving_medians(
                file_path=f"{output_dir}/evaluated_front.csv",
                x=fitness_func,
                y=filenames,
                normalized=False,
                label="Techniques Weights",
                output_path=f"{output_dir}/moving_medians_techniches_vs_{fitness_func}.pdf",
            )

        auprs = {}
        aurocs = {}
        for f in filenames:
            values = dream_list_of_links(
                challenge=challenge,
                network_id=network_id,
                synapse_file=synapse_file,
                confidence_list=f"{confidence_folder}/{f}",
            )

            str_aupr = re.search("AUPR: (.*)\\n", values)
            auprs[f] = float(str_aupr.group(1))
            str_auroc = re.search("AUROC: (.*)\\n", values)
            aurocs[f] = float(str_auroc.group(1))

        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=aurocs,
            metric="AUROC",
            output_path=f"{output_dir}/polar_plot_AUROC.pdf",
        )

        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=auprs,
            metric="AUPR",
            output_path=f"{output_dir}/polar_plot_AUPR.pdf",
        )


def generic_list_of_links(
    confidence_list: Path,
    gs_binary_matrix: Path,
):
    """Evaluate one confidence list against a generic gold standard."""

    print(
        f"Evaluate {confidence_list} prediction with respect {gs_binary_matrix} gold standard"
    )

    Path(temp_folder_str).mkdir(exist_ok=True)

    with open(gs_binary_matrix) as f:
        gene_names = f.readline().replace("\n", "").replace('"', "").split(",")
        del gene_names[0]

    df = pd.DataFrame(0.0, index=gene_names, columns=gene_names)
    with open(confidence_list, "r") as f:
        lines = f.readlines()
    for line in lines:
        vline = line.replace("\n", "").split(",")
        df.at[vline[0], vline[1]] = float(vline[2])

    tmp_inferred_matrix_dir = f"{temp_folder_str}/{Path(confidence_list).name}"
    df.to_csv(tmp_inferred_matrix_dir, sep=",")

    tmp_gsbm_dir = f"{temp_folder_str}/{Path(gs_binary_matrix).name}"
    shutil.copyfile(gs_binary_matrix, tmp_gsbm_dir)

    image = f"adriansegura99/geneci_evaluate_generic-prediction:{tag}"

    if image not in available_images:
        print("Downloading docker image ...")
        client.images.pull(repository=image)

    container = client.containers.run(
        image=image,
        volumes=get_volume(temp_folder_str),
        command=f"{tmp_inferred_matrix_dir} {tmp_gsbm_dir}",
        detach=True,
        tty=True,
    )

    logs, _ = wait_and_close_container(container)
    print(logs)

    shutil.rmtree(temp_folder_str)

    return logs


def generic_weight_distribution(
    weight_file_summand: Optional[List[str]],
    gs_binary_matrix: Path,
):
    """Evaluate one weighted confidence distribution against a generic gold standard."""

    second_temp_folder_str = "tmp-" + "".join(
        random.choices(string.ascii_lowercase, k=10)
    )

    weighted_confidence(
        weight_file_summand=weight_file_summand,
        output_file=Path(f"./{second_temp_folder_str}/temporal_list.csv"),
    )

    values = generic_list_of_links(
        confidence_list=f"./{second_temp_folder_str}/temporal_list.csv",
        gs_binary_matrix=gs_binary_matrix,
    )

    shutil.rmtree(second_temp_folder_str)

    return values


def generic_pareto_front(
    weights_file: Path,
    fitness_file: Path,
    confidence_folder: Path,
    gs_binary_matrix: Path,
    output_dir: Path = "<<weights_file_dir>>",
    plot_metrics: bool = True,
):
    """Evaluate a full Pareto front against a generic gold standard."""

    if str(output_dir) == "<<weights_file_dir>>":
        output_dir = Path(weights_file).parent
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    filenames, weights = get_weights(weights_file)

    auprs = []
    aurocs = []

    for solution in weights:
        weight_file_summand = []
        for i in range(len(solution)):
            weight_file_summand.append(
                f"{solution[i]}*{confidence_folder}/{filenames[i]}"
            )

        values = generic_weight_distribution(
            weight_file_summand=weight_file_summand,
            gs_binary_matrix=gs_binary_matrix,
        )

        str_aupr = re.search('AUPR: (.*)"', values)
        auprs.append(float(str_aupr.group(1)))
        str_auroc = re.search('AUROC: (.*)"', values)
        aurocs.append(float(str_auroc.group(1)))

    acc_means = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs, aurocs)]

    auprs_scaled = (np.array(auprs) - min(auprs)) / (max(auprs) - min(auprs))
    aurocs_scaled = (np.array(aurocs) - min(aurocs)) / (max(aurocs) - min(aurocs))
    score = [(aupr + auroc) / 2 for aupr, auroc in zip(auprs_scaled, aurocs_scaled)]

    fitness_df = pd.read_csv(fitness_file)
    objective_labels = list(fitness_df.columns)

    evaluation_df = pd.DataFrame(
        data={"score": score, "acc_mean": acc_means, "aupr": auprs, "auroc": aurocs}
    )
    df = pd.concat([fitness_df, evaluation_df], axis=1)

    sorted_idx = np.argsort([-s for s in score])

    write_evaluation_csv(
        f"{output_dir}/evaluated_front.csv",
        sorted_idx,
        [f"{confidence_folder}/{f}" for f in filenames],
        objective_labels,
        weights,
        df.copy(),
    )

    if plot_metrics:
        fig = px.parallel_coordinates(
            df,
            color="acc_mean",
            dimensions=df.columns,
            color_continuous_scale=px.colors.sequential.Blues,
            title="Evaluated graph of parallel coordinates",
        )
        fig.write_html(f"{output_dir}/evaluated_parallel_coordinates.html")

        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUROC",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUROC.pdf",
        )
        plot_moving_medians(
            file_path=f"{output_dir}/evaluated_front.csv",
            x="AUPR",
            y=objective_labels,
            normalized=True,
            label="Normalized Objectives Scores",
            output_path=f"{output_dir}/moving_medians_objectives_vs_AUPR.pdf",
        )

        for fitness_func in objective_labels:
            plot_moving_medians(
                file_path=f"{output_dir}/evaluated_front.csv",
                x=fitness_func,
                y=filenames,
                normalized=False,
                label="Techniques Weights",
                output_path=f"{output_dir}/moving_medians_techniches_vs_{fitness_func}.pdf",
            )

        auprs = {}
        aurocs = {}
        for f in filenames:
            values = generic_list_of_links(
                confidence_list=f"{confidence_folder}/{f}",
                gs_binary_matrix=gs_binary_matrix,
            )

            str_aupr = re.search('AUPR: (.*)"', values)
            auprs[f] = float(str_aupr.group(1))
            str_auroc = re.search('AUROC: (.*)"', values)
            aurocs[f] = float(str_auroc.group(1))

        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=aurocs,
            metric="AUROC",
            output_path=f"{output_dir}/polar_plot_AUROC.pdf",
        )

        plot_polar(
            file_path=f"{output_dir}/evaluated_front.csv",
            techniques_dict_scores=auprs,
            metric="AUPR",
            output_path=f"{output_dir}/polar_plot_AUPR.pdf",
        )


__all__ = [
    "evaluation_data",
    "dream_list_of_links",
    "dream_weight_distribution",
    "dream_pareto_front",
    "generic_list_of_links",
    "generic_weight_distribution",
    "generic_pareto_front",
]
