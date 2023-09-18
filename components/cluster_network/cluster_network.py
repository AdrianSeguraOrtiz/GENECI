import networkx as nx
import community
from infomap import Infomap
from enum import Enum
import csv
import math
import typer

def create_weighted_undirected_graph(G):
    H = nx.Graph()
    for u, v, key, data in G.edges(data=True, keys=True):
        if H.has_edge(u, v):
            H[u][v]['weight'] += data['weight']
        else:
            H.add_edge(u, v, weight=data['weight'])
    return H

def map_communities_to_directed_multigraph(partition):
    communities = {}
    for node, community_id in partition.items():
        if community_id in communities:
            communities[community_id].add(node)
        else:
            communities[community_id] = {node}
    return communities

def apply_clustering_algorithm(H, algorithm):
    if algorithm == 'louvain':
        partition = community.best_partition(H, weight='weight')
    elif algorithm == 'infomap':
        im = Infomap()
        im.add_networkx_graph(H, weight="weight")
        im.run(preferred_number_of_modules= math.ceil(H.number_of_nodes()/200))
        modules = im.get_modules()
        partition = {}
        for node, group in modules.items():
            partition[im.get_name(node)] = group
    else:
        raise Exception("Algorithm not implemented")
    return partition

def read_network_from_csv(file_path):
    G = nx.MultiDiGraph()
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            u, v, weight = row
            G.add_edge(u, v, weight=float(weight))
    return G

def write_community_results(communities, G, output_folder):
    for community_id, nodes in communities.items():
        filename = f'./{output_folder}/comunidad_{community_id}.csv'
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            for u in nodes:
                for v in nodes:
                    if G.has_edge(u, v):
                        weight = G[u][v][0]['weight']
                        writer.writerow([u, v, weight])

def write_intercommunity_relations(G, communities, output_folder):
    with open(f'./{output_folder}/relaciones_intercomunitarias.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for u, v, key, data in G.edges(data=True, keys=True):
            in_community = any(u in nodes and v in nodes for nodes in communities.values())
            if not in_community:
                writer.writerow([u, v, data['weight']])

class Algorithm(str, Enum):
    louvain = "louvain"
    infomap = "infomap"

def cluster_network(
    confidence_list: str = typer.Option(
        ..., help="Path of the CSV file with the confidence list to be clustering"
    ),
    algorithm: Algorithm = typer.Option("infomap", help="Clustering algorithm"),
    output_folder: str = typer.Option(..., help="Path to output folder"),
):

    # Leer la descripción de la red desde el archivo CSV de entrada
    G = read_network_from_csv(confidence_list)

    # Convertir multigrafo dirigido ponderado en grafo no dirigido ponderado
    H = create_weighted_undirected_graph(G)

    # Ejecutar el algoritmo de Louvain adaptado para multigrafos ponderados dirigidos
    partition = apply_clustering_algorithm(H, 'infomap')

    # Obtener comunidades
    communities = map_communities_to_directed_multigraph(partition)

    # Escribir los resultados en archivos CSV separados para las comunidades
    write_community_results(communities, G, output_folder)

    # Escribir las relaciones intercomunitarias en un archivo CSV
    write_intercommunity_relations(G, communities, output_folder)


if __name__ == "__main__":
    typer.run(cluster_network)
