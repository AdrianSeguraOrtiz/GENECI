import csv
import itertools
from enum import Enum
from pathlib import Path
from typing import List, Optional
from my_d3graph import d3graph, vec2adjmat

import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import typer
from pyvis.network import Network

def my_draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=None,
    label_pos=0.5,
    font_size=10,
    font_color="k",
    font_family="sans-serif",
    font_weight="normal",
    alpha=None,
    bbox=None,
    horizontalalignment="center",
    verticalalignment="center",
    ax=None,
    rotate=True,
    clip_on=True,
    rad=0,
):
    """Draw edge labels.

    Parameters
    ----------
    G : graph
        A networkx graph

    pos : dictionary
        A dictionary with nodes as keys and positions as values.
        Positions should be sequences of length 2.

    edge_labels : dictionary (default={})
        Edge labels in a dictionary of labels keyed by edge two-tuple.
        Only labels for the keys in the dictionary are drawn.

    label_pos : float (default=0.5)
        Position of edge label along edge (0=head, 0.5=center, 1=tail)

    font_size : int (default=10)
        Font size for text labels

    font_color : string (default='k' black)
        Font color string

    font_weight : string (default='normal')
        Font weight

    font_family : string (default='sans-serif')
        Font family

    alpha : float or None (default=None)
        The text transparency

    bbox : Matplotlib bbox, optional
        Specify text box properties (e.g. shape, color etc.) for edge labels.
        Default is {boxstyle='round', ec=(1.0, 1.0, 1.0), fc=(1.0, 1.0, 1.0)}.

    horizontalalignment : string (default='center')
        Horizontal alignment {'center', 'right', 'left'}

    verticalalignment : string (default='center')
        Vertical alignment {'center', 'top', 'bottom', 'baseline', 'center_baseline'}

    ax : Matplotlib Axes object, optional
        Draw the graph in the specified Matplotlib axes.

    rotate : bool (deafult=True)
        Rotate edge labels to lie parallel to edges

    clip_on : bool (default=True)
        Turn on clipping of edge labels at axis boundaries

    Returns
    -------
    dict
        `dict` of labels keyed by edge

    Examples
    --------
    >>> G = nx.dodecahedral_graph()
    >>> edge_labels = nx.draw_networkx_edge_labels(G, pos=nx.spring_layout(G))

    Also see the NetworkX drawing examples at
    https://networkx.org/documentation/latest/auto_examples/index.html

    See Also
    --------
    draw
    draw_networkx
    draw_networkx_nodes
    draw_networkx_edges
    draw_networkx_labels
    """
    import matplotlib.pyplot as plt
    import numpy as np

    if ax is None:
        ax = plt.gca()
    if edge_labels is None:
        labels = {(u, v): d for u, v, d in G.edges(data=True)}
    else:
        labels = edge_labels
    text_items = {}
    for (n1, n2), label in labels.items():
        (x1, y1) = pos[n1]
        (x2, y2) = pos[n2]
        (x, y) = (
            x1 * label_pos + x2 * (1.0 - label_pos),
            y1 * label_pos + y2 * (1.0 - label_pos),
        )
        pos_1 = ax.transData.transform(np.array(pos[n1]))
        pos_2 = ax.transData.transform(np.array(pos[n2]))
        linear_mid = 0.5 * pos_1 + 0.5 * pos_2
        d_pos = pos_2 - pos_1
        rotation_matrix = np.array([(0, 1), (-1, 0)])
        ctrl_1 = linear_mid + rad * rotation_matrix @ d_pos
        ctrl_mid_1 = 0.5 * pos_1 + 0.5 * ctrl_1
        ctrl_mid_2 = 0.5 * pos_2 + 0.5 * ctrl_1
        bezier_mid = 0.5 * ctrl_mid_1 + 0.5 * ctrl_mid_2
        (x, y) = ax.transData.inverted().transform(bezier_mid)

        if rotate:
            # in degrees
            angle = np.arctan2(y2 - y1, x2 - x1) / (2.0 * np.pi) * 360
            # make label orientation "right-side-up"
            if angle > 90:
                angle -= 180
            if angle < -90:
                angle += 180
            # transform data coordinate angle to screen coordinate angle
            xy = np.array((x, y))
            trans_angle = ax.transData.transform_angles(
                np.array((angle,)), xy.reshape((1, 2))
            )[0]
        else:
            trans_angle = 0.0
        # use default box of white with white border
        if bbox is None:
            bbox = dict(boxstyle="round", ec=(1.0, 1.0, 1.0), fc=(1.0, 1.0, 1.0))
        if not isinstance(label, str):
            label = str(label)  # this makes "1" and 1 labeled the same

        t = ax.text(
            x,
            y,
            label,
            size=font_size,
            color=font_color,
            family=font_family,
            weight=font_weight,
            alpha=alpha,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            rotation=trans_angle,
            transform=ax.transData,
            bbox=bbox,
            zorder=1,
            clip_on=clip_on,
        )
        text_items[(n1, n2)] = t

    ax.tick_params(
        axis="both",
        which="both",
        bottom=False,
        left=False,
        labelbottom=False,
        labelleft=False,
    )

    return text_items


class NodesDistribution(str, Enum):
    Spring = "Spring"
    Circular = "Circular"
    Kamada_kawai = "Kamada_kawai"


class Mode(str, Enum):
    Static2D = "Static2D"
    Interactive2D = "Interactive2D"
    Compare2D = "Compare2D"
    Interactive3D = "Interactive3D"


def draw_network(
    confidence_list: Optional[List[str]] = typer.Option(
        ..., help="Paths of the CSV files with the confidence lists to be represented"
    ),
    mode: Mode = typer.Option("Interactive2D", help="Mode of representation"),
    nodes_distribution: NodesDistribution = typer.Option(
        "Spring", help="Node distribution in graph. Note: Interactive2D mode has its own distribution of nodes, so in case of be selected this parameter will be ignored"
    ),
    confidence_cut_off: float = typer.Option(
        0.5, help="Cut off value for confidence"
    ),
    output_folder: str = typer.Option(..., help="Path to output folder"),
):

    if mode == Mode.Interactive3D:
        list_colors = [
            "#ffadad",
            "#ffd6a5",
            "#fdffb6",
            "#caffbf",
            "#9bf6ff",
            "#a0c4ff",
            "#bdb2ff",
            "#ffc6ff",
            "#e27396",
            "#84dcc6",
        ]
        iter_colors = itertools.cycle(list_colors)
        tuples = list()

        for conf_list in confidence_list:
            with open(conf_list, "r") as f:
                reader = csv.reader(f)
                tuples += [(row[0], row[1], float(row[2])) for row in reader if float(row[2]) >= confidence_cut_off]

        DG = nx.DiGraph()
        DG.add_weighted_edges_from(tuples)

        match nodes_distribution:
            case "Spring":
                spring_3D = nx.spring_layout(DG, dim=3, seed=5)
            case "Circular":
                spring_3D = nx.circular_layout(DG, dim=3)
            case "Kamada_kawai":
                spring_3D = nx.kamada_kawai_layout(DG, dim=3)

        x_nodes = [spring_3D[i][0] for i in DG.nodes()]
        y_nodes = [spring_3D[i][1] for i in DG.nodes()]
        z_nodes = [spring_3D[i][2] for i in DG.nodes()]

        traces = {}
        traces["trace_nodes"] = go.Scatter3d(
            x=x_nodes,
            y=y_nodes,
            z=z_nodes,
            mode="markers+text",
            marker=dict(
                symbol="circle",
                size=5,
                color="black",
                line=dict(color="black", width=2),
            ),
            text=list(DG.nodes()),
            textposition="top center",
            hoverinfo="none",
            showlegend=False,
        )

        for conf_list in confidence_list:
            with open(conf_list, "r") as f:
                reader = csv.reader(f)
                tuples = [(row[0], row[1], float(row[2])) for row in reader if float(row[2]) >= confidence_cut_off]

            DG = nx.DiGraph()
            DG.add_weighted_edges_from(tuples)
            color = next(iter_colors)

            edge_list = DG.edges()
            x_edges = []
            y_edges = []
            z_edges = []
            for edge in edge_list:
                x_coords = [spring_3D[edge[0]][0], spring_3D[edge[1]][0], None]
                x_edges.append(x_coords)

                y_coords = [spring_3D[edge[0]][1], spring_3D[edge[1]][1], None]
                y_edges.append(y_coords)

                z_coords = [spring_3D[edge[0]][2], spring_3D[edge[1]][2], None]
                z_edges.append(z_coords)

            weights = list(nx.get_edge_attributes(DG, "weight").values())
            visible = len(traces) == 1
            for i in range(DG.number_of_edges()):
                traces[f"trace_edge_{i}_of_{Path(conf_list).name}"] = go.Scatter3d(
                    x=x_edges[i],
                    y=y_edges[i],
                    z=z_edges[i],
                    legendgroup=f"{Path(conf_list).name}",
                    name=f"{Path(conf_list).name}",
                    showlegend=i == 0,
                    line=dict(width=weights[i] * 10, color=color),
                    text=f"{list(DG.edges())[i]}: {round(weights[i], 2)}",
                    hoverinfo="text",
                    visible=True if visible else "legendonly",
                )

        axis = dict(
            showbackground=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            showspikes=False,
            title="",
        )

        layout = go.Layout(
            title=f"Networks of all input files",
            showlegend=True,
            scene=dict(
                xaxis=dict(axis),
                yaxis=dict(axis),
                zaxis=dict(axis),
            ),
            margin=dict(t=100),
        )

        data = list(traces.values())
        fig = go.Figure(data=data, layout=layout)
        fig.write_html(f"{output_folder}/interactive_3D_network.html")

    elif mode == Mode.Static2D:
        for conf_list in confidence_list:
            with open(conf_list, "r") as f:
                reader = csv.reader(f)
                tuples = [(row[0], row[1], float(row[2])) for row in reader if float(row[2]) >= confidence_cut_off]

            DG = nx.DiGraph()
            DG.add_weighted_edges_from(tuples)

            dict_edge_weights = nx.get_edge_attributes(DG, "weight")

            curved_edges = [edge for edge in DG.edges() if reversed(edge) in DG.edges()]
            straight_edges = list(set(DG.edges()) - set(curved_edges))

            curved_weights = [
                4 * v for k, v in dict_edge_weights.items() if k in curved_edges
            ]
            straight_weights = [
                4 * v for k, v in dict_edge_weights.items() if k in straight_edges
            ]

            node_sizes = [v * 75 for _, v in DG.degree(weight="weight")]

            match nodes_distribution:
                case "Spring":
                    pos = nx.spring_layout(DG, seed=5)
                case "Circular":
                    pos = nx.circular_layout(DG)
                case "Kamada_kawai":
                    pos = nx.kamada_kawai_layout(DG)

            # nodes
            nx.draw_networkx_nodes(DG, pos, node_size=node_sizes)
            # node labels
            nx.draw_networkx_labels(DG, pos, font_size=10)

            # edges
            nx.draw_networkx_edges(
                DG,
                pos,
                edgelist=curved_edges,
                width=curved_weights,
                connectionstyle=f"arc3, rad = 0.2",
            )
            nx.draw_networkx_edges(
                DG, pos, edgelist=straight_edges, width=straight_weights
            )

            # edge weight labels
            if DG.number_of_nodes() < 15:
                curved_edge_labels = {
                    k: round(v, 2)
                    for k, v in dict_edge_weights.items()
                    if k in curved_edges and v > (1 - confidence_cut_off)/2 + confidence_cut_off
                }
                straight_edge_labels = {
                    k: round(v, 2)
                    for k, v in dict_edge_weights.items()
                    if k in straight_edges and v > (1 - confidence_cut_off)/2 + confidence_cut_off
                }
                my_draw_networkx_edge_labels(
                    DG,
                    pos,
                    edge_labels=curved_edge_labels,
                    rotate=False,
                    rad=0.2,
                    font_size=6,
                )
                nx.draw_networkx_edge_labels(
                    DG, pos, edge_labels=straight_edge_labels, rotate=False, font_size=6
                )

            plt.axis("off")
            plt.title(f"Static network for {Path(conf_list).name} file")
            plt.savefig(f"{output_folder}/static_2D_{Path(conf_list).stem}_network.pdf")
            plt.close()
    
    elif mode == Mode.Interactive2D:
        for conf_list in confidence_list:
            data = pd.read_csv(conf_list, header=None)
            data.columns = ['source', 'target', 'weight']

            # Convert data to an adjacencia matrix
            adjmat = vec2adjmat(data['source'], data['target'], data['weight']*100)

            # Create and visualize the directed graph
            d3 = d3graph()
            d3.graph(adjmat)
            d3.set_edge_properties(directed=True)
            d3.set_node_properties(color='cluster', fontcolor='node_color', edge_color='cluster', size='degree', opacity='degree')

            # Ssave the graph
            d3.show(filepath= f"{output_folder}/interactive_2D_{Path(conf_list).stem}_network.html", set_slider=confidence_cut_off*100)

    elif mode == Mode.Compare2D:
        colors = [
            "#FF9999",  # Rosa pastel oscurecido
            "#80CCCC",  # Azul cielo oscurecido
            "#CCCC99",  # Amarillo pálido oscurecido
            "#99CC99",  # Verde menta oscurecido
            "#CC99FF",  # Lila suave oscurecido
            "#FFB366",  # Melocotón oscurecido
            "#BFBFBF",  # Gris perla oscurecido
            "#99FFFF",  # Turquesa claro oscurecido
            "#9999FF",  # Lavanda oscurecido
            "#FFE0CC"   # Beige claro oscurecido
        ]
        color_map = {}
        iter_colors = itertools.cycle(colors)
        
        # Initialize the pyvis graph
        net = Network(notebook=False, directed=True, height="1000px", width="100%")

        # Fill graph
        for conf_list in confidence_list:
            data = pd.read_csv(conf_list)
            color = next(iter_colors)
            color_map[Path(conf_list).stem] = color
            for _, row in data.iterrows():
                source, target, weight = row
                
                # Discard interactions below the threshold
                if weight < confidence_cut_off:
                    continue
                title = f"{weight:.2f}"
                
                # Make sure the nodes exist before adding the edges
                if source not in net.nodes:
                    net.add_node(source, title=source, shape="ellipse")
                if target not in net.nodes:
                    net.add_node(target, title=target, shape="ellipse")
                    
                # Add the edge with the corresponding color and title
                net.add_edge(source, target, title=title, color=color, value=weight)

        net.set_options("""
        {
            "edges": {
                "scaling": {
                    "min": 0,
                    "max": 5
                },
                "smooth": true
            },
            "physics": {
                "maxVelocity": 15
            }
        }
        """)

        # Save and show visualization
        # Guarda y muestra la visualización
        output_path = f"{output_folder}/compare_2D_network.html"
        net.show(output_path, notebook=False)

        # Crea la leyenda como HTML
        legend_html = "<div id='legend' style='position:absolute; top:10px; right:10px; width:200px; background-color:#FFF; padding:10px; border:1px solid #000;'>"
        legend_html += "<h4>Leyend</h4>"
        for file_name, color in color_map.items():
            legend_html += f"<p><span style='display:inline-block; width:12px; height:12px; margin-right:5px; background-color:{color};'></span>{file_name}</p>"
        legend_html += "</div>"

        # Lee el contenido HTML actual
        with open(output_path, "r") as file:
            html_content = file.read()

        # Inserta la leyenda antes del final del body
        html_content = html_content.replace("</body>", f"{legend_html}</body>")

        # Sobrescribe el archivo con la leyenda añadida
        with open(output_path, "w") as file:
            file.write(html_content)

if __name__ == "__main__":
    typer.run(draw_network)
