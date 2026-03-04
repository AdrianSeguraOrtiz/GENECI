import colorsys
import math
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.cm import viridis
from matplotlib.path import Path
from sklearn.preprocessing import MaxAbsScaler
from tqdm import tqdm


def delete_common_prefix_and_sufix(lista):
    # Find common prefix
    prefijo_comun = os.path.commonprefix(lista)

    # Remove common prefix from each element
    lista_sin_prefijo = [s[len(prefijo_comun) :] for s in lista]

    # Find common suffix (reverse strings, find common prefix, reverse again)
    sufijo_comun = os.path.commonprefix([s[::-1] for s in lista])[::-1]

    # Remove common suffix from each element
    lista_final = [
        s[: -len(sufijo_comun)] if sufijo_comun else s for s in lista_sin_prefijo
    ]

    return lista_final


def polar_to_cartesian(r, theta):
    return np.array([r * np.cos(theta), r * np.sin(theta)])


def draw_sector(
    start_angle=0,
    end_angle=60,
    radius=1.0,
    width=0.2,
    lw=2,
    ls="-",
    ax=None,
    fc=(1, 0, 0),
    ec=(0, 0, 0),
    z_order=1,
):
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle
    start_angle *= np.pi / 180.0
    end_angle *= np.pi / 180.0

    # https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
    opt = 4.0 / 3.0 * np.tan((end_angle - start_angle) / 4.0) * radius
    inner = radius * (1 - width)

    verts_path = [
        polar_to_cartesian(radius, start_angle),
        polar_to_cartesian(radius, start_angle)
        + polar_to_cartesian(opt, start_angle + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle)
        + polar_to_cartesian(opt, end_angle - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle),
        polar_to_cartesian(inner, end_angle),
        polar_to_cartesian(inner, end_angle)
        + polar_to_cartesian(opt * (1 - width), end_angle - 0.5 * np.pi),
        polar_to_cartesian(inner, start_angle)
        + polar_to_cartesian(opt * (1 - width), start_angle + 0.5 * np.pi),
        polar_to_cartesian(inner, start_angle),
        polar_to_cartesian(radius, start_angle),
    ]

    codes_paths = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]

    if ax is None:
        return verts_path, codes_paths
    else:
        path = Path(verts_path, codes_paths)
        patch = patches.PathPatch(
            path, facecolor=fc, edgecolor=ec, lw=lw, linestyle=ls, zorder=z_order
        )
        ax.add_patch(patch)
        return patch


def draw_chord(
    start_angle1=0,
    end_angle1=60,
    start_angle2=180,
    end_angle2=240,
    radius=1.0,
    chord_width=0.7,
    ax=None,
    color=(1, 0, 0),
):
    if start_angle1 > end_angle1:
        start_angle1, end_angle1 = end_angle1, start_angle1
    if start_angle2 > end_angle2:
        start_angle2, end_angle2 = end_angle2, start_angle2
    start_angle1 *= np.pi / 180.0
    end_angle1 *= np.pi / 180.0
    start_angle2 *= np.pi / 180.0
    end_angle2 *= np.pi / 180.0

    opt_angle1 = 4.0 / 3.0 * np.tan((end_angle1 - start_angle1) / 4.0) * radius
    opt_angle2 = 4.0 / 3.0 * np.tan((end_angle2 - start_angle2) / 4.0) * radius
    rchord = radius * (1 - chord_width)

    verts_path = [
        polar_to_cartesian(radius, start_angle1),
        polar_to_cartesian(radius, start_angle1)
        + polar_to_cartesian(opt_angle1, start_angle1 + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle1)
        + polar_to_cartesian(opt_angle1, end_angle1 - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle1),
        polar_to_cartesian(rchord, end_angle1),
        polar_to_cartesian(rchord, start_angle2),
        polar_to_cartesian(radius, start_angle2),
        polar_to_cartesian(radius, start_angle2)
        + polar_to_cartesian(opt_angle2, start_angle2 + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle2)
        + polar_to_cartesian(opt_angle2, end_angle2 - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle2),
        polar_to_cartesian(rchord, end_angle2),
        polar_to_cartesian(rchord, start_angle1),
        polar_to_cartesian(radius, start_angle1),
    ]

    codes_path = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
    ]

    if ax is None:
        return verts_path, codes_path
    else:
        path = Path(verts_path, codes_path)
        patch = patches.PathPatch(
            path, facecolor=color + (0.5,), edgecolor=color + (0.4,), lw=2, alpha=0.5
        )
        ax.add_patch(patch)
        return patch


def hover_over_bin(event, handle_tickers, handle_plots, colors, fig):
    for iobj, obj_bins in enumerate(handle_tickers):
        for ibin, bin_patch in enumerate(obj_bins):
            cont, ind = bin_patch.contains(event)
            if cont:
                if plt.getp(bin_patch, "facecolor") == (1, 1, 1, 1):
                    plt.setp(bin_patch, facecolor=colors[iobj])
                    for h in handle_plots[iobj][ibin]:
                        h.set_visible(True)
                else:
                    plt.setp(bin_patch, facecolor=(1, 1, 1, 1))
                    for h in handle_plots[iobj][ibin]:
                        h.set_visible(False)
                break

        fig.canvas.draw_idle()


def chord_diagram(
    solutions: pd.DataFrame,
    nbins="auto",
    ax=None,
    prop_labels=dict(fontsize=12, ha="center", va="center"),
    pad=6,
):
    points_matrix = np.array(solutions.values.tolist())
    (npoints, nobj) = np.shape(points_matrix)

    hsv_tuples = [(x * 1.0 / nobj, 0.5, 0.5) for x in range(nobj)]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))

    if ax is None:
        fig = plt.figure(figsize=(6, 6))
        ax = plt.axes([0, 0, 1, 1], aspect="equal")

    ax.set_xlim(-2.3, 2.3)
    ax.set_ylim(-2.3, 2.3)
    ax.axis("off")

    y = np.array([1.0 / nobj] * nobj) * (360 - pad * nobj)
    sector_angles = []
    labels_pos_and_ros = []

    start_angle = 0
    for i in range(nobj):
        end_angle = start_angle + y[i]
        sector_angles.append((start_angle, end_angle))
        angle_diff = 0.5 * (start_angle + end_angle)
        if -30 <= angle_diff <= 210:
            angle_diff -= 90
        else:
            angle_diff -= 270
        angle_text = start_angle - 2.5
        if -30 <= angle_text <= 210:
            angle_text -= 90
        else:
            angle_text -= 270

        labels_pos_and_ros.append(
            tuple(
                polar_to_cartesian(1.0, 0.5 * (start_angle + end_angle) * np.pi / 180.0)
            )
            + (angle_diff,)
            + tuple(polar_to_cartesian(0.725, (start_angle - 2.5) * np.pi / 180.0))
            + (angle_text,)
            + tuple(polar_to_cartesian(0.85, (start_angle - 2.5) * np.pi / 180.0))
            + (angle_text,)
        )
        start_angle = end_angle + pad

    arc_points = []
    for point in points_matrix:
        arc_points.append([])
        idim = 0

        for _ in point:
            angle_point = (
                sector_angles[idim][0]
                + (sector_angles[idim][1] - sector_angles[idim][0]) * point[idim]
            )
            arc_points[-1].append((angle_point, angle_point))
            idim = idim + 1

    max_hist_values = []
    handle_tickers = []
    handle_plots = []

    for iobj in tqdm(range(nobj), ascii=True, desc="Chord diagram"):
        draw_sector(
            start_angle=sector_angles[iobj][0],
            end_angle=sector_angles[iobj][1],
            radius=0.925,
            width=0.225,
            ax=ax,
            fc=(1, 1, 1, 0.0),
            ec=(0, 0, 0),
            lw=2,
            z_order=10,
        )
        draw_sector(
            start_angle=sector_angles[iobj][0],
            end_angle=sector_angles[iobj][1],
            radius=0.925,
            width=0.05,
            ax=ax,
            fc=colors[iobj],
            ec=(0, 0, 0),
            lw=2,
            z_order=10,
        )
        draw_sector(
            start_angle=sector_angles[iobj][0],
            end_angle=sector_angles[iobj][1],
            radius=0.7 + 0.15,
            width=0.0,
            ax=ax,
            fc=colors[iobj],
            ec=colors[iobj],
            lw=2,
            ls=":",
            z_order=5,
        )

        hist_values, bins_dim = np.histogram(points_matrix[:, iobj], bins=nbins)
        relative_height_bin_pre = 0.025
        max_hist_values.append(max(hist_values))
        handle_tickers.append([])
        handle_plots.append([])

        for index_bin in range(len(hist_values)):
            start_angle_bin = (
                sector_angles[iobj][0]
                + (sector_angles[iobj][1] - sector_angles[iobj][0])
                * bins_dim[index_bin]
            )
            end_angle_bin = (
                sector_angles[iobj][0]
                + (sector_angles[iobj][1] - sector_angles[iobj][0])
                * bins_dim[index_bin + 1]
            )
            relative_height_bin = max(
                0.15 * hist_values[index_bin] / max(hist_values), 0.025
            )

            handle_tickers[-1].append(
                draw_sector(
                    start_angle=start_angle_bin,
                    end_angle=end_angle_bin,
                    radius=0.69,
                    width=0.08,
                    ax=ax,
                    lw=1,
                    fc=(1, 1, 1),
                    ec=(0, 0, 0),
                )
            )
            handle_plots[-1].append([])

            draw_sector(
                start_angle=start_angle_bin,
                end_angle=end_angle_bin,
                radius=0.7 + relative_height_bin,
                width=0,
                ax=ax,
                lw=1,
                fc=colors[iobj],
                ec=colors[iobj],
            )
            plot_point1 = polar_to_cartesian(
                0.7 + relative_height_bin_pre, start_angle_bin * np.pi / 180.0
            )
            plot_point2 = polar_to_cartesian(
                0.7 + relative_height_bin, start_angle_bin * np.pi / 180.0
            )
            plt.plot(
                [plot_point1[0], plot_point2[0]],
                [plot_point1[1], plot_point2[1]],
                c=colors[iobj],
                lw=1,
            )
            relative_height_bin_pre = relative_height_bin

            if index_bin == len(hist_values) - 1:
                plot_point1 = polar_to_cartesian(
                    0.7 + relative_height_bin, end_angle_bin * np.pi / 180.0
                )
                plot_point2 = polar_to_cartesian(0.725, end_angle_bin * np.pi / 180.0)
                plt.plot(
                    [plot_point1[0], plot_point2[0]],
                    [plot_point1[1], plot_point2[1]],
                    c=colors[iobj],
                    lw=1,
                )

            for ipoint in range(len(points_matrix)):
                plot_point1 = polar_to_cartesian(
                    0.6, arc_points[ipoint][iobj][0] * np.pi / 180.0
                )
                plot_point2 = polar_to_cartesian(
                    0.6, arc_points[ipoint][iobj][0] * np.pi / 180.0
                )
                plt.plot(
                    [plot_point1[0], plot_point2[0]],
                    [plot_point1[1], plot_point2[1]],
                    marker="o",
                    markersize=3,
                    c=colors[iobj],
                    lw=2,
                )

                if (
                    bins_dim[index_bin]
                    < points_matrix[ipoint, iobj]
                    <= bins_dim[index_bin + 1]
                ):
                    for jdim in range(nobj):
                        if jdim >= 1:
                            handle_plots[iobj][index_bin].append(
                                draw_chord(
                                    arc_points[ipoint][jdim - 1][0],
                                    arc_points[ipoint][jdim - 1][1],
                                    arc_points[ipoint][jdim][0],
                                    arc_points[ipoint][jdim][1],
                                    radius=0.55,
                                    color=colors[iobj],
                                    chord_width=1,
                                    ax=ax,
                                )
                            )
                            handle_plots[iobj][index_bin][-1].set_visible(False)
                    handle_plots[iobj][index_bin].append(
                        draw_chord(
                            arc_points[ipoint][-1][0],
                            arc_points[ipoint][-1][1],
                            arc_points[ipoint][0][0],
                            arc_points[ipoint][0][1],
                            radius=0.55,
                            color=colors[iobj],
                            chord_width=1,
                            ax=ax,
                        )
                    )
                    handle_plots[iobj][index_bin][-1].set_visible(False)

    obj_labels = solutions.columns.tolist()

    prop_legend_bins = dict(fontsize=9, ha="center", va="center")

    for i in range(nobj):
        p0, p1 = polar_to_cartesian(0.975, sector_angles[i][0] * np.pi / 180.0)
        ax.text(p0, p1, "0", **prop_legend_bins)
        p0, p1 = polar_to_cartesian(0.975, sector_angles[i][1] * np.pi / 180.0)
        ax.text(p0, p1, "1", **prop_legend_bins)
        ax.text(
            labels_pos_and_ros[i][0],
            labels_pos_and_ros[i][1],
            obj_labels[i],
            rotation=labels_pos_and_ros[i][2],
            **prop_labels,
        )
        ax.text(
            labels_pos_and_ros[i][3],
            labels_pos_and_ros[i][4],
            "0",
            **prop_legend_bins,
            color=colors[i],
        )
        ax.text(
            labels_pos_and_ros[i][6],
            labels_pos_and_ros[i][7],
            str(max_hist_values[i]),
            **prop_legend_bins,
            color=colors[i],
        )

    plt.axis([-1.2, 1.2, -1.2, 1.2])
    fig.canvas.mpl_connect(
        "button_press_event",
        lambda event: hover_over_bin(event, handle_tickers, handle_plots, colors, fig),
    )
    plt.show()


def plot_moving_medians(
    file_path: str, x: str, y: list[str], normalized: bool, label: str, output_path: str
):
    # Load data
    data = pd.read_csv(file_path)

    # Set the first row as header
    data.columns = data.iloc[0]
    data = data[1:]

    # Convert to numeric
    data = data.apply(pd.to_numeric)

    # Normalize objective columns
    data_normalized = data.copy()
    if normalized:
        scaler = MaxAbsScaler()
        data_normalized[y] = scaler.fit_transform(data[y])

    # If objective was optimized in negative, add 1
    for column in y:
        if all(v < 0 for v in data_normalized[column]):
            data_normalized[column] += 1

    # Sort by chosen metric
    data_normalized_sorted_by_metric = data_normalized.sort_values(by=x)

    # Function to compute moving median
    def calculate_moving_median(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[
            (dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)
        ]
        mean_values = window_data[objective_columns].median()
        return mean_values

    # Function to compute first quartile within window
    def calculate_q1_within_window(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[
            (dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)
        ]
        q1_values = window_data[objective_columns].quantile(0.25)
        return q1_values

    # Function to compute third quartile within window
    def calculate_q3_within_window(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[
            (dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)
        ]
        q3_values = window_data[objective_columns].quantile(0.75)
        return q3_values

    # Window size
    window_size = (max(data_normalized[x]) - min(data_normalized[x])) / 10

    # Compute moving medians and quartiles
    moving_medians_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_moving_median(
            row, data_normalized_sorted_by_metric, y, window_size
        ),
        axis=1,
    )
    q1_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_q1_within_window(
            row, data_normalized_sorted_by_metric, y, window_size
        ),
        axis=1,
    )
    q3_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_q3_within_window(
            row, data_normalized_sorted_by_metric, y, window_size
        ),
        axis=1,
    )

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot moving medians with IQR shading
    for column in y:
        ax.plot(
            data_normalized_sorted_by_metric[x],
            moving_medians_normalized[column],
            label=column,
        )
        ax.fill_between(
            data_normalized_sorted_by_metric[x],
            q1_normalized[column],
            q3_normalized[column],
            alpha=0.2,
        )

    # Configure title and labels
    ax.set_title(f"Moving Medians of {label} \n by {x} with IQR Shading", fontsize=20)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(
        f"Moving Medians of {label} \n with window size of {round(window_size, 3)}",
        fontsize=14,
    )

    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.7, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc="upper left", bbox_to_anchor=(1.04, 1), fontsize=12)

    # Save plot
    plt.savefig(output_path)


def plot_polar(
    file_path: str, techniques_dict_scores: dict, metric: str, output_path: str
):
    # Load "evaluated_front.csv" to obtain weights
    evaluated_front = pd.read_csv(file_path, skiprows=[0])

    # Extract columns with weights
    weight_columns = [col for col in evaluated_front.columns if col.endswith(".csv")]
    techniques_names = delete_common_prefix_and_sufix(weight_columns)
    individual_weights = evaluated_front[weight_columns]
    individual_scores = evaluated_front[metric]

    # Collect technique scores in same order as evaluated file
    techniques_scores = []
    for tec in weight_columns:
        techniques_scores.append(techniques_dict_scores[tec])

    # Compute polar coordinates for individuals
    def calculate_polar_coordinates(weights, num_techniques):
        angles = np.linspace(0, 2 * np.pi, num_techniques, endpoint=False)
        coordinates = weights.dot(np.exp(1j * angles))
        return np.angle(coordinates), np.abs(coordinates)

    num_techniques = len(weight_columns)
    individual_angles, individual_radii = calculate_polar_coordinates(
        individual_weights.values, num_techniques
    )

    # Create polar plot
    _, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(polar=True))

    # Plot points
    technique_angles = np.linspace(0, 2 * np.pi, num_techniques, endpoint=False)
    angles = individual_angles.tolist() + technique_angles.tolist()
    radii = individual_radii.tolist() + [1] * num_techniques
    scores = individual_scores.tolist() + techniques_scores
    sc = ax.scatter(angles, radii, c=scores, cmap="viridis", alpha=0.7)

    # Plot individual techniques
    techniques_scores_normalized = (techniques_scores - np.min(scores)) / (
        np.max(scores) - np.min(scores)
    )
    for i, angle in enumerate(technique_angles):
        ax.scatter(
            angle,
            1,
            color=viridis(techniques_scores_normalized[i]),
            edgecolors="black",
            linewidth=1,
            s=200,
        )

    # Colorbar
    cbar = plt.colorbar(sc, orientation="vertical", pad=0.25)
    cbar.set_label(metric)

    # Add labels for technique scores in colorbar
    scores = techniques_scores + [individual_scores.median(), individual_scores.max()]
    labels = techniques_names + ["Median BIO-INSIGHT", "Best BIO-INSIGHT"]
    sorted_indices = np.argsort(scores)
    sorted_scores = np.array(scores)[sorted_indices]
    sorted_labels = np.array(labels)[sorted_indices]

    # Minimum distance between labels
    min_distance = (np.max(sorted_scores) - np.min(sorted_scores)) * 0.025

    adjusted_positions = []
    last_position = -np.inf
    for score, label in zip(sorted_scores, sorted_labels):
        if score - last_position < min_distance:
            adjusted_position = last_position + min_distance
        else:
            adjusted_position = score
        adjusted_positions.append(adjusted_position)
        last_position = adjusted_position

    for i, (label, adjusted_position) in enumerate(
        zip(sorted_labels, adjusted_positions)
    ):
        cbar.ax.axhline(
            y=sorted_scores[i],
            color="black" if "BIO-INSIGHT" not in label else "white",
            linewidth=1,
        )
        cbar.ax.text(
            -0.2,
            adjusted_position,
            f"{label} ({sorted_scores[i]:.4f})",
            va="center",
            ha="right",
            fontsize=8,
            color="black",
        )

    # Technique labels
    ax.set_xticks(technique_angles)
    ax.set_xticklabels(techniques_names, fontsize=10)

    # Title
    ax.set_title(f"Polar Plot of Individuals by Weights and {metric}", size=16)

    plt.savefig(output_path)
