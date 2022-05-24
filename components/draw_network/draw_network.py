import typer
import csv
from typing import List, Optional
import networkx as nx
import matplotlib.pyplot as plt

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
    rad=0
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
        linear_mid = 0.5*pos_1 + 0.5*pos_2
        d_pos = pos_2 - pos_1
        rotation_matrix = np.array([(0,1), (-1,0)])
        ctrl_1 = linear_mid + rad*rotation_matrix@d_pos
        ctrl_mid_1 = 0.5*pos_1 + 0.5*ctrl_1
        ctrl_mid_2 = 0.5*pos_2 + 0.5*ctrl_1
        bezier_mid = 0.5*ctrl_mid_1 + 0.5*ctrl_mid_2
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

def draw_network(
        confidence_list: Optional[List[str]] = typer.Option(..., help="Paths of the CSV files with the confidence lists to be represented."),
    ):

    if len(confidence_list) == 1:
        print("Make DiGraph")

        with open(confidence_list[0], "r") as f:
            reader = csv.reader(f)
            tuples = [(row[0], row[1], float(row[2])) for row in reader]

        DG = nx.DiGraph()
        DG.add_weighted_edges_from(tuples)
        dict_edge_weights = nx.get_edge_attributes(DG, "weight")

        curved_edges = [edge for edge in DG.edges() if reversed(edge) in DG.edges()]
        straight_edges = list(set(DG.edges()) - set(curved_edges))

        curved_edges_very_large = [k for k,v in dict_edge_weights.items() if v > 0.75 and k in curved_edges]
        straight_edges_very_large = [k for k,v in dict_edge_weights.items() if v > 0.75 and k in straight_edges]
        
        curved_edges_large = [k for k,v in dict_edge_weights.items() if v <= 0.75 and v > 0.5 and k in curved_edges]
        straight_edges_large = [k for k,v in dict_edge_weights.items() if v <= 0.75 and v > 0.5 and k in straight_edges]
        
        curved_edges_small = [k for k,v in dict_edge_weights.items() if v <= 0.5 and v > 0.25 and k in curved_edges]
        straight_edges_small = [k for k,v in dict_edge_weights.items() if v <= 0.5 and v > 0.25 and k in straight_edges]
        
        curved_edges_very_small = [k for k,v in dict_edge_weights.items() if v <= 0.25 and k in curved_edges]
        straight_edges_very_small = [k for k,v in dict_edge_weights.items() if v <= 0.25 and k in straight_edges]

        pos = nx.spring_layout(DG, seed=7)

        # nodes
        nx.draw_networkx_nodes(DG, pos)
        # node labels
        nx.draw_networkx_labels(DG, pos, font_size=10)

        # edges
        nx.draw_networkx_edges(DG, pos, edgelist=curved_edges_very_large, width=4, connectionstyle=f'arc3, rad = 0.2')
        nx.draw_networkx_edges(DG, pos, edgelist=straight_edges_very_large, width=4)

        nx.draw_networkx_edges(DG, pos, edgelist=curved_edges_large, width=3, connectionstyle=f'arc3, rad = 0.2')
        nx.draw_networkx_edges(DG, pos, edgelist=straight_edges_large, width=3)

        nx.draw_networkx_edges(DG, pos, edgelist=curved_edges_small, width=2, connectionstyle=f'arc3, rad = 0.2')
        nx.draw_networkx_edges(DG, pos, edgelist=straight_edges_small, width=2)

        nx.draw_networkx_edges(DG, pos, edgelist=curved_edges_very_small, width=0.25, connectionstyle=f'arc3, rad = 0.2')
        nx.draw_networkx_edges(DG, pos, edgelist=straight_edges_very_small, width=0.25)

        # edge weight labels
        curved_edge_labels = {key : round(dict_edge_weights[key], 2) for key in dict_edge_weights if key in curved_edges_very_large + curved_edges_large + curved_edges_small}
        straight_edge_labels = {key : round(dict_edge_weights[key], 2) for key in dict_edge_weights if key in straight_edges_very_large + straight_edges_large + straight_edges_small}
        my_draw_networkx_edge_labels(DG, pos, edge_labels=curved_edge_labels, rotate=False, rad = 0.2, font_size=6)
        nx.draw_networkx_edge_labels(DG, pos, edge_labels=straight_edge_labels, rotate=False, font_size=6)

        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig("weight_network.png")

    else:
        print("Make MultiGraph")



if __name__ == "__main__":
    typer.run(draw_network)