import csv
import math
from enum import Enum

import community
import igraph as ig
import leidenalg
import markov_clustering as mc
import networkx as nx
import scipy.sparse as sp
import typer
from infomap import Infomap


def split_oversized_communities(H, algorithm_fn, preferred_size, min_size, max_recursion=10, current_level=0, internal_force=False):
    partition = algorithm_fn(H) if not internal_force else algorithm_fn(H, preferred_size)
    communities = map_communities_to_directed_multigraph(partition, min_size)
    print(f"Partition found at level {current_level} for the network of {H.number_of_nodes()} nodes: {len(communities)} communities")

    final_partition = {}
    current_label = 0

    for nodes in communities.values():
        if len(nodes) > preferred_size and current_level < max_recursion:
            # Crear subgrafo inducido
            subgraph = H.subgraph(nodes)
            # Recursión
            sub_partition = split_oversized_communities(subgraph, algorithm_fn, preferred_size, min_size, max_recursion, current_level + 1, internal_force)
            # Añadir al particionado global
            for node, label in sub_partition.items():
                final_partition[node] = current_label + label
            current_label += max(sub_partition.values()) + 1
        else:
            for node in nodes:
                final_partition[node] = current_label
            current_label += 1

    return final_partition


def nx_to_igraph(nx_graph):
    """Converts a NetworkX graph to an igraph graph."""
    mapping = {node: idx for idx, node in enumerate(nx_graph.nodes())}
    edges = [(mapping[u], mapping[v]) for u, v in nx_graph.edges()]
    weights = [nx_graph[u][v]['weight'] for u, v in nx_graph.edges()]
    
    ig_graph = ig.Graph(edges=edges)
    ig_graph.vs['name'] = list(mapping.values())
    ig_graph.es['weight'] = weights

    return ig_graph


def apply_louvain(H):
    """Applies the Louvain algorithm to graph H."""
    return community.best_partition(H, weight='weight')

def apply_leiden(H):
    """Applies the Leiden algorithm to graph H."""
    ig_graph = nx_to_igraph(H)
    partition = leidenalg.find_partition(
        ig_graph,
        leidenalg.RBConfigurationVertexPartition,
        weights='weight'
    )
    return {list(H.nodes())[idx]: cid for cid, cluster in enumerate(partition) for idx in cluster}

def apply_infomap(H, preferred_size=None, trials=5):
    """Applies the Infomap algorithm to graph H. If a preferred_size is given, runs multiple trials and selects the one with nearest max community size."""
    
    if preferred_size is None:
        # Ejecución simple sin optimización de tamaño
        im = Infomap()
        im.add_networkx_graph(H, weight='weight')
        im.run()
        modules = im.get_modules()
        print(modules)
        return {im.get_name(node): group for node, group in modules.items()}
    
    # Ejecución múltiple si se busca controlar el tamaño máximo
    best_partition = None
    best_diff = float('inf')

    for _ in range(trials):
        im = Infomap()
        im.add_networkx_graph(H, weight='weight')
        im.run(preferred_number_of_modules=math.ceil(H.number_of_nodes() / preferred_size))
        modules = im.get_modules()
        
        clusters = {}
        for node, group in modules.items():
            clusters.setdefault(group, []).append(im.get_name(node))

        max_size = max(len(c) for c in clusters.values())
        diff = abs(max_size - preferred_size)
        
        if diff < best_diff:
            best_diff = diff
            best_partition = {n: g for g, nodes in clusters.items() for n in nodes}

    return best_partition


def apply_mcl(H, preferred_size=None, trials=[1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3]):
    """Applies the Markov Clustering algorithm.
    If preferred_size is given, selects the inflation value that minimizes max cluster size."""
    
    nodes = list(H.nodes())
    node_idx = {n: i for i, n in enumerate(nodes)}

    rows, cols, weights = [], [], []
    for u, v in H.edges():
        rows.append(node_idx[u])
        cols.append(node_idx[v])
        weights.append(H[u][v]['weight'])

    matrix = sp.coo_matrix((weights, (rows, cols)), shape=(len(nodes), len(nodes)))

    if preferred_size is None:
        # Ejecución directa sin tuning
        result = mc.run_mcl(matrix)
        clusters = mc.get_clusters(result)
        return {nodes[i]: cid for cid, c in enumerate(clusters) for i in c}

    # Búsqueda de mejor partición según tamaño máximo
    best_partition = None
    best_diff = float('inf')

    for infl in trials:
        result = mc.run_mcl(matrix, inflation=infl)
        clusters = mc.get_clusters(result)
        max_size = max(len(c) for c in clusters)
        diff = abs(max_size - preferred_size)

        if diff < best_diff:
            best_diff = diff
            best_partition = {nodes[i]: cid for cid, c in enumerate(clusters) for i in c}

    return best_partition


def create_weighted_undirected_graph(G):
    """Aggregates weights of directed multigraph edges into a single undirected graph."""
    H = nx.Graph()
    for u, v, _, data in G.edges(data=True, keys=True):
        if H.has_edge(u, v):
            H[u][v]['weight'] += data['weight']
        else:
            H.add_edge(u, v, weight=data['weight'])
    return H


def map_communities_to_directed_multigraph(partition, min_size=5):
    """Maps partition result into community groups."""
    communities = {}
    for node, community_id in partition.items():
        communities.setdefault(community_id, set()).add(node)
    return {cid: nodes for cid, nodes in communities.items() if len(nodes) >= min_size}


def apply_clustering_algorithm(H, algorithm, preferred_size, min_size):
    """Dispatches the clustering algorithm specified."""
    if algorithm == 'Louvain':
        return split_oversized_communities(H, apply_louvain, preferred_size, min_size)
    elif algorithm == 'Infomap':
        return split_oversized_communities(H, apply_infomap, preferred_size, min_size, internal_force=True)
    elif algorithm == 'Leiden':
        return split_oversized_communities(H, apply_leiden, preferred_size, min_size)
    elif algorithm == 'MCL':
        return split_oversized_communities(H, apply_mcl, preferred_size, min_size, internal_force=True)
    else:
        raise Exception("Algorithm not implemented")


def read_network_from_csv(file_path):
    """Reads a directed multigraph with weights from a CSV file."""
    G = nx.MultiDiGraph()
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for u, v, weight in reader:
            G.add_edge(u, v, weight=float(weight))
    return G


def write_community_results(communities, G, output_folder):
    """Writes each community's internal connections to a separate CSV file."""
    for community_id, nodes in communities.items():
        with open(f'{output_folder}/community_{community_id}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for u in nodes:
                for v in nodes:
                    if G.has_edge(u, v):
                        weight = G[u][v][0]['weight']
                        writer.writerow([u, v, weight])


def write_intercommunity_relations(G, communities, output_folder):
    """Writes all inter-community edges to a CSV file."""
    with open(f'{output_folder}/intermediate_relations.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for u, v, _, data in G.edges(data=True, keys=True):
            if not any(u in c and v in c for c in communities.values()):
                writer.writerow([u, v, data['weight']])


class Algorithm(str, Enum):
    Louvain = "Louvain"
    Infomap = "Infomap"
    Leiden = "Leiden"
    MCL = "MCL"


def cluster_network(
    confidence_list: str = typer.Option(..., help="Path of the CSV file with the confidence list to be clustered"),
    algorithm: Algorithm = typer.Option("Infomap", help="Clustering algorithm to apply"),
    preferred_size: int = typer.Option(100, help="Preferred number of nodes per community"),
    min_size: int = typer.Option(5, help="Minimum size of the communities"),
    output_folder: str = typer.Option(..., help="Output folder to write community files")
):
    """Main pipeline to read a network, apply community detection, and save results."""
    G = read_network_from_csv(confidence_list)
    H = create_weighted_undirected_graph(G)
    partition = apply_clustering_algorithm(H, algorithm.value, preferred_size, min_size)
    communities = map_communities_to_directed_multigraph(partition, min_size)
    write_community_results(communities, G, output_folder)
    write_intercommunity_relations(G, communities, output_folder)


if __name__ == "__main__":
    typer.run(cluster_network)