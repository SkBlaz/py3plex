## Compute many possible network statistics

import scipy.io
import networkx as nx
import pandas as pd

def core_network_statistics(G,labels=None,name="example"):
    rframe = pd.DataFrame(columns=["Name",
                                   "classes",
                                   "nodes",
                                   "edges",
                                   "degree",
                                   "diameter",
                                   "connected components",
                                   "clustering coefficient",
                                   "density",
                                   "flow_hierarchy"])
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
        
    if labels is not  None:
        number_of_classes = labels.shape[1]
    else:
        number_of_classes = None

    mean_degree = np.mean(nx.degree(G).values())
    diameter = nx.diameter(G)
    flow_hierarchy = nx.flow_hierarchy(G)
    
    point = {"Name": name,
             "classes":number_of_classes,
             "nodes":nodes,
             "edges":edges,
             "diameter":diameter,
             "degree":mean_degree,
             "flow hierarchy":flow_hierarchy,
             "connected components":cc,
             "clustering coefficient":clustering,
             "density":dx}
    rframe = rframe.append(point,ignore_index=True)
    return rframe
