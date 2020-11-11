# Compute many possible network statistics

import networkx as nx
import pandas as pd
import numpy as np
from operator import itemgetter


def identify_n_hubs(G, top_n=100, node_type=None):

    if node_type is not None:
        target_nodes = []
        for n in G.nodes(data=True):
            try:
                if n[0][1] == node_type:
                    target_nodes.append(n[0])
            except:
                pass
    else:
        target_nodes = G.nodes()

    degree_dict = {x: G.degree(x) for x in target_nodes}
    top_n_id = {
        x[0]: x[1]
        for e, x in enumerate(
            sorted(degree_dict.items(), key=itemgetter(1), reverse=True))
        if e < top_n
    }
    return top_n_id


def core_network_statistics(G, labels=None, name="example"):
    rframe = pd.DataFrame(columns=[
        "Name", "classes", "nodes", "edges", "degree", "diameter",
        "connected components", "clustering coefficient", "density",
        "flow_hierarchy"
    ])
    nodes = len(G.nodes())
    edges = len(G.edges())
    cc = len(list(nx.connected_components(G.to_undirected())))

    try:
        cc = nx.average_clustering(G.to_undirected())
    except:
        cc = None

    try:
        dx = nx.density(G)
    except:
        dx = None

    clustering = None

    if labels is not None:
        number_of_classes = labels.shape[1]
    else:
        number_of_classes = None

    node_degree_vector = list(dict(nx.degree(G)).values())
    mean_degree = np.mean(node_degree_vector)

    try:
        diameter = nx.diameter(G)
    except:
        diameter = "intractable"

    try:
        flow_hierarchy = nx.flow_hierarchy(G)
    except:
        flow_hierarchy = "intractable"

    point = {
        "Name": name,
        "classes": number_of_classes,
        "nodes": nodes,
        "edges": edges,
        "diameter": diameter,
        "degree": mean_degree,
        "flow hierarchy": flow_hierarchy,
        "connected components": cc,
        "clustering coefficient": clustering,
        "density": dx
    }
    rframe = rframe.append(point, ignore_index=True)
    return rframe
