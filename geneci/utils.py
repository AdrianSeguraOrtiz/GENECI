import colorsys
import math
import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib import pyplot as plt
from matplotlib.cm import viridis
from matplotlib.path import Path
from sklearn.preprocessing import MaxAbsScaler
from iteround import saferound
from tqdm import tqdm
import os

# Create dict of techniques cpus
cpus_dict = dict()
cpus_dict.update(
    dict.fromkeys(["JUMP3", "LOCPCACMI", "NONLINEARODES", "GRNVBEM", "CMI2NI"], 4)
)
cpus_dict.update(
    dict.fromkeys(
        [
            "TIGRESS",
            "PCACMI",
            "PLSNET",
            "INFERELATOR",
            "GENIE3_RF",
            "GRNBOOST2",
            "GENIE3_ET",
        ],
        3,
    )
)
cpus_dict.update(dict.fromkeys(["KBOOST", "LEAP"], 2))
cpus_dict.update(
    dict.fromkeys(
        [
            "ARACNE",
            "BC3NET",
            "C3NET",
            "CLR",
            "MRNET",
            "MRNETB",
            "PCIT",
            "MEOMI",
            "NARROMI",
            "RSNET",
            "PIDC",
            "PUC",
        ],
        1,
    )
)

def delete_common_prefix_and_sufix(lista):
    # Encontrar el prefijo común
    prefijo_comun = os.path.commonprefix(lista)
    
    # Eliminar prefijo común de cada elemento
    lista_sin_prefijo = [s[len(prefijo_comun):] for s in lista]
    
    # Encontrar el sufijo común (invierte cada cadena, encuentra el prefijo común y luego lo invierte de nuevo)
    sufijo_comun = os.path.commonprefix([s[::-1] for s in lista])[::-1]
    
    # Eliminar sufijo común de cada elemento
    lista_final = [s[:-len(sufijo_comun)] if sufijo_comun else s for s in lista_sin_prefijo]
    
    return lista_final

def polar_to_cartesian(r, theta):
    return np.array([r * np.cos(theta), r * np.sin(theta)])


def draw_sector(
    start_angle=0, end_angle=60, radius=1.0, width=0.2, lw=2, ls="-", ax=None, fc=(1, 0, 0), ec=(0, 0, 0), z_order=1
):
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle
    start_angle *= np.pi / 180.0
    end_angle *= np.pi / 180.0

    # https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
    opt = 4.0 / 3.0 * np.tan((end_angle - start_angle) / 4.0) * radius
    inner = radius * (1 - width)

    vertsPath = [
        polar_to_cartesian(radius, start_angle),
        polar_to_cartesian(radius, start_angle) + polar_to_cartesian(opt, start_angle + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle) + polar_to_cartesian(opt, end_angle - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle),
        polar_to_cartesian(inner, end_angle),
        polar_to_cartesian(inner, end_angle) + polar_to_cartesian(opt * (1 - width), end_angle - 0.5 * np.pi),
        polar_to_cartesian(inner, start_angle) + polar_to_cartesian(opt * (1 - width), start_angle + 0.5 * np.pi),
        polar_to_cartesian(inner, start_angle),
        polar_to_cartesian(radius, start_angle),
    ]

    codesPaths = [
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
        return vertsPath, codesPaths
    else:
        path = Path(vertsPath, codesPaths)
        patch = patches.PathPatch(path, facecolor=fc, edgecolor=ec, lw=lw, linestyle=ls, zorder=z_order)
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

    optAngle1 = 4.0 / 3.0 * np.tan((end_angle1 - start_angle1) / 4.0) * radius
    optAngle2 = 4.0 / 3.0 * np.tan((end_angle2 - start_angle2) / 4.0) * radius
    rchord = radius * (1 - chord_width)

    vertsPath = [
        polar_to_cartesian(radius, start_angle1),
        polar_to_cartesian(radius, start_angle1) + polar_to_cartesian(optAngle1, start_angle1 + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle1) + polar_to_cartesian(optAngle1, end_angle1 - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle1),
        polar_to_cartesian(rchord, end_angle1),
        polar_to_cartesian(rchord, start_angle2),
        polar_to_cartesian(radius, start_angle2),
        polar_to_cartesian(radius, start_angle2) + polar_to_cartesian(optAngle2, start_angle2 + 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle2) + polar_to_cartesian(optAngle2, end_angle2 - 0.5 * np.pi),
        polar_to_cartesian(radius, end_angle2),
        polar_to_cartesian(rchord, end_angle2),
        polar_to_cartesian(rchord, start_angle1),
        polar_to_cartesian(radius, start_angle1),
    ]

    codesPath = [
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

    if ax == None:
        return vertsPath, codesPath
    else:
        path = Path(vertsPath, codesPath)
        patch = patches.PathPatch(path, facecolor=color + (0.5,), edgecolor=color + (0.4,), lw=2, alpha=0.5)
        ax.add_patch(patch)
        return patch


def hover_over_bin(event, handle_tickers, handle_plots, colors, fig):
    for iobj, obj_bins in enumerate(handle_tickers):
        for ibin, bin_patch in enumerate(obj_bins):
            cont, ind = bin_patch.contains(event)
            if cont:
                if (plt.getp(bin_patch, "facecolor") == (1,1,1,1)):
                    plt.setp(bin_patch, facecolor=colors[iobj])
                    for h in handle_plots[iobj][ibin]:
                        h.set_visible(True)
                else:
                    plt.setp(bin_patch, facecolor=(1,1,1,1))
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
    (NPOINTS, NOBJ) = np.shape(points_matrix)

    HSV_tuples = [(x * 1.0 / NOBJ, 0.5, 0.5) for x in range(NOBJ)]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))

    if ax is None:
        fig = plt.figure(figsize=(6, 6))
        ax = plt.axes([0, 0, 1, 1], aspect="equal")

    ax.set_xlim(-2.3, 2.3)
    ax.set_ylim(-2.3, 2.3)
    ax.axis("off")

    y = np.array([1.0 / NOBJ] * NOBJ) * (360 - pad * NOBJ)
    sector_angles = []
    labels_pos_and_ros = []

    start_angle = 0
    for i in range(NOBJ):
        end_angle = start_angle + y[i]
        sector_angles.append((start_angle, end_angle))
        angle_diff = 0.5 * (start_angle + end_angle)
        if -30 <= angle_diff <= 210:
            angle_diff -= 90
        else:
            angle_diff -= 270
        angleText = start_angle - 2.5
        if -30 <= angleText <= 210:
            angleText -= 90
        else:
            angleText -= 270

        labels_pos_and_ros.append(
            tuple(polar_to_cartesian(1.0, 0.5 * (start_angle + end_angle) * np.pi / 180.0))
            + (angle_diff,)
            + tuple(polar_to_cartesian(0.725, (start_angle - 2.5) * np.pi / 180.0))
            + (angleText,)
            + tuple(polar_to_cartesian(0.85, (start_angle - 2.5) * np.pi / 180.0))
            + (angleText,)
        )
        start_angle = end_angle + pad

    arc_points = []
    for point in points_matrix:
        arc_points.append([])
        idim = 0

        for _ in point:
            anglePoint = sector_angles[idim][0] + (sector_angles[idim][1] - sector_angles[idim][0]) * point[idim]
            arc_points[-1].append((anglePoint, anglePoint))
            idim = idim + 1

    max_hist_values = []
    handle_tickers = []
    handle_plots = []

    for iobj in tqdm(range(NOBJ), ascii=True, desc="Chord diagram"):
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

        histValues, binsDim = np.histogram(points_matrix[:, iobj], bins=nbins)
        relativeHeightBinPre = 0.025
        max_hist_values.append(max(histValues))
        handle_tickers.append([])
        handle_plots.append([])

        for indexBin in range(len(histValues)):
            startAngleBin = (
                sector_angles[iobj][0] + (sector_angles[iobj][1] - sector_angles[iobj][0]) * binsDim[indexBin]
            )
            endAngleBin = (
                sector_angles[iobj][0] + (sector_angles[iobj][1] - sector_angles[iobj][0]) * binsDim[indexBin + 1]
            )
            relativeHeightBin = max(0.15 * histValues[indexBin] / max(histValues), 0.025)

            handle_tickers[-1].append(
                draw_sector(
                    start_angle=startAngleBin,
                    end_angle=endAngleBin,
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
                start_angle=startAngleBin,
                end_angle=endAngleBin,
                radius=0.7 + relativeHeightBin,
                width=0,
                ax=ax,
                lw=1,
                fc=colors[iobj],
                ec=colors[iobj],
            )
            plotPoint1 = polar_to_cartesian(0.7 + relativeHeightBinPre, startAngleBin * np.pi / 180.0)
            plotPoint2 = polar_to_cartesian(0.7 + relativeHeightBin, startAngleBin * np.pi / 180.0)
            plt.plot([plotPoint1[0], plotPoint2[0]], [plotPoint1[1], plotPoint2[1]], c=colors[iobj], lw=1)
            relativeHeightBinPre = relativeHeightBin


            if indexBin == len(histValues) - 1:
                plotPoint1 = polar_to_cartesian(0.7 + relativeHeightBin, endAngleBin * np.pi / 180.0)
                plotPoint2 = polar_to_cartesian(0.725, endAngleBin * np.pi / 180.0)
                plt.plot([plotPoint1[0], plotPoint2[0]], [plotPoint1[1], plotPoint2[1]], c=colors[iobj], lw=1)

            for ipoint in range(len(points_matrix)):
                plotPoint1 = polar_to_cartesian(0.6, arc_points[ipoint][iobj][0] * np.pi / 180.0)
                plotPoint2 = polar_to_cartesian(0.6, arc_points[ipoint][iobj][0] * np.pi / 180.0)
                plt.plot(
                    [plotPoint1[0], plotPoint2[0]],
                    [plotPoint1[1], plotPoint2[1]],
                    marker="o",
                    markersize=3,
                    c=colors[iobj],
                    lw=2,
                )

                if binsDim[indexBin] < points_matrix[ipoint, iobj] <= binsDim[indexBin + 1]:
                    for jdim in range(NOBJ):
                        if jdim >= 1:
                            handle_plots[iobj][indexBin].append(
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
                            handle_plots[iobj][indexBin][-1].set_visible(False)
                    handle_plots[iobj][indexBin].append(
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
                    handle_plots[iobj][indexBin][-1].set_visible(False)

    obj_labels = solutions.columns.tolist()

    prop_legend_bins = dict(fontsize=9, ha="center", va="center")

    for i in range(NOBJ):
        p0, p1 = polar_to_cartesian(0.975, sector_angles[i][0] * np.pi / 180.0)
        ax.text(p0, p1, "0", **prop_legend_bins)
        p0, p1 = polar_to_cartesian(0.975, sector_angles[i][1] * np.pi / 180.0)
        ax.text(p0, p1, "1", **prop_legend_bins)
        ax.text(
            labels_pos_and_ros[i][0],
            labels_pos_and_ros[i][1],
            obj_labels[i],
            rotation=labels_pos_and_ros[i][2],
            **prop_labels
        )
        ax.text(labels_pos_and_ros[i][3], labels_pos_and_ros[i][4], "0", **prop_legend_bins, color=colors[i])
        ax.text(
            labels_pos_and_ros[i][6],
            labels_pos_and_ros[i][7],
            str(max_hist_values[i]),
            **prop_legend_bins,
            color=colors[i]
        )

    plt.axis([-1.2, 1.2, -1.2, 1.2])
    fig.canvas.mpl_connect(
        "button_press_event", lambda event: hover_over_bin(event, handle_tickers, handle_plots, colors, fig)
    )
    plt.show()
    
    
def plot_moving_medians(file_path: str, x: str, y: list[str], normalized: bool, label: str, output_path: str):
    # Cargar los datos
    data = pd.read_csv(file_path)

    # Establecer la primera fila como encabezado
    data.columns = data.iloc[0]
    data = data[1:]

    # Convertir los datos a tipos numéricos
    data = data.apply(pd.to_numeric)

    # Normalizar las columnas de objetivos
    data_normalized = data.copy()
    if normalized:
        scaler = MaxAbsScaler()
        data_normalized[y] = scaler.fit_transform(data[y])
    
    # Si el objetivo se optimizaba en negativo le sumamos 1
    for column in y:
        if all(v < 0 for v in data_normalized[column]):
            data_normalized[column] += 1

    # Ordenar los datos por la métrica elegida
    data_normalized_sorted_by_metric = data_normalized.sort_values(by=x)

    # Función para calcular la media móvil
    def calculate_moving_median(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[(dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)]
        mean_values = window_data[objective_columns].median()
        return mean_values

    # Función para calcular el primer cuartil dentro de la ventana
    def calculate_q1_within_window(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[(dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)]
        q1_values = window_data[objective_columns].quantile(0.25)
        return q1_values

    # Función para calcular el tercer cuartil dentro de la ventana
    def calculate_q3_within_window(row, dataframe, objective_columns, window_size):
        lower_bound = row[x] - window_size
        upper_bound = row[x] + window_size
        window_data = dataframe[(dataframe[x] >= lower_bound) & (dataframe[x] <= upper_bound)]
        q3_values = window_data[objective_columns].quantile(0.75)
        return q3_values

    # Definir el tamaño de la ventana
    window_size = (max(data_normalized[x]) - min(data_normalized[x])) / 10

    # Calcular las medianas móviles y los cuartiles para los datos normalizados
    moving_medians_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_moving_median(row, data_normalized_sorted_by_metric, y, window_size), axis=1
    )
    q1_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_q1_within_window(row, data_normalized_sorted_by_metric, y, window_size), axis=1
    )
    q3_normalized = data_normalized_sorted_by_metric.apply(
        lambda row: calculate_q3_within_window(row, data_normalized_sorted_by_metric, y, window_size), axis=1
    )

    # Crear la figura y los ejes para la gráfica
    fig, ax = plt.subplots(figsize=(12, 8))


    # Graficar las medias móviles con el área sombreada para la desviación estándar en los datos normalizados
    for column in y:
        ax.plot(data_normalized_sorted_by_metric[x], moving_medians_normalized[column], label=column)
        ax.fill_between(data_normalized_sorted_by_metric[x],
                        q1_normalized[column],
                        q3_normalized[column],
                        alpha=0.2)

    # Configurar el título de la gráfica y las etiquetas
    ax.set_title(f'Moving Medians of {label} \n by {x} with IQR Shading', fontsize=20)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(f'Moving Medians of {label} \n with window size of {round(window_size, 3)}', fontsize=14)

    # Añadir la leyenda a la gráfica
    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.7, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc='upper left', bbox_to_anchor=(1.04, 1), fontsize=12)

    # Mostrar la gráfica
    plt.savefig(output_path)
    
def plot_polar(file_path: str, techniques_dict_scores: dict, metric: str, output_path: str):
    # Cargamos el archivo "evaluated_front.csv" nuevamente para obtener los pesos de los individuos.
    evaluated_front = pd.read_csv(file_path, skiprows=[0])
        
    # Vamos a extraer solo las columnas de pesos que terminan en '.csv'
    weight_columns = [col for col in evaluated_front.columns if col.endswith('.csv')]
    techniques_names = delete_common_prefix_and_sufix(weight_columns)
    individual_weights = evaluated_front[weight_columns]
    individual_scores = evaluated_front[metric]

    # Coger los valores de las técnicas en el mismo orden que el fichero evaluado del frente
    techniques_scores = []
    for tec in weight_columns:
        techniques_scores.append(techniques_dict_scores[tec])

    # Función para calcular las coordenadas polares de los individuos en función de sus pesos
    def calculate_polar_coordinates(weights, num_techniques):
        # Calculamos el ángulo de cada técnica
        angles = np.linspace(0, 2 * np.pi, num_techniques, endpoint=False)
        # Calculamos las coordenadas polares de los individuos
        coordinates = weights.dot(np.exp(1j * angles))
        return np.angle(coordinates), np.abs(coordinates)

    # Calcular las coordenadas polares de los individuos
    num_techniques = len(weight_columns)
    individual_angles, individual_radii = calculate_polar_coordinates(individual_weights.values, num_techniques)

    # Crear la gráfica polar
    _, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(polar=True))

    # Dibujar los puntos normales
    technique_angles = np.linspace(0, 2 * np.pi, num_techniques, endpoint=False)
    angles = individual_angles.tolist() + technique_angles.tolist()
    radii = individual_radii.tolist() + [1] * num_techniques
    scores = individual_scores.tolist() + techniques_scores
    sc = ax.scatter(angles, radii, c=scores, cmap='viridis', alpha=0.7)

    # Dibujar los puntos especiales para las técnicas individuales
    techniques_scores_normalized = (techniques_scores - np.min(scores)) / (np.max(scores) - np.min(scores))
    for i, angle in enumerate(technique_angles):
        ax.scatter(angle, 1, color=viridis(techniques_scores_normalized[i]), edgecolors='black', linewidth=1, s=200)

    # Añadir la barra de colores que indica los valores de AUROC
    cbar = plt.colorbar(sc, orientation='vertical', pad=0.25)
    cbar.set_label(metric)

    # Añadir marcas y etiquetas para los valores AUROC de cada técnica en la barra de colores
    scores = techniques_scores + [individual_scores.median(), individual_scores.max()]
    labels = techniques_names + ['Median BIO-INSIGHT', 'Best BIO-INSIGHT']
    sorted_indices = np.argsort(scores)
    sorted_scores = np.array(scores)[sorted_indices]
    sorted_labels = np.array(labels)[sorted_indices]

    # Definir la distancia mínima entre las etiquetas (este valor puede ajustarse según la necesidad)
    min_distance = (np.max(sorted_scores) - np.min(sorted_scores)) * 0.025

    # Crear listas para almacenar las posiciones ajustadas de las etiquetas
    adjusted_positions = []

    # Inicializar la última posición añadida
    last_position = -np.inf

    # Iterar sobre los scores y etiquetas ordenados para ajustar la posición de las etiquetas
    for score, label in zip(sorted_scores, sorted_labels):
        # Si la posición actual está muy cerca de la última posición ajustada, mover la etiqueta un poco más arriba
        if score - last_position < min_distance:
            adjusted_position = last_position + min_distance
        else:
            adjusted_position = score
        adjusted_positions.append(adjusted_position)
        last_position = adjusted_position

    # Ahora puedes usar 'adjusted_positions' para colocar tus etiquetas en el colorbar sin que se superpongan
    for i, (label, adjusted_position) in enumerate(zip(sorted_labels, adjusted_positions)):
        cbar.ax.axhline(y=sorted_scores[i], color='black' if "BIO-INSIGHT" not in label else 'white', linewidth=1)
        cbar.ax.text(-0.2, adjusted_position, f'{label} ({sorted_scores[i]:.4f})', va='center', ha='right', fontsize=8, color='black')


    # Añadir etiquetas para las técnicas
    ax.set_xticks(technique_angles)
    ax.set_xticklabels(techniques_names, fontsize=10)

    # Título de la gráfica
    ax.set_title(f'Polar Plot of Individuals by Weights and {metric}', size=16)

    plt.savefig(output_path)


def simple_consensus(
    files: list[str],
    method: str,
    output_file: str,
):
    # Cargar archivos
    dfs = [pd.read_csv(f, header=None, names=["source", "target", f"confidence{i}"]) for i, f in enumerate(files)]

    # Fusionar por source y target
    res = dfs.pop(0)
    for df in dfs:
        res = pd.merge(res, df, on=["source", "target"], how="outer")
    res = res.fillna(0)

    confidence_cols = [col for col in res.columns if col.startswith("confidence")]

    # Aplicar método de consenso
    if method == "MeanWeights":
        res["score"] = res[confidence_cols].mean(axis=1)

    elif method == "MedianWeights":
        res["score"] = res[confidence_cols].median(axis=1)

    elif method == "RankAverage":
        for col in confidence_cols:
            res[col + "_rank"] = res[col].rank(method="average", ascending=False)
        rank_cols = [col + "_rank" for col in confidence_cols]
        res["avg_rank"] = res[rank_cols].mean(axis=1)
        res["score"] = 1 - (res["avg_rank"] - res["avg_rank"].min()) / (res["avg_rank"].max() - res["avg_rank"].min())

    elif method == "BayesianFusion":
        alpha_prior = 1
        beta_prior = 1
        res["alpha"] = alpha_prior + res[confidence_cols].sum(axis=1)
        res["beta"] = beta_prior + (1 - res[confidence_cols]).sum(axis=1)
        res["score"] = res["alpha"] / (res["alpha"] + res["beta"])

    else:
        raise ValueError(f"Unsupported method: {method}")

    # Guardar resultado
    res[["source", "target", "score"]].to_csv(output_file, header=False, index=False)


def get_expression_data_from_module(expression_data_file: str, module_file: str, output_file: str):
    # Cargar la red del módulo y extraer genes únicos (source y target)
    module_df = pd.read_csv(module_file)
    genes = set(module_df.iloc[:, 0]) | set(module_df.iloc[:, 1])

    # Cargar los datos de expresión
    expression_df = pd.read_csv(expression_data_file, index_col=0)

    # Filtrar las filas correspondientes a los genes de la subred
    filtered_df = expression_df.loc[expression_df.index.intersection(genes)]

    # Guardar el subconjunto en el archivo de salida
    filtered_df.to_csv(output_file)

    return filtered_df

# Function to obtain the optimal distribution of cores given a set of techniques
def get_optimal_cpu_distribution(tecs, cores_ids):

    # Calculate cpus vector for our input
    cpus_list = list()
    for tec in tecs:
        cpus_list.append(cpus_dict.get(tec))

    # We group the techniques of equal amount of cpus required.
    # For each group we store its members and the sum of the total number of cpus they need.
    groups = list()
    group_sums = list()
    for cpu in set(cpus_list):
        members = [i for i in range(len(cpus_list)) if cpus_list[i] == cpu]
        groups.append(members)
        group_sums.append(len(members) * cpu)

    # For each group we store the number of cpus that the system can offer them (in decimals).
    scaled_groups_sums = [
        (gsum / sum(group_sums)) * len(cores_ids) for gsum in group_sums
    ]

    # If the number of cpus required is less than the number of cpus available, we set the sum
    # of the non-parallelisable group of techniques to the consistent maximum (1 for each). In
    # case the number of required cpus is greater than those offered by the system, we set the
    # sum of the non-parallelisable group of techniques to the minimum between (available/required)/2
    # and 0.5 fo each. The amount of cpus left over or missing after this imposition is distributed
    # in order of preference to the rest of the groups.
    if 1 in set(cpus_list):
        cpus_set_list = list(set(cpus_list))
        idx_group_of_ones = cpus_set_list.index(1)

        factor = (
            1
            if len(cores_ids) > sum(cpus_list)
            else min(
                0.5,
                (scaled_groups_sums[idx_group_of_ones] / group_sums[idx_group_of_ones])
                / 2,
            )
        )
        ones_sum = group_sums[idx_group_of_ones] * factor
        surplus = scaled_groups_sums[idx_group_of_ones] - ones_sum
        scaled_groups_sums[idx_group_of_ones] = ones_sum

        cpus_set_list[idx_group_of_ones] = 0
        surplus_distributed = [
            (cpu / max(1, sum(cpus_set_list))) * surplus for cpu in cpus_set_list
        ]
        scaled_groups_sums = [
            sum(x) for x in zip(scaled_groups_sums, surplus_distributed)
        ]

    # After redistribution we round up the number of cpus safely for each group
    safe_groups_sums = saferound(scaled_groups_sums, places=0)

    # We assign to each technique the number of cpus that corresponds to it within its group,
    # specifying the id of each assigned cpu.
    cpus_cnt = 0
    res = dict.fromkeys(tecs, list())
    for idx_group in range(len(groups)):
        cpus_group = int(safe_groups_sums[idx_group])
        cpus_ids = (
            cores_ids[cpus_cnt : (cpus_group + cpus_cnt)]
            if cpus_group != 0
            else [cores_ids[max(0, cpus_group - 1)]]
        )
        cpus_cnt += cpus_group

        members = groups[idx_group]

        if len(members) < len(cpus_ids):
            cycle_members = itertools.cycle(members)
            for cpu_id in cpus_ids:
                member = next(cycle_members)
                res[tecs[member]] = res[tecs[member]] + [cpu_id]
        else:
            cpus_ids = itertools.cycle(cpus_ids)
            for member in members:
                res[tecs[member]] = res[tecs[member]] + [next(cpus_ids)]

    # Return final dict
    return res