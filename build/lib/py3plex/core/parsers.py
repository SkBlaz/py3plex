## these are the parser methods
# Conventions:
# 1.) node types are given as "type"
# 2.) edge types are given as "type"
# 3.) node classes are given as "labels", e.g. "1;5;7" indicates the node is labeled as 1 5 and with 7th class
# 3.) edge classes are given as "labels", e.g. "1;5;7" indicates the edge is labeled as 1 5 and with 7th class

import networkx as nx
import itertools
import operator
import numpy as np
import scipy.io
from collections import defaultdict, Counter

def parse_gml(file_name,directed):
    H = nx.read_gml(file_name)
    if directed:
        H.to_directed()

    ## add labels
    return (H,None)

def parse_nx(nx_object,directed):
    return (nx_object,None)

def parse_matrix(file_name,directed):
    mat = scipy.io.loadmat(file_name)
    labels= mat['group']
    if directed:
        cn = nx.DiGraph()
        core_network= nx.from_scipy_sparse_matrix(mat['network'],create_using=cn)
    else:
        cn = nx.Graph()
        core_network= nx.from_scipy_sparse_matrix(mat['network'],create_using=cn)
    return(core_network,labels)

def parse_gpickle(file_name, directed):
    return (nx.read_gpickle(file_name),None)

def parse_gpickle_biomine(file_name,directed):

    ## convert the biomine
    input_graph = nx.read_gpickle(file_name)
    type_segments = defaultdict(list)
    for node in input_graph.nodes(data=True):
        type_segments[node[0].split("_")[0]].append(node[0])        

    for edge in input_graph.edges(data=True):
        edge[2]['type'] = edge[2]['key']
        
    networks = []
    labs = []
    inverse_mapping = {}

    ## assign node types
    for k,v in type_segments.items():
        for x in v:
            inverse_mapping[x] = k

    node_types = {}
    for gnode in input_graph.nodes(data=False):
        node_types[gnode] = inverse_mapping[gnode]

    for n in input_graph.nodes(data=True):
        n[1]['type'] = node_types[n[0]]

    return (input_graph,None)


def parse_gaf_to_uniprot_GO(gaf_mappings,filter_terms=None):
    uniGO = defaultdict(list)    
    with open(gaf_mappings) as im:
        for line in im:
            parts = line.split("\t")
            try:
                if "GO:" in parts[4]:
                    uniGO[parts[1]].append(parts[4]) ## GO and ref both added
                if "GO:" in parts[3]:
                    uniGO[parts[1]].append(parts[3])
            except:
                pass

    all_terms = list(itertools.chain(*uniGO.values()))
    if filter_terms is not None:
        sorted_d = sorted(Counter(all_terms).items(), key=operator.itemgetter(1),reverse=True)
        top_100 = [x[0] for x in sorted_d[0:filter_terms]]
        new_map = defaultdict(list)
        for k,v in uniGO.items():
            v = [x for x in v if x in top_100]
            new_map[k] = v        
        return new_map
    
    else:
        return uniGO

def parse_multi_edgelist(input_name,directed):

    if directed:
        G = nx.MultiDiGraph()
        
    else:
        G = nx.MultiGraph()
    
    with open(input_name) as IN:
        for line in IN:
            node_first,layer_first,node_second,layer_second,weight = line.strip().split()
            G.add_node(node_first,type=layer_first)
            G.add_node(node_second,type=layer_second)
            G.add_edge(node_first,node_second,weight=weight)
    return (G,None)

def parse_simple_edgelist(input_name,directed):

    if directed:
        G = nx.MultiDiGraph()
        
    else:
        G = nx.MultiGraph()
    
    with open(input_name) as IN:
        for line in IN:
            parts = line.strip().split()
            if len(parts) > 2:
                node_first,layer_first,weight = parts
            else:
                node_first,layer_first = parts
                weight = 1
            G.add_node(node_first)
            G.add_node(node_second)
            G.add_edge(node_first,node_second,weight=weight)
    return (G,None)

def parse_embedding(input_name):

    meta = None
    embedding_matrix = []
    embedding_indices = []
    with open(input_name) as IN:
        for line in IN:
            line = line.strip().split()
            if len(line) == 2:
                meta = line
            else:
                embedding_matrix.append(line[1:])
                embedding_indices.append(line[0])
    embedding_matrix = np.matrix(embedding_matrix)
    embedding_indices = np.array(embedding_indices)    
    return (embedding_matrix,embedding_indices)

## main parser method
def parse_network(input_name,f_type = "gml",directed=False,label_delimiter=None):
    if f_type == "gml":
        return parse_gml(input_name,directed)
    
    elif f_type == "nx":
        return parse_nx(input_name,directed)

    elif f_type == "sparse":
        return parse_matrix(input_name,directed)

    elif f_type == "gpickle_biomine":
        return parse_gpickle_biomine(input_name,directed)

    elif f_type == "gpickle":
        return parse_gpickle(input_name,directed)

    elif f_type == "multiedgelist":
        return parse_multi_edgelist(input_name,directed)

    elif f_type == "edgelist":
        return parse_simple_edgelist(input_name,directed)
                
if __name__ == "__main__":
    print ("Testing parser")
#    print (nx.info(parse_gml("../../datasets/imdb_gml.gml",f_type="gml",directed=False)))
#    print (nx.info(parse_network("../../datasets/epigenetics.gpickle",f_type="gpickle_biomine",directed=False)))
    #print (nx.info(parse_network("../../datasets/multiedgelist.txt",f_type="multiedgelist",directed=False)))

    parse_embedding("../../datasets/karate.emb")
